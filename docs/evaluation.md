# Evaluation contract

The initial set has 20 targets: eight positive, twelve negative, and seven
before/after pairs, across five repositories and six PR families. All are
development material. Eight of the fourteen rubric dimensions have examples;
the other six have no seed examples. A separate [authored calibration study](calibration.md)
covers all fourteen checks. Neither set estimates production precision.

`sources.json` pins downloads by full commit and SHA256. `targets.jsonl` contains
the source selection, dimension, group, track, and split. `labels.jsonl` contains
the verdict, provenance, rationale, pair relationship, and proposed witness.
The runner constructs model input from an allowlist of source spans and files;
it does not serialize these dataset rows into the prompt.

Two test cases have a neutral behavior focus shared across both revisions. This
defines the evaluated part of the suite without giving the expected answer or
mutation to the model. For ex_slop fixtures, every context mode sends only the
embedded Elixir code, never the outer test name or `assert_issue` oracle.

## Context experiments

- `target`: exact marked lines, without related files.
- `window`: target plus up to forty neighboring lines on each side and explicit
  related sources.
- `file`: whole target file plus explicit related sources.

The checker accepts explicit spans and related files. It does not claim to
resolve a complete Elixir call graph. Context that exceeds `--max-chars` fails
preflight; it is never silently truncated. Missing files or invalid source
hashes make eval targets unassessed. Source comments can contain useful contracts
but are untrusted input and can influence a model despite the prompt boundary.

`minimal` prompts state the predicate and required evidence. `examples` adds the
positive and hard-negative examples. `--rubrics` accepts an alternative JSON bank
with the same fields for controlled experiments. These examples were developed
alongside the seed set; measuring this set is development fit, not generalization.

## Metrics

A prediction is positive when `probability >= threshold`. The probability from
generative models is self-reported, and need not be calibrated or interchangeable
with a Decisions probability. Thresholds need validation for the model, prompts, and source selection in use.
The published calibration study tested one shared pair of thresholds across fourteen
checks. The fitted pair failed its held-out test; it did not validate individual checks.

Primary macro balanced accuracy averages `(TP / P + TN / N) / 2` over dimensions
with both labels. `P` and `N` include unassessed targets, so missing assessments
cannot improve this score. The confusion matrix separately counts unassessed
targets instead of relabeling them negative. Single-class dimensions have null
balanced accuracy and remain visible in the dimension report.

Coverage is assessed / all targets. `accuracy_all_targets` treats unassessed as
failures; `accuracy_assessed` conditions on assessed targets. Both are shown.

A fix pair passes only when both sides are assessed and the positive crosses
the warning threshold while the negative falls below it. A smaller score after
the fix is insufficient. Incomplete pairs from an explicit subset are counted
separately.

Hard-negative false-positive rate uses assessed hard negatives as its denominator
and is always accompanied by hard-negative coverage. Zero assessed negatives
produces null FPR. Results by track separate behavioral/semantic cases, the
Boundary preference, and Logflare's deterministic duplicate-setup baseline.

Threshold sweeps use stored probabilities, without more model calls. They refuse
holdout labels. Adding calibration/holdout data requires different repositories;
manifest validation prevents repository and PR-family overlap across splits.

## Reproduction and limits

Runs save `run.json`, append-only `predictions.jsonl`, `report.json`, and an
`experiment.json` snapshot of manifests, rubrics, and rendered request templates. The run
fingerprint includes actual request bodies, provider settings, source packets,
and labels. Resume refuses a changed plan and skips every completed row,
including previously unassessed rows. Use a new output directory to repeat a
failed experiment. Provider error bodies and API keys are never saved.

Model aliases and provider behavior can change; a request hash cannot freeze a
remote service. Pin model versions where offered and repeat trials before
claiming a stable effect. Published initial runs contain one trial per cell.
Latency is total per-call wall time, including retries; usage includes only
values supplied by the provider. No provider-reported cost means unknown cost.

Run behavioral witnesses with:

```sh
uv run slop-decisions fetch
uv run python scripts/run_witnesses.py
```

The script reproduces the whole Tesla cookie and path-template test modules and
performs one controlled mutation for each. Old suites must let the mutant
survive; repaired suites must fail exactly one test. Other witnesses execute
extracted upstream loops/functions using explicit transport, telemetry, or
chunk-reader stubs. They establish the narrow behavior under test, not the
correctness of entire upstream applications. The Boundary preference and setup
deduplication remain candidate judgments; the intentional delay is source-reviewed.
