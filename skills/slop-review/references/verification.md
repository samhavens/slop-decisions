# Failure masking and debugging residue

These checks follow observed cleanup and agent-debugging complaints. They are
not a general concurrency or defensive-programming audit.

For a rescue or fallback, distinguish legitimate absence from an unexpected
failure. A successful empty query can mean `:not_found`; a database exception
cannot establish that fact. A log entry does not restore meaning that a caller
lost. Preserve a documented best-effort boundary that retains the required error
information. The legacy rule ID `success_shaped_failure` now covers false ordinary
domain errors as well as false success.

For defensive internal scaffolding, trace every path into the helper. Extra nil
checks after a validated internal boundary may encode impossible states. Public
input validation is different. For duplicated implementations, name the existing
owner and compare contracts; similar code can implement independent policies.

For test-environment workarounds, recover the original failure from history or a
local reproduction. Determine which state the new sleep, seed, global setting,
serialization or special production path can change. Use a control to establish
whether it addresses the cause. Missing explanation alone is not a defect.
`async: false` can be correct for a real process-global resource. A timeout can
be part of a real integration contract.

For weakened verification, keep one credible broken behavior fixed while
comparing the old and new checks. Did changing an exact amount to `is_number/1`,
accepting a snapshot, excluding the owner file or narrowing a gate let it pass?
Then look for an independent requirement change or a stronger retained test.
Removing a useless assertion, fixing an invalid fixture, or honoring a new
requirement is not automatically weakening. Never repair a real bug by deleting
its only failing evidence.

[Sources and evidence limits](sources.md) · [Coverage preservation](test-contracts.md)
