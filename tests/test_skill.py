import json
import re
import shutil
from pathlib import Path

from slop_decisions.rubrics import load_rubrics

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "slop-review"


def test_skill_rules_match_the_api_rules():
    # A standalone install must retain both the predicates and their exceptions.
    rules = json.loads((SKILL / "references" / "rules.json").read_text())
    assert rules == list(load_rubrics().values())


def test_skill_references_work_after_standalone_install(tmp_path):
    installed = tmp_path / ".agents" / "skills" / "slop-review"
    shutil.copytree(SKILL, installed)
    instructions = (installed / "SKILL.md").read_text()
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", instructions)
    local_links = [link for link in links if "://" not in link and not link.startswith("#")]
    assert local_links, "The installed skill must include its rules."
    for link in local_links:
        target = (installed / link.split("#")[0]).resolve()
        assert target.is_relative_to(installed.resolve())
        assert target.is_file(), f"Missing standalone skill resource: {link}"
    assert json.loads((installed / "references" / "rules.json").read_text())
