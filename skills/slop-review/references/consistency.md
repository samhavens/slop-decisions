# Interleavings, partial completion and retries

For `non_atomic_invariant`, name the promise and all writers. Write a schedule:
A reads, B reads, A commits, B commits. What prevents both from acting on the same
old fact? Inspect migrations, constraint columns and predicates, tenant scope,
locks, conditional updates and conflict handling. A transaction groups work but
does not by itself serialize competing checks. Check the actual isolation level.
For a multi-step operation, also stop after each durable effect and inspect the
recovery path. Do not claim a race if a supplied atomic boundary prevents it.

Ecto's `unsafe_validate_unique` can give early feedback. A matching database
unique index enforces uniqueness; `unique_constraint` maps its violation to a
changeset error. The changeset declaration alone does not create the index.
Missing migrations can block a conclusion. See
[Ecto uniqueness](https://hexdocs.pm/ecto/Ecto.Changeset.html#unsafe_validate_unique/4)
and [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html).

For `unsafe_retry`, simulate: remote effect commits, response is lost, caller
retries. Include worker restart and redelivery. Follow one logical operation's
identity across attempts. Verify atomic receiver deduplication, payload matching,
retention time and conflict responses. A freshly generated key per attempt, a
local flag set after the call, or the mere presence of a key header is insufficient.
State-setting writes and effective reconciliation can make retries safe. See
[AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

For `multiplicative_retries`, draw the actual retrying call path, including library
and job settings. Distinguish attempts from additional retries. Four worker
attempts times three client attempts can make twelve downstream attempts. Check
which failures reach each layer, backoff, shared deadlines and cancellation.
A timeout that is restarted per layer is not an end-to-end deadline. Compare the
result with an explicit load or latency budget; without one, report the known
amplification as a question rather than inventing a violation. Backoff spreads
attempts but does not reduce their count. See
[AWS retry guidance](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).
