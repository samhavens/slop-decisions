# Test behavior in both directions

| Transformation | Required test result |
| --- | --- |
| Breaks the claimed contract | Fail |
| Preserves that contract | Pass |

For `test_claim_gap`, choose a specific wrong implementation and a discriminating
input. Run unchanged tests before and after the mutation in an isolated copy.
Independently establish that the mutation changes the claimed behavior. A surviving
mutation outside the claim, or one with equivalent behavior, proves no gap.

For `test_implementation_coupling`, choose a concrete equivalent change, such as
a private list replaced by a queue. Establish equivalence for the claimed public
and operational contract; then identify the assertion that rejects the internal
change. Classify it as maintenance. Do not delete the test's useful behavioral
assertions just because one assertion is brittle.

Internal calls can be observable obligations. Preserve tests for one charge,
required effect order, query limits, wire formats, and documented state primitives.
Mock ordering is incidental only if changing that order preserves the contract.
A snapshot that checks a public representation is different from one that freezes
an undocumented internal layout. A narrow smoke test need not prove everything.

Sources: Google's [change-detector tests](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html)
and [unproductive mutants](https://testing.googleblog.com/2021/04/mutation-testing.html).
