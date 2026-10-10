# slop-decisions

Agents can write working code that becomes hard to understand and maintain.
slop-decisions gives Codex 26 checks for defects, wrong abstractions, hidden
coupling, and unsafe retries that static checks such as [ex_slop](https://github.com/elixir-vibe/ex_slop) cannot judge.

**We recommend using both.**

## Use it

In Codex, ask:

```text
Use $skill-installer to install https://github.com/samhavens/slop-decisions/tree/main/skills/slop-review
```

Then, in your code project:

```text
$slop-review Review my changes against origin/main.
```

Codex reviews all 26 rules in the current session. It reads related code and tests,
then gives findings with evidence. There are no separate checker API calls;
normal Codex usage still applies.

[Install and select rules](docs/codex.md) · [Use with tests and CI](docs/ci.md) ·
[Review results](reports/discovery-2026-10-10/README.md)

The experimental API checker and eval suite support **OpenAI, OpenRouter, and
local models**. See [API setup](docs/usage.md), [model options](docs/models.md),
and [evaluation limits](docs/results.md). Model scores are not a reliable merge gate.

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
| UI state sent through the server<br>`client_state_round_trip` | Opening a static help modal waits for an event that only changes visibility. |
| State lost after reconnect<br>`liveview_reconnect_state_loss` | A wizard keeps earlier answers only in assigns and cannot restore them after remount. |
| Database reads repeated per record<br>`per_record_database_read` | A helper calls `Repo.preload` for each post instead of loading the association for the list. |
| Shared code that mixes separate policies<br>`false_unification` | Trial signup passes flags to skip billing steps in a shared completion function. |
| Tests tied to private implementation<br>`test_implementation_coupling` | A counter test fails after a private state change that preserves all public behavior. |
| Private process details spread across callers<br>`scattered_process_interface` | Several modules update an Agent's private map fields. |
| Too much data sent to a process<br>`oversized_process_capture` | An audit task captures a large parsed request just to read its ID. |
| Independent instances share global settings<br>`global_configuration_coupling` | Starting client B changes the endpoint used by client A. |
| Ordinary work repeated by macros<br>`unnecessary_compile_time_work` | A macro copies the same runtime parser into every caller. |
| A check and update can race<br>`non_atomic_invariant` | Two reservations read the last available slot before either claims it. |
| A retry repeats a side effect<br>`unsafe_retry` | A lost response causes a shipment retry with a new idempotency key. |
| Retry layers multiply work<br>`multiplicative_retries` | Four worker attempts each make three client attempts, exceeding a four-request budget. |

[Full rules and exceptions](src/slop_decisions/data/rubrics.json) ·
[Review methods and sources](skills/slop-review/references/investigation.md) ·
[Phoenix and Ecto examples](docs/phoenix.md) ·
[Compare models](docs/run-eval.md) · [Calibration](docs/calibration.md) ·
[Contribute](CONTRIBUTING.md) · [MIT license](LICENSE)
