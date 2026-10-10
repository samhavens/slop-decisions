"""Behavior controls for authored adaptations of observed agent-slop cleanups."""

import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "accumulation"
CASES = json.loads((SUITE / "cases.json").read_text())
HARNESS = runpy.run_path(str(ROOT / "scripts" / "skill_eval.py"))
ELIXIR = pytest.mark.skipif(not shutil.which("elixir"), reason="requires Elixir")


def snapshot(number, side="after"):
    return json.loads((SUITE / "inputs" / f"change-{number:02d}" / "source.json").read_text())[
        side
    ].copy()


def run(tmp_path, files, probe=None, tests=None):
    directory = tmp_path / f"run-{len(list(tmp_path.iterdir()))}"
    directory.mkdir()
    HARNESS["write_files"](directory, files)
    libs = sorted(directory.glob("lib/*.ex"))
    paths = (
        [directory / p for p in tests]
        if tests is not None
        else sorted(directory.glob("test/*.exs"))
    )
    expression = "Enum.each(System.argv(), &Code.require_file/1)"
    if probe:
        expression += "; " + probe
    return subprocess.run(
        ["elixir", "-e", expression, *map(str, libs + paths)],
        text=True,
        capture_output=True,
        timeout=20,
    )


def passed(result):
    assert result.returncode == 0, result.stdout + result.stderr


def rejected(result, assertion):
    assert result.returncode == 2, result.stdout + result.stderr
    assert assertion in result.stdout, result.stdout


def test_accumulation_preparation_keeps_labels_and_provenance_out_of_review(tmp_path):
    result = HARNESS["prepare"](tmp_path / "arm", ROOT / "skills/slop-review", suite=SUITE)
    assert result["cases"] == 12
    arm = tmp_path / "arm"
    tasks = json.loads((arm / "tasks.json").read_text())
    assert {t["case_id"] for t in tasks} == {c["case_id"] for c in CASES if c["pilot"]}
    assert not (arm / "cases.json").exists()
    assert not (arm / "provenance.json").exists()
    assert (arm / "request.txt").read_text().endswith((SUITE / "request.txt").read_text())
    for task in tasks:
        source = snapshot(int(task["case_id"].split("-")[1]))
        for path, text in source.items():
            assert (arm / task["repository"] / path).read_text() == text


@ELIXIR
def test_all_accumulation_source_parses(tmp_path):
    paths = []
    for case in CASES:
        data = json.loads((SUITE / case["source"]).read_text())
        for side in ["before", "after"]:
            directory = tmp_path / case["case_id"] / side
            HARNESS["write_files"](directory, data[side])
            paths.extend(directory.rglob("*.ex"))
            paths.extend(directory.rglob("*.exs"))
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
    passed(result)


@ELIXIR
def test_disabled_persistence_passes_manufactured_proofs_but_fails_retained_owner(tmp_path):
    for n in [1, 2, 3]:
        files = snapshot(n)
        passed(run(tmp_path, files))
        files["lib/accounts.ex"] = files["lib/accounts.ex"].replace(
            "Agent.update(store, &Map.put(&1, row.id, row))", ":ok"
        )
        if n == 2:
            rejected(run(tmp_path, files), "Accounts.get(store, 42) == row")
        else:
            passed(run(tmp_path, files))
        passed(
            run(
                tmp_path,
                files,
                tests=[],
                probe=(
                    "{:ok, s} = Agent.start_link(fn -> %{} end); "
                    ":ok = Accounts.save(s, %{id: 42}); nil = Accounts.get(s, 42)"
                ),
            )
        )
    files = snapshot(4)
    passed(run(tmp_path, files))
    files["lib/presenter.ex"] = files["lib/presenter.ex"].replace('-> "Access denied"', '-> "Sent"')
    rejected(run(tmp_path, files), 'Presenter.submit(gateway, :request) == "Access denied"')


@ELIXIR
def test_circular_oracle_and_unreachable_guard_controls(tmp_path):
    for n in [5, 6]:
        files = snapshot(n)
        passed(run(tmp_path, files))
        files["lib/price.ex"] = files["lib/price.ex"].replace("price * quantity", "price")
        passed(run(tmp_path, files, tests=[], probe="200 = Checkout.total([{200, 2}])"))
        if n == 5:
            passed(run(tmp_path, files))
        else:
            rejected(run(tmp_path, files), "Checkout.total([{200, 2}]) == 400")
    for n in [7, 8]:
        files = snapshot(n)
        passed(run(tmp_path, files))
        files["lib/documents.ex"] = files["lib/documents.ex"].replace(
            "if row.owner == user", "if true"
        )
        passed(
            run(
                tmp_path,
                files,
                tests=[],
                probe=(
                    "{:ok, s} = Agent.start_link(fn -> %{1 => %{owner: :alice}} end); "
                    ":ok = Documents.delete(s, 1, :bob); 0 = map_size(Agent.get(s, & &1))"
                ),
            )
        )
        if n == 7:
            passed(run(tmp_path, files))
        else:
            rejected(run(tmp_path, files), "Documents.delete(store, 1, :bob)")


@ELIXIR
def test_redundancy_needs_retained_owner_and_distinct_boundary_control(tmp_path):
    files = snapshot(9)
    passed(run(tmp_path, files))
    files["lib/profile.ex"] = files["lib/profile.ex"].replace(
        "String.downcase()", "String.upcase()"
    )
    rejected(
        run(tmp_path, files, tests=["test/profile_test.exs"]), "Profile.name(input) == expected"
    )
    rejected(
        run(tmp_path, files, tests=["test/normalize_test.exs"]), "Normalize.name(input) == expected"
    )
    files = snapshot(10)
    passed(run(tmp_path, files))
    files["lib/profile.ex"] = files["lib/profile.ex"].replace(
        'Map.fetch!("name")', 'Map.fetch!("city")'
    )
    passed(run(tmp_path, files, tests=["test/normalize_test.exs"]))
    rejected(run(tmp_path, files, tests=["test/profile_test.exs"]), "Profile.from_query")


@ELIXIR
def test_constructor_and_clock_boundaries_have_meaningful_controls(tmp_path):
    passed(run(tmp_path, snapshot(11)))
    files = snapshot(12)
    passed(run(tmp_path, files))
    files["lib/job.ex"] = files["lib/job.ex"].replace("String.trim(name)", "name")
    rejected(run(tmp_path, files), 'Job.new("  Build ")')
    files = snapshot(14)
    passed(run(tmp_path, files))
    files["lib/receipt.ex"] = files["lib/receipt.ex"].replace("clock.now()", "0")
    rejected(run(tmp_path, files), "Receipt.stamp(42, FixedClock)")


@ELIXIR
def test_removing_test_seam_keeps_coverage_that_rejects_a_broken_record(tmp_path):
    files = snapshot(13)
    passed(run(tmp_path, files))
    del files["test/state_test.exs"]
    files["lib/ledger.ex"] = files["lib/ledger.ex"].replace(
        "  def __test_state__(pid), do: Agent.get(pid, & &1)\n", ""
    )
    passed(run(tmp_path, files))
    files["lib/ledger.ex"] = files["lib/ledger.ex"].replace(
        "Agent.update(pid, &%{entries: [n | &1.entries]})", ":ok"
    )
    rejected(run(tmp_path, files), "App.add_charge(pid, 3) == 3")


@ELIXIR
def test_environment_repair_has_an_independent_cause(tmp_path):
    rejected(run(tmp_path, snapshot(15, "before")), "Accounts.get(store, 43) == row")
    files = snapshot(15)
    passed(run(tmp_path, files))
    files["test/lookup_test.exs"] = (
        files["test/lookup_test.exs"]
        .replace("Process.sleep(50)", ":ok")
        .replace("async: false", "async: true")
    )
    passed(run(tmp_path, files))
    passed(run(tmp_path, snapshot(16)))


@ELIXIR
def test_weaker_assertions_and_valid_pruning_have_opposite_control_results(tmp_path):
    for side in ["before", "after"]:
        files = snapshot(17, side)
        passed(run(tmp_path, files))
        files["lib/refund.ex"] = files["lib/refund.ex"].replace("div(original, 2)", "1")
        if side == "before":
            rejected(run(tmp_path, files), "Refund.amount(200) == 100")
        else:
            passed(run(tmp_path, files))
    files = snapshot(18)
    passed(run(tmp_path, snapshot(18, "before")))
    passed(run(tmp_path, files))
    files["lib/counter.ex"] = files["lib/counter.ex"].replace("Agent.update(pid, &(&1 + n))", ":ok")
    rejected(run(tmp_path, files), "Counter.value(pid) == 2")


@ELIXIR
def test_unexpected_failure_and_real_absence_remain_distinct(tmp_path):
    passed(
        run(
            tmp_path,
            snapshot(19, "before"),
            probe=(
                'result = try do Resolver.provider_id("id", fn _ -> '
                'raise "catalog offline" end) rescue RuntimeError -> :outage end; '
                ":outage = result"
            ),
        )
    )
    passed(
        run(
            tmp_path,
            snapshot(19),
            probe=(
                '{:error, :program_not_found} = Resolver.provider_id("id", '
                'fn _ -> raise "catalog offline" end)'
            ),
        )
    )
    passed(run(tmp_path, snapshot(20)))
