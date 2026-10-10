# Review agent slop with Codex

The skill looks for manufactured evidence, repeated tests, test-only production
machinery and weakened verification in Elixir changes. Its 13 default rules come
from [observed cleanups and agent reports](../skills/slop-review/references/sources.md).
It is a focused review, not a complete correctness audit.

## Install

In Codex, ask:

```text
Use $skill-installer to install https://github.com/samhavens/slop-decisions/tree/main/skills/slop-review
```

No Python package or checker API key is needed. Start a new turn after installation.
If the skill does not appear, restart Codex. See [Codex skills](https://developers.openai.com/codex/skills/).

For a manual install, copy the complete `skills/slop-review` directory into
`~/.agents/skills/`. For a team, put it in the project's `.agents/skills/` and commit
it. Keep the references: they contain the exceptions and preservation rules.

## Review

```text
$slop-review Check my changes against origin/main for accumulated slop.
```

This includes branch commits, staged and unstaged edits, and non-ignored new files.
The skill follows related code, test setup and CI selection. Fetch the comparison
ref if it is missing or stale. Without a ref, it reviews local changes against `HEAD`.

You can narrow the review:

```text
$slop-review Review test/orders_test.exs. Only check mock_defined_behavior and unreachable_negative_control.
```

Or explicitly request an older, broader check:

```text
$slop-review Review lib/ship_order.ex and its callers for unsafe_retry.
```

A slop finding must explain the false confidence or unnecessary machinery. A
consolidation recommendation must name the retained test and the failure it
still catches. Review alone does not edit your tests. If you ask for cleanup, the
same preservation standard applies to the changes.

The skill uses your current Codex model and allowance. It does not start a
separate checker. See [tests and CI](ci.md) for scripted runs,
[dependency guidance](../skills/slop-review/references/investigation.md#dependency-contracts)
for optional `usage_rules` support, and the
[eval guide](../evals/accumulation/README.md) for evidence and limits.
