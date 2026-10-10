# Contributing

Use Python 3.11 or later and uv:

```sh
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

Provider tests run offline, including a real loopback HTTP server exercised by
the CLI. Do not add paid network requests to the default tests. The separate
witness workflow downloads hash-pinned public source and needs Elixir.
That workflow also runs the ExUnit example against a local test server.

For a new check, define one observable predicate, the evidence needed to assess
it, a search trigger, an investigation, primary-source links, a concrete positive
witness, and a hard negative with similar syntax. Add an executable
counterexample where possible. Do not infer whether a person used AI.

The standalone Codex skill is in `skills/slop-review`. When you change
`src/slop_decisions/data/rubrics.json`, copy it to the skill's
`references/rules.json`. Tests check that both copies match and that the skill's
references work outside this repository. Test review instructions on a small
repository with known defects and valid lookalikes; do not give the reviewer the
answer key. Check its evidence and missed cases, not just its wording.
Use the [Phoenix review cases](evals/phoenix/README.md) for the LiveView and
database rule boundaries. Use the [discovery eval](evals/discovery/README.md) to
test ordinary diffs without rule hints, with matched plain and skill reviews.
Keep new examples separate from published eval inputs.

For a new case, add pinned source and spans to `data/seed/targets.jsonl`, and put
labels, rationale, provenance, and grading witnesses in `labels.jsonl`. The
package data lives under `src/slop_decisions/`. Keep every revision, neighboring
target, and mutation from a repository in the same split. Development examples
cannot later become a holdout. Check upstream licensing before redistributing
source; the included manifest fetches it on demand.

Changes to prompts, examples, source selection, and thresholds should be tested
separately. Save the run settings and individual outcomes, including failures.
Report coverage alongside accuracy. A failing provider call is never a clean
assessment. For threshold studies, use the [calibration case format](calibration/README.md)
and preserve the fit before holdout calls. Verify saved results with
`uv run python scripts/verify_calibration.py`.

When reporting performance, identify candidate/preference labels
and distinguish full upstream tests from extracted-unit witnesses.

For reader documentation, use [ASD-STE100](https://www.asd-ste100.org/).
State the problem and benefit first. Keep the README to setup and the pattern table.
Put setup options, API details, and evidence in linked guides.

Choose default slop patterns from inspected cleanups or concrete agent reports,
not by adding another general review principle. Record provenance and distinguish
Elixir adaptations from mined patches. Keep a hard negative and a preservation
control: a cleanup must retain the contract, not just lower the test count.
Update `src/slop_decisions/data/slop-rules.json` and the standalone skill subset together; older
checks stay available by explicit selection. See the
[accumulation suite](evals/accumulation/README.md).
