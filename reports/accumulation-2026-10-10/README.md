# Slop review: evidence and preservation

The focused skill found all six target slop problems in this twelve-diff pilot
and preserved all four useful-test changes. Its removal advice named retained
tests and showed that those tests still reject broken behavior.

This is a small authored demonstration of the review distinctions, not a measure
of accuracy on production code or improvement over plain Codex review.

| Outcome | Result |
| --- | ---: |
| Supported slop findings | 6/6 |
| Useful-test changes without warnings | 4/4 |
| Missing shared coverage left undecided | 1/1 |
| Unrelated general defect kept outside slop scope | 1/1 |

The findings cover declaration-only proof, a fixture supplying the asserted
effect, a negative test that misses its guard, repeated coverage, a test-only
production export, and a weakened assertion. All six have executed controls.

The clean cases retain a public capability declaration, a caller's rejection
handling, a distinct integration boundary, and a storage refactor that removes a
private-state assertion. The scope case still contains an arithmetic bug; a slop
review does not replace a correctness review.

For both proposed removals, the reviewer ran the named retained test alone and
showed that it rejects the relevant broken implementation. The fixtures supply
no project runner or CI configuration. Both reviews disclose that external test
selection remains unverified; this pilot does not establish end-to-end CI
preservation.

[Raw reviews](results.json) · [Case audit](audit.json) ·
[Executed controls](probes.json) · [Status scores](scores.json)

## Time, scope and reproduction

One fresh **gpt-6-astra** reviewer with **max reasoning** used local source,
history and tools. It completed 39 local Elixir executions in **3m 26s** of total
review time. The session used 68,360 uncached input tokens, 464,256 cached input
tokens and 9,233 output tokens. These are cumulative runtime counts across tool
turns, not unique prompt lengths. Output includes reasoning. Development and
scoring are excluded. The run used normal Codex usage, with no separate checker
API calls; these counts are not an API invoice.

Inputs, labels and the skill were frozen at
[`8fedaae`](https://github.com/samhavens/slop-decisions/commit/8fedaaee4140113250c9744a1c319a2a9a7e28db).
The reviewer received source snapshots and the skill, without labels, suspected
rules or expected findings. Those inputs stayed unchanged. The evidence audit
checks the findings and controls separately from status matches.

The cases are authored Elixir adaptations of the same patterns taught in the
skill. They are not held-out upstream patches. All twelve share one reviewer
context, and several are paired examples. There is one trial, no plain-review
comparison, and no rerun or tuning against these results. Six focused patterns
have blind positive cases here; the full 22-case fixture set also has local
controls for circular expectations, mechanical expansion, environment workarounds
and failure masking. Those extra cases have no blind-review result in this report.

[Run settings, usage and hashes](run.json) · [Reviewer request](request.txt) ·
[Verification plan](../../docs/plans/agent-slop.md) ·
[Prepare and score a run](../../evals/accumulation/README.md) ·
[Source provenance](../../skills/slop-review/references/sources.md)
