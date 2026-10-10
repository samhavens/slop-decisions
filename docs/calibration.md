# Calibrate thresholds

A high model score can still be wrong. Fit thresholds on labeled code, then test them on separate cases before you use them.

## Current result

**The fitted Decisions profile failed validation. It is not a new default.**
The checker still uses 0.8 as an experimental fallback for both thresholds.
Output marks each threshold as a fallback, an explicit setting, or a validated profile.

The study used `gpt-6-luna`, fourteen checks, and 112 authored Elixir cases.
It fit thresholds on 56 cases, then tested the frozen choice on 56 other cases.
Each set had 14 defects, 28 clean cases, and 14 cases with insufficient source.
Related cases stayed in one set. Labels and witnesses were not model input.

| Held-out result | Old defaults | Fitted profile |
| --- | ---: | ---: |
| Context gate | 0.80 | 0.65 |
| Warning threshold | 0.80 | 1.00 |
| Defects found | 7/14 | 1/14 |
| False warnings on clean code | 1/28 | 1/28 |
| Assessments with sufficient source | 26/42 | 29/42 |
| Assessments despite missing source | 1/14 | 3/14 |
| Review cost: `5 × false warnings + missed defects` | 12 | 18 |

The fitted profile failed all three release checks: coverage, missing-source rejection, and review cost.
On the separate 20-case public-source set, it found none of the eight defects.
No further threshold search used the held-out results.

These small fixtures test the check rules. They do not estimate production accuracy.
All 112 packets passed syntax checks. Forty-five behavioral witnesses passed.
Other labels require source review; witness success does not prove a design preference.
Thirteen model refusals remain unassessed. No request was repeated.

The study made 132 requests and used 149,762 input tokens in 21.16 seconds of model-call time.
Estimated API cost was **$0.015**, using the [Decisions list price](https://developers.openai.com/api/docs/guides/decisions).
This is an estimate, not a billing record.

See the [fixed plan](calibration-plan.md), [cases](../calibration/cases.jsonl),
[fit](../reports/calibration-2026-10-10/profile.json), and
[full results](../reports/calibration-2026-10-10/summary.json).
The results include scores by check, reliability bins, Brier scores, and uncertainty intervals.
Threshold fitting does not make the reported probabilities calibrated.

## Run a study

Install from the repository and set `OPENAI_API_KEY`.
Prepare separate calibration and holdout families with the [case format](../calibration/README.md).
Use new cases for a new test; the published holdout is now public development material.

```sh
slop-calibrate collect --cases my-cases.jsonl --split calibration \
  --model gpt-6-luna --out runs/calibration --stop-after 3
# Inspect the pilot, then resume the same run.
slop-calibrate collect --cases my-cases.jsonl --split calibration \
  --model gpt-6-luna --out runs/calibration
slop-calibrate fit runs/calibration --out runs/profile.json
slop-calibrate collect --cases my-cases.jsonl --split holdout \
  --model gpt-6-luna --out runs/holdout --profile runs/profile.json
slop-calibrate validate runs/holdout --profile runs/profile.json \
  --out runs/validation.json
```

Validation saves the result and returns exit code 3 if the profile fails.
Use `--format json --full` to print the complete result.
A passing file can supply thresholds to the checker:

```sh
slop-decisions check lib/orders.ex --provider openai --model gpt-6-luna \
  --calibration runs/validation.json
```

The checker rejects failed profiles, untested checks, and changes to the model, API, endpoint, context mode, or check prompts.
Explicit `--threshold` and `--context-threshold` values override an accepted profile.
The output marks these overrides; their combined policy has not passed validation.

This two-score workflow is for Decisions. Local models and OpenRouter retain their existing
[eval and threshold-sweep workflow](run-eval.md). Do not reuse a Decisions threshold for another model.

To verify the published study without API calls:

```sh
uv run slop-decisions fetch
uv run python scripts/verify_calibration.py
uv run python scripts/calibration_witnesses.py
```
