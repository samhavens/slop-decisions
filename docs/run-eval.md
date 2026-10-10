# Compare models

Use the evaluation set to compare models before you select one for code review.
Read the [results and limits](results.md) before you interpret a score.

## Run an evaluation

[Set up your model](models.md). Run all commands from the same directory.
Download the source files:

```sh
slop-decisions fetch
```

This command downloads exact source revisions and verifies their file hashes.
See [source licenses](../THIRD_PARTY.md).

Inspect the plan without a model request:

```sh
slop-decisions eval --provider local --model qwen3:8b \
  --out runs/local --dry-run
```

Run the evaluation:

```sh
slop-decisions eval --provider local --model qwen3:8b --out runs/local
```

For OpenAI or OpenRouter, change the [provider options](models.md).
Select a different output directory for each run.
Use `--resume` after an interruption. Keep the same model, inputs, and options.

| Option | Use |
| --- | --- |
| `--limit 3` | Run only three cases for an initial trial. |
| `--dimension NAME` | Select one type of defect. |
| `--track semantic` | Exclude preference and duplicate-setup cases. |
| `--context target`, `window`, or `file` | Change the amount of source. |
| `--prompt minimal` or `examples` | Omit or include prompt examples. |
| `--rubrics FILE` | Use your own check definitions. |

Change one variable at a time. Keep the expected answers fixed.

## Read and compare scores

The output directory contains:

- `report.json`: scores, coverage, time, and token use.
- `predictions.jsonl`: each model result.
- `run.json`: run settings.
- `experiment.json`: source references, expected answers, checks, and request templates.

Compare coverage as well as accuracy. A failed request remains unassessed and reduces the main accuracy score.
The report includes cost only when the provider supplies it.

Recalculate scores or compare thresholds without new model requests:

```sh
slop-decisions score runs/local/predictions.jsonl --threshold 0.8 --format json
slop-decisions sweep runs/local/predictions.jsonl \
  --thresholds 0.5,0.65,0.8,0.9,0.95 --format json
```

These commands expect the full selected dataset split.
For a partial run, repeat `--case-id` to select its intended cases.
Threshold sweeps refuse holdout data.

The `eval` command returns exit code 1 if any case is unassessed.
It does not fail because accuracy is low.
See the [evaluation method](evaluation.md) for score definitions and dataset rules.
