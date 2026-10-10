# Use the experimental API checker

For a review in your existing session, use [the Codex skill](codex.md).
The API checker makes one model request per file and rule. Its scores are
experimental; review findings before changing code or blocking a merge.

Install with [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.11 or later:

```sh
uv tool install git+https://github.com/samhavens/slop-decisions.git
```

Set `OPENAI_API_KEY` in your environment, then check a file:

```sh
slop-decisions check lib/orders.ex
```

This uses all 26 rules with OpenAI `gpt-6-luna` through the Responses API.
For [a local model](models.md#local-models), start Ollama, then run:

```sh
ollama pull qwen3:8b
slop-decisions check lib/orders.ex --provider local --model qwen3:8b
```

[Select OpenRouter or another server](models.md) with the same command.
Run commands from the root of your code repository.
Replace the paths below with your own files.

## Select code and checks

List the available checks:

```sh
slop-decisions checks
```

Select a check with `--rule`. Add related files when the check needs them:

```sh
slop-decisions check lib/orders.ex \
  --rule success_shaped_failure \
  --lines 20:60 --related lib/repo.ex
```

This command examines lines 20–60. The model also receives the full target file and `lib/repo.ex`.
Supply the called function when its behavior could change the result.
For a test check, supply the test and the code under test.

Repeat `--rule` to select more checks. Omit it to use [all 26 rules](../README.md#patterns).
`--dimension` is an alias for `--rule`.
With `--rubrics FILE`, the default is every rule in that file.

Pass more than one input file to examine several files. Use `--lines` with one input file only.
Use `--root PATH` if your files are in a different directory.

Select how much source to include:

| Option | Source sent to the model |
| --- | --- |
| `--context target` | The selected lines and any explicit `--related` files. |
| `--context window` | The selected lines, up to 40 lines on each side, and related files. |
| `--context file` | The full target file and related files. This is the default. |

Inspect the source selection before you send it:

```sh
slop-decisions check lib/orders.ex --dry-run --format json
```

`--dry-run` makes no model request.
`--max-checks` limits the number of checks; the default is 200.
Each file uses one check per selected rule. A plan above the limit fails before any request.
`--max-chars` limits the source size; the default is 100,000 characters per input.
The checker rejects excess source instead of removing part of it.

Use `--changed` to select changed Elixir files. See [API tests and CI](api-ci.md) for
Git comparison rules, JUnit reports, and an ExUnit example.

## Read results

An `assessed` result includes the model's estimate of the defect probability.
A probability at or above `--threshold` produces a warning. The fallback is 0.8.
This value is experimental. [Calibration](calibration.md) can measure a threshold
on a labeled dataset; it does not establish reliability on a new project.
`threshold_policy` shows where each threshold came from. Use `--calibration FILE`
to apply a passing profile, or supply explicit threshold values.

An `unassessed` result means the check could not give an answer.
This can follow a failed request, an invalid reply, a refusal, or insufficient source.
Do not treat it as a result with no defects.

The default output format is TOON. Use `--format json` for JSON.
Progress messages go to stderr.

| Exit code | Meaning |
| --- | --- |
| 0 | All results were below the warning threshold, or no changed files needed a check. |
| 1 | At least one check was unassessed. This takes priority over warnings. |
| 2 | An argument, setting, or input was invalid. |
| 3 | At least one check produced a warning; all checks were assessed. |
| 130 | The command was interrupted. |

Examine each result before you change code. The checker does not change your files.

## Use Python

Create a source packet and select one check:

```python
from pathlib import Path
from slop_decisions.context import build_packet
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics

packet = build_packet(Path('.'), 'lib/orders.ex', 20, 60)
rubric = load_rubrics()['success_shaped_failure']
with Provider(ProviderConfig(provider='local', model='qwen3:8b')) as model:
    result = model.assess(packet, rubric)
print(result)
```
