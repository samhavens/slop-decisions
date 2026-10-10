# Review skill upgrade: verification plan

Ship a standalone Codex skill that can discover abstraction, coupling, test-contract,
and temporal problems in ordinary Elixir diffs. Keep the API checker usable with
OpenAI, OpenRouter, and local models. Do not change published labels or old results.

## Acceptance

- Add nine distinct rules: false_unification, test_implementation_coupling,
  scattered_process_interface, oversized_process_capture,
  global_configuration_coupling, unnecessary_compile_time_work,
  non_atomic_invariant, unsafe_retry, and multiplicative_retries.
- Each rule has primary-source links, a search trigger, required context, an
  investigation, a concrete positive witness, and a valid lookalike.
- Add focused abstraction, OTP/configuration, test-contract, Ecto/retry, and
  investigation references. Include history, misuse probes, root-cause variant
  searches, and optional usage_rules guidance without adding dependencies.
- Preserve diff scope, explicit uncertainty, independent policies, meaningful
  macro work, global policy, atomic constraints, and idempotency exceptions.
- Keep reader docs short, put pain and value first, and retain the pattern table.

## Verification before release

1. Add tests for enriched rubric loading and provider prompts before changing
   their implementation. Preserve legacy custom rubric files and all providers.
2. Add fresh multi-file diff fixtures with positives, clean changes, justified
   complexity, and missing contracts. Validate Elixir syntax and run meaningful
   witnesses for behavior, interleavings, equivalent changes, and attempt counts.
3. Run one bounded blind pilot on twelve ordinary diffs with three reviewers:
   frozen v0.6.0 skill, upgraded skill, and plain review. Use the same inherited
   model/settings, identical tools/source/history, neutral case IDs, no rule
   hints, and no labels. Reviewers may inspect related files and Git history.
   Freeze inputs and expected outcomes before review. Do not tune on this run.
4. Score root causes and evidence, not matching rule names or prose. Preserve raw
   reviews, inputs, arm settings, usage, and disagreements. Report the pilot as
   authored development evidence, not an unseen accuracy benchmark or proof of
   a general improvement. Do not expand paid/provider testing without a budget.
5. Run the existing Python tests/lint/build, new witnesses, standalone skill
   validator, and a fresh-eyes read. Verify installation outside the repository.
6. Publish v0.7.0 as an experimental prerelease after CI passes. Update the local
   installed skill, bring main forward, and archive this managed worktree.
