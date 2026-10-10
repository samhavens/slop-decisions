# slop-decisions

Agent coding sessions can leave tests that prove nothing, repeated coverage, and
production code built only to support those tests. slop-decisions helps Codex find
that clutter while keeping the checks that catch real failures.

Use it with static checks such as [ex_slop](https://github.com/elixir-vibe/ex_slop).
This skill reviews context and evidence; it does not guess who wrote the code.

## Use it

In Codex, ask:

```text
Use $skill-installer to install https://github.com/samhavens/slop-decisions/tree/main/skills/slop-review
```

Then, in your Elixir project:

```text
$slop-review Check my changes against origin/main for accumulated slop.
```

The skill uses **13 focused checks** in your current session. It reads the real
code and tests, identifies what a test actually proves, and names retained coverage
before recommending removal. It makes no separate checker API calls; normal
Codex usage applies.

[Install and select checks](docs/codex.md) · [Tests and CI](docs/ci.md) ·
[Evidence and eval limits](evals/accumulation/README.md)

## Patterns

| Pattern | Example |
| --- | --- |
| Declaration substituted for behavior | “Persists the record” only inspects a changeset. |
| Mock or fixture supplies the behavior | Setup inserts the expected row before testing whether save writes it. |
| Circular expected value | Expected and actual both use the same broken calculation. |
| Negative test misses its guard | An ownership test supplies a nonexistent record and exits before authorization. |
| Repeated coverage across layers | A new helper matrix repeats a stronger existing owner test with no distinct risk. |
| Mechanical case expansion | A loop constructs structs and reads back every supplied field. |
| Test-only production scaffolding | A new export exists only to inspect private state in a weak test. |
| Tests tied to private implementation | A storage refactor preserves public behavior but breaks a private-map assertion. |
| Weakened verification | An exact refund assertion becomes `is_integer/1`, accepting wrong amounts. |
| Test-environment workaround | A test repair adds a sleep that cannot address the actual failure. |
| Failure disguised as a normal outcome | A database exception becomes `:not_found`. |
| Defensive internal scaffolding | Private helpers accept nil after a boundary guarantees a valid struct. |
| Duplicated implementation | A new helper repeats behavior already owned by another module. |

Similar syntax can be valid. Public capability declarations, real integration
boundaries, useful adapters and justified isolation must survive a cleanup.
[Rules and exceptions](skills/slop-review/references/rules.json) ·
[Sources from real cleanups](skills/slop-review/references/sources.md) ·
[Coverage preservation](skills/slop-review/references/test-contracts.md)

The experimental API checker supports **OpenAI, OpenRouter, and local models**,
with the same 13 defaults. [API setup](docs/usage.md) · [Model options](docs/models.md).
The [22 broader review checks](skills/slop-review/references/broader-review.md)
remain available by explicit selection. This is not a general code-quality gate.

[Contribute](CONTRIBUTING.md) · [MIT license](LICENSE)
