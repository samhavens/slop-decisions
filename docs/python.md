# Review Python slop with Codex

Use `slop-review-python` to find weak test evidence and accumulated production
machinery in Python projects. It preserves the original skill's 13 focused
predicates and evidence standards, with Python examples and exceptions.
It is a standalone skill; no checker package or separate model API key is needed.

## Install

In Codex, ask:

```text
Use $skill-installer to install https://github.com/samhavens/slop-decisions/tree/main/skills/slop-review-python
```

For a manual install, copy the complete `skills/slop-review-python` directory into
`~/.agents/skills/`. For a project install, copy it into `.agents/skills/` in that
project. Keep the references and license with the skill. Its distinct name lets
it coexist with the Elixir skill.

## Review

```text
$slop-review-python Review this codebase for accumulated slop.
```

```text
$slop-review-python Review my changes against origin/main for accumulated slop.
```

```text
$slop-review-python Review tests/test_orders.py. Only check mock_defined_behavior and unreachable_negative_control.
```

Review alone does not edit code. If you ask for cleanup, the skill must preserve
each needed contract, name retained coverage before consolidation, and check that
the retained test runs in the relevant gate.

## Python distinctions

| Pattern | What the review checks |
| --- | --- |
| Manufactured evidence | Fixtures, autouse setup, patch targets, and mock side effects that supply the behavior a test claims to prove. |
| Async evidence | Whether an assertion proves a call, an await, scheduled work, or the real effect required by the contract. |
| Persistence evidence | Whether the contract concerns construction, staging, flush, commit, or an independent database read. |
| Runtime guards | Actual validation and reachable callers; annotations alone do not prove invalid input impossible. |
| Repeated tests | Distinct boundaries, interacting parameters, property-based invariants, supported environments, and CI selection. |
| Public interfaces | Package exports, entry points, decorators, dynamic imports, SDK compatibility, and useful dependency seams. |
| Weakened verification | Assertions, tolerances, snapshots, warning filters, skips, xfail behavior, and verification gates. |

Use the reviewed project's interpreter, test runner, framework versions, and
plugins. The skill does not require pytest, uv, a particular ORM, or an async
framework. It does not include the original skill's optional Elixir/OTP/Phoenix
checks or add Python support to the experimental API checker.

## Evidence and limits

The [rules](../skills/slop-review-python/references/rules.json) retain the upstream
pattern provenance. Their Python examples are authored adaptations, not a mined
Python corpus. The [synthetic development cases](../evals/python/README.md) include
weak tests and useful lookalikes with executable broken controls. They do not
establish detection accuracy on Python projects. Upstream Elixir evaluation
scores do not transfer to this skill.

[Coverage preservation](../skills/slop-review-python/references/test-contracts.md)
· [Runtime sources](../skills/slop-review-python/references/sources.md)
