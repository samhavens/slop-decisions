# Use the checker

[Set up a model](models.md) first. Run commands from the root of your code repository.
Replace the paths below with your own files.

## Select code and checks

List the available checks:

```sh
slop-decisions checks
```

Select a check with `--dimension`. Add related files when the check needs them:

```sh
slop-decisions check lib/orders.ex --model qwen3:8b \
  --dimension success_shaped_failure \
  --lines 20:60 --related lib/repo.ex
```

This command examines lines 20–60. The model also receives the full target file and `lib/repo.ex`.
Supply the called function when its behavior could change the result.
For a test check, supply the test and the code under test.

Repeat `--dimension` to select more checks. Omit it to use the three defaults:

- Failed work that returns a successful result.
- Tests that an incorrect implementation can pass.
- Loops that repeatedly scan accumulated data.

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
slop-decisions check lib/orders.ex --model qwen3:8b \
  --dimension success_shaped_failure --dry-run --format json
```

`--dry-run` makes no model request.
`--max-checks` limits the number of checks; the default is 20.
`--max-chars` limits the source size; the default is 100,000 characters per input.
The checker rejects excess source instead of removing part of it.

## Read results

An `assessed` result includes the model's estimate of the defect probability.
A probability at or above `--threshold` produces a warning. The default is 0.8.
This value is experimental; see [results and limits](results.md).

An `unassessed` result means the check could not give an answer.
This can follow a failed request, an invalid reply, a refusal, or insufficient source.
Do not treat it as a result with no defects.

The default output format is TOON. Use `--format json` for JSON.
Progress messages go to stderr.

| Exit code | Meaning |
| --- | --- |
| 0 | All selected checks returned results below the warning threshold. |
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
