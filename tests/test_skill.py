import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from slop_decisions.context import build_packet
from slop_decisions.rubrics import default_rule_names, load_rubrics

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "slop-review"


def test_skill_rules_match_the_api_rules():
    # A standalone install must retain both the predicates and their exceptions.
    rules = json.loads((SKILL / "references" / "rules.json").read_text())
    bank = load_rubrics()
    assert rules == [bank[name] for name in default_rule_names()]
    broader = json.loads((SKILL / "references" / "broader-rules.json").read_text())
    assert broader == [r for name, r in bank.items() if name not in default_rule_names()]


@pytest.mark.parametrize("skill_name", ["slop-review", "slop-review-python"])
def test_skill_references_work_after_standalone_install(tmp_path, skill_name):
    installed = tmp_path / ".agents" / "skills" / skill_name
    shutil.copytree(ROOT / "skills" / skill_name, installed)
    local_links = []
    for document in installed.rglob("*.md"):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if "://" in link or link.startswith("#"):
                continue
            local_links.append(link)
            target = (document.parent / link.split("#")[0]).resolve()
            assert target.is_relative_to(installed.resolve())
            assert target.is_file(), f"Missing standalone skill resource: {link}"
    assert local_links, "The installed skill must include its rules."
    assert json.loads((installed / "references" / "rules.json").read_text())


def test_python_skill_preserves_focused_predicates_and_exceptions():
    python_skill = ROOT / "skills" / "slop-review-python"
    rules = json.loads((python_skill / "references" / "rules.json").read_text())
    bank = load_rubrics()
    assert [rule["name"] for rule in rules] == default_rule_names()
    for rule in rules:
        original = bank[rule["name"]]
        for field in ("predicate", "severity", "sources"):
            assert rule[field] == original[field]
        for field in (
            "required_context",
            "search_trigger",
            "investigation",
            "positive",
            "negative",
        ):
            assert isinstance(rule[field], str) and rule[field].strip()


def test_phoenix_examples_cover_boundaries_and_build_source_only_packets():
    directory = ROOT / "evals" / "phoenix"
    cases = json.loads((directory / "cases.json").read_text())
    bank = load_rubrics()
    assert {case["dimension"] for case in cases} == {
        "client_state_round_trip",
        "liveview_reconnect_state_loss",
        "per_record_database_read",
    }
    assert len({case["case_id"] for case in cases}) == len(cases)
    for dimension in {case["dimension"] for case in cases}:
        assert dimension in bank
        assert {case["expected"] for case in cases if case["dimension"] == dimension} == {
            "defect",
            "clean",
            "unassessable",
        }
    for case in cases:
        source = (directory / case["path"]).read_text()
        packet = build_packet(directory, case["path"], 1, len(source.splitlines()))
        assert packet["files"][0]["content"] == source.rstrip("\n")
        assert not {"expected", "rationale", "case_id"} & packet.keys()


@pytest.mark.skipif(not shutil.which("elixir"), reason="requires Elixir")
def test_phoenix_examples_parse_as_elixir():
    paths = sorted((ROOT / "evals" / "phoenix" / "inputs").glob("*.ex"))
    assert paths
    result = subprocess.run(
        [
            "elixir",
            "-e",
            "Enum.each(System.argv(), fn p -> Code.string_to_quoted!(File.read!(p)) end)",
            *map(str, paths),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
