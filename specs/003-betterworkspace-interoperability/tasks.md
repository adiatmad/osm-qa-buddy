# Tasks: BetterWorkspace Review Interoperability

## Discovery

- [ ] Confirm the smallest externally supported BetterWorkspace/JOSM review-candidate input boundary.
- [ ] Record maintainer feedback and version constraints.
- [ ] Decide whether task IDs are required in the first handoff.
- [ ] Decide whether priority metadata is necessary; default to omission unless required.

## Contract

- [ ] Define the minimal review-candidate fields from the confirmed boundary.
- [ ] Define provenance and failure behavior.
- [ ] Document the human-review boundary.
- [ ] Verify the contract does not depend on private BetterWorkspace/Todo internals.

## Implementation

- [ ] Create the smallest producer/export path required by the accepted contract.
- [ ] Reuse existing QA Buddy finding and task-attribution data.
- [ ] Add focused regression tests.
- [ ] Add Windows/JOSM manual acceptance evidence.

## Quality gate

- [ ] Run the relevant automated tests.
- [ ] Inspect the complete diff for unrelated changes and speculative abstractions.
- [ ] Confirm existing JOSM validation and task attribution behavior remains unchanged.
- [ ] Update durable documentation if the confirmed contract introduces a lasting integration rule.
