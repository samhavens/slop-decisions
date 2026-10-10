"""Fit operating thresholds on calibration data; keep holdout evaluation separate."""

import json
import math
from collections import Counter
from statistics import mean

from slop_decisions.context import digest
from slop_decisions.dataset import read_jsonl
from slop_decisions.providers import probability

GRID = tuple(i / 20 for i in range(21))
POLICY = {"false_warning_cost": 5, "max_unsafe_context_rate": 0.1, "min_known_coverage": 0.7}


def load_cases(path):
    cases = read_jsonl(path)
    indexed(cases, [])
    families, packets = {}, {}
    for case in cases:
        split = case["split"]
        if split not in {"calibration", "holdout"}:
            raise ValueError("suite split must be calibration or holdout")
        family = case["family"]
        if not isinstance(family, str) or not family:
            raise ValueError("case family must be a nonempty string")
        if families.setdefault(family, split) != split:
            raise ValueError("a family crosses calibration and holdout")
        packet = case["packet"]
        if set(packet) != {"target", "files"} or not packet["files"]:
            raise ValueError("packet must contain only target and files")
        target = packet["target"]
        if set(target) - {"path", "start_line", "end_line", "focus"}:
            raise ValueError("unexpected target fields")
        for span in [target, *packet["files"]]:
            if (
                not isinstance(span.get("path"), str)
                or not span["path"]
                or type(span.get("start_line")) is not int
                or type(span.get("end_line")) is not int
                or not 1 <= span["start_line"] <= span["end_line"]
            ):
                raise ValueError("invalid source or target span")
        if "focus" in target and not isinstance(target["focus"], str):
            raise ValueError("target focus must be a string")
        for source in packet["files"]:
            if set(source) != {"path", "start_line", "end_line", "content"}:
                raise ValueError("unexpected source fields")
            if source["end_line"] - source["start_line"] + 1 != len(source["content"].splitlines()):
                raise ValueError("source line range does not match content")
        paths = [f["path"] for f in packet["files"]]
        if len(set(paths)) != len(paths):
            raise ValueError("duplicate source path")
        if not any(
            f["path"] == target["path"]
            and f["start_line"] <= target["start_line"] <= target["end_line"] <= f["end_line"]
            for f in packet["files"]
        ):
            raise ValueError("target is not covered by its source file")
        # Ignore focus metadata when checking for repeated source across splits.
        identity = digest(sorted(f["content"] for f in packet["files"]))
        if packets.setdefault(identity, split) != split:
            raise ValueError("an identical source packet crosses splits")
        json.dumps(packet, allow_nan=False)
    for dimension in {c["dimension"] for c in cases}:
        for split in ("calibration", "holdout"):
            labels = {
                c["expected"] for c in cases if c["dimension"] == dimension and c["split"] == split
            }
            if labels != {"defect", "clean", "unassessable"}:
                raise ValueError("each check needs all three labels in both splits")
    return cases


def indexed(cases, predictions):
    gold = {}
    for case in cases:
        if not isinstance(case["case_id"], str) or not case["case_id"]:
            raise ValueError("case ID must be a nonempty string")
        if case["case_id"] in gold or case["expected"] not in {"defect", "clean", "unassessable"}:
            raise ValueError("duplicate case or invalid expected result")
        gold[case["case_id"]] = case
    if not gold:
        raise ValueError("no cases selected")
    rows = {}
    for row in predictions:
        name = row["case_id"]
        if name in rows:
            raise ValueError("duplicate prediction")
        if name not in gold:
            raise ValueError("prediction has no matching case")
        if "decision_scores" in row:
            values = row["decision_scores"]
            rows[name] = (
                probability(values["context_probability"]),
                probability(values["defect_probability"]),
            )
        else:
            rows[name] = None
    return gold, rows


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p, z2 = successes / total, z * z
    center = (p + z2 / (2 * total)) / (1 + z2 / total)
    half = z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / (1 + z2 / total)
    return [max(0.0, center - half), min(1.0, center + half)]


def measure(cases, predictions, context_threshold, threshold):
    probability(context_threshold)
    probability(threshold)
    gold, rows = indexed(cases, predictions)
    counts = Counter()
    for name, case in gold.items():
        truth = case["expected"]
        values = rows.get(name)
        observed = (
            ("defect" if values[1] >= threshold else "clean")
            if values is not None and values[0] >= context_threshold
            else "unassessable"
        )
        counts["cases"] += 1
        counts["unknown"] += observed == "unassessable"
        counts["correct"] += observed == truth
        if truth == "unassessable":
            counts["insufficient_context_cases"] += 1
            counts["unsafe_context_acceptances"] += observed != "unassessable"
            counts["unsafe_warnings"] += observed == "defect"
        else:
            counts["known_cases"] += 1
            counts["known_assessed"] += observed != "unassessable"
            counts["known_correct"] += observed == truth
            counts["positives" if truth == "defect" else "negatives"] += 1
            counts["false_warnings"] += truth == "clean" and observed == "defect"
            counts["missed_defects"] += truth == "defect" and observed != "defect"
            counts["true_warnings"] += truth == "defect" and observed == "defect"
    result = {
        name: counts[name]
        for name in (
            "cases",
            "known_cases",
            "known_assessed",
            "known_correct",
            "positives",
            "negatives",
            "insufficient_context_cases",
            "unsafe_context_acceptances",
            "unsafe_warnings",
            "false_warnings",
            "missed_defects",
            "true_warnings",
            "unknown",
            "correct",
        )
    }
    result.update(
        known_coverage=counts["known_assessed"] / counts["known_cases"]
        if counts["known_cases"]
        else None,
        unsafe_context_rate=counts["unsafe_context_acceptances"]
        / counts["insufficient_context_cases"]
        if counts["insufficient_context_cases"]
        else None,
        review_cost=POLICY["false_warning_cost"] * counts["false_warnings"]
        + counts["missed_defects"],
        warning_precision=counts["true_warnings"]
        / (counts["true_warnings"] + counts["false_warnings"])
        if counts["true_warnings"] + counts["false_warnings"]
        else None,
        false_warning_rate=counts["false_warnings"] / counts["negatives"]
        if counts["negatives"]
        else None,
        context_threshold=context_threshold,
        threshold=threshold,
    )
    return result


def fit_thresholds(cases, predictions):
    gold, rows = indexed(cases, predictions)
    if set(gold) != set(rows):
        raise ValueError("fit requires a complete run, including failed requests")
    if any(case["split"] != "calibration" for case in cases):
        raise ValueError("fit accepts calibration cases only; never dev or holdout")
    if {c["expected"] for c in cases} != {"defect", "clean", "unassessable"}:
        raise ValueError("calibration requires defects, clean code, and insufficient context")
    gates = [measure(cases, predictions, gate, 0.8) for gate in GRID]
    eligible = [
        r
        for r in gates
        if r["unsafe_context_rate"] <= POLICY["max_unsafe_context_rate"]
        and r["known_coverage"] >= POLICY["min_known_coverage"]
    ]
    if not eligible:
        raise ValueError("no context gate meets safety and coverage requirements")
    gate = max(eligible, key=lambda r: (r["known_coverage"], r["context_threshold"]))[
        "context_threshold"
    ]
    thresholds = [measure(cases, predictions, gate, threshold) for threshold in GRID]
    selected = min(thresholds, key=lambda r: (r["review_cost"], -r["threshold"]))
    return {
        "context_threshold": gate,
        "threshold": selected["threshold"],
        "policy": dict(POLICY),
        "calibration": selected,
        "baseline": measure(cases, predictions, 0.8, 0.8),
        "context_sweep": gates,
        "threshold_sweep": thresholds,
    }


def diagnostics(cases, predictions, context_threshold, threshold):
    report = measure(cases, predictions, context_threshold, threshold)
    report["dimensions"] = {}
    for dimension in sorted({c["dimension"] for c in cases}):
        subset = [c for c in cases if c["dimension"] == dimension]
        ids = {c["case_id"] for c in subset}
        report["dimensions"][dimension] = measure(
            subset, [r for r in predictions if r["case_id"] in ids], context_threshold, threshold
        )
    gold, rows = indexed(cases, predictions)
    report["reliability"] = {}
    for name, index in [("context", 0), ("defect", 1)]:
        values = [
            (
                scores[index],
                int(
                    case["expected"] != "unassessable"
                    if index == 0
                    else case["expected"] == "defect"
                ),
            )
            for key, case in gold.items()
            if (scores := rows.get(key)) is not None
            and (index == 0 or case["expected"] != "unassessable")
        ]
        bins = []
        for bucket in range(5):
            start = bucket / 5
            group = [(p, y) for p, y in values if min(int(p * 5), 4) == bucket]
            bins.append(
                {
                    "lower": start,
                    "upper": round(start + 0.2, 1),
                    "count": len(group),
                    "mean_probability": mean(p for p, _ in group) if group else None,
                    "observed_rate": mean(y for _, y in group) if group else None,
                }
            )
        report["reliability"][name] = {
            "count": len(values),
            "brier_score": mean((p - y) ** 2 for p, y in values) if values else None,
            "bins": bins,
        }
    report["casewise_wilson_95"] = {
        "warning_precision": wilson(
            report["true_warnings"], report["true_warnings"] + report["false_warnings"]
        ),
        "false_warning_rate": wilson(report["false_warnings"], report["negatives"]),
        "unsafe_context_rate": wilson(
            report["unsafe_context_acceptances"], report["insufficient_context_cases"]
        ),
        "caveat": (
            "Descriptive binomial intervals; paired and authored cases "
            "are not independent production samples."
        ),
    }
    return report
