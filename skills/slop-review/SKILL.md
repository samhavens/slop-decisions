---
name: slop-review
description: Review Elixir code for semantic defects, weak tests, and needless complexity using 17 evidence-based rules. Use when asked to check changed code for slop, apply slop-decisions rules, or review Elixir code that passes static checks but may hide a behavior or maintenance problem.
---

# Review with evidence

Use the current session to review the code. Read [all rules](references/rules.json),
including their required context and negative examples. Apply all 17 unless the
user selects a subset. Do not run `slop-decisions check`, call a separate provider,
or start one agent per rule. The rules guide a review; they are not a scorecard.

## Select the code

Use the user's files or diff scope. If none is given, review local changes against
`HEAD`. For a requested branch or ref, find its merge base with `HEAD` and compare
the current working tree against that commit. Include committed branch changes,
staged and unstaged edits, and untracked files that Git does not ignore.

Use `git status --short`, `git diff --no-ext-diff --no-textconv --no-renames`, and
`git ls-files --others --exclude-standard` from the repository root. Read new files
separately and deleted code from the base revision. Do not silently replace a
missing base ref or treat merge conflicts as a completed review.

Start with changed `.ex` and `.exs` code. Read complete functions and relevant
callers, schemas, configuration, tests, and helpers, even when they did not change.
Report issues introduced or exposed by the change. Review older issues only if
the user requests a broader review. If there are no changes, say so.

For a large diff, prioritize behavior and state changes. State which files remain
unreviewed. Do not imply that sampling one file checks a whole project.

## Test each candidate finding

Trace the contract before deciding that a pattern is a problem:

- Follow callers and validators before claiming an invalid input is reachable.
- Read the server operation before claiming that authorization exists only in the UI.
- Check ownership, supervision, and timers before calling a process unnecessary.
- Check both readers and writers before claiming that stored values can disagree.
- Read assertion helpers and fixtures before claiming that a test proves nothing.
- Check dependency versions and behavior before proposing a framework replacement.
- For LiveView and database checks, use the [Phoenix and Ecto boundaries](references/phoenix.md).

Try to refute each candidate with the rule's negative examples and the actual
code. A familiar shape is not evidence. If a needed contract is unavailable,
state what prevents a decision instead of inventing a finding.

For a defect, give a reachable input or sequence, the expected result, and the
actual result supported by the code. Run a focused test or probe when practical.
Say whether the evidence comes from execution or inspection.

For a test gap, name the behavior the test claims and a concrete incorrect
implementation that its assertions would accept. When practical, use an isolated
copy to run the unchanged tests first, apply that mutation, and run them again.
Confirm that the mutation changes the claimed behavior with a discriminating
input. Report an unexecuted mutation as an inspection finding. Weak tests do not
by themselves mean that the production code is broken. A narrow smoke test need
not prove unrelated behavior.

For a maintenance issue, show the specific burden and the simpler equivalent.
Respect useful boundaries, distinct contracts, and deliberate snapshots. Omit
style preferences without a concrete benefit. Keep review edits and mutations
out of the user's working files unless the user also asks for a fix.

## Report useful findings

Lead with actionable findings, ordered by impact. For each one, include:

- The rule and kind: **defect**, **test gap**, or **maintenance**.
- The file and line, trigger, consequence, and evidence.
- The smallest useful correction or discriminating test.

Combine overlapping findings. Do not fill a quota or list empty rule results.
Do not assign a probability or treat the absence of findings as a test pass.
End with the scope reviewed, tests actually run, and any missing evidence or
unreviewed files. If no finding is supported, say that plainly and include those
limits. Keep the report concise.
