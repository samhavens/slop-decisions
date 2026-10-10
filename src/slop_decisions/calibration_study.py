"""Collect, fit, and validate threshold studies with frozen source packets."""

import argparse
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
from slop_decisions.providers import Provider, ProviderConfig, build_request
from slop_decisions.rubrics import load_rubrics


def contract(config, rubrics, mode="file", variant="examples"):
    return {
        "provider": config.provider,
        "api": config.transport_api,
        "base_url": config.url,
        "context": mode,
        "templates": {
            name: build_request(config, {"source_packet": "REPLACE_WITH_PACKET"}, rubric, variant)
            for name, rubric in sorted(rubrics.items())
        },
    }


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
        if any(run[k] != v for k, v in plan.items()):
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
                failures = failures + 1 if "decision_scores" not in row else 0
                print(f"[{len(existing)}/{len(selected)}] {case['case_id']}", file=sys.stderr)
                if failures >= 2:
                    raise ValueError("stopped after two consecutive requests without raw scores")
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
    selection = profile["selection"]
    report = diagnostics(run["cases"], rows, selection["context_threshold"], selection["threshold"])
    baseline = measure(run["cases"], rows, 0.8, 0.8)
    accepted = (
        report["known_coverage"] >= POLICY["min_known_coverage"]
        and report["unsafe_context_rate"] <= POLICY["max_unsafe_context_rate"]
        and report["review_cost"] <= baseline["review_cost"]
    )
    result = {
        "profile_hash": digest(profile),
        "holdout_run_id": run["run_id"],
        "predictions_hash": digest(rows),
        "accepted": accepted,
        "holdout": report,
        "baseline": baseline,
    }
    write_json(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("collect", help="Collect raw scores; resume exactly matching runs")
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--split", choices=["calibration", "holdout"], required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--profile", type=Path)
    p.add_argument("--stop-after", type=int, help="Bound new calls for a protocol pilot")
    p = commands.add_parser("fit", help="Select gates using only a complete calibration run")
    p.add_argument("run", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p = commands.add_parser("validate", help="Score the frozen profile on untouched holdout cases")
    p.add_argument("run", type=Path)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            result = collect(
                args.cases,
                args.split,
                args.out,
                ProviderConfig(provider="openai", model=args.model, retries=0),
                profile_path=args.profile,
                stop_after=args.stop_after,
            )
        elif args.command == "fit":
            result = fit(args.run, args.out)
        else:
            result = validate(args.run, args.profile, args.out)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
