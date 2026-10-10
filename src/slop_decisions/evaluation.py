"""Scoring is pure and never treats an absent assessment as a negative."""

from collections import defaultdict
from statistics import mean

from slop_decisions.providers import probability


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def score(
    labels: list[dict],
    predictions: list[dict],
    threshold: float = 0.8,
    *,
    include_tracks: bool = True,
) -> dict:
    probability(threshold)
    gold = {}
    for row in labels:
        key = (row["case_id"], row["dimension"])
        if key in gold or type(row["label"]) is not bool:
            raise ValueError("duplicate label or non-boolean label")
        if "hard_negative" in row and type(row["hard_negative"]) is not bool:
            raise ValueError("hard_negative must be boolean")
        gold[key] = row
    if not gold:
        raise ValueError("no labels selected")
    pred = {}
    for row in predictions:
        key = (row["case_id"], row["dimension"])
        if key in pred:
            raise ValueError("duplicate prediction")
        if key not in gold:
            raise ValueError("prediction has no matching label")
        result = row["result"]
        if result["status"] == "assessed":
            pred[key] = probability(result["probability"]) >= threshold
        elif result["status"] == "unassessed":
            pred[key] = None
        else:
            raise ValueError("invalid prediction state")
    dimensions = defaultdict(
        lambda: dict(tp=0, tn=0, fp=0, fn=0, positives=0, negatives=0, unassessed=0)
    )
    pairs = defaultdict(list)
    hard_total = hard_assessed = hard_fp = assessed = correct = 0
    for key, row in gold.items():
        label = row["label"]
        value = pred.get(key)
        counts = dimensions[row["dimension"]]
        counts["positives" if label else "negatives"] += 1
        if value is None:
            counts["unassessed"] += 1
        else:
            assessed += 1
            correct += int(value == label)
            counts[("tp" if value else "fn") if label else ("fp" if value else "tn")] += 1
        if row.get("hard_negative"):
            if label:
                raise ValueError("hard negative has positive label")
            hard_total += 1
            hard_assessed += int(value is not None)
            hard_fp += int(value is True)
        if row.get("pair_id"):
            pairs[(row["dimension"], row["pair_id"])].append((label, value))
    for counts in dimensions.values():
        p, n = counts["positives"], counts["negatives"]
        # Unknowns are failures in the primary score, on either side of the predicate.
        counts["balanced_accuracy"] = (counts["tp"] / p + counts["tn"] / n) / 2 if p and n else None
        counts["precision"] = ratio(counts["tp"], counts["tp"] + counts["fp"])
        counts["recall"] = ratio(counts["tp"], p)
    complete_pairs = [
        rows for rows in pairs.values() if len(rows) == 2 and {r[0] for r in rows} == {True, False}
    ]
    passing = sum(
        all(value is not None and label == value for label, value in rows)
        for rows in complete_pairs
    )
    bas = [
        d["balanced_accuracy"] for d in dimensions.values() if d["balanced_accuracy"] is not None
    ]
    report = {
        "threshold": threshold,
        "targets": len(gold),
        "assessed": assessed,
        "unassessed": len(gold) - assessed,
        "coverage": assessed / len(gold),
        "accuracy_all_targets": correct / len(gold),
        "accuracy_assessed": ratio(correct, assessed),
        "macro_balanced_accuracy": mean(bas) if bas else None,
        "balanced_dimensions": len(bas),
        "dimensions": dict(dimensions),
        "pairs": len(complete_pairs),
        "pairs_passed": passing,
        "incomplete_pairs": len(pairs) - len(complete_pairs),
        "paired_fix_accuracy": ratio(passing, len(complete_pairs)),
        "hard_negatives": hard_total,
        "hard_negative_false_positives": hard_fp,
        "hard_negative_fpr": ratio(hard_fp, hard_assessed),
        "hard_negative_coverage": ratio(hard_assessed, hard_total),
    }
    if include_tracks:
        tracks = sorted({r["track"] for r in labels if "track" in r})
        report["tracks"] = {}
        for track in tracks:
            rows = [r for r in labels if r.get("track") == track]
            keys = {(r["case_id"], r["dimension"]) for r in rows}
            subset = [r for r in predictions if (r["case_id"], r["dimension"]) in keys]
            report["tracks"][track] = score(rows, subset, threshold, include_tracks=False)
    return report


def sweep(labels: list[dict], predictions: list[dict], thresholds: list[float]) -> dict:
    if any(row.get("split") not in {"dev", "calibration"} for row in labels):
        raise ValueError("threshold tuning is restricted to dev/calibration; never use holdout")
    if not thresholds:
        raise ValueError("at least one threshold is required")
    reports = [score(labels, predictions, threshold) for threshold in sorted(set(thresholds))]
    return {
        "split": sorted({r["split"] for r in labels}),
        "reports": reports,
        "note": "Development fit is not held-out performance. Freeze thresholds before holdout.",
    }
