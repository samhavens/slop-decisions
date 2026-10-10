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

For a new check, define one observable predicate, the evidence needed to assess
it, a positive case, and a hard negative with similar syntax. Add an executable
counterexample where possible. Do not infer whether a person used AI.

For a new case, add pinned source and spans to `data/seed/targets.jsonl`, and put
labels, rationale, provenance, and grading witnesses in `labels.jsonl`. The
package data lives under `src/slop_decisions/`. Keep every revision, neighboring
target, and mutation from a repository in the same split. Development examples
cannot later become a holdout. Check upstream licensing before redistributing
source; the included manifest fetches it on demand.

Changes to prompts, examples, source selection, and thresholds should be tested
separately. Save the run settings and individual outcomes, including failures.
Report coverage alongside accuracy. A failing provider call is never a clean
assessment. When reporting performance, identify candidate/preference labels
and distinguish full upstream tests from extracted-unit witnesses.
