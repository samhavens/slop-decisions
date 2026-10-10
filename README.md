# slop-decisions

Agents can write working code with patterns that make a project hard to understand and maintain over time.
slop-decisions uses [Jev-style decision models](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
to check Elixir code for patterns that static checks such as [ex_slop](https://github.com/elixir-vibe/ex_slop) cannot judge.

**We recommend using both.**

## Use it

Install with [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.11 or later.
Set `OPENAI_API_KEY` in your environment, then run:

```sh
uv tool install git+https://github.com/samhavens/slop-decisions.git
slop-decisions check lib/orders.ex
```

This runs **all 14 rules** with OpenAI `gpt-6-luna` through the Responses API, with a reason for each result.
Review the results before you change code. See the [model comparison](docs/results.md).

Use a local model with [Ollama running](docs/models.md#local-models):

```sh
ollama pull qwen3:8b
slop-decisions check lib/orders.ex --provider local --model qwen3:8b
```

Restrict the rules with `--rule`. Repeat it to select more than one:

```sh
slop-decisions check lib/orders.ex \
  --rule success_shaped_failure --rule derived_state_drift
```

Check changed files in tests or CI:

```sh
slop-decisions check --changed origin/main --junit results/slop.xml
```

This checks current `.ex` and `.exs` files changed since the common ancestor with `origin/main`.
Omit `origin/main` to check local changes since `HEAD`.
See [CI and ExUnit setup](docs/ci.md), [OpenRouter and other servers](docs/models.md),
or [file, line, and context options](docs/usage.md).

## Patterns

Each rule asks about behavior and context. Matching syntax alone is not enough.

| Pattern / rule | Example it looks for |
| --- | --- |
| Failure reported as success<br>`success_shaped_failure` | A failed database query returns `{:ok, []}`. |
| Support for invalid internal inputs<br>`invalid_state_accommodation` | Private helpers accept `nil` and maps after a boundary guarantees a struct. |
| Tests that cannot detect a defect<br>`test_claim_gap` | An encoding test uses only text that needs no encoding. |
| Duplicate behavior<br>`semantic_duplicate` | A test repeats setup that an existing helper already provides. |
| Process with no runtime purpose<br>`process_without_runtime_reason` | A GenServer runs pure calculations without owning state or coordinating work. |
| Abstraction with no useful role<br>`policy_free_abstraction` | Several configurable layers all lead to the same fixed operation. |
| Stored values that disagree<br>`derived_state_drift` | Removing an item leaves the stored item count unchanged. |
| One state stored as several flags<br>`disguised_state_machine` | One operation can be both `loading` and `loaded`. |
| Delay used to wait for completion<br>`timing_instead_of_synchronization` | A test calls `Process.sleep/1`, then assumes a worker has finished. |
| Access control only in the UI<br>`presentation_only_authorization` | The UI hides Delete, but the server accepts the delete event from any user. |
| Duplicate framework behavior<br>`framework_reimplementation` | Custom casting and validation repeat the available Ecto changeset behavior. |
| Comments that repeat the code<br>`semantic_comment_noise` | “Fetch users” appears directly above `fetch_users()`. |
| Repeated scans of growing data<br>`avoidable_repeated_traversal` | Each received chunk causes another length scan of the entire accumulated body. |
| Wrapper that changes nothing<br>`redundant_wrapper` | An exhaustive `case` returns every input unchanged. |

[Full rules and exceptions](src/slop_decisions/data/rubrics.json) ·
[Compare models](docs/run-eval.md) · [Calibration](docs/calibration.md) ·
[Contribute](CONTRIBUTING.md) · [MIT license](LICENSE)
