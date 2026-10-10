"""Bind fitted operating thresholds to the exact model request contract."""

from slop_decisions.calibration import POLICY
from slop_decisions.context import digest
from slop_decisions.providers import build_request, probability


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


def accepted(report, baseline, policy):
    return (
        report["known_coverage"] is not None
        and report["unsafe_context_rate"] is not None
        and report["known_coverage"] >= policy["min_known_coverage"]
        and report["unsafe_context_rate"] <= policy["max_unsafe_context_rate"]
        and report["review_cost"] <= baseline["review_cost"]
    )


def thresholds(config, rubrics, mode, variant, *, validation=None, context=None, warning=None):
    fitted = None
    source = "uncalibrated_default"
    if validation is not None:
        profile = validation["profile"]
        selection = profile["selection"]
        if digest(profile) != validation["profile_hash"]:
            raise ValueError("calibration profile fingerprint mismatch")
        if selection["policy"] != POLICY:
            raise ValueError("unsupported calibration policy")
        if not validation["accepted"] or not accepted(
            validation["holdout"], validation["baseline"], POLICY
        ):
            raise ValueError("calibration profile failed held-out validation")
        if any(
            validation["holdout"][k] != selection[k] for k in ("context_threshold", "threshold")
        ):
            raise ValueError("validation used different thresholds")
        recorded = profile["contract"]
        if not rubrics.keys() <= recorded["templates"].keys():
            raise ValueError("calibration profile does not match the selected checks")
        scoped = {**recorded, "templates": {name: recorded["templates"][name] for name in rubrics}}
        if scoped != contract(config, rubrics, mode, variant):
            raise ValueError(
                "calibration profile does not match model, API, endpoint, context, or rubrics"
            )
        fitted = selection
        source = "validated_profile"
    defaults = fitted or {"context_threshold": 0.8, "threshold": 0.8}
    result = {
        "context_threshold": probability(
            context if context is not None else defaults["context_threshold"]
        ),
        "threshold": probability(warning if warning is not None else defaults["threshold"]),
        "context_source": "explicit" if context is not None else source,
        "warning_source": "explicit" if warning is not None else source,
    }
    if config.transport_api != "decisions":
        result["context_source"] = "not_used_by_transport"
    if fitted:
        result["profile_hash"] = validation["profile_hash"]
    return result
