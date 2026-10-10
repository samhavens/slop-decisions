"""Author the fixed contract fixtures. No model output is used to make labels."""
# ruff: noqa: E501 -- preserve the Elixir source and witness literals.

import json
from pathlib import Path
from textwrap import dedent

CASES = []


def code(value):
    return dedent(value).strip() + "\n"


def group(split, dimension, focus, defect, repair, control, missing, reasons, witnesses=None):
    witnesses = witnesses or {}
    family = f"{split}-{dimension}"
    for role, source, expected, reason in zip(
        ("defect", "repair", "control", "missing"),
        (defect, repair, control, missing),
        ("defect", "clean", "clean", "unassessable"),
        reasons,
        strict=True,
    ):
        content = code(source)
        end = len(content.splitlines())
        CASES.append(
            {
                "case_id": f"{family}-{role}",
                "family": family + ("-control" if role == "control" else ""),
                "split": split,
                "dimension": dimension,
                "expected": expected,
                "basis": "executable" if role in witnesses else "source_review",
                "rationale": reason,
                "witness": code(witnesses[role]) if role in witnesses else None,
                "packet": {
                    "target": {
                        "path": "sample.ex",
                        "start_line": 1,
                        "end_line": end,
                        "focus": focus,
                    },
                    "files": [
                        {"path": "sample.ex", "start_line": 1, "end_line": end, "content": content}
                    ],
                },
            }
        )


s = "calibration"
group(
    s,
    "success_shaped_failure",
    "Return contract of read/1.",
    """defmodule Sample do
      # The argument is the result of the authoritative database query.
      def read({:ok, rows}), do: {:ok, rows}
      def read({:error, _reason}), do: {:ok, []}
    end""",
    """defmodule Sample do
      def read({:ok, rows}), do: {:ok, rows}
      def read({:error, reason}), do: {:error, reason}
    end""",
    """defmodule Sample do
      # A cache miss is normal; database is the authoritative lookup.
      def read(cache, database) do
        case cache.() do
          {:ok, rows} -> {:ok, rows}
          :miss -> database.()
        end
      end
    end""",
    """defmodule Sample do
      def read(query), do: Storage.read(query)
    end""",
    (
        "A database error becomes a successful empty query.",
        "The error remains an error.",
        "An optional cache miss falls back to the authority.",
        "Storage.read and its failure contract are absent.",
    ),
    {
        "defect": 'unless Sample.read({:error, :offline}) == {:ok, []}, do: raise("witness")',
        "repair": 'unless Sample.read({:error, :offline}) == {:error, :offline}, do: raise("witness")',
        "control": 'unless Sample.read(fn -> :miss end, fn -> {:error, :offline} end) == {:error, :offline}, do: raise("witness")',
    },
)

group(
    s,
    "invalid_state_accommodation",
    "Private name/1 after run/1 normalization; this is the complete module.",
    """defmodule Sample do
      def run(input), do: name(%{name: to_string(input)})
      defp name(nil), do: ""
      defp name(%{"name" => n}), do: n
      defp name(%{name: n}), do: n
    end""",
    """defmodule Sample do
      def run(input), do: name(%{name: to_string(input)})
      defp name(%{name: n}), do: n
    end""",
    """defmodule Sample do
      # Public adapter accepts both JSON maps and internal maps.
      def name(%{"name" => n}), do: n
      def name(%{name: n}), do: n
    end""",
    """defmodule Sample do
      def run(input), do: Format.name(Normalizer.normalize(input))
    end""",
    (
        "Only atom-key maps can reach the private helper.",
        "The helper accepts only its actual internal contract.",
        "The public adapter intentionally supports both formats.",
        "Neither normalization nor the helper contract is supplied.",
    ),
)

group(
    s,
    "test_claim_gap",
    "The supplied assertion suite's ability to detect an abs/1 implementation replaced by identity.",
    """defmodule Sample do
      def magnitude(x), do: abs(x)
      def test, do: 4 = magnitude(4)
    end""",
    """defmodule Sample do
      def magnitude(x), do: abs(x)
      def test do
        4 = magnitude(4)
        4 = magnitude(-4)
      end
    end""",
    """defmodule Sample do
      def magnitude(x), do: abs(x)
      def test, do: assert_magnitudes(&magnitude/1)
      defp assert_magnitudes(f) do
        4 = f.(4)
        4 = f.(-4)
      end
    end""",
    """defmodule Sample do
      def test, do: Assertions.magnitudes(&Numbers.magnitude/1)
    end""",
    (
        "Identity passes the only assertion.",
        "A negative input kills identity.",
        "The supplied helper kills the same mutant.",
        "Assertions and implementation are absent.",
    ),
    {
        "defect": "Sample.test()\n4 = (fn x -> x end).(4)",
        "repair": 'Sample.test()\nif (fn x -> x end).(-4) == 4, do: raise("mutant survived")',
        "control": 'Sample.test()\nif (fn x -> x end).(-4) == 4, do: raise("mutant survived")',
    },
)

group(
    s,
    "semantic_duplicate",
    "export/1 versus the existing canonical invoice_total/1; both consumers use the same billing policy.",
    """defmodule Sample do
      def invoice_total(lines), do: Enum.reduce(lines, 0, fn {price, qty}, n -> n + price * qty end)
      def export(lines), do: Enum.reduce(lines, 0, fn {price, qty}, n -> n + price * qty end)
    end""",
    """defmodule Sample do
      def invoice_total(lines), do: Enum.reduce(lines, 0, fn {price, qty}, n -> n + price * qty end)
      def export(lines), do: invoice_total(lines)
    end""",
    """defmodule Sample do
      # Refunds use original prices; new sales use discounted prices.
      def refund(lines), do: Enum.reduce(lines, 0, fn x, n -> n + x.original * x.qty end)
      def sale(lines), do: Enum.reduce(lines, 0, fn x, n -> n + x.discounted * x.qty end)
    end""",
    """defmodule Sample do
      def export(lines), do: Enum.reduce(lines, 0, fn {p, q}, n -> n + p * q end)
    end""",
    (
        "Export repeats the complete billing rule.",
        "Export calls the canonical operation.",
        "The similar reductions enforce different price policies.",
        "No existing domain operation is supplied for comparison.",
    ),
)

group(
    s,
    "process_without_runtime_reason",
    "The full process and its sole client. There are no other children, timers, resources, or callers.",
    """defmodule Sample do
      use GenServer
      def start_link, do: GenServer.start_link(__MODULE__, nil)
      def init(nil), do: {:ok, nil}
      def square(pid, n), do: GenServer.call(pid, {:square, n})
      def handle_call({:square, n}, _, nil), do: {:reply, n * n, nil}
    end
    defmodule Client do
      def run(n) do
        {:ok, pid} = Sample.start_link()
        result = Sample.square(pid, n)
        GenServer.stop(pid)
        result
      end
    end""",
    """defmodule Sample do
      def square(n), do: n * n
    end
    defmodule Client do
      def run(n), do: Sample.square(n)
    end""",
    """defmodule Sample do
      use GenServer
      def start_link, do: GenServer.start_link(__MODULE__, 0)
      def init(n), do: {:ok, n}
      def next(pid), do: GenServer.call(pid, :next)
      def handle_call(:next, _, n), do: {:reply, n, n + 1}
    end
    # Shared by concurrent clients that require distinct sequence numbers.""",
    """defmodule Client do
      def run(pid, n), do: GenServer.call(pid, {:square, n})
    end""",
    (
        "Every call owns a disposable process for pure multiplication.",
        "The process is removed.",
        "The process serializes ownership of a shared sequence.",
        "Process initialization, state, and lifecycle are absent.",
    ),
)

group(
    s,
    "policy_free_abstraction",
    "Private route/2 and its only caller in this complete module.",
    """defmodule Sample do
      def encode(n), do: route(n, :decimal)
      defp route(n, :decimal), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      def encode(n), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      @doc "Stable public entry point for decimal IDs; callers need not know the storage library."
      def encode(n), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      def encode(n), do: Router.route(n)
    end""",
    (
        "A private constant option adds no choice or boundary.",
        "The constant route is removed.",
        "A documented public API is a useful boundary.",
        "The router's policy and consumers are missing.",
    ),
)

group(
    s,
    "derived_state_drift",
    "Stored count versus items after remove/2. All state transitions are shown.",
    """defmodule Sample do
      def new(xs), do: %{items: xs, count: length(xs)}
      def remove(s, x), do: %{s | items: List.delete(s.items, x)}
    end""",
    """defmodule Sample do
      def new(xs), do: %{items: xs, count: length(xs)}
      def remove(s, x) do
        xs = List.delete(s.items, x)
        %{s | items: xs, count: length(xs)}
      end
    end""",
    """defmodule Sample do
      def new(xs), do: %{items: xs, original_count: length(xs)}
      # original_count is a historical snapshot, not a current count.
      def remove(s, x), do: %{s | items: List.delete(s.items, x)}
    end""",
    """defmodule Sample do
      def new(xs), do: %{items: xs, count: length(xs)}
      def remove(s, x), do: Collection.remove(s, x)
    end""",
    (
        "Removing an item leaves a stale count.",
        "Both representations change together.",
        "The snapshot has a different meaning.",
        "The update path is absent.",
    ),
    {
        "defect": 's = Sample.remove(Sample.new([:a]), :a)\nunless s.count != length(s.items), do: raise("witness")',
        "repair": 's = Sample.remove(Sample.new([:a]), :a)\nunless s.count == length(s.items), do: raise("witness")',
        "control": 's = Sample.remove(Sample.new([:a]), :a)\nunless s.original_count == 1 and s.items == [], do: raise("witness")',
    },
)

group(
    s,
    "disguised_state_machine",
    "Flags for one request, with the complete transitions shown.",
    """defmodule Sample do
      def new, do: %{loading: true, loaded: false, failed: false}
      def finish(s), do: %{s | loaded: true}
      def fail(s), do: %{s | failed: true}
    end""",
    """defmodule Sample do
      def new, do: :loading
      def finish(:loading), do: :loaded
      def fail(:loading), do: :failed
    end""",
    """defmodule Sample do
      # These are independent account capabilities.
      def new, do: %{can_export: false, can_import: false}
      def export(s), do: %{s | can_export: true}
      def import_data(s), do: %{s | can_import: true}
    end""",
    """defmodule Sample do
      def finish(s), do: Workflow.transition(s, :done)
    end""",
    (
        "Completion leaves loading and loaded true together.",
        "One phase replaces competing flags.",
        "Both capabilities can validly coexist.",
        "State and transition implementations are missing.",
    ),
    {
        "defect": 's = Sample.finish(Sample.new())\nunless s.loading and s.loaded, do: raise("witness")',
        "repair": ":loaded = Sample.finish(Sample.new())",
        "control": 's = Sample.new() |> Sample.export() |> Sample.import_data()\nunless s.can_export and s.can_import, do: raise("witness")',
    },
)

group(
    s,
    "timing_instead_of_synchronization",
    "Ordering between worker completion and reading the message.",
    """defmodule Sample do
      def run(f) do
        parent = self()
        spawn(fn -> send(parent, {:value, f.()}) end)
        Process.sleep(10)
        receive do
          {:value, x} -> x
        after
          0 -> :missing
        end
      end
    end""",
    """defmodule Sample do
      def run(f) do
        parent = self()
        spawn(fn -> send(parent, {:value, f.()}) end)
        receive do
          {:value, x} -> x
        after
          1000 -> :timeout
        end
      end
    end""",
    """defmodule Sample do
      # Tests the timeout branch: the server must deliberately answer late.
      def test do
        parent = self()
        spawn(fn -> Process.sleep(100); send(parent, :late) end)
        :timeout = receive do
          :late -> :reply
        after
          1 -> :timeout
        end
      end
    end""",
    """defmodule Sample do
      def run(f), do: Scheduler.finish(f)
    end""",
    (
        "Ten milliseconds cannot establish worker completion.",
        "The receive observes completion.",
        "Delay is the behavior needed to exercise a timeout.",
        "Scheduling and completion behavior are missing.",
    ),
)

group(
    s,
    "presentation_only_authorization",
    "Delete button and server delete handler, including all called authorization logic.",
    """defmodule Sample do
      def show_delete?(viewer, row), do: viewer.id == row.owner
      # Store.delete performs only persistence, without access checks.
      def delete(_viewer, row), do: Store.delete(row)
    end
    defmodule Store do
      def delete(row), do: {:deleted, row.id}
    end""",
    """defmodule Sample do
      def show_delete?(viewer, row), do: viewer.id == row.owner
      def delete(viewer, row) do
        if viewer.id == row.owner, do: Store.delete(row), else: {:error, :forbidden}
      end
    end
    defmodule Store do
      def delete(row), do: {:deleted, row.id}
    end""",
    """defmodule Sample do
      def show_delete?(viewer, row), do: viewer.id == row.owner
      def delete(viewer, row), do: Store.delete(viewer, row)
    end
    defmodule Store do
      def delete(viewer, row) do
        if viewer.id == row.owner, do: {:deleted, row.id}, else: {:error, :forbidden}
      end
    end""",
    """defmodule Sample do
      def show_delete?(viewer, row), do: viewer.id == row.owner
      def delete(viewer, row), do: Store.delete(viewer, row)
    end""",
    (
        "A caller can bypass the hidden button.",
        "The server enforces ownership.",
        "The context enforces ownership.",
        "The called context may authorize; its body is absent.",
    ),
    {
        "defect": "{:deleted, 3} = Sample.delete(%{id: 1}, %{owner: 2, id: 3})",
        "repair": "{:error, :forbidden} = Sample.delete(%{id: 1}, %{owner: 2, id: 3})",
        "control": "{:error, :forbidden} = Sample.delete(%{id: 1}, %{owner: 2, id: 3})",
    },
)

group(
    s,
    "framework_reimplementation",
    "request_values/2 in a project using Plug 1.16. Request header names are already lowercase.",
    """defmodule Sample do
      # Plug.Conn.get_req_header(conn, name) returns all matching values in order.
      # https://hexdocs.pm/plug/1.16.0/Plug.Conn.html#get_req_header/2
      def request_values(conn, name) do
        for {key, value} <- conn.req_headers, key == name, do: value
      end
    end""",
    """defmodule Sample do
      # Plug 1.16 get_req_header/2 returns all values for a lowercase request header name.
      def request_values(conn, name), do: Plug.Conn.get_req_header(conn, name)
    end""",
    """defmodule Sample do
      # Plug 1.16 get_req_header/2 uses exact lowercase name matching.
      # This adapter instead supports a prefix query across several header names.
      def request_values(conn, prefix) do
        for {key, value} <- conn.req_headers, String.starts_with?(key, prefix), do: {key, value}
      end
    end""",
    """defmodule Sample do
      def request_values(conn, name), do: Headers.lookup(conn, name)
    end""",
    (
        "The installed header accessor has the same contract.",
        "The framework accessor is used.",
        "Prefix lookup has materially different semantics.",
        "Custom lookup and installed facility contract are absent.",
    ),
)

group(
    s,
    "semantic_comment_noise",
    "The implementation comment immediately before the return expression.",
    """defmodule Sample do
      def next(n) do
        # Add one to n.
        n + 1
      end
    end""",
    """defmodule Sample do
      def next(n) do
        # Zero is reserved by the wire protocol.
        n + 1
      end
    end""",
    """defmodule Sample do
      @doc "Return the next sequence number."
      def next(n), do: n + 1
    end""",
    """defmodule Sample do
      # Reserve the next sequence number.
    end""",
    (
        "The comment restates addition.",
        "The comment explains an external constraint.",
        "Public API documentation is outside this predicate.",
        "No adjacent implementation is supplied.",
    ),
)

group(
    s,
    "avoidable_repeated_traversal",
    "Index generation in the complete reducer.",
    """defmodule Sample do
      def index(xs) do
        Enum.reduce(xs, [], fn x, acc -> [{length(acc), x} | acc] end)
      end
    end""",
    """defmodule Sample do
      def index(xs) do
        {acc, _} = Enum.reduce(xs, {[], 0}, fn x, {acc, n} -> {[{n, x} | acc], n + 1} end)
        acc
      end
    end""",
    """defmodule Sample do
      # Output includes every distinct prefix, so materializing each prefix is required.
      def prefixes(xs) do
        {_, out} = Enum.reduce(xs, {[], []}, fn x, {acc, out} ->
          acc = [x | acc]
          {acc, [Enum.reverse(acc) | out]}
        end)
        Enum.reverse(out)
      end
    end""",
    """defmodule Sample do
      def index(xs), do: Enum.reduce(xs, [], &Indexer.step/2)
    end""",
    (
        "length repeatedly walks an ever-growing linked list.",
        "A local index replaces repeated length calls.",
        "Each traversal constructs a required distinct output.",
        "The recursive step is absent.",
    ),
    {
        "defect": "[{2, :c}, {1, :b}, {0, :a}] = Sample.index([:a, :b, :c])",
        "repair": "[{2, :c}, {1, :b}, {0, :a}] = Sample.index([:a, :b, :c])",
        "control": "[[:a], [:a, :b]] = Sample.prefixes([:a, :b])",
    },
)

group(
    s,
    "redundant_wrapper",
    "The case expression in run/1 (or its replacement expression), not the public function boundary.",
    """defmodule Sample do
      def run(x) do
        case x do
          {:ok, v} -> {:ok, v}
          other -> other
        end
      end
    end""",
    """defmodule Sample do
      def run(x), do: x
    end""",
    """defmodule Sample do
      def run(x) do
        case x do
          {:ok, v} -> {:ok, v}
        end
      end
    end""",
    """defmodule Sample do
      def run(x), do: Wrapper.convert(x)
    end""",
    (
        "Every case returns its input unchanged.",
        "The case is removed.",
        "The partial case raises on unmatched inputs.",
        "The wrapper implementation is absent.",
    ),
    {
        "defect": 'for x <- [nil, 1, {:ok, 2}, :error], do: (unless Sample.run(x) == x, do: raise("witness"))',
        "repair": 'for x <- [nil, 1, {:ok, 2}, :error], do: (unless Sample.run(x) == x, do: raise("witness"))',
        "control": 'try do\n Sample.run(:error)\n raise("expected failure")\nrescue\n CaseClauseError -> :ok\nend',
    },
)

s = "holdout"
group(
    s,
    "success_shaped_failure",
    "Counter named delivered counts completed sends, never attempts. All send and metric paths are shown.",
    """defmodule Sample do
      def send_message(send_fn, payload) do
        result = send_fn.(payload)
        %{result: result, delivered: 1}
      end
    end""",
    """defmodule Sample do
      def send_message(send_fn, payload) do
        result = send_fn.(payload)
        delivered = if result == :ok, do: 1, else: 0
        %{result: result, delivered: delivered}
      end
    end""",
    """defmodule Sample do
      # attempted counts calls whether they succeed or fail.
      def send_message(send_fn, payload) do
        result = send_fn.(payload)
        %{result: result, attempted: 1}
      end
    end""",
    """defmodule Sample do
      def send_message(send_fn, payload), do: Delivery.send(send_fn, payload)
    end""",
    (
        "A failed send counts as delivered.",
        "Only a successful send counts as delivered.",
        "Attempt telemetry is valid on failure.",
        "Delivery and telemetry semantics are absent.",
    ),
    {
        "defect": '%{delivered: 1, result: {:error, :closed}} = Sample.send_message(fn _ -> {:error, :closed} end, "x")',
        "repair": '%{delivered: 0, result: {:error, :closed}} = Sample.send_message(fn _ -> {:error, :closed} end, "x")',
        "control": '%{attempted: 1, result: {:error, :closed}} = Sample.send_message(fn _ -> {:error, :closed} end, "x")',
    },
)

group(
    s,
    "invalid_state_accommodation",
    "Internal deliver/1, reached only through submit/1 in the complete module.",
    """defmodule Sample do
      def submit(text) when is_binary(text), do: deliver({:message, text})
      defp deliver({:message, text}), do: byte_size(text)
      defp deliver(text) when is_binary(text), do: byte_size(text)
      defp deliver([]), do: 0
    end""",
    """defmodule Sample do
      def submit(text) when is_binary(text), do: deliver({:message, text})
      defp deliver({:message, text}), do: byte_size(text)
    end""",
    """defmodule Sample do
      @doc "Accept a wire tuple or a legacy string."
      def submit({:message, text}), do: byte_size(text)
      def submit(text) when is_binary(text), do: byte_size(text)
    end""",
    """defmodule Sample do
      def submit(text), do: Transport.deliver(Envelope.make(text))
    end""",
    (
        "The private helper accommodates two excluded representations.",
        "Only the tagged representation is accepted internally.",
        "The legacy format belongs to the public contract.",
        "Envelope normalization and internal delivery are missing.",
    ),
)

group(
    s,
    "test_claim_gap",
    "The supplied test suite's ability to detect sort/1 replaced by identity.",
    """defmodule Sample do
      def sort(xs), do: Enum.sort(xs)
      def test, do: [1, 2, 3] = sort([1, 2, 3])
    end""",
    """defmodule Sample do
      def sort(xs), do: Enum.sort(xs)
      def test do
        [1, 2, 3] = sort([1, 2, 3])
        [1, 2, 3] = sort([3, 1, 2])
      end
    end""",
    """defmodule Sample do
      def sort(xs), do: Enum.sort(xs)
      def test do
        result = sort([3, 1, 2])
        [1, 2, 3] = result
      end
    end""",
    """defmodule Sample do
      def test, do: Checks.sorted_examples(&Ordering.sort/1)
    end""",
    (
        "Identity passes the sorted-only fixture.",
        "An unsorted input kills identity.",
        "The result assertion discriminates the mutant.",
        "Neither the assertions nor the implementation is supplied.",
    ),
    {
        "defect": "Sample.test()\n[1, 2, 3] = (fn xs -> xs end).([1, 2, 3])",
        "repair": 'Sample.test()\nif (fn xs -> xs end).([3, 1, 2]) == [1, 2, 3], do: raise("mutant survived")',
        "control": 'Sample.test()\nif (fn xs -> xs end).([3, 1, 2]) == [1, 2, 3], do: raise("mutant survived")',
    },
)

group(
    s,
    "semantic_duplicate",
    "The retry policy in poll/2 and the existing retryable?/1 helper. These paths have the same retry contract.",
    """defmodule Sample do
      def retryable?(status), do: status == 429 or status >= 500
      def poll(status, remaining) do
        if remaining > 0 and (status == 429 or status >= 500), do: :retry, else: :stop
      end
    end""",
    """defmodule Sample do
      def retryable?(status), do: status == 429 or status >= 500
      def poll(status, remaining) do
        if remaining > 0 and retryable?(status), do: :retry, else: :stop
      end
    end""",
    """defmodule Sample do
      # The legacy provider rate-limits through 403; the new provider uses 429.
      def legacy_retry?(status), do: status == 403 or status >= 500
      def current_retry?(status), do: status == 429 or status >= 500
    end""",
    """defmodule Sample do
      def poll(status, remaining), do: Retry.decide(status, remaining)
    end""",
    (
        "The same retry policy is independently encoded twice.",
        "The existing policy is reused.",
        "Provider contracts differ.",
        "The target policy and any canonical operation are absent.",
    ),
)

group(
    s,
    "process_without_runtime_reason",
    "An Agent created for every string conversion. This is the full lifecycle and sole consumer.",
    """defmodule Sample do
      def format(n) do
        {:ok, pid} = Agent.start_link(fn -> n end)
        result = Agent.get(pid, &Integer.to_string/1)
        Agent.stop(pid)
        result
      end
    end""",
    """defmodule Sample do
      def format(n), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      # Concurrent clients share this set to claim each ID at most once.
      def start_link, do: Agent.start_link(fn -> MapSet.new() end)
      def claim(pid, id) do
        Agent.get_and_update(pid, fn seen ->
          {not MapSet.member?(seen, id), MapSet.put(seen, id)}
        end)
      end
    end""",
    """defmodule Sample do
      def format(pid), do: Agent.get(pid, & &1)
    end""",
    (
        "A temporary process only stores the local argument for a pure conversion.",
        "The pure function needs no process.",
        "Atomic claim ownership requires coordination.",
        "The Agent's owner, initializer, updates, and consumers are absent.",
    ),
)

group(
    s,
    "policy_free_abstraction",
    "Private stringify/1 and serialize/1 in this complete module.",
    """defmodule Sample do
      def label(n), do: stringify(n)
      defp stringify(n), do: serialize(n)
      defp serialize(n), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      def label(n), do: Integer.to_string(n)
    end""",
    """defmodule Sample do
      # The injected reader is the test boundary for filesystem access.
      def load(path, reader) do
        with {:ok, bytes} <- reader.(path), do: {:ok, String.trim(bytes)}
      end
    end""",
    """defmodule Sample do
      def label(n), do: Serializers.stringify(n)
    end""",
    (
        "Two private names provide no separate policy or seam.",
        "Private forwarding layers are removed.",
        "The reader is an actual external-resource test seam.",
        "Serializer policy and supported callers are missing.",
    ),
)

group(
    s,
    "derived_state_drift",
    "Total byte count versus buffered chunks; push/2 and reset/1 are all updates.",
    """defmodule Sample do
      def new, do: %{chunks: [], bytes: 0}
      def push(s, chunk), do: %{s | chunks: [chunk | s.chunks], bytes: s.bytes + byte_size(chunk)}
      def reset(s), do: %{s | chunks: []}
    end""",
    """defmodule Sample do
      def new, do: %{chunks: [], bytes: 0}
      def push(s, chunk), do: %{s | chunks: [chunk | s.chunks], bytes: s.bytes + byte_size(chunk)}
      def reset(s), do: %{s | chunks: [], bytes: 0}
    end""",
    """defmodule Sample do
      # lifetime_bytes measures all traffic, including data no longer buffered.
      def new, do: %{chunks: [], lifetime_bytes: 0}
      def push(s, x), do: %{s | chunks: [x | s.chunks], lifetime_bytes: s.lifetime_bytes + byte_size(x)}
      def reset(s), do: %{s | chunks: []}
    end""",
    """defmodule Sample do
      def new, do: %{chunks: [], bytes: 0}
      def push(s, x), do: Buffer.push(s, x)
      def reset(s), do: Buffer.reset(s)
    end""",
    (
        "Reset leaves an old byte count after discarding data.",
        "Reset restores both representations.",
        "Lifetime traffic is not the size of current storage.",
        "Buffer transitions are not supplied.",
    ),
    {
        "defect": '%{chunks: [], bytes: 3} = Sample.new() |> Sample.push("abc") |> Sample.reset()',
        "repair": '%{chunks: [], bytes: 0} = Sample.new() |> Sample.push("abc") |> Sample.reset()',
        "control": '%{chunks: [], lifetime_bytes: 3} = Sample.new() |> Sample.push("abc") |> Sample.reset()',
    },
)

group(
    s,
    "disguised_state_machine",
    "Mutually exclusive lifecycle phases of one job; complete initialization and transitions.",
    """defmodule Sample do
      def new, do: %{queued: true, running: false, done: false}
      def start(s), do: %{s | running: true}
      def finish(s), do: %{s | running: false, done: true}
    end""",
    """defmodule Sample do
      def new, do: :queued
      def start(:queued), do: :running
      def finish(:running), do: :done
    end""",
    """defmodule Sample do
      # Visibility and edit permission have independent meanings.
      def new, do: %{visible: false, editable: false}
      def show(s), do: %{s | visible: true}
      def allow_edit(s), do: %{s | editable: true}
    end""",
    """defmodule Sample do
      def start(s), do: JobState.start(s)
      def finish(s), do: JobState.finish(s)
    end""",
    (
        "Running and completed jobs can remain queued.",
        "One atom encodes the phase.",
        "Visibility and permission can validly coexist.",
        "Job state and its transitions are absent.",
    ),
    {
        "defect": 's = Sample.new() |> Sample.start() |> Sample.finish()\nunless s.queued and s.done, do: raise("witness")',
        "repair": ":done = Sample.new() |> Sample.start() |> Sample.finish()",
        "control": 's = Sample.new() |> Sample.show() |> Sample.allow_edit()\nunless s.visible and s.editable, do: raise("witness")',
    },
)

group(
    s,
    "timing_instead_of_synchronization",
    "Waiting for asynchronous task output before inspecting its result.",
    """defmodule Sample do
      def run(f) do
        task = Task.async(f)
        Process.sleep(20)
        Task.yield(task, 0)
      end
    end""",
    """defmodule Sample do
      def run(f) do
        task = Task.async(f)
        {:ok, Task.await(task, 5000)}
      end
    end""",
    """defmodule Sample do
      # A timeout API must return nil when work remains unfinished.
      def test do
        task = Task.async(fn -> Process.sleep(1000); :done end)
        nil = Task.yield(task, 0)
        Task.shutdown(task, :brutal_kill)
      end
    end""",
    """defmodule Sample do
      def run(f), do: Jobs.join(f)
    end""",
    (
        "A fixed wait does not establish task completion.",
        "Await observes task completion.",
        "The task is deliberately delayed to test nonblocking timeout.",
        "Join's timing and synchronization implementation is missing.",
    ),
)

group(
    s,
    "presentation_only_authorization",
    "Editing through the server event, not only displaying the edit control.",
    """defmodule Sample do
      def editable?(user, doc), do: user.team == doc.team
      def event(user, doc, title), do: Documents.update(user, doc, title)
    end
    defmodule Documents do
      def update(_user, doc, title), do: {:ok, %{doc | title: title}}
    end""",
    """defmodule Sample do
      def editable?(user, doc), do: user.team == doc.team
      def event(user, doc, title) do
        if editable?(user, doc), do: Documents.update(doc, title), else: {:error, :forbidden}
      end
    end
    defmodule Documents do
      def update(doc, title), do: {:ok, %{doc | title: title}}
    end""",
    """defmodule Sample do
      def editable?(user, doc), do: user.team == doc.team
      def event(user, doc, title), do: Documents.update(user, doc, title)
    end
    defmodule Documents do
      def update(%{team: t}, %{team: t} = doc, title), do: {:ok, %{doc | title: title}}
      def update(_, _, _), do: {:error, :forbidden}
    end""",
    """defmodule Sample do
      def editable?(user, doc), do: user.team == doc.team
      def event(user, doc, title), do: Documents.update(user, doc, title)
    end""",
    (
        "The server ignores the team restriction.",
        "The event checks the team before updating.",
        "Pattern matching in the context enforces the same restriction.",
        "The context's authorization behavior is missing.",
    ),
    {
        "defect": '{:ok, %{title: "new"}} = Sample.event(%{team: 1}, %{team: 2, title: "old"}, "new")',
        "repair": '{:error, :forbidden} = Sample.event(%{team: 1}, %{team: 2, title: "old"}, "new")',
        "control": '{:error, :forbidden} = Sample.event(%{team: 1}, %{team: 2, title: "old"}, "new")',
    },
)

group(
    s,
    "framework_reimplementation",
    "digits?/1 in a project using Elixir 1.18's standard library; the whole string must be ASCII decimal digits, without a sign.",
    """defmodule Sample do
      # Installed Regex.match?(~r/\\A[0-9]+\\z/, text) tests this exact language.
      def digits?(""), do: false
      def digits?(text), do: walk(text)
      defp walk(<<>>), do: true
      defp walk(<<c, rest::binary>>) when c >= ?0 and c <= ?9, do: walk(rest)
      defp walk(_), do: false
    end""",
    """defmodule Sample do
      # Elixir 1.18 Regex.match?/2 supports these ASCII anchors and character classes.
      def digits?(text), do: Regex.match?(~r/\\A[0-9]+\\z/, text)
    end""",
    """defmodule Sample do
      # Unlike a whole-string predicate, this parser returns the remaining suffix.
      def digits(text), do: walk(text, "")
      defp walk(<<c, rest::binary>>, acc) when c >= ?0 and c <= ?9, do: walk(rest, acc <> <<c>>)
      defp walk(rest, acc), do: {acc, rest}
    end""",
    """defmodule Sample do
      def digits?(text), do: Scanner.decimal?(text)
    end""",
    (
        "The recursive recognizer duplicates an available library predicate.",
        "The supplied library predicate is used.",
        "A suffix-returning parser has a different contract.",
        "Scanner's implementation and available facilities are missing.",
    ),
    {
        "defect": 'for x <- ["", "0", "123", "1x", "-2", "12\\n"] do\n unless Sample.digits?(x) == Regex.match?(~r/\\A[0-9]+\\z/, x), do: raise("witness")\nend',
        "repair": 'true = Sample.digits?("123")\nfalse = Sample.digits?("-1")',
        "control": '{"123", "rest"} = Sample.digits("123rest")',
    },
)

group(
    s,
    "semantic_comment_noise",
    "Comments inside the function body.",
    """defmodule Sample do
      def active(users) do
        # Filter the users by active status.
        Enum.filter(users, & &1.active)
      end
    end""",
    """defmodule Sample do
      def active(users) do
        # Inactive accounts retain records for audit but cannot receive email.
        Enum.filter(users, & &1.active)
      end
    end""",
    """defmodule Sample do
      def first(users) do
        # Database order is priority order; sorting here would change the recipient.
        List.first(users)
      end
    end""",
    """defmodule Sample do
      # Filter the eligible recipients.
    end""",
    (
        "The comment restates the visible filter.",
        "The comment gives the business constraint.",
        "The comment explains why order must stay unchanged.",
        "The adjacent implementation is not supplied.",
    ),
)

group(
    s,
    "avoidable_repeated_traversal",
    "Growing chunk list and repeated byte-limit checks in receive_chunks/2.",
    """defmodule Sample do
      def receive_chunks(chunks, limit) do
        Enum.reduce_while(chunks, [], fn chunk, acc ->
          next = [chunk | acc]
          if :erlang.iolist_size(next) > limit, do: {:halt, :too_large}, else: {:cont, next}
        end)
      end
    end""",
    """defmodule Sample do
      def receive_chunks(chunks, limit) do
        Enum.reduce_while(chunks, {[], 0}, fn chunk, {acc, size} ->
          size = size + :erlang.iolist_size(chunk)
          if size > limit, do: {:halt, :too_large}, else: {:cont, {[chunk | acc], size}}
        end)
        |> case do
          :too_large -> :too_large
          {acc, _} -> acc
        end
      end
    end""",
    """defmodule Sample do
      # Each chunk is independent; the reduction never rescans earlier chunks.
      def receive_chunks(chunks, limit) do
        Enum.reduce_while(chunks, 0, fn chunk, size ->
          size = size + :erlang.iolist_size(chunk)
          if size > limit, do: {:halt, :too_large}, else: {:cont, size}
        end)
      end
    end""",
    """defmodule Sample do
      def receive_chunks(chunks, limit), do: Collector.consume(chunks, limit)
    end""",
    (
        "Each iteration traverses all previous chunks again.",
        "The counter only measures each new chunk.",
        "Each byte is visited once.",
        "The consuming loop is missing.",
    ),
    {
        "defect": ':too_large = Sample.receive_chunks(["ab", "cd"], 3)\n["cd", "ab"] = Sample.receive_chunks(["ab", "cd"], 4)',
        "repair": ':too_large = Sample.receive_chunks(["ab", "cd"], 3)\n["cd", "ab"] = Sample.receive_chunks(["ab", "cd"], 4)',
        "control": ':too_large = Sample.receive_chunks(["ab", "cd"], 3)\n4 = Sample.receive_chunks(["ab", "cd"], 4)',
    },
)

group(
    s,
    "redundant_wrapper",
    "The cond expression in run/1 (or its replacement), excluding the public function boundary.",
    """defmodule Sample do
      def run(x) do
        cond do
          is_integer(x) -> x
          is_binary(x) -> x
          true -> x
        end
      end
    end""",
    """defmodule Sample do
      def run(value), do: value
    end""",
    """defmodule Sample do
      def run(%{id: id, name: name}), do: %{id: id, name: name}
    end""",
    """defmodule Sample do
      def run(x), do: Mapper.project(x)
    end""",
    (
        "All exhaustive cond branches return the input unchanged.",
        "The cond is removed; the specified target contains no conditional wrapper.",
        "Map reconstruction drops extra keys and can raise on missing keys.",
        "The projection implementation is missing.",
    ),
    {
        "defect": 'for x <- [nil, 1, "x", %{}], do: (unless Sample.run(x) == x, do: raise("witness"))',
        "repair": 'for x <- [nil, 1, "x", %{}], do: (unless Sample.run(x) == x, do: raise("witness"))',
        "control": '%{id: 1, name: "a"} = Sample.run(%{id: 1, name: "a", extra: true})\nfalse = Map.has_key?(Sample.run(%{id: 1, name: "a", extra: true}), :extra)',
    },
)
if __name__ == "__main__":
    path = Path(__file__).with_name("cases.jsonl")
    path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in CASES))
    print(f"Wrote {len(CASES)} cases")
