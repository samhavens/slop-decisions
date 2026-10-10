"""Verify the frozen study and recompute every calibration result, without API calls."""

import argparse
import json
import runpy
import tempfile
from pathlib import Path

from verify_reports import verify

from slop_decisions.calibration import diagnostics, fit_thresholds, load_cases, measure
from slop_decisions.calibration_study import read_json, read_run, validate
from slop_decisions.context import digest
from slop_decisions.dataset import read_jsonl

ROOT = Path("reports/calibration-2026-10-10")


def summary(root=ROOT):
    profile = read_json(root / "profile.json")
    chosen = profile["selection"]
    result = {"selection": {k: chosen[k] for k in ["context_threshold", "threshold", "policy"]}}
    usage, latency, requests = 0, 0, 0
    for split in ("calibration", "holdout", "seed-regression"):
        if split == "seed-regression":
            experiment = read_json(root / split / "experiment.json")
            cases = [
                dict(r, expected="defect" if r["label"] else "clean") for r in experiment["labels"]
            ]
            rows = read_jsonl(root / split / "predictions.jsonl")
        else:
            run, rows = read_run(root / split)
            cases = run["cases"]
        result[split] = {
            "candidate": diagnostics(cases, rows, chosen["context_threshold"], chosen["threshold"]),
            "baseline": measure(cases, rows, 0.8, 0.8),
            "refusals": sum(r["result"].get("reason") == "provider_refusal" for r in rows),
            "input_tokens": sum(r["usage"].get("input_tokens", 0) for r in rows),
            "latency_seconds": round(sum(r["latency_seconds"] for r in rows), 4),
        }
        usage += result[split]["input_tokens"]
        latency += result[split]["latency_seconds"]
        requests += sum(r["attempts"] for r in rows)
    result["total"] = {
        "requests": requests,
        "input_tokens": usage,
        "latency_seconds": round(latency, 4),
        "estimated_cost_usd": usage * 0.1 / 1_000_000,
        "cost_basis": (
            "Decisions list price, $0.10 per million input tokens; estimate, not billed cost."
        ),
        "pricing_source": "https://developers.openai.com/api/docs/guides/decisions",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path(".cache/slop-decisions/sources"))
    args = parser.parse_args()
    cases = load_cases(Path("calibration/cases.jsonl"))
    authored = runpy.run_path("calibration/build_suite.py")["CASES"]
    assert cases == authored
    assert read_json(ROOT / "witnesses.json")["suite_hash"] == digest(cases)
    profile = read_json(ROOT / "profile.json")
    for split in ("calibration", "holdout"):
        run, rows = read_run(ROOT / split)
        assert run["suite_hash"] == digest(cases)
        assert run["cases"] == [c for c in cases if c["split"] == split]
        assert len(rows) == len(run["cases"])
        if split == "calibration":
            assert profile["selection"] == fit_thresholds(run["cases"], rows)
            assert profile["calibration_run_id"] == run["run_id"]
            assert profile["predictions_hash"] == digest(rows)
            assert profile["contract"] == run["contract"]
    with tempfile.TemporaryDirectory() as tmp:
        actual = validate(ROOT / "holdout", ROOT / "profile.json", Path(tmp) / "validation.json")
        assert actual == read_json(ROOT / "validation.json")
    verify(ROOT / "seed-regression", args.cache)
    assert summary() == read_json(ROOT / "summary.json")
    print(
        json.dumps(
            {
                "verified": True,
                "authored_cases": len(cases),
                "profile_accepted": actual["accepted"],
                "total": summary()["total"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
