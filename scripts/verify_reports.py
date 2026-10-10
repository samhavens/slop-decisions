"""Verify published request fingerprints and scores without making model calls."""

import argparse
import copy
import json
from pathlib import Path

from slop_decisions.context import digest
from slop_decisions.dataset import packet_for, read_jsonl
from slop_decisions.evaluation import score, sweep


def verify(directory: Path, cache: Path):
    meta = json.loads((directory / "run.json").read_text())
    experiment = json.loads((directory / "experiment.json").read_text())
    predictions = read_jsonl(directory / "predictions.jsonl")
    requests, jobs = [], []
    for target in experiment["targets"]:
        packet = packet_for(target, experiment["sources"], cache, meta["mode"])
        body = copy.deepcopy(experiment["request_templates"][target["dimension"]])
        evidence = json.dumps(packet, ensure_ascii=False, allow_nan=False)
        if "questions" in body:
            body["input"] = evidence
        else:
            body["input" if "input" in body else "messages"][1]["content"] = evidence
        requests.append(body)
        jobs.append({"target": target, "packet": packet})
    plan = digest(
        {
            "version": meta["version"],
            "config": meta["config"],
            "mode": meta["mode"],
            "requests": requests,
            "jobs": jobs,
        }
    )
    assert digest({"request_plan": plan, "labels": experiment["labels"]}) == meta["run_id"]
    assert digest(experiment["labels"]) == meta["dataset_label_hash"]
    assert digest(experiment["rubrics"]) == meta["rubrics_hash"]
    assert len(predictions) == len(jobs)
    packets = {j["target"]["case_id"]: digest(j["packet"]) for j in jobs}
    assert all(r["packet_hash"] == packets[r["case_id"]] for r in predictions)
    actual = score(experiment["labels"], predictions, meta["threshold"])
    recorded = json.loads((directory / "report.json").read_text())
    for key, value in actual.items():
        if key == "tracks":
            # Earlier reports predate track summaries; the truth labels are unchanged.
            continue
        assert recorded[key] == value, (directory.name, key)
    tracks = {t["case_id"]: t["track"] for t in experiment["targets"]}
    labels = [dict(r, track=tracks[r["case_id"]]) for r in experiment["labels"]]
    thresholds = json.loads((directory / "thresholds.json").read_text())
    assert thresholds == sweep(labels, predictions, [r["threshold"] for r in thresholds["reports"]])
    return {"run": directory.name, "targets": len(jobs), "verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=Path("reports/2026-10-10"))
    parser.add_argument("--cache", type=Path, default=Path(".cache/slop-decisions/sources"))
    args = parser.parse_args()
    directories = sorted(p.parent for p in args.reports.glob("*/run.json"))
    if not directories:
        parser.error("no saved runs found")
    print(json.dumps({"runs": [verify(p, args.cache) for p in directories]}, indent=2))


if __name__ == "__main__":
    main()
