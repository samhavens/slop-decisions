# Changed-code checks

Make the first run useful: OpenAI with all 14 checks, local models by explicit choice,
and a README that explains the problem and shows each pattern.

## Verification before implementation

- Exercise the installed CLI against a local HTTP server. With no model options,
  it must use OpenAI Decisions, `gpt-6-luna`, and every rule. Selecting local or
  OpenRouter must require a model. Repeated rule options must not repeat requests.
- Use temporary Git repositories to test changed-file selection. Include branch
  changes, staged and unstaged edits, untracked files, renames, deletions, empty
  files, ignored files, paths with spaces, bad refs, and merge conflicts.
- Check the complete current contents of changed `.ex` and `.exs` files. Compare
  from the merge base to include branch work and local edits. Report skipped
  deleted and empty files. An empty selection must pass without a key or request.
- Test command exit codes and JUnit output for pass, warning, and unassessed
  results. Run the documented ExUnit example against a local test server.
- Reject bad inputs and excess checks before any model request. Keep existing
  provider, source, calibration, and credential isolation tests passing.
- Run lint, formatting, the full test suite, build/install checks, and the existing
  report and Elixir witness checks. Re-read changed code before publication.

The optional Norma clarification is pending. The general command and JUnit
report will work in ordinary test/CI runners. A named integration must match the
actual tool's documented interface.
