# Phoenix rule verification

Add three rules to the shared bank and installed Codex skill: UI-only server round
trips, loss of required state after a LiveView disconnect/remount, and avoidable
per-record database reads. Preserve valid server operations, automatic form
recovery, and batched preloads as negative examples.

Before implementation, add failing CLI tests that select the new rules through
each supported provider without paid requests. Keep the standalone skill's rule
copy consistent with the package. Add authored examples with positive, valid,
and missing-context cases for each rule; keep labels outside review packets.

Use a blind independent review of those examples to check the rule boundaries.
Parse the Elixir snippets, run the existing offline tests, lint, build, and verify
the installed skill. Keep published evaluation inputs and measurements unchanged;
new source-review examples are not calibrated detector results.
