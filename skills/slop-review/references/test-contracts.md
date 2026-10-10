# Does the test add evidence?

Read the claim, setup, production owner and assertion together. A test name is
not a specification on its own: check the surrounding contract and callers.

## Manufactured proof

| Candidate | Discriminating control | Legitimate lookalike |
| --- | --- | --- |
| Declaration substituted for behavior | Disable the write/start/delivery while preserving the changeset, child spec or flag. | The public contract is capability discovery or the child specification itself. |
| Mock-defined behavior | Trace the asserted receipt, decision, ordering or row back through setup. Replace the real owner with a no-op or wrong decision. | The caller must forward a result or handle a rejection supplied by a dependency. |
| Circular expected value | Introduce one error in the helper shared by actual and expected. | Independent known values or invariants constrain the result; a shared factory merely builds input. |
| Unreachable negative control | Satisfy all other prerequisites, then bypass only the intended guard. | Removing that guard allows the forbidden action and makes the test fail. |

A rejection mock can prove how a caller handles `{:error, :unauthorized}`. It
cannot prove that the mocked policy correctly rejects a user. A pre-existing row
cannot prove that an operation inserted it. A changeset is not a database write.

For authorization, start with an existing record, valid request and authenticated
identity. Keep only ownership/permission wrong. A nonexistent record may exit
before authorization. Check side effects as well as the result when they are the
contract. If the test is conditionally registered, verify that it runs at all.

Establish the baseline before the broken control. Confirm that the control
changes the claimed behavior independently of the assertion under review. A
control that changes setup instead of the owner may only prove the fixture.

## Accumulated coverage

For a candidate duplicate, compare what the two tests can distinguish:

1. Name the existing test, file and production boundary.
2. Identify the same concrete failure both reject.
3. Try a failure in the added boundary that the existing test cannot reach.
4. Check that the retained test runs in the relevant supported environment and CI
   selection. A skipped or unrouted test is not retained coverage.

A unit test and HTTP test may protect different contracts. A test replayed through
a transparent helper and the same mocks may add none. Mocking the HTTP boundary
away does not prove that an HTTP test is redundant. Do not make one-test-per-contract
a rigid quota: speed, localization and supported environments can justify layers.

For a matrix or inventory, identify what different application defect each extra
row detects. Struct literal read-backs exercise Elixir itself. Custom constructor
validation, defaults, interacting options and published protocol inventories have
independent value. An exact string check is useful when it fixes a specified wire
key and survives an internal identifier rename.

For a test-only production seam, trace all callers and public commitments. A
private-state getter or unused reverse mapper may exist only to feed a weak test.
A clock, adapter or documented SDK export may remain useful even if tests supply
its only alternate implementation. Lack of local callers cannot disprove external
use. Do not preserve dead scaffolding by adding replacement tests for it.

## Preserve before pruning

Use three distinct outcomes: retain useful coverage, consolidate into a named
retained test, or keep the contract and repair its proof. Delete a pure language
read-back only after ruling out an independent public/default/compatibility
contract; no new tautological replacement is needed.

Before removal, build a small coverage map: candidate test → failure → retained
test/location → gate → control result. It can be a few lines in the review; do not
create a campaign ledger unless the user requests a broad cleanup. If the map has
a gap, keep or repair the necessary coverage. Record an inspection-only conclusion
as such. If cleanup is requested, test the retained boundary after the edit and
check that its deliberate broken control still fails.

[Source patches and provenance](sources.md) · [Focused predicates](rules.json)
