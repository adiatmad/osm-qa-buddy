# Tasks: BetterWorkspace Review Interoperability

## Discovery

- [x] Confirm the OSM-layer handoff boundary.
- [x] Record the agreed first-milestone scope: candidate ways plus referenced nodes.
- [x] Treat task IDs as optional metadata.
- [x] Omit priority metadata from the interoperability contract.

## Contract

- [x] Define review-candidate semantics.
- [x] Define the minimal OSM layer and sidecar manifest fields.
- [x] Define provenance and failure behavior.
- [x] Document the human-review boundary.
- [x] Verify the contract does not depend on private BetterWorkspace/Todo internals.

## Implementation

- [x] Create the smallest standalone candidate-layer exporter.
- [x] Reuse existing QA Buddy finding output.
- [x] Preserve candidate OSM objects without QA-specific tags.
- [x] Add focused regression tests.
- [x] Document the Windows/JOSM manual acceptance path.

## Quality gate

- [ ] Run the focused exporter tests.
- [ ] Run the existing repository test suite.
- [x] Inspect the implementation for unrelated changes and speculative abstractions.
- [x] Confirm existing JOSM validation and task attribution behavior remains available.
- [x] Keep BetterWorkspace integration optional and dependency-free.
- [ ] Perform Windows/JOSM manual acceptance.
