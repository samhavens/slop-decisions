import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

from slop_decisions.rubrics import load_rubrics

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "discovery"
CASES = json.loads((SUITE / "cases.json").read_text())
HARNESS = runpy.run_path(str(ROOT / "scripts" / "skill_eval.py"))
ELIXIR = pytest.mark.skipif(not shutil.which("elixir"), reason="requires Elixir")


def source(number):
    return json.loads((SUITE / f"inputs/change-{number:02}/source.json").read_text())


def execute(tmp_path, number, probe="", *, version="after", replacements=None, test=False):
    files = dict(source(number)[version])
    for path, pairs in (replacements or {}).items():
        for old, new in pairs:
            assert old in files[path]
            files[path] = files[path].replace(old, new)
    scratch = tmp_path / f"run-{len(list(tmp_path.iterdir()))}"
    scratch.mkdir()
    HARNESS["write_files"](scratch, files)
    # Explicit ordering loads macro definitions before their consumers.
    libraries = sorted(path for path in files if path.endswith(".ex"))
    if "lib/fields.ex" in libraries:
        libraries.remove("lib/fields.ex")
        libraries.insert(0, "lib/fields.ex")
    args = ["elixir"]
    for path in libraries:
        args += ["-r", path]
    if test:
        for path in sorted(path for path in files if path.endswith("_test.exs")):
            args += ["-r", path]
    args += ["-e", probe or ":ok"]
    return subprocess.run(args, cwd=scratch, capture_output=True, text=True, timeout=30)


def passed(result):
    assert result.returncode == 0, result.stdout + result.stderr


def test_each_new_rule_has_a_positive_and_a_valid_lookalike():
    bank = load_rubrics()
    dimensions = {case["dimension"] for case in CASES}
    assert len(dimensions) == 9
    for name in dimensions:
        rule = bank[name]
        assert rule["sources"] and rule["search_trigger"] and rule["investigation"]
        assert {"finding", "no_finding"} <= {
            case["expected"] for case in CASES if case["dimension"] == name
        }
    assert any(case["expected"] == "insufficient_context" for case in CASES)


def test_prepared_repos_have_real_diffs_and_no_answer_keys(tmp_path):
    result = HARNESS["prepare"](tmp_path / "arm", ROOT / "skills" / "slop-review")
    arm = Path(result["directory"])
    tasks = json.loads((arm / "tasks.json").read_text())
    assert len(tasks) == 12
    assert all(set(task) == {"case_id", "repository", "base"} for task in tasks)
    assert not list(arm.rglob("source.json"))
    assert not (arm / "cases.json").exists()
    assert (arm / "skill" / "references" / "consistency.md").is_file()
    for task in tasks:
        repo = arm / task["repository"]
        assert HARNESS["git"](repo, "status", "--porcelain")
        assert HARNESS["git"](repo, "rev-parse", "HEAD") == task["base"]
        expected = json.loads((SUITE / "inputs" / task["case_id"] / "source.json").read_text())
        for path, content in expected["after"].items():
            assert (repo / path).read_text() == content
    history = HARNESS["git"](arm / "cases/change-06", "log", "-p", "--", "lib/status_server.ex")
    assert "+  def handle_call({:snapshot, :v1}" in history
    with pytest.raises(ValueError, match="exists"):
        HARNESS["prepare"](arm)
    plain = tmp_path / "plain"
    HARNESS["prepare"](plain)
    assert not (plain / "skill").exists()
    assert (plain / "tasks.json").read_bytes() == (arm / "tasks.json").read_bytes()


@ELIXIR
def test_all_discovery_source_parses(tmp_path):
    paths = []
    for case in CASES:
        snapshots = json.loads((SUITE / case["source"]).read_text())
        for version in ("before", "after"):
            for name, content in snapshots[version].items():
                path = tmp_path / case["case_id"] / version / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                paths.append(str(path))
    passed(
        subprocess.run(
            [
                "elixir",
                "-e",
                "Enum.each(System.argv(), fn p -> Code.string_to_quoted!(File.read!(p)) end)",
                *paths,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    )


@ELIXIR
def test_specializing_policies_preserves_the_supported_results(tmp_path):
    # Equivalence validates the repair; the maintenance burden is still source-reviewed.
    probe = """
    for subtotal <- [0, 2, 100], tax <- [0, 1, 17] do
      result = Billing.complete(%{subtotal: subtotal, tax: tax})
      true = result == %{kind: :invoice, total: subtotal + tax, paid: true}
    end
    for days <- [1, 7, 30] do
      true = Trials.activate(%{days: days}) == %{kind: :trial, days: days, paid: false}
    end
    """
    for version in ("before", "after"):
        passed(execute(tmp_path, 1, probe, version=version))
    passed(
        execute(
            tmp_path,
            2,
            '"1,2" = Export.encode([1, 2], :csv); "1\\t2" = Export.encode([1, 2], :tsv)',
        )
    )


@ELIXIR
def test_equivalent_private_state_breaks_only_the_brittle_assertion(tmp_path):
    replacements = {
        "lib/counter.ex": [
            ("fn -> %{value: 0} end", "fn -> 0 end"),
            ("&%{&1 | value: &1.value + amount}", "&(&1 + amount)"),
            ("& &1.value", "& &1"),
        ]
    }
    passed(execute(tmp_path, 3, test=True))
    passed(execute(tmp_path, 3, test=True, version="before", replacements=replacements))
    result = execute(tmp_path, 3, test=True, replacements=replacements)
    assert result.returncode != 0
    assert "Assertion with == failed" in result.stdout and "get_state" in result.stdout
    passed(execute(tmp_path, 4, test=True))
    result = execute(
        tmp_path,
        4,
        test=True,
        replacements={
            "lib/checkout.ex": [
                ("do: gateway.(id)", "do: (gateway.(id); gateway.(id))"),
            ]
        },
    )
    assert result.returncode != 0 and "refute_received" in result.stdout


@ELIXIR
def test_process_layout_and_public_protocol_boundaries(tmp_path):
    probe = """
    {:ok, pid} = Worklist.start_link()
    Worklist.add(pid, :a)
    1 = Dashboard.pending_count(pid)
    [:a] = Export.pending_ids(pid)
    {:ok, :a} = Worklist.take(pid)
    """
    passed(execute(tmp_path, 5, probe))
    # Renaming a private key leaves the owner's public behavior intact, while two callers break.
    replacement = {"lib/worklist.ex": [("pending", "jobs")]}
    passed(
        execute(
            tmp_path,
            5,
            "{:ok, p} = Worklist.start_link(); Worklist.add(p, :a); {:ok, :a} = Worklist.take(p)",
            replacements=replacement,
        )
    )
    for caller in ["Dashboard.pending_count", "Export.pending_ids"]:
        result = execute(
            tmp_path,
            5,
            f"{{:ok, p}} = Worklist.start_link(); {caller}(p)",
            replacements=replacement,
        )
        assert result.returncode != 0 and "KeyError" in result.stderr
    passed(execute(tmp_path, 6, test=True))


@ELIXIR
def test_two_reservations_can_interleave_between_real_agent_calls(tmp_path):
    # The barrier fixes a legal schedule between the read and write; it adds no data changes.
    replacement = {
        "lib/slots.ex": [
            (
                "Agent.update(pid, &(&1 - 1))",
                """
      send(Process.whereis(:witness), {:read_complete, self()})
      receive do :resume -> :ok end
      Agent.update(pid, &(&1 - 1))
    """,
            )
        ]
    }
    passed(
        execute(
            tmp_path,
            7,
            """
    Process.register(self(), :witness)
    {:ok, pool} = Slots.start_link(1)
    jobs = for _ <- 1..2, do: Task.async(fn -> Slots.reserve(pool) end)
    pids = for _ <- 1..2 do
      receive do {:read_complete, pid} -> pid after 1000 -> raise "barrier timeout" end
    end
    Enum.each(pids, &send(&1, :resume))
    [:ok, :ok] = Enum.map(jobs, &Task.await/1)
    -1 = Slots.available(pool)
    """,
            replacements=replacement,
        )
    )
    passed(
        execute(
            tmp_path,
            8,
            """
    {:ok, pool} = Slots.start_link(1)
    jobs = for _ <- 1..100, do: Task.async(fn -> Booking.reserve(pool) end)
    results = Enum.map(jobs, &Task.await/1)
    1 = Enum.count(results, &(&1 == :ok))
    99 = Enum.count(results, &(&1 == :full))
    0 = Slots.available(pool)
    """,
        )
    )


@ELIXIR
def test_retry_identity_changes_number_of_real_model_effects(tmp_path):
    for number, count in [(9, 2), (10, 1)]:
        passed(
            execute(
                tmp_path,
                number,
                f"""
        {{:ok, carrier}} = Shipping.start_link()
        ShipOrder.run(carrier, %{{operation_id: "shipment-1"}})
        {count} = map_size(Shipping.shipments(carrier))
        """,
            )
        )


@ELIXIR
def test_process_capture_environment_excludes_unused_payload_after_extraction(tmp_path):
    for number, condition in [(13, "> 10000"), (14, "< 32")]:
        src = source(number)["after"]["lib/audit.ex"]
        line = next(line.strip() for line in src.splitlines() if "Task.start(" in line)
        closure = line.removeprefix("Task.start(").removesuffix(")")
        passed(
            execute(
                tmp_path,
                number,
                f"""
        request = %{{id: make_ref(), payload: Enum.map(1..10000, &%{{n: &1}})}}
        fun = Audit.record(request, self())
        {{:env, env}} = :erlang.fun_info(fun, :env)
        true = :erts_debug.flat_size(env) {condition}
        """,
                replacements={"lib/audit.ex": [(line, closure)]},
            )
        )


@ELIXIR
def test_client_instances_and_captured_defaults(tmp_path):
    passed(
        execute(tmp_path, 15, 'a = Client.new("a"); _b = Client.new("b"); "b" = Client.endpoint(a)')
    )
    passed(
        execute(
            tmp_path,
            16,
            """
    Application.put_env(:review_fixture, :endpoint, "a")
    a = Client.new([])
    b = Client.new(endpoint: "b")
    Application.put_env(:review_fixture, :endpoint, "c")
    "a" = Client.endpoint(a)
    "b" = Client.endpoint(b)
    "c" = Client.endpoint(Client.new([]))
    """,
        )
    )


@ELIXIR
def test_macro_replacement_and_required_syntax_capture(tmp_path):
    for version in ("before", "after"):
        passed(
            execute(
                tmp_path,
                17,
                """
        for values <- [[1], [0, 2, -3], [100, 200]] do
          input = Enum.join(values, " , ")
          ^values = FirstReader.read(input)
          ^values = SecondReader.read(input)
        end
        try do
          FirstReader.read("no integer")
          raise "should reject"
        rescue
          ArgumentError -> :ok
        end
        """,
                version=version,
            )
        )
    passed(
        execute(
            tmp_path,
            18,
            """
    require Contracts
    :ok = Contracts.check(2 > 1)
    try do
      Contracts.check(1 > 2)
      raise "should reject"
    rescue
      e in RuntimeError -> "check failed: 1 > 2" = e.message
    end
    """,
        )
    )


@ELIXIR
def test_nested_retry_budget_counts_attempts_including_first(tmp_path):
    for number, count in [(19, 12), (20, 4)]:
        passed(
            execute(
                tmp_path,
                number,
                f"""
        Process.put(:requests, 0)
        transport = fn ->
          Process.put(:requests, Process.get(:requests) + 1)
          {{:error, :busy}}
        end
        {{:error, :busy}} = Lookup.run(transport)
        {count} = Process.get(:requests)
        """,
            )
        )
