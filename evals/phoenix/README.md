# Phoenix review cases

Nine authored examples cover the three Phoenix and Ecto rules. Each rule has a
defect, a valid lookalike, and a case with missing context. The labels come from
source review using the [framework contracts](../../skills/slop-review/references/phoenix.md).
They are development examples, not calibrated detector results.

To test a reviewer, give it the `slop-review` skill and the files in `inputs/`.
Use `case_id`, `dimension`, and `path` from `cases.json` to select each check.
Keep `expected` and `rationale` out of the review input. Ask for a supported
finding, no supported finding, or the specific missing evidence for each case.
Compare its evidence with the labels; do not grade matching wording.

The snippets target LiveView 1.x and Ecto 3.x behavior. They are source excerpts,
not a runnable Phoenix application. Syntax checks do not verify browser recovery
or database performance. Keep the published calibration fixtures unchanged.
