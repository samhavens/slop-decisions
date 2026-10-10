import json

import httpx
import pytest

from slop_decisions.context import build_packet
from slop_decisions.evaluation import score, sweep
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics


def prediction(case_id, probability=None):
    result = (
        {"status": "assessed", "probability": probability}
        if probability is not None
        else {"status": "unassessed", "reason": "timeout"}
    )
    return {"case_id": case_id, "dimension": "success_shaped_failure", "result": result}


def labels():
    return [
        {
            "case_id": "a",
            "dimension": "success_shaped_failure",
            "label": True,
            "pair_id": "pair",
            "hard_negative": False,
            "split": "dev",
        },
        {
            "case_id": "b",
            "dimension": "success_shaped_failure",
            "label": False,
            "pair_id": "pair",
            "hard_negative": True,
            "split": "dev",
        },
        {
            "case_id": "c",
            "dimension": "success_shaped_failure",
            "label": True,
            "pair_id": None,
            "hard_negative": False,
            "split": "dev",
        },
        {
            "case_id": "d",
            "dimension": "success_shaped_failure",
            "label": False,
            "pair_id": None,
            "hard_negative": True,
            "split": "dev",
        },
    ]


def test_errors_reduce_coverage_and_cannot_pass_a_pair():
    report = score(
        labels(),
        [prediction("a", 0.9), prediction("b"), prediction("c", 0.9), prediction("d", 0.1)],
        0.8,
    )
    assert report["coverage"] == 0.75
    assert report["macro_balanced_accuracy"] == 0.75
    assert report["paired_fix_accuracy"] == 0
    assert report["hard_negative_coverage"] == 0.5


def test_missing_is_not_clean_and_duplicates_are_rejected():
    assert score(labels(), [], 0.8)["coverage"] == 0
    with pytest.raises(ValueError, match="duplicate"):
        score(labels(), [prediction("a", 0.9)] * 2, 0.8)


def test_pair_requires_both_sides_cross_threshold():
    report = score(labels(), [prediction("a", 0.9), prediction("b", 0.85)], 0.8)
    assert report["paired_fix_accuracy"] == 0


def test_single_class_dimension_is_not_balanced_accuracy():
    report = score(labels()[:1], [prediction("a", 0.9)], 0.8)
    assert report["macro_balanced_accuracy"] is None


def test_holdout_cannot_be_used_for_threshold_sweep():
    gold = [dict(row, split="holdout") for row in labels()]
    with pytest.raises(ValueError, match="holdout"):
        sweep(gold, [], [0.5, 0.8])


def test_context_has_only_selected_source_and_bounds(tmp_path):
    (tmp_path / "example.ex").write_text("line one\nline two\nline three\n")
    packet = build_packet(tmp_path, "example.ex", 2, 2, mode="target")
    assert packet["files"][0]["content"] == "line two"
    assert packet["files"][0]["start_line"] == 2
    with pytest.raises(ValueError):
        build_packet(tmp_path, "../secret", 1, 1)
    with pytest.raises(ValueError):
        build_packet(tmp_path, "example.ex", 1, 10)


def test_context_rejects_oversize_instead_of_silent_truncation(tmp_path):
    (tmp_path / "a.ex").write_text("a" * 1000)
    with pytest.raises(ValueError, match="budget"):
        build_packet(tmp_path, "a.ex", 1, 1, max_chars=50)


@pytest.mark.parametrize(
    "provider,api,path",
    [
        ("openai", "decisions", "/v1/decisions"),
        ("openai", "responses", "/v1/responses"),
        ("openrouter", "chat", "/v1/chat/completions"),
        ("local", "chat", "/v1/chat/completions"),
    ],
)
def test_provider_wire_protocol_and_key_isolation(monkeypatch, provider, api, path):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-private")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-private")
    rubric = load_rubrics()["success_shaped_failure"]
    verdict = {
        "status": "assessed",
        "probability": 0.9,
        "reason": "failed send reported as success",
    }

    def handle(request):
        assert request.url.path == path
        body = json.loads(request.content)
        auth = request.headers.get("Authorization")
        assert (
            auth
            == {
                "openai": "Bearer openai-private",
                "openrouter": "Bearer router-private",
                "local": None,
            }[provider]
        )
        if api == "decisions":
            names = [q["name"] for q in body["questions"]]
            assert names == ["context_sufficient", "success_shaped_failure"]
            return httpx.Response(
                200,
                json={
                    "answers": [
                        {"name": name, "type": "predicate", "probability": 0.9} for name in names
                    ]
                },
            )
        if api == "responses":
            assert body["store"] is False
            assert body["text"]["format"]["type"] == "json_schema"
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": json.dumps(verdict)}],
                        }
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(verdict)}}]
            },
        )

    config = ProviderConfig(
        provider=provider, api=api, model="test-model", base_url="http://127.0.0.1/v1"
    )
    with Provider(config, transport=httpx.MockTransport(handle)) as client:
        result = client.assess({"target": {}, "files": []}, rubric)
    assert result["result"]["status"] == "assessed"
    assert result["result"]["probability"] == 0.9


@pytest.mark.parametrize("bad", [True, "0.9", -1, 2, float("nan"), None])
def test_invalid_probability_is_never_clean(bad):
    def handle(_):
        content = json.dumps({"status": "assessed", "probability": bad, "reason": "test"})
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
        )

    with Provider(
        ProviderConfig(provider="local", model="x"), transport=httpx.MockTransport(handle)
    ) as client:
        result = client.assess({}, load_rubrics()["success_shaped_failure"])
    assert result["result"]["status"] == "unassessed"


@pytest.mark.parametrize("reverse", [False, True])
def test_decisions_maps_distinct_scores_by_name_without_inverting_them(monkeypatch, reverse):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    answers = [
        {"type": "predicate", "name": "context_sufficient", "probability": 0.99},
        {"type": "predicate", "name": "derived_state_drift", "probability": 0.03},
    ]
    if reverse:
        answers.reverse()
    with Provider(
        ProviderConfig(provider="openai", model="gpt-6-luna", api="decisions"),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"answers": answers})),
    ) as provider:
        row = provider.assess({}, load_rubrics()["derived_state_drift"])
    assert row["result"] == {
        "status": "assessed",
        "probability": 0.03,
        "context_probability": 0.99,
    }
    assert row["decision_scores"] == {"context_probability": 0.99, "defect_probability": 0.03}


@pytest.mark.parametrize("finish", ["length", "content_filter", "tool_calls", None])
def test_truncated_or_nontext_answer_cannot_pass(finish):
    def handle(_):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": finish,
                        "message": {
                            "content": '{"status":"assessed","probability":0,"reason":"ok"}'
                        },
                    }
                ]
            },
        )

    with Provider(
        ProviderConfig(provider="local", model="x"), transport=httpx.MockTransport(handle)
    ) as client:
        result = client.assess({}, load_rubrics()["success_shaped_failure"])
    assert result["result"]["status"] == "unassessed"


def test_toon_empty_objects_and_quoted_keys_match_reference_encoding():
    from slop_decisions.output import toon

    value = {"object": {}, "rows": [{}, {"n": 1}], "value:colon": {"x": True}}
    assert "\n".join(toon(value)) == ('object:\nrows[2]:\n  -\n  - n: 1\n"value:colon":\n  x: true')
