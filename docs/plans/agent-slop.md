# Agent slop: scope and verification

Refocus the default skill on residue from agent coding sessions: manufactured
proof, redundant coverage, test-only production machinery, and weakened checks.
Use observed cleanup patches to select patterns. Do not infer code authorship.

## Deliverable

- Thirteen default rules: nine focused test/verification additions, plus failure
  masking, defensive internal scaffolding, duplicated implementations, and brittle
  tests. Refine success_shaped_failure to include false domain outcomes.
- Preserve prior general-review checks by explicit rule selection. Keep their
  broader references out of the default skill route. Use the same default subset
  for the API checker; custom rule banks continue to select all their rules.
- Sources must distinguish inspected patches, author reports and our Elixir
  adaptations. Pin commits and paths. Do not claim the original code was produced
  by a particular model without evidence.
- Every removal recommendation must name the retained test, boundary, failure
  mode and a discriminating check, or establish that the test checks only language
  behavior with no application contract. Keep a needed contract when its assertion
  is weak. Lower test counts and line coverage alone are not success criteria.
- Keep the README focused on the pain and benefit, with a concise pattern table.

## Verification before publication

1. Write failing regressions for default/explicit/custom rule selection before
   changing the CLI. Preserve all provider contracts and historical eval inputs.
2. Add Elixir adaptations of inspected cleanup patterns and valid lookalikes.
   Execute witnesses that distinguish broken behavior from manufactured proof,
   independent coverage from repetition, and valid cleanup from lost protection.
3. Freeze a twelve-diff pilot before one fresh independent skill reviewer runs.
   Use ordinary local source/history, no answer key or rule hints, no provider
   API calls and no external services. Review the evidence, not rule-name matches.
   Include an unrelated general defect to test the narrower boundary. Do not
   expand the pilot or claim production accuracy from authored examples.
4. Check source/rule consistency, standalone links, skill validity, tests, lint,
   package build and CI. Re-read changed code with fresh-eyes.
5. Publish v0.8.0 as a prerelease, update the local installed skill, bring main
   forward, and archive this worktree. Publish raw outcomes and limitations.
