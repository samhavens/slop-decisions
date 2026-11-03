# Failure masking and debugging residue

Use these checks for demonstrated accumulated machinery or false confidence, not
as a general exception-handling, concurrency, or defensive-programming audit.

## Ordinary results that hide failure

Distinguish a successful lookup with no row from a failed lookup. A blanket
`except Exception: return None`, empty collection, or ordinary not-found result
may erase a database outage or programming failure. Follow the fallback into its
caller; a log line does not restore a distinction the return contract lost.

Exercise an unexpected failure separately from genuine absence. Preserve narrow
expected exception mappings and documented best-effort behavior that retains the
information its consumers require. Inspect the actual exception hierarchy and
supported Python/framework version, particularly for cancellation and shutdown;
do not assume `except Exception` catches every failure.

## Internal accommodations and duplication

Trace all paths through the normalization boundary before calling an alternate
representation impossible. Type annotations alone do not establish that boundary.
Check bypass construction, deserialization, mutable state, inheritance, and
dynamic entry points. Keep guards needed by supported callers. Remove repeated
normalization only when runtime evidence establishes the internal contract.

For duplicated implementations, name both owners and compare behavior, side
effects, errors, policy, and reasons to change. Fixture scopes and resource
lifetimes can make similar setup intentionally different. Do not replace
independent policies with a flag-heavy abstraction just to remove repeated lines.

## Test-environment workarounds

Recover the original failure from targeted history or a local reproduction.
Trace what a new sleep, rerun marker, global seed, wider fixture scope, disabled
parallelism, or production `test_mode` branch can actually change. Demonstrate a
mismatch with the failure mechanism or a hidden failure before reporting it.
Missing rationale alone is not a finding.

Preserve real resource isolation, deterministic seeds, and waits for actual
completion. Tests of deadlines, backoff, expiry, or debounce can legitimately
depend on time. Prefer a bounded observable completion condition when completion
is the contract. Inspect teardown, event-loop ownership, background tasks,
process-global caches, and environment restoration when they explain the failure;
do not expand every review into a concurrency audit.

## Weakened verification

Hold the requirement and a credible broken implementation fixed while comparing
old and new checks. An exact refund assertion changed to `isinstance(..., int)`,
an unjustified tolerance, a new skip/xfail, broader warning suppression, accepted
snapshots, or a narrower CI command can allow previously rejected wrong behavior.
Check `xfail` run/strict settings and whether CI propagates failures when relevant.

Look for an independent requirement change or a stronger retained check first.
Deleting a useless assertion, fixing an invalid fixture, or applying a justified
numeric tolerance is not automatically erosion. Never remove the only evidence
of a real failure merely to make the suite green.

[Coverage preservation](test-contracts.md) · [Sources and limits](sources.md)
