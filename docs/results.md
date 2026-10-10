# Choose a model

Use OpenAI Responses when you need a written reason for each result.
It scored higher than Decisions and the tested local model on the public-source evaluation.

```sh
slop-decisions check lib/orders.ex --api responses
```

Use `--related PATH` to supply code that a check needs, such as a called function or a test helper.
See [source selection](usage.md) and [provider setup](models.md).

## Compare the measured results

These runs used the same 20 code targets and a warning threshold of 0.8.
The OpenAI model was `gpt-6-luna`. Decisions is the current default.

| Configuration | Correct / all targets | Assessed / all targets | Model-call time |
| --- | ---: | ---: | ---: |
| OpenAI Responses | 17/20 | 19/20 | 102.68 s |
| OpenAI Decisions | 10/20 | 14/20 | 3.10 s |
| Local Qwen3-0.6B, 4-bit | 10/20 | 20/20 | 70.17 s |

Unassessed targets count against the score. Times cover all 20 targets in one run.
These are development results; they do not establish accuracy on your project.
The set covers eight of the fourteen rules and includes four code-design judgments.

The local run verifies the MLX connection with that small model.
OpenRouter has protocol tests but no published live evaluation.
Do not assume that another model will have the same accuracy.

## Before you require a passing check

Run an [evaluation on labeled code](run-eval.md) from your project.
Measure missed defects, false warnings, and checks that cannot give an answer.
Use a [validated threshold profile](calibration.md) for the exact model and settings you will run.
No validated profile is included in this release.

[Full measurements and source evidence](../reports/2026-10-10/README.md) ·
[Threshold measurements](../reports/calibration-2026-10-10/README.md) ·
[Score definitions](evaluation.md)
