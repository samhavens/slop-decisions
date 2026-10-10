# Decisions threshold study — October 10, 2026

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

See the [fixed plan](plan.md), [cases](../../calibration/cases.jsonl),
[fit](profile.json), and
[full results](summary.json).
The results include scores by check, reliability bins, Brier scores, and uncertainty intervals.
Threshold fitting does not make the reported probabilities calibrated.
