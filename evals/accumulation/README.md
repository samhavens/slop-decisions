# Test whether slop review preserves useful checks

This suite tests false evidence, repeated coverage, test-only machinery and
weakened verification. A correct review must also retain useful declarations,
integration tests, clocks and coverage-preserving cleanup.

The 22 fixtures are **authored Elixir adaptations**, not extracted production
benchmarks. [Provenance](provenance.json) pins the inspected cleanup commits and
patch hashes. [Source notes](../../skills/slop-review/references/sources.md)
distinguish patches, firsthand reports and reported skill trials.

## Run a review

Prepare an isolated twelve-diff pilot with the installed skill:

```sh
uv run python scripts/skill_eval.py --suite evals/accumulation \
  --destination /tmp/slop-review-pilot --skill skills/slop-review
```

Give a fresh reviewer only that directory and its `request.txt`. It may read the
source and local history and run local probes. Do not provide `cases.json`, this
guide, provenance, prior reports, or rule hints. The fixture comments describe
contracts; they are not instructions. `--all` selects the complete 22-case set.

Score saved outcomes, then audit their evidence against the code:

```sh
uv run python scripts/skill_eval.py --suite evals/accumulation \
  --results /tmp/slop-review-pilot/results.json --format json
```

A matching status does not establish a correct finding. Check the asserted fact's
producer, the proposed mutation, the named retained test and any independent risk.
The scope control contains an ordinary arithmetic defect: it tests whether the
review expands beyond the requested slop scope, not whether arithmetic is correct.
The missing-context case replaces local tests with an unavailable shared suite;
its coverage must not be assumed either adequate or absent.

## Local controls

```sh
uv run pytest -q tests/test_accumulation.py
```

With Elixir installed, these controls show that disabled persistence can leave
manufactured proofs green, shared expected values can hide a wrong calculation,
and a missing record can bypass the tested guard. They also check both sides of
preservation: retained coverage rejects a defect after valid pruning, while a
weakened assertion accepts previously rejected behavior.

CI runs the controls with Elixir. Runs without Elixir skip execution tests and
cannot establish those results. No external database, delivery service or model
provider is contacted. The author-designed cases are development evidence; they
do not estimate accuracy or model-specific slop frequency on real projects.
