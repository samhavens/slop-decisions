# Explicit broader checks

The [22 broader predicates](broader-rules.json) remain available when the user
selects them by name or explicitly requests a broader review. They are not the
default definition of slop. Apply the selected contract and exceptions; do not
load the complete general checklist for an ordinary slop review.

- [Abstractions](abstractions.md): independent policies and interface burden.
- [OTP and configuration](otp.md): process boundaries, capture and shared settings.
- [Consistency and retries](consistency.md): overlap, idempotency and attempt budgets.
- [Phoenix and Ecto](phoenix.md): UI state, reconnects and per-record reads.

The API checker accepts each rule by `--rule NAME`. Its default is the same
13-rule slop set as the skill. Old published evaluations retain their original
rules, labels and scope.
