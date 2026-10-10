# Set warning thresholds

Choose warning settings from labeled code.
Test them on separate code before you use them in CI.

The Decisions API supplies two scores: whether the source is sufficient, and whether the defect is present.
The context gate controls whether the checker can assess the code.
The warning threshold controls when an assessed result produces a warning.

The built-in values are both 0.8. They are experimental; no validated profile is included in this release.
Use the [model comparison](results.md) to choose a configuration before fitting its thresholds.

## Fit and verify a profile

Set `OPENAI_API_KEY`. Prepare calibration and holdout cases with the [case format](../calibration/README.md).
Keep related code in one set. Label the cases before making model requests.
Keep the holdout separate until the profile is fixed.

```sh
slop-calibrate collect --cases my-cases.jsonl --split calibration \
  --model gpt-6-luna --out runs/calibration --stop-after 3
```

Inspect the first three results. Continue with the same command without `--stop-after 3`, then fit and test:

```sh
slop-calibrate collect --cases my-cases.jsonl --split calibration \
  --model gpt-6-luna --out runs/calibration
slop-calibrate fit runs/calibration --out runs/profile.json
slop-calibrate collect --cases my-cases.jsonl --split holdout \
  --model gpt-6-luna --out runs/holdout --profile runs/profile.json
slop-calibrate validate runs/holdout --profile runs/profile.json \
  --out runs/validation.json
```

Validation returns exit code 3 if the profile does not meet the requirements.
A passing profile must assess at least 70% of sufficient-source cases and at most 10% of insufficient-source cases.
Its review cost must be no higher than the built-in settings: `5 × false warnings + missed defects`.
See the [selection policy](../reports/calibration-2026-10-10/plan.md) for the full method.

## Apply a passing profile

```sh
slop-decisions check lib/orders.ex --api decisions --calibration runs/validation.json
```

The profile must match the model, API, endpoint, source selection, prompts, and selected rules.
The checker rejects a profile that failed validation.
Changing `--threshold` or `--context-threshold` overrides the profile.
The combined settings have not passed that profile's validation.

This workflow supports Decisions. Use the [evaluation and threshold-sweep commands](run-eval.md)
for local models, OpenRouter, or OpenAI Responses. Do not transfer thresholds between models.

Use new holdout cases after changing a configuration in response to test results.
The published cases are development material and cannot supply another independent test.

[Published measurements](../reports/calibration-2026-10-10/README.md) ·
[Raw predictions and profile](../reports/calibration-2026-10-10/) ·
[Verification script](../scripts/verify_calibration.py)
