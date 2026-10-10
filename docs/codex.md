# Review with Codex

The skill uses all 17 rules in your current Codex session. Codex can read callers,
validators, and tests to check whether a suspicious pattern is a real problem.
Each finding must include a code location and evidence.
See the [measured review results and limits](../reports/skill-2026-10-10/README.md).

## Install

In Codex, ask:

```text
Use $skill-installer to install https://github.com/samhavens/slop-decisions/tree/main/skills/slop-review
```

No Python package or checker API key is needed. Start a new turn after installation.
If the skill does not appear, restart Codex. See [Codex skills](https://developers.openai.com/codex/skills/).

For a manual install, clone this repository, then copy its `skills/slop-review`
folder into `~/.agents/skills/`. For a team, copy it into your project's
`.agents/skills/` and commit it. Include the whole folder: it contains the rules
and their exceptions.

## Review

In your code project, ask:

```text
$slop-review Review my changes against origin/main.
```

This includes branch commits, staged and unstaged changes, and new files that Git
does not ignore. The skill starts with changed Elixir files, then follows the
related code. Fetch `origin/main` first if it is missing or stale.

You can select files or rules in plain language:

```text
$slop-review Review lib/orders.ex and its tests. Only check success_shaped_failure and test_claim_gap.
```

Without a ref or file selection, the skill reviews local changes against `HEAD`.
Findings distinguish code defects, weak tests, and maintenance issues. A test gap
can exist in correct code. An incomplete review must say what remains unchecked.

The skill adds no separate checker API calls. It still uses your Codex model and
usage allowance. Use the existing session to reuse context. For a new scripted
review and CI options, see [tests and CI](ci.md).
