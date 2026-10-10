# Initial development results — October 10, 2026

See the later [112-case calibration study](../calibration-2026-10-10/README.md) for threshold selection and held-out results.

The strongest tested configuration was **OpenAI Responses with the explicit
behavior focus and the relevant callee contract**: 18/20 correct, 20/20 assessed,
87.5% macro balanced accuracy, and 5/7 strict before/after pairs. This is fit to a
small development set, not a validated production detector. Six rubric dimensions
have no seed examples, and no repository-disjoint holdout has been collected.

OpenAI Decisions and a local model both completed live runs. The tested local
model was `mlx-community/Qwen3-0.6B-4bit`, served by MLX on an Apple Silicon Mac,
with thinking disabled. It assessed every target but got only 10/20 correct.
That establishes a working local integration; it does not establish useful
quality for this small model. Other local servers share the Chat Completions
adapter but were not individually live-tested.

OpenRouter authentication, request construction, and response parsing are covered
by offline protocol tests. There was no OpenRouter credential available for a
live run. No cloud credential was reused for the local server.

## Main comparison

All OpenAI rows used `gpt-6-luna`. Each row is one trial on the same 20 development
targets, at warning threshold **0.8**. Decisions used a separate context gate of
0.8. Except `minimal`, prompts included positive and hard-negative examples.
Except `target`, source packets included the whole target file and named related
files. Retries were disabled for these runs. Unknowns count against accuracy.

| Saved run | Assessed | Correct / all | Macro BA | Fix pairs | Hard-negative FP / assessed | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [decisions-file](decisions-file/report.json) | 14/20 | 10/20 | 45.8% | 1/7 | 1/9 | 3.10 |
| [decisions-minimal](decisions-minimal/report.json) | 15/20 | 9/20 | 37.5% | 1/7 | 1/9 | 3.55 |
| [decisions-target](decisions-target/report.json) | 5/20 | 3/20 | 16.7% | 0/7 | 1/2 | 4.34 |
| [responses-file](responses-file/report.json) | 19/20 | 17/20 | 83.3% | 4/7 | 1/11 | 102.68 |
| [responses-focused](responses-focused/report.json) | 19/20 | 17/20 | 83.3% | 4/7 | 1/12 | 119.56 |
| [responses-focused-context](responses-focused-context/report.json) | 20/20 | 18/20 | 87.5% | 5/7 | 1/12 | 108.67 |
| [local-qwen](local-qwen/report.json) | 20/20 | 10/20 | 50.0% | 0/7 | 3/12 | 70.17 |

There are twelve hard negatives. The FPR denominator excludes unassessed cases,
so compare its coverage as well as its rate. Latency is the sum of model-call wall
times, excluding source downloads and server/model setup. It is not a throughput
benchmark; remote load, caching, and local hardware differ.

The combined score includes two preference targets and two duplicate-setup
baseline targets. For the final Responses run, the **semantic track alone** was
15/16 correct, 16/16 assessed, 93.75% macro BA, 4/5 pairs, and 1/10 hard-negative
false positives. Track summaries for every run are in
[analysis.json](analysis.json).

## What changed and what still fails

1. An initial three-target Decisions pilot asked for abstention inside the defect
   predicate and yielded zero assessed targets. A separate context-sufficiency
   predicate made the next pilot assess all three. The published main runs all
   use that two-question protocol.
2. Removing examples lowered Decisions development fit; reducing context to the
   target span sharply reduced coverage. Source selection mattered more than
   brevity for these cases.
3. The baseline Responses run flagged an unrelated missing assertion outside the
   marked Tesla behavior. Explicitly instructing the model to respect `target.focus`
   did **not** eliminate that false positive.
4. Adding Logflare's pinned `Pool` callee file supplied its return contract and
   error path. The final Responses run assessed both egress revisions correctly.
   No label or witness was added to the model input. With only one trial per
   variant, this is a useful development observation, not an isolated causal
   estimate.
5. The two remaining errors are the repaired Tesla private-data test, flagged
   for missing coverage of a different behavior, and the Boundary preference
   example. The latter may reflect reasonable disagreement with a candidate
   simplification label. It is reported separately rather than treated as a
   verified correctness defect.

## Threshold experiment

Sweeps reuse the saved probabilities at 0.5, 0.65, 0.8, 0.9, 0.95, and 0.99.
No model was called during threshold selection. The final Responses run achieves
its same best macro BA at 0.5 through 0.9; moving the threshold does not repair
its remaining errors. Decisions-minimal improves from 37.5% to 45.8% at 0.5, still
well below the generative configuration. The local model remains at 50% macro BA
throughout this grid.

Each run directory contains `thresholds.json`, including false positives,
coverage, per-dimension scores, and pairs at every threshold. These are development
fits, not calibrated probability estimates. The checker retains its explicit,
experimental 0.8 default rather than claiming an optimized deployment threshold.

## Usage and cost

| Run | Input tokens | Output tokens |
| --- | ---: | ---: |
| decisions-file | 77,072 | 0 |
| decisions-minimal | 76,061 | 0 |
| decisions-target | 19,718 | 0 |
| responses-file | 72,127 | 7,236 |
| responses-focused | 72,627 | 9,612 |
| responses-focused-context | 75,043 | 8,633 |
| local-qwen | 71,913 | 834 |

Counts are provider-reported. For Chat Completions, input/output correspond to
prompt/completion tokens. The providers did not return a monetary cost for these
runs; cost remains unknown. Decisions returning zero output tokens does not imply
zero cost. The local row excludes model download and hardware/energy cost.

## Label evidence and reproducibility

[Executable witnesses](../../scripts/run_witnesses.py) passed locally on Elixir 1.20.2
and OTP 29. They ran 160 test executions in twelve groups, including two expected
mutant failures. Four target labels have mutation evidence from complete pinned
upstream test modules; eleven have extracted-unit evidence; one intentional delay
is source-reviewed. Four preference/duplicate-setup labels remain candidates.
The witness runner checks these expected outcomes, rather than requiring the
intentionally broken mutants to pass.

Saved predictions include reasons where the API provides them, usage, latency,
and packet hashes. Each `experiment.json` includes the exact manifests, rubrics,
and rendered request templates for that run. Early reports retain the original
candidate-status labels; later label evidence annotations do not change any
boolean verdict. The aggregate analysis adds track metadata to early runs.

Verify all seven saved request fingerprints, source packets, label/rubric hashes,
scores, and threshold sweeps without a model call:

```sh
uv sync --locked
uv run slop-decisions fetch
uv run python scripts/verify_reports.py
uv run python scripts/run_witnesses.py
```

The original discussion's ZIP was unavailable. This repository independently
reconstructs its documented public cases and supplies new executable witnesses;
it does not claim byte-for-byte recovery. Public PR links, pinned source spans,
and label rationales are in the seed manifests. See
[provenance and upstream licenses](../../THIRD_PARTY.md).
