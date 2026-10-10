import json

import httpx
import pytest

from slop_decisions.calibration import fit_thresholds, measure
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics


def cases(split="calibration"):
    return [
        {"case_id": "bug", "family": "one", "split": split, "dimension": "x", "expected": "defect"},
        {"case_id": "fix", "family": "one", "split": split, "dimension": "x", "expected": "clean"},
        {"case_id": "edge", "family": "two", "split": split, "dimension": "x", "expected": "clean"},
        {
            "case_id": "absent",
            "family": "three",
            "split": split,
            "dimension": "x",
            "expected": "unassessable",
        },
    ]


def predictions():
    return [
        {"case_id": name, "decision_scores": {"context_probability": c, "defect_probability": p}}
        for name, c, p in [
            ("bug", 0.95, 0.75),
            ("fix", 0.95, 0.2),
            ("edge", 0.9, 0.3),
            ("absent", 0.4, 0.99),
        ]
    ]


def test_context_gate_keeps_raw_scores_but_never_calls_it_clean(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    response = {
        "answers": [
            {"type": "predicate", "name": "context_sufficient", "probability": 0.2},
            {"type": "predicate", "name": "success_shaped_failure", "probability": 0.9},
        ]
    }
    with Provider(
        ProviderConfig(provider="openai", model="x"),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response)),
    ) as provider:
        row = provider.assess({}, load_rubrics()["success_shaped_failure"])
    assert row["result"]["status"] == "unassessed"
    assert "probability" not in row["result"]
    assert row["decision_scores"] == {"context_probability": 0.2, "defect_probability": 0.9}


def test_fit_selects_both_gates_and_breaks_ties_conservatively():
    fit = fit_thresholds(cases(), predictions())
    assert fit["context_threshold"] == 0.9
    assert fit["threshold"] == 0.75
    report = measure(cases(), predictions(), 0.9, 0.75)
    assert report["false_warnings"] == 0
    assert report["missed_defects"] == 0
    assert report["unsafe_context_acceptances"] == 0
    assert report["known_coverage"] == 1


def test_holdout_is_never_used_to_fit():
    with pytest.raises(ValueError, match="calibration"):
        fit_thresholds(cases("holdout"), predictions())


def test_missing_refused_or_censored_scores_remain_unknown():
    rows = predictions()[:1] + [
        {"case_id": "fix", "result": {"status": "unassessed", "reason": "provider_refusal"}}
    ]
    report = measure(cases(), rows, 0.8, 0.8)
    assert report["known_assessed"] == 1
    assert report["missed_defects"] == 1
    assert report["false_warnings"] == 0
    assert report["insufficient_context_cases"] == 1
    assert report["unknown"] == 3


def test_fit_rejects_unsafe_or_unusable_gates():
    rows = predictions()
    for row in rows:
        row["decision_scores"]["context_probability"] = 0.5
    with pytest.raises(ValueError, match="coverage"):
        fit_thresholds(cases(), rows)


def test_calibration_is_pure_and_rejects_duplicate_or_alien_results():
    labels, rows = cases(), predictions()
    before = json.dumps([labels, rows])
    fit_thresholds(labels, rows)
    assert json.dumps([labels, rows]) == before
    with pytest.raises(ValueError, match="duplicate"):
        measure(labels, rows + rows[:1], 0.8, 0.8)
    with pytest.raises(ValueError, match="matching"):
        measure(labels, rows + [{"case_id": "alien"}], 0.8, 0.8)


def test_fit_requires_complete_predictions():
    with pytest.raises(ValueError, match="complete"):
        fit_thresholds(cases(), predictions()[:-1])


def test_reliability_bins_count_each_boundary_once():
    from slop_decisions.calibration import diagnostics

    rows = predictions()
    for row, p in zip(rows, [0.2, 0.4, 0.6, 1.0], strict=True):
        row["decision_scores"]["context_probability"] = p
    result = diagnostics(cases(), rows, 0.8, 0.8)
    assert sum(b["count"] for b in result["reliability"]["context"]["bins"]) == 4


def test_suite_rejects_leaked_families_and_packets(tmp_path):
    from pathlib import Path

    from slop_decisions.calibration import load_cases

    suite = load_cases(Path("calibration/cases.jsonl"))
    assert len(suite) == 112
    suite[-1]["family"] = suite[0]["family"]
    path = tmp_path / "cases.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in suite))
    with pytest.raises(ValueError, match="family"):
        load_cases(path)


def test_study_resumes_pilot_freezes_fit_then_scores_holdout(tmp_path, monkeypatch):
    from pathlib import Path

    from slop_decisions import calibration_study as study
    from slop_decisions.calibration import load_cases

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    suite = load_cases(Path("calibration/cases.jsonl"))
    small = [c for c in suite if c["dimension"] == "success_shaped_failure"]
    path = tmp_path / "cases.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in small))
    sent = []

    def respond(request):
        body = json.loads(request.content)
        assert "case_id" not in body["input"]
        assert "rationale" not in body["input"]
        c, p = [(0.99, 0.9), (0.99, 0.01), (0.99, 0.01), (0.01, 0.9)][len(sent) % 4]
        sent.append(body)
        return httpx.Response(
            200,
            json={
                "answers": [
                    {"type": "predicate", "name": "context_sufficient", "probability": c},
                    {"type": "predicate", "name": "success_shaped_failure", "probability": p},
                ]
            },
        )

    monkeypatch.setattr(
        study, "Provider", lambda conf: Provider(conf, transport=httpx.MockTransport(respond))
    )
    config = ProviderConfig(provider="openai", model="x", retries=0)
    cal, hold, profile = tmp_path / "cal", tmp_path / "hold", tmp_path / "profile.json"
    with pytest.raises(ValueError, match="frozen"):
        study.collect(path, "holdout", hold, config)
    assert not sent
    assert study.collect(path, "calibration", cal, config, stop_after=3)["completed"] == 3
    with pytest.raises(ValueError, match="complete"):
        study.fit(cal, profile)
    assert study.collect(path, "calibration", cal, config)["completed"] == 4
    study.collect(path, "calibration", cal, config)
    assert len(sent) == 4
    fit = study.fit(cal, profile)
    assert fit["context_threshold"] == 0.95
    assert fit["threshold"] == 0.9
    with pytest.raises(ValueError, match="exists"):
        study.fit(cal, profile)
    before = profile.read_bytes()
    study.collect(path, "holdout", hold, config, profile_path=profile)
    receipt = study.validate(hold, profile, tmp_path / "validation.json")
    assert receipt["accepted"]
    assert set(receipt["profile"]["contract"]["templates"]) == {"success_shaped_failure"}
    assert receipt["holdout"]["known_correct"] == 3
    assert profile.read_bytes() == before
    from dataclasses import replace

    from slop_decisions.cli import parser, run
    from slop_decisions.profiles import thresholds

    bank = {"success_shaped_failure": load_rubrics()["success_shaped_failure"]}
    policy = thresholds(config, bank, "file", "examples", validation=receipt)
    assert policy["context_threshold"] == 0.95
    assert policy["threshold"] == 0.9
    assert policy["warning_source"] == "validated_profile"
    with pytest.raises(ValueError, match="selected checks"):
        thresholds(config, load_rubrics(), "file", "examples", validation=receipt)
    for changed in [
        replace(config, model="other"),
        replace(config, api="responses"),
        replace(config, base_url="https://other.example/v1"),
        replace(config, provider="local", api="chat"),
        replace(config, provider="openrouter", api="chat"),
    ]:
        with pytest.raises(ValueError, match="does not match"):
            thresholds(changed, bank, "file", "examples", validation=receipt)
    for mode, variant in [("window", "examples"), ("file", "minimal")]:
        with pytest.raises(ValueError, match="does not match"):
            thresholds(config, bank, mode, variant, validation=receipt)
    changed_bank = {
        **bank,
        "success_shaped_failure": {**bank["success_shaped_failure"], "predicate": "changed"},
    }
    with pytest.raises(ValueError, match="does not match"):
        thresholds(config, changed_bank, "file", "examples", validation=receipt)
    with pytest.raises(ValueError, match="failed"):
        thresholds(config, bank, "file", "examples", validation={**receipt, "accepted": False})
    (tmp_path / "sample.ex").write_text("defmodule Sample do\nend\n")
    arguments = [
        "check",
        "sample.ex",
        "--root",
        str(tmp_path),
        "--model",
        "x",
        "--provider",
        "openai",
        "--dimension",
        "success_shaped_failure",
        "--calibration",
        str(tmp_path / "validation.json"),
        "--dry-run",
    ]
    report, code = run(parser().parse_args(arguments))
    assert code == 0
    assert report["threshold_policy"]["context_threshold"] == 0.95
    assert report["threshold_policy"]["threshold"] == 0.9
    manual, _ = run(
        parser().parse_args(arguments + ["--threshold", "0.7", "--context-threshold", "0.5"])
    )
    assert manual["threshold_policy"]["threshold"] == 0.7
    assert manual["threshold_policy"]["context_threshold"] == 0.5
    assert manual["threshold_policy"]["warning_source"] == "explicit"
    assert manual["threshold_policy"]["context_source"] == "explicit"
    assert len(sent) == 8
    with pytest.raises(ValueError, match="mismatch"):
        study.collect(path, "calibration", cal, ProviderConfig(provider="openai", model="other"))


def test_valid_refusals_do_not_trigger_the_request_failure_stop(tmp_path, monkeypatch):
    from pathlib import Path

    from slop_decisions import calibration_study as study

    monkeypatch.setenv("OPENAI_API_KEY", "test")

    def refusal(request):
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "answers": [
                    {"type": "refusal", "name": q["name"], "refusal": "Cannot assess"}
                    for q in body["questions"]
                ]
            },
        )

    monkeypatch.setattr(
        study, "Provider", lambda conf: Provider(conf, transport=httpx.MockTransport(refusal))
    )
    result = study.collect(
        Path("calibration/cases.jsonl"),
        "calibration",
        tmp_path / "run",
        ProviderConfig(provider="openai", model="x"),
        stop_after=3,
    )
    assert result["completed"] == 3


def test_published_rejected_profile_is_blocked_before_any_request(tmp_path):
    from pathlib import Path

    from slop_decisions.cli import parser, run

    (tmp_path / "sample.ex").write_text("defmodule Sample do\nend\n")
    args = parser().parse_args(
        [
            "check",
            "sample.ex",
            "--root",
            str(tmp_path),
            "--provider",
            "openai",
            "--model",
            "gpt-6-luna",
            "--calibration",
            str(Path("reports/calibration-2026-10-10/validation.json")),
            "--dry-run",
        ]
    )
    with pytest.raises(ValueError, match="failed held-out"):
        run(args)


def test_collection_stops_after_two_request_errors(tmp_path, monkeypatch):
    from pathlib import Path

    from slop_decisions import calibration_study as study
    from slop_decisions.dataset import read_jsonl

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(
        study,
        "Provider",
        lambda conf: Provider(conf, transport=httpx.MockTransport(lambda _: httpx.Response(500))),
    )
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="two consecutive request failures"):
        study.collect(
            Path("calibration/cases.jsonl"),
            "calibration",
            output,
            ProviderConfig(provider="openai", model="x", retries=0),
            stop_after=3,
        )
    rows = read_jsonl(output / "predictions.jsonl")
    assert len(rows) == 2
    assert all(r["result"]["reason"] == "http_500" for r in rows)


def test_validation_cli_returns_rejection_code_and_saves_evidence(tmp_path, monkeypatch, capsys):
    from slop_decisions import calibration_study as study

    output = tmp_path / "validation.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "slop-calibrate",
            "validate",
            "reports/calibration-2026-10-10/holdout",
            "--profile",
            "reports/calibration-2026-10-10/profile.json",
            "--out",
            str(output),
            "--format",
            "json",
            "--full",
        ],
    )
    assert study.main() == 3
    document = json.loads(output.read_text())
    assert document == json.loads(capsys.readouterr().out)
    assert document["accepted"] is False


def test_validation_cannot_overwrite_its_frozen_profile(tmp_path):
    from pathlib import Path

    from slop_decisions import calibration_study as study

    frozen = tmp_path / "profile.json"
    frozen.write_bytes(Path("reports/calibration-2026-10-10/profile.json").read_bytes())
    before = frozen.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        study.validate(Path("reports/calibration-2026-10-10/holdout"), frozen, frozen)
    assert frozen.read_bytes() == before


def test_suite_rejects_invalid_target_ranges_before_requests(tmp_path):
    from pathlib import Path

    from slop_decisions.calibration import load_cases

    suite = load_cases(Path("calibration/cases.jsonl"))
    suite[0]["packet"]["target"]["end_line"] = 999
    path = tmp_path / "cases.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in suite))
    with pytest.raises(ValueError, match="target"):
        load_cases(path)
