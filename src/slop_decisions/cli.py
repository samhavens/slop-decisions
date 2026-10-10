import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import httpx

from slop_decisions import __version__
from slop_decisions.context import build_packet
from slop_decisions.dataset import fetch_sources, load_dataset, packet_for, read_jsonl
from slop_decisions.evaluation import score, sweep
from slop_decisions.output import emit
from slop_decisions.profiles import thresholds
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics
from slop_decisions.runner import run_eval


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def common(parser, *, default=argparse.SUPPRESS):
    parser.add_argument("--format", choices=["toon", "json"], default=default)


def model_options(parser):
    parser.add_argument("--provider", choices=["openai", "openrouter", "local"], default="local")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api", choices=["decisions", "responses", "chat"])
    parser.add_argument("--base-url", help="API root including /v1; defaults to provider endpoint")
    parser.add_argument(
        "--key-env", help="Name of environment variable; never put a key in arguments"
    )
    parser.add_argument("--json-mode", choices=["schema", "object", "none"], default="schema")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Omitted by default for compatibility with reasoning models",
    )
    parser.add_argument(
        "--context-threshold",
        type=float,
        help="Override the Decisions context gate (fallback: 0.8, uncalibrated)",
    )
    parser.add_argument("--context", choices=["target", "window", "file"], default="file")
    parser.add_argument("--max-chars", type=int, default=100_000)
    parser.add_argument("--prompt", choices=["minimal", "examples"], default="examples")
    parser.add_argument(
        "--rubrics", type=Path, help="JSON bank for controlled prompt/example experiments"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        help="Override the warning threshold (fallback: 0.8, uncalibrated)",
    )
    parser.add_argument(
        "--calibration", type=Path, help="Validation JSON from slop-calibrate; must pass and match"
    )


def dataset_options(parser):
    parser.add_argument("--dataset", type=Path, help="Directory containing sources/targets/labels")
    parser.add_argument("--cache", type=Path, default=Path(".cache/slop-decisions/sources"))


def config(args):
    return ProviderConfig(
        **{
            name: getattr(args, name)
            for name in (
                "provider",
                "model",
                "api",
                "base_url",
                "key_env",
                "json_mode",
                "timeout",
                "retries",
                "max_tokens",
                "temperature",
            )
        },
        context_threshold=args.context_threshold if args.context_threshold is not None else 0.8,
    )


def model_policy(args, bank):
    conf = config(args)
    validation = json.loads(args.calibration.read_text()) if args.calibration else None
    policy = thresholds(
        conf,
        bank,
        args.context,
        args.prompt,
        validation=validation,
        context=args.context_threshold,
        warning=args.threshold,
    )
    return replace(conf, context_threshold=policy["context_threshold"]), policy


def parser():
    root = Parser(description="Named semantic code checks and pinned-source evaluations.")
    root.add_argument("--version", action="version", version=__version__)
    common(root, default="toon")
    commands = root.add_subparsers(dest="command", parser_class=Parser)
    p = commands.add_parser("checks", help="List narrow check predicates")
    common(p)
    p.add_argument("--full", action="store_true", help="Include all rubric fields")
    p = commands.add_parser(
        "check",
        help="Assess explicit files/spans; no code is executed",
        epilog="Examples: slop-decisions check lib/a.ex --model qwen3:8b; "
        "slop-decisions check lib/a.ex --lines 20:45 --model gpt-6-luna "
        "--provider openai --dimension success_shaped_failure",
    )
    common(p)
    model_options(p)
    p.add_argument("files", nargs="+", help="Source paths relative to --root")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--lines", help="Inclusive start:end; requires exactly one input file")
    p.add_argument(
        "--related", action="append", default=[], help="Explicit contract/callee/helper file"
    )
    p.add_argument(
        "--dimension", action="append", help="Repeat to select checks; defaults to three"
    )
    p.add_argument(
        "--max-checks", type=int, default=20, help="Fail before requests if plan exceeds limit"
    )
    p.add_argument("--dry-run", action="store_true", help="Show source packets without model calls")
    p = commands.add_parser("fetch", help="Fetch and hash-check pinned public source files")
    common(p)
    dataset_options(p)
    p = commands.add_parser("dataset", help="Validate and summarize dataset provenance")
    common(p)
    dataset_options(p)
    p = commands.add_parser("packet", help="Inspect the exact source-only input for one target")
    common(p)
    dataset_options(p)
    p.add_argument("case_id")
    p.add_argument("--context", choices=["target", "window", "file"], default="file")
    p = commands.add_parser(
        "eval",
        help="Run a reproducible evaluation and save JSONL",
        epilog="Examples: slop-decisions eval --model qwen3:8b --out runs/local; "
        "slop-decisions eval --provider openai --model gpt-6-luna --out runs/oai",
    )
    common(p)
    dataset_options(p)
    model_options(p)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", choices=["dev", "calibration", "holdout"], default="dev")
    p.add_argument("--track", choices=["semantic", "preference", "deterministic_baseline"])
    p.add_argument("--dimension", action="append")
    p.add_argument("--limit", type=int, help="Bound the number of targets before requests")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    for name in ("score", "sweep"):
        p = commands.add_parser(
            name,
            help="Score saved predictions"
            if name == "score"
            else "Sweep thresholds on dev/calibration without new model calls",
        )
        common(p)
        dataset_options(p)
        p.add_argument("predictions", type=Path)
        p.add_argument("--split", choices=["dev", "calibration", "holdout"], default="dev")
        p.add_argument("--case-id", action="append", help="Explicit bounded-pilot target set")
        if name == "score":
            p.add_argument("--threshold", type=float, default=0.8)
        else:
            p.add_argument("--thresholds", default="0.5,0.65,0.8,0.9,0.95")
    return root


def run(args):
    if args.command is None:
        sources, targets, labels = load_dataset()
        return {
            "bin": str(Path(sys.argv[0]).resolve()).replace(str(Path.home()), "~"),
            "description": "Check semantic code defects with local or hosted models.",
            "checks": len(load_rubrics()),
            "development_targets": len(targets),
            "help": ["slop-decisions checks", "slop-decisions fetch", "slop-decisions eval --help"],
        }, 0
    if args.command == "checks":
        rubrics = load_rubrics()
        return {
            "checks": list(rubrics.values())
            if args.full
            else [
                {"name": r["name"], "severity": r["severity"], "predicate": r["predicate"]}
                for r in rubrics.values()
            ]
        }, 0
    if args.command == "check":
        bank = load_rubrics(args.rubrics)
        names = list(
            dict.fromkeys(
                args.dimension
                or ["success_shaped_failure", "test_claim_gap", "avoidable_repeated_traversal"]
            )
        )
        if any(n not in bank for n in names):
            raise ValueError("unknown dimension; run slop-decisions checks")
        conf, policy = model_policy(args, {name: bank[name] for name in names})
        if len(args.files) * len(names) > args.max_checks:
            raise ValueError(
                "plan exceeds --max-checks; narrow inputs or explicitly raise the limit"
            )
        if args.lines and len(args.files) != 1:
            raise ValueError("--lines requires exactly one input file")
        packets = []
        for file in args.files:
            if args.lines:
                start, end = map(int, args.lines.split(":"))
            else:
                from slop_decisions.context import safe_path

                start, end = 1, len(safe_path(args.root, file).read_text().splitlines())
            packets.append(
                build_packet(
                    args.root,
                    file,
                    start,
                    end,
                    mode=args.context,
                    related=tuple(args.related),
                    max_chars=args.max_chars,
                )
            )
        if args.dry_run:
            return {
                "checks": len(packets) * len(names),
                "packets": packets,
                "threshold_policy": policy,
            }, 0
        results = []
        with Provider(conf) as client:
            for packet in packets:
                for name in names:
                    observation = client.assess(packet, bank[name], args.prompt)
                    results.append({"target": packet["target"], "dimension": name, **observation})
        unassessed = sum(r["result"]["status"] == "unassessed" for r in results)
        warnings = sum(
            r["result"]["status"] == "assessed"
            and r["result"]["probability"] >= policy["threshold"]
            for r in results
        )
        return {
            "warnings": warnings,
            "unassessed": unassessed,
            "threshold": policy["threshold"],
            "threshold_policy": policy,
            "results": results,
        }, 1 if unassessed else (3 if warnings else 0)
    sources, targets, labels = load_dataset(args.dataset)
    if args.command == "fetch":
        return fetch_sources(sources, args.cache), 0
    if args.command == "dataset":
        return {
            "sources": len(sources),
            "targets": len(targets),
            "positives": sum(r["label"] for r in labels),
            "negatives": sum(not r["label"] for r in labels),
            "pairs": len({r["pair_id"] for r in labels if r.get("pair_id")}),
            "splits": sorted({t["split"] for t in targets}),
            "label_statuses": sorted({r["status"] for r in labels}),
            "note": "Development candidates; no locked holdout or deployment precision claim.",
        }, 0
    if args.command == "packet":
        matches = [t for t in targets if t["case_id"] == args.case_id]
        if not matches:
            raise ValueError("unknown case ID")
        return packet_for(matches[0], sources, args.cache, args.context), 0
    if args.command == "eval":
        bank = load_rubrics(args.rubrics)
        targets = [
            t
            for t in targets
            if t["split"] == args.split
            and (not args.track or t["track"] == args.track)
            and (not args.dimension or t["dimension"] in args.dimension)
        ]
        if args.limit is not None:
            if args.limit < 1:
                raise ValueError("--limit must be positive")
            targets = targets[: args.limit]
        if not targets:
            raise ValueError("no targets match these filters")
        conf, policy = model_policy(
            args, {name: bank[name] for name in {t["dimension"] for t in targets}}
        )
        ids = {t["case_id"] for t in targets}
        labels = [r for r in labels if r["case_id"] in ids]
        report = run_eval(
            targets,
            labels,
            sources,
            args.cache,
            bank,
            conf,
            args.out,
            mode=args.context,
            variant=args.prompt,
            max_chars=args.max_chars,
            threshold=policy["threshold"],
            threshold_policy=policy,
            resume=args.resume,
            dry_run=args.dry_run,
        )
        return report, 1 if report.get("unassessed", report.get("context_errors", 0)) else 0
    labels = [
        r
        for r in labels
        if r["split"] == args.split and (not args.case_id or r["case_id"] in args.case_id)
    ]
    predictions = read_jsonl(args.predictions)
    if args.command == "score":
        return score(labels, predictions, args.threshold), 0
    return sweep(labels, predictions, [float(t) for t in args.thresholds.split(",")]), 0


def main():
    args = None
    try:
        args = parser().parse_args()
        value, code = run(args)
        emit(value, args.format)
        return code
    except (ValueError, OSError, KeyError, TypeError, httpx.HTTPError) as error:
        # Never include HTTP request objects or provider bodies in CLI errors.
        message = "network request failed" if isinstance(error, httpx.HTTPError) else str(error)
        emit(
            {"error": message, "help": "slop-decisions --help"},
            args.format if args else ("json" if "json" in sys.argv else "toon"),
        )
        return 2
    except KeyboardInterrupt:
        emit({"error": "interrupted; completed evaluation rows are saved for --resume"})
        return 130


if __name__ == "__main__":
    sys.exit(main())
