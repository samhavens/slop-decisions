import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from slop_decisions import __version__
from slop_decisions.context import digest
from slop_decisions.dataset import packet_for, read_jsonl
from slop_decisions.evaluation import score
from slop_decisions.providers import Provider, ProviderConfig, build_request, unknown


def plan_run(targets, sources, cache, rubrics, config, mode, variant, max_chars):
    # Prepare every packet before the first billable call; fail closed per target.
    jobs = []
    for target in targets:
        rubric = rubrics[target["dimension"]]
        try:
            packet = packet_for(target, sources, cache, mode, max_chars)
            error = None
        except (OSError, ValueError):
            packet = None
            error = "missing_invalid_or_oversize_context"
        jobs.append({"target": target, "packet": packet, "context_error": error, "rubric": rubric})
    fingerprint = digest(
        {
            "version": __version__,
            "config": asdict(config),
            "mode": mode,
            "requests": [
                build_request(config, j["packet"], j["rubric"], variant)
                for j in jobs
                if j["packet"] is not None
            ],
            "jobs": [{"target": j["target"], "packet": j["packet"]} for j in jobs],
        }
    )
    return jobs, fingerprint


def run_eval(
    targets: list[dict],
    labels: list[dict],
    sources: list[dict],
    cache: Path,
    rubrics: dict,
    config: ProviderConfig,
    output: Path,
    *,
    mode="file",
    variant="examples",
    max_chars=100_000,
    threshold=0.8,
    resume=False,
    dry_run=False,
) -> dict:
    target_keys = [(t["case_id"], t["dimension"]) for t in targets]
    if len(target_keys) != len(set(target_keys)) or set(target_keys) != {
        (r["case_id"], r["dimension"]) for r in labels
    }:
        raise ValueError("targets must be unique and match the selected labels exactly")
    score(labels, [], threshold)  # Validate the scoring contract before any paid calls.
    jobs, fingerprint = plan_run(targets, sources, cache, rubrics, config, mode, variant, max_chars)
    fingerprint = digest({"request_plan": fingerprint, "labels": labels})
    if dry_run:
        return {
            "targets": len(jobs),
            "ready": sum(j["packet"] is not None for j in jobs),
            "context_errors": sum(j["packet"] is None for j in jobs),
            "run_id": fingerprint,
            "max_requests": len(jobs) * (config.retries + 1),
            "context_characters": sum(
                len(json.dumps(j["packet"])) for j in jobs if j["packet"] is not None
            ),
        }
    if output.exists() and not resume:
        raise ValueError("output exists; choose a new directory or use --resume")
    output.mkdir(parents=True, exist_ok=True)
    meta_path = output / "run.json"
    rows_path = output / "predictions.jsonl"
    existing = []
    if resume:
        if not meta_path.exists():
            raise ValueError("--resume requires an existing run.json")
        if json.loads(meta_path.read_text())["run_id"] != fingerprint:
            raise ValueError("resume configuration/context mismatch; use a new output directory")
        existing = read_jsonl(rows_path) if rows_path.exists() else []
        # Reject duplicates, alien targets, and bad states before issuing more calls.
        score(labels, existing, threshold)
    else:
        meta = {
            "run_id": fingerprint,
            "version": __version__,
            "config": asdict(config),
            "mode": mode,
            "prompt_variant": variant,
            "threshold": threshold,
            "started_at": datetime.now(UTC).isoformat(),
            "targets": [t["case_id"] for t in targets],
            "dataset_label_hash": digest(labels),
            "rubrics_hash": digest(rubrics),
        }
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        experiment = {
            "sources": sources,
            "targets": targets,
            "labels": labels,
            "rubrics": rubrics,
            "request_templates": {
                name: build_request(
                    config, {"source_packet": "REPLACE_WITH_PACKET"}, rubric, variant
                )
                for name, rubric in rubrics.items()
            },
        }
        (output / "experiment.json").write_text(json.dumps(experiment, indent=2) + "\n")
    seen = {r["case_id"] for r in existing}
    pending = [j for j in jobs if j["target"]["case_id"] not in seen]
    with rows_path.open("a", encoding="utf-8") as handle:
        # Avoid credentials/network setup when every job already finished or lacks context.
        client = Provider(config) if any(j["packet"] is not None for j in pending) else None
        try:
            for index, job in enumerate(pending, 1):
                target = job["target"]
                print(f"[{index}/{len(pending)}] {target['case_id']}", file=sys.stderr)
                observation = (
                    client.assess(job["packet"], job["rubric"], variant)
                    if job["packet"] is not None
                    else {
                        "result": unknown(job["context_error"]),
                        "usage": {},
                        "attempts": 0,
                        "latency_seconds": 0,
                    }
                )
                row = {
                    "case_id": target["case_id"],
                    "dimension": target["dimension"],
                    "packet_hash": digest(job["packet"]),
                    **observation,
                }
                handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                handle.flush()
                existing.append(row)
        finally:
            if client:
                client.client.close()
    report = score(labels, existing, threshold)
    report["run_id"] = fingerprint
    report["latency_seconds"] = round(sum(r["latency_seconds"] for r in existing), 4)
    report["usage"] = {
        key: sum(r["usage"].get(key, 0) for r in existing)
        for key in sorted({k for r in existing for k in r["usage"]})
    }
    report["cost_note"] = "Cost is reported only when returned by the provider; absent is unknown."
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report
