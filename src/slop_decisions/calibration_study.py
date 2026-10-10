"""Collect, fit, and validate threshold studies with frozen source packets."""

import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from slop_decisions.calibration import (
    POLICY,
    diagnostics,
    fit_thresholds,
    indexed,
    load_cases,
    measure,
)
from slop_decisions.context import digest
from slop_decisions.dataset import read_jsonl
from slop_decisions.profiles import accepted, contract
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def read_json(path):
    return json.loads(path.read_text())


def read_run(directory):
    run = read_json(directory / "run.json")
    recorded_id = run["run_id"]
    if digest({k: v for k, v in run.items() if k != "run_id"}) != recorded_id:
        raise ValueError("run fingerprint mismatch")
    cases = run["cases"]
    rows = read_jsonl(directory / "predictions.jsonl")
    indexed(cases, rows)
    gold = {c["case_id"]: c for c in cases}
    for row in rows:
        case = gold[row["case_id"]]
        if row["run_id"] != recorded_id or row["packet_hash"] != digest(case["packet"]):
            raise ValueError("prediction fingerprint mismatch")
        if row["dimension"] != case["dimension"]:
            raise ValueError("prediction dimension mismatch")
    return run, rows


def collect(cases_path, split, output, config, *, profile_path=None, stop_after=None):
    if config.transport_api != "decisions":
        raise ValueError("two-predicate calibration requires the Decisions transport")
    if stop_after is not None and stop_after < 1:
        raise ValueError("--stop-after must be positive")
    cases = load_cases(cases_path)
    bank = load_rubrics()
    if any(c["dimension"] not in bank for c in cases):
        raise ValueError("unknown check in suite")
    bank = {name: bank[name] for name in {c["dimension"] for c in cases}}
    current_contract = contract(config, bank)
    frozen = None
    if split == "holdout":
        if profile_path is None:
            raise ValueError("holdout collection requires a frozen --profile")
        frozen = read_json(profile_path)
        if frozen["suite_hash"] != digest(cases) or frozen["contract"] != current_contract:
            raise ValueError("profile does not match suite or request contract")
    selected = [c for c in cases if c["split"] == split]
    if not selected:
        raise ValueError("empty split")
    plan = {
        "suite_hash": digest(cases),
        "cases": selected,
        "contract": current_contract,
        "config": asdict(config),
        "profile_hash": digest(frozen) if frozen else None,
    }
    existing = []
    if output.exists():
        run, existing = read_run(output)
        recorded_config = {
            **run["config"],
            "api": run["config"]["api"] or run["contract"]["api"],
        }
        requested_config = {**plan["config"], "api": config.transport_api}
        if recorded_config != requested_config or any(
            run[k] != v for k, v in plan.items() if k != "config"
        ):
            raise ValueError("resume configuration, cases, or profile mismatch")
    else:
        output.mkdir(parents=True)
        run = {**plan, "started_at": datetime.now(UTC).isoformat()}
        run["run_id"] = digest(run)
        write_json(output / "run.json", run)
        (output / "predictions.jsonl").touch()
    pending = [c for c in selected if c["case_id"] not in {r["case_id"] for r in existing}]
    if stop_after is not None:
        pending = pending[:stop_after]
    if pending:
        failures = 0
        with Provider(config) as client, (output / "predictions.jsonl").open("a") as handle:
            for case in pending:
                observation = client.assess(case["packet"], bank[case["dimension"]])
                row = {
                    "case_id": case["case_id"],
                    "dimension": case["dimension"],
                    "packet_hash": digest(case["packet"]),
                    "run_id": run["run_id"],
                    **observation,
                }
                handle.write(json.dumps(row, allow_nan=False) + "\n")
                handle.flush()
                existing.append(row)
                failed = (
                    "decision_scores" not in row
                    and row["result"].get("reason") != "provider_refusal"
                )
                failures = failures + 1 if failed else 0
                print(f"[{len(existing)}/{len(selected)}] {case['case_id']}", file=sys.stderr)
                if failures >= 2:
                    raise ValueError("stopped after two consecutive request failures")
    return {"completed": len(existing), "planned": len(selected), "run_id": run["run_id"]}


def fit(directory, output):
    if output.exists():
        raise ValueError("profile exists; choose a new path to preserve the frozen selection")
    run, rows = read_run(directory)
    result = fit_thresholds(run["cases"], rows)
    profile = {
        "contract": run["contract"],
        "suite_hash": run["suite_hash"],
        "calibration_run_id": run["run_id"],
        "predictions_hash": digest(rows),
        "selection": result,
    }
    write_json(output, profile)
    return {
        "profile_hash": digest(profile),
        "context_threshold": result["context_threshold"],
        "threshold": result["threshold"],
        "calibration": result["calibration"],
    }


def validate(directory, profile_path, output):
    protected = [profile_path, directory / "run.json", directory / "predictions.jsonl"]
    if output.resolve() in {p.resolve() for p in protected}:
        raise ValueError("validation must not overwrite the frozen profile or run evidence")
    profile = read_json(profile_path)
    run, rows = read_run(directory)
    if run["profile_hash"] != digest(profile) or run["contract"] != profile["contract"]:
        raise ValueError("holdout was not collected against this frozen profile")
    if run["suite_hash"] != profile["suite_hash"]:
        raise ValueError("holdout suite mismatch")
    if any(c["split"] != "holdout" for c in run["cases"]):
        raise ValueError("validation requires holdout only")
    if len(rows) != len(run["cases"]):
        raise ValueError("validation requires a complete run")
    if {c["expected"] for c in run["cases"]} != {"defect", "clean", "unassessable"}:
        raise ValueError("validation requires all three labels")
    selection = profile["selection"]
    report = diagnostics(run["cases"], rows, selection["context_threshold"], selection["threshold"])
    baseline = measure(run["cases"], rows, 0.8, 0.8)
    result = {
        "profile_hash": digest(profile),
        "holdout_run_id": run["run_id"],
        "predictions_hash": digest(rows),
        "accepted": accepted(report, baseline, POLICY),
        "profile": profile,
        "holdout": report,
        "baseline": baseline,
    }
    write_json(output, result)
    return result


def parser():
    from slop_decisions.cli import Parser, common

    root = Parser(description=__doc__)
    common(root, default="toon")
    commands = root.add_subparsers(dest="command", parser_class=Parser)
    p = commands.add_parser(
        "collect",
        help="Collect raw scores; resume exactly matching runs",
        epilog="Example: slop-calibrate collect --cases cases.jsonl --split calibration "
        "--model gpt-6-luna --out runs/calibration --stop-after 3",
    )
    common(p)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--split", choices=["calibration", "holdout"], required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--profile", type=Path)
    p.add_argument("--stop-after", type=int, help="Bound new calls for a protocol pilot")
    p = commands.add_parser(
        "fit",
        help="Select gates using only a complete calibration run",
        epilog="Example: slop-calibrate fit runs/calibration --out runs/profile.json",
    )
    common(p)
    p.add_argument("run", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--full", action="store_true", help="Include all fit counts on stdout")
    p = commands.add_parser(
        "validate",
        help="Score the frozen profile on untouched holdout cases",
        epilog="Example: slop-calibrate validate runs/holdout --profile runs/profile.json "
        "--out runs/validation.json",
    )
    common(p)
    p.add_argument("run", type=Path)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--full", action="store_true", help="Include all results and the profile on stdout"
    )
    return root


def main():
    from slop_decisions.output import emit

    args = None
    try:
        args = parser().parse_args()
        if args.command is None:
            result = {
                "bin": str(Path(sys.argv[0]).resolve()).replace(str(Path.home()), "~"),
                "description": "Fit and test Decisions thresholds on separate labeled source sets.",
                "checks": len(load_rubrics()),
                "policy": POLICY,
                "help": [
                    "slop-calibrate collect --help",
                    "slop-calibrate fit --help",
                    "slop-calibrate validate --help",
                ],
            }
        elif args.command == "collect":
            result = collect(
                args.cases,
                args.split,
                args.out,
                ProviderConfig(provider="openai", model=args.model, api="decisions", retries=0),
                profile_path=args.profile,
                stop_after=args.stop_after,
            )
        elif args.command == "fit":
            result = fit(args.run, args.out)
        else:
            result = validate(args.run, args.profile, args.out)
        code = 3 if result.get("accepted") is False else 0
        if args.command == "validate" and not args.full:
            report = result["holdout"]
            result = {
                "accepted": result["accepted"],
                "context_threshold": report["context_threshold"],
                "threshold": report["threshold"],
                "known_coverage": report["known_coverage"],
                "unsafe_context_rate": report["unsafe_context_rate"],
                "true_warnings": report["true_warnings"],
                "false_warnings": report["false_warnings"],
                "missed_defects": report["missed_defects"],
                "out": str(args.out),
            }
        elif args.command == "fit" and not args.full:
            result = {k: v for k, v in result.items() if k != "calibration"} | {
                "out": str(args.out)
            }
        emit(result, args.format)
        return code
    except (ValueError, OSError, KeyError, TypeError) as error:
        command = args.command if args and args.command else "collect"
        emit(
            {
                "error": str(error),
                "help": f"slop-calibrate {command} --help",
            },
            args.format if args else ("json" if "json" in sys.argv else "toon"),
        )
        return 2
    except KeyboardInterrupt:
        emit({"error": "interrupted; rerun the same collect command to resume"})
        return 130


if __name__ == "__main__":
    sys.exit(main())
