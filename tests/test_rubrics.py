import json

import pytest

from slop_decisions.providers import ProviderConfig, build_request
from slop_decisions.rubrics import instructions, load_rubrics


def legacy_rule():
    return {
        "name": "example",
        "predicate": "Can two requests violate the invariant?",
        "required_context": "Both writes and the storage contract.",
        "positive": "Both requests read the last slot before either writes.",
        "negative": "A conditional write checks and reserves the slot atomically.",
        "severity": "warning",
    }


def test_legacy_custom_rules_keep_working(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps([legacy_rule()]))
    assert load_rubrics(path) == {"example": legacy_rule()}
    assert "Predicate:" in instructions(load_rubrics(path)["example"])


@pytest.mark.parametrize("variant", ["minimal", "examples"])
@pytest.mark.parametrize(
    "provider,api",
    [("openai", "responses"), ("openai", "decisions"), ("openrouter", "chat"), ("local", "chat")],
)
def test_investigation_reaches_every_provider_and_prompt_variant(tmp_path, provider, api, variant):
    rule = dict(
        legacy_rule(),
        search_trigger="Read followed by write.",
        investigation="Interleave two requests and inspect the atomic boundary.",
        sources=["https://hexdocs.pm/ecto/Ecto.Changeset.html"],
    )
    path = tmp_path / "rules.json"
    path.write_text(json.dumps([rule]))
    loaded = load_rubrics(path)["example"]
    request = build_request(
        ProviderConfig(provider=provider, api=api, model="test"), {}, loaded, variant
    )
    if api == "decisions":
        prompt = request["questions"][1]["instructions"]
    else:
        prompt = request["input" if api == "responses" else "messages"][0]["content"]
    assert rule["investigation"] in prompt
    assert rule["required_context"] in prompt
    assert (rule["positive"] in prompt) == (variant == "examples")


@pytest.mark.parametrize(
    "extra",
    [
        {"investigation": ""},
        {"investigation": []},
        {"search_trigger": " "},
        {"sources": "https://example.com"},
        {"sources": []},
        {"sources": [None]},
        {"sources": ["javascript:alert(1)"]},
        {"sources": ["https://"]},
        {"unknown": "ignored?"},
    ],
)
def test_malformed_review_metadata_is_rejected(tmp_path, extra):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps([dict(legacy_rule(), **extra)]))
    with pytest.raises(ValueError):
        load_rubrics(path)


@pytest.mark.parametrize("data", [{}, [None], ["example"], []])
def test_invalid_rule_banks_fail_with_a_user_error(tmp_path, data):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_rubrics(path)
