"""Run pinned source witnesses. Requires Elixir; never used as model context.

Only Tesla's two test modules are reproduced as upstream suites. Other cases
use extracted code and explicit stubs; they are unit witnesses, not integration
or whole-project reproductions. No third-party dependencies are installed.
"""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from slop_decisions.dataset import load_dataset, packet_for, verify_source


def run_elixir(name, body, expected_failures=0):
    prelude = "ExUnit.start(autorun: false)\n"
    ending = """
r = ExUnit.run()
IO.puts("WITNESS_RESULT #{r.total} #{r.failures}")
"""
    with tempfile.TemporaryDirectory(prefix="slop-witness-") as directory:
        script = Path(directory) / "witness.exs"
        script.write_text(prelude + body + ending)
        result = subprocess.run(["elixir", str(script)], capture_output=True, text=True, timeout=60)
    match = re.search(r"WITNESS_RESULT (\d+) (\d+)", result.stdout)
    if result.returncode or not match or int(match[2]) != expected_failures or int(match[1]) == 0:
        raise RuntimeError(f"{name} failed:\n{result.stdout}\n{result.stderr}")
    return {
        "witness": name,
        "tests": int(match[1]),
        "observed_test_failures": int(match[2]),
        "expected_test_failures": expected_failures,
        "verified": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path(".cache/slop-decisions/sources"))
    parser.add_argument("--out", type=Path, default=Path("runs/witnesses.json"))
    args = parser.parse_args()
    if not shutil.which("elixir"):
        raise SystemExit("Elixir is required for witnesses; install it, then rerun this command.")
    sources, targets, _ = load_dataset()
    by_id = {t["case_id"]: t for t in targets}

    def source(repo, revision, path):
        item = next(
            s for s in sources if (s["repo"], s["revision"], s["path"]) == (repo, revision, path)
        )
        return verify_source(args.cache, item).read_text()

    def target(cid):
        return packet_for(by_id[cid], sources, args.cache, "target")["files"][0]["content"]

    results = []
    # Four exact embedded code fixtures. Only module names change for isolation.
    modules = "\n".join(
        target(cid).replace("defmodule Test do", f"defmodule {name} do")
        for cid, name in [
            ("identity-exhaustive", "Exhaustive"),
            ("identity-partial", "Partial"),
            ("identity-projection", "Projection"),
            ("identity-unwrap", "Unwrap"),
        ]
    )
    results.append(
        run_elixir(
            "ex_slop_identity_semantics",
            modules
            + """
defmodule IdentityWitness do
  use ExUnit.Case
  test "exhaustive wrapper preserves each supplied value" do
    for x <- [nil, :other, {:ok, 1}, {:error, :failed}, %{a: 1, extra: 2}, [1, 2]] do
      assert Exhaustive.foo(x) == x
    end
  end
  test "partial wrapper preserves an unmatched-input exception" do
    assert Partial.foo({:ok, 1}) == {:ok, 1}
    assert_raise CaseClauseError, fn -> Partial.foo(:other) end
  end
  test "projection discards extra keys" do
    assert Projection.foo(%{a: 1, extra: 2}) == %{a: 1}
    refute Projection.foo(%{a: 1, extra: 2}) == %{a: 1, extra: 2}
  end
  test "unwrap changes the result" do
    assert Unwrap.foo({:ok, 1}) == 1
    refute Unwrap.foo({:ok, 1}) == {:ok, 1}
  end
end
""",
        )
    )
    # Reproduce both whole upstream test modules, baseline and controlled mutation.
    repo = "elixir-tesla/tesla"
    for side, rev in [
        ("before", "2f4b7f3608b3569cd12bc80216dba868926355d7"),
        ("after", "be1943321590014e61316194dd2d3d38e96a2d54"),
    ]:
        path_module = source(repo, rev, "lib/tesla/open_api/path_template.ex")
        path_tests = source(repo, rev, "test/tesla/open_api/path_template_test.exs")
        original = "      :error ->\n        :error"
        assert path_module.count(original) == 1
        mutant = path_module.replace(
            original, '      :error ->\n        raise "missing key mutant"'
        )
        results.append(
            run_elixir(f"tesla_private_{side}_baseline", path_module + "\n" + path_tests)
        )
        results.append(
            run_elixir(
                f"tesla_private_{side}_mutant",
                mutant + "\n" + path_tests,
                expected_failures=int(side == "after"),
            )
        )
        param = source(repo, rev, "lib/tesla/param.ex")
        cookie = source(repo, rev, "lib/tesla/open_api/cookie_param.ex")
        collection = source(repo, rev, "lib/tesla/open_api/cookie_params.ex")
        tests = source(repo, rev, "test/tesla/open_api/cookie_params_test.exs")
        original = 'Param.encode_unreserved(key) <> "=" <> encode_form_value(param, value)'
        assert cookie.count(original) == 1
        mutant = cookie.replace(
            original, 'to_string(key) <> "=" <> encode_form_value(param, value)'
        )
        results.append(
            run_elixir(
                f"tesla_cookie_{side}_baseline", "\n".join([param, cookie, collection, tests])
            )
        )
        results.append(
            run_elixir(
                f"tesla_cookie_{side}_mutant",
                "\n".join([param, mutant, collection, tests]),
                expected_failures=int(side == "after"),
            )
        )
    # Stream implementation intact; explicit fake transport supplies its callback events.
    transport = """
defmodule Finch.Response do
  defstruct [:status, :headers, :body]
end
defmodule Finch do
  def stream(mode, _name, _acc, callback, _opts) do
    status = callback.({:status, 200}, nil)
    callback.({:headers, []}, status)
    callback.({:data, "hello"}, nil)
    case mode do
      :complete -> {:ok, nil}
      :closed -> {:error, :closed}
      :timeout -> receive do :never -> {:ok, nil} end
    end
  end
end
defmodule Tesla.Error do
  defexception [:env, :reason]
  def message(e), do: inspect(e.reason)
end
"""
    for side, module in [("before", "OldStream"), ("after", "NewStream")]:
        fragment = target(f"tesla-stream-{side}").replace("defp stream(", "def stream(", 1)
        transport += (
            f"\ndefmodule {module} do\n"
            + fragment
            + """
  defp handle_stream_response({:ok, _}, ref, owner), do: send(owner, {ref, :eof})
  defp handle_stream_response({:error, error}, ref, owner), do: send(owner, {ref, {:error, error}})
"""
        )
        if side == "after":
            transport += "  defp unwrap_error(error), do: error\n"
        transport += "end\n"
    results.append(
        run_elixir(
            "tesla_stream_extracted_unit",
            transport
            + """
defmodule StreamWitness do
  use ExUnit.Case
  test "old stream silently accepts closed and timed-out responses" do
    for mode <- [:closed, :timeout] do
      {:ok, response} = OldStream.stream(mode, nil, receive_timeout: 100)
      assert Enum.to_list(response.body) == ["hello"]
    end
  end
  test "new stream signals each failure after consuming a chunk" do
    for mode <- [:closed, :timeout] do
      {:ok, response} = NewStream.stream(mode, nil, [receive_timeout: 100], %{})
      error = assert_raise Tesla.Error, fn -> Enum.to_list(response.body) end
      assert error.reason == mode
    end
  end
  test "both versions preserve successful completion" do
    {:ok, old} = OldStream.stream(:complete, nil, receive_timeout: 100)
    {:ok, new} = NewStream.stream(:complete, nil, [receive_timeout: 100], %{})
    assert Enum.to_list(old.body) == ["hello"]
    assert Enum.to_list(new.body) == ["hello"]
  end
end
""",
        )
    )
    # Metrics: exact batch implementation, explicit sending/formatting/telemetry stubs.
    telemetry = """
defmodule Broadway.Message do
  defstruct [:data, :failed]
  def failed(message, reason), do: %{message | failed: reason}
end
defmodule Pool do
  def send(result, _), do: result
end
defmodule Syslog do
  def format(event, _), do: event
end
defmodule :telemetry do
  def execute(event, measurements, metadata) do
    Process.put(:events, [{event, measurements, metadata} | Process.get(:events, [])])
  end
end
"""
    for side, name in [("before", "OldPipeline"), ("after", "NewPipeline")]:
        telemetry += (
            f"\ndefmodule {name} do\n"
            + target(f"logflare-egress-{side}")
            + """
  defp lookup_backend(_), do: %{config: %{}, metadata: %{}}
  defp fail_batch(messages, reason), do: Enum.map(messages, &Broadway.Message.failed(&1, reason))
end
"""
        )
    results.append(
        run_elixir(
            "logflare_egress_extracted_unit",
            telemetry
            + """
defmodule EgressWitness do
  use ExUnit.Case
  test "old code emits egress on failure; repaired code emits only on success" do
    for module <- [OldPipeline, NewPipeline], result <- [:ok, {:error, :closed}] do
      Process.put(:events, [])
      context = %{pool: result, backend_id: 1, source_id: 2, source_token: "source",
                  backend_token: "backend", user_id: 3, system_source: false}
      messages = [struct(Broadway.Message, data: "hello")]
      returned = module.handle_batch(:syslog, messages, nil, context)
      expected = if(module == OldPipeline or result == :ok, do: 1, else: 0)
      assert length(Process.get(:events)) == expected
      assert hd(returned).failed == if(result == :ok, do: nil, else: :closed)
    end
  end
end
""",
        )
    )
    # Exact accumulation loops; controlled chunk reader; count structure visits rather than timing.
    loops = ""
    for side, name in [("before", "OldReader"), ("after", "NewReader")]:
        fragment = target(f"bandit-traversal-{side}")
        fragment = fragment.split("    # do_read_chunk will")[0]
        fragment = fragment.replace("IO.iodata_length(", "measure(")
        entry = (
            "do_read_chunked_data!(nil, chunks, <<>>, opts)"
            if side == "before"
            else "do_read_chunked_data!(nil, chunks, <<>>, 0, opts)"
        )
        loops += (
            f"\ndefmodule {name} do\n"
            + fragment
            + f"\n  def read(chunks, opts), do: {entry}\n"
            + """
  defp do_read_chunk!(_, [], _, _), do: {<<>>, []}
  defp do_read_chunk!(_, [chunk | rest], max, _) do
    if byte_size(chunk) <= max do
      {chunk, rest}
    else
      <<head::binary-size(max), tail::binary>> = chunk
      {head, [tail | rest]}
    end
  end
  defp measure(data) do
    Process.put(:work, Process.get(:work, 0) + visits(data))
    IO.iodata_length(data)
  end
  defp visits([]), do: 0
  defp visits([head | tail]), do: 1 + visits(head) + visits(tail)
  defp visits(_), do: 1
end
"""
        )
    results.append(
        run_elixir(
            "bandit_accumulation_extracted_unit",
            loops
            + """
defmodule ReaderWitness do
  use ExUnit.Case
  test "both implementations preserve data, buffers, and length limits" do
    for size <- 1..8, count <- 1..20, limit <- [1, size, size*count, size*count+1] do
      chunks = List.duplicate(String.duplicate("x", size), count)
      old = OldReader.read(chunks, length: limit)
      new = NewReader.read(chunks, length: limit)
      assert old == new
      {_, data, _} = new
      assert IO.iodata_length(data) == min(limit, size*count)
    end
  end
  test "old work grows quadratically and new work linearly" do
    work = fn module, n ->
      Process.put(:work, 0)
      module.read(List.duplicate("x", n), length: n+1)
      Process.get(:work)
    end
    assert work.(OldReader, 200) > 3 * work.(OldReader, 100)
    assert work.(NewReader, 200) == 2 * work.(NewReader, 100)
    assert work.(OldReader, 100) > 20 * work.(NewReader, 100)
  end
end
""",
        )
    )
    version = subprocess.run(
        ["elixir", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    report = {
        "elixir": version,
        "results": results,
        "scope": (
            "Tesla cookie/private full upstream test modules with controlled mutations; "
            "identity, stream, metrics, and accumulation extracted-unit witnesses. "
            "Boundary taste and setup duplication remain candidate judgments."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
