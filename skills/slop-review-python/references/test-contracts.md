# Does the test add evidence?

Read the claim, setup, production owner, and assertion together. A test name is
not a specification on its own; check the public contract and callers.

## Manufactured proof

| Candidate | Discriminating control | Useful lookalike |
| --- | --- | --- |
| Declaration substituted for behavior | Disable the database write, task execution, or delivery while preserving the object, registration, or flag. | A public schema, plugin inventory, or capability declaration is itself the specified contract. |
| Mock-defined behavior | Trace the receipt, decision, ordering, or stored row back through fixtures and mock side effects; replace the real owner with a no-op or wrong decision. | The caller must forward a dependency result, await it, or handle its documented rejection. |
| Circular expected value | Introduce one credible error in the helper shared by actual and expected. | Independent known values or invariants constrain the output; a shared factory only constructs input. |
| Unreachable negative control | Satisfy every other prerequisite, then bypass only the intended guard. | Bypassing that guard allows the forbidden action and makes the denial test fail. |

Inspect `conftest.py`, autouse fixtures, monkeypatches, and the namespace where a
patched name is looked up. A mock supplying a rejection can prove the caller's
response; it cannot prove the mocked authorization policy. `spec` and `autospec`
constrain mock interfaces, not the truth of their configured return values.

For authorization, use an existing record, valid input, and authenticated identity;
keep only the permission wrong. A missing row or invalid request may reject before
authorization. `pytest.raises(Exception)` can accept the unrelated failure. Check
the intended exception or response and forbidden side effects. Confirm that the
test is collected, selected, and actually reaches the guard.

Establish a passing baseline before a broken control. Confirm independently that
the control changes the claimed behavior rather than breaking collection, setup,
or an unrelated prerequisite. A surviving control supports only the particular
gap it demonstrates. Do not describe a hypothetical control as executed.

## Python boundaries

| Boundary | What to establish | What to preserve |
| --- | --- | --- |
| Async calls | `AsyncMock.assert_called_once_with` establishes a call, not an await. Use await evidence when the caller promises to await. Neither mock assertion proves the real dependency's effect. | A forwarding/awaiting contract can legitimately end at the mock boundary. Scheduling can also be correct when ownership and completion are tested at their actual boundary. |
| Persistence | Separate construction, adding to a unit of work, flush, and commit. ORM identity-map reads and fixture-populated rows may survive a removed write. Use an independent read at the promised transaction boundary. | A repository may promise to stage work while its caller owns commit. Test transactions, savepoints, and in-memory database connection rules can limit what a second connection proves. |
| Runtime validity | An annotation, `TypedDict`, `cast`, or dataclass field type does not enforce runtime validity. Trace actual validation, all supported entry paths, and later mutation before deleting guards. | Public adapters, deserialization paths, dynamic callers, and framework validation that the installed version really executes. |
| Parametrization | Identify distinct application defects or interacting dimensions; do not confuse many generated cases with strong evidence. | Default factories, `__post_init__`, descriptors, validation, boundary cases, property-based invariants, and independently specified compatibility inventories. |
| Call counts and internals | Show a concrete equivalent implementation that fails only an incidental assertion. | Exactly one charge, required await/cleanup, a query budget, wire order, or a documented representation can be the contract. |

Do not demand production network calls to prove an integration boundary. Use the
project's permitted local integration setup, and state when an external boundary
remains unverified. Check installed framework behavior using
[primary documentation](sources.md#python-runtime-and-framework-contracts).

## Accumulated coverage

For a candidate duplicate:

1. Name the retained test, file or node ID, and production boundary.
2. Identify the concrete failure both tests reject.
3. Try a failure specific to the added layer: imports, dependency wiring,
   serialization, transactions, cleanup, or task ownership may distinguish it.
4. Check markers, skips, `xfail` behavior, platform/version conditions, fixtures,
   plugins, and CI commands. A test outside the relevant gate is not retained
   coverage for that gate.

Do not impose one-test-per-contract quotas. Fast feedback, fault localization, and
different supported environments can justify layers. Mocking the HTTP or worker
boundary away does not demonstrate that its integration test is redundant.

For a test-only seam, trace public and dynamic consumers as well as local callers.
An inspection getter may only sustain a weak private-state test. A clock adapter,
documented package export, or registered plugin can remain useful even if tests
supply its only alternate implementation. An underscore or absence of direct
callers does not prove that a symbol has no contract. Do not preserve unused
scaffolding by manufacturing replacement tests for it.

## Preserve before pruning

Use three outcomes: retain useful coverage, consolidate into a named retained
test, or keep the contract and repair its proof. Delete a pure language read-back
only after excluding independent default, validation, public, and compatibility
requirements; do not add a tautological replacement.

Before removal, build a small map: candidate test → failure → retained test and
location → execution gate → control result. Keep or repair coverage when the map
has a gap. Mark inspection-only conclusions explicitly. If cleanup is requested,
run the retained boundary after the edit and check that the deliberate broken
control still fails. Revert probe mutations; leave only the requested correction.
