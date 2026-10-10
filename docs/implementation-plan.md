# Implementation and verification plan

Build a Python CLI and library for the semantic Elixir checks described in the
source discussion. Ship named predicates, a pinned public-source development
set, context construction, provider adapters, evaluation, and calibration.

Verification commitments, before implementation:

- Exercise the CLI through subprocesses and actual local HTTP protocol fixtures.
- Check OpenAI Decisions, Responses, and OpenAI-compatible Chat Completions wire
  formats, authentication isolation, malformed output, refusals, truncation,
  timeouts, bounded retry, and missing context. Unknown must never mean clean.
- Validate pinned revisions and content hashes; keep labels, reviews, source
  revision names, witnesses, and before/after metadata out of model packets.
- Test scoring with hand-calculated confusion matrices, missing predictions,
  single-class dimensions, hard negatives, and strict before/after pairs.
- Keep PR families and repositories in one split. Reject tuning on a holdout.
- Run executable Elixir witnesses where feasible. Distinguish extracted-unit
  witnesses, upstream test reproduction, and unevaluated candidate judgments.
- Run a bounded live model pilot and publish the measured scope and failures.
- Check installation from the built wheel, documentation examples, CI, and
  fresh-eyes review before publishing the MIT-licensed repository.

The original ZIP attachment could not be downloaded because its authenticated
browser session was unavailable. Reconstruct the documented 20 targets from
public pinned revisions; do not claim byte-for-byte recovery of that artifact.
