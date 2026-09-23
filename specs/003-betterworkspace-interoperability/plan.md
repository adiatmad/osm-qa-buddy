# Plan: BetterWorkspace Review Interoperability

## Phase 1 — Boundary confirmation

1. Confirm the agreed OSM-layer handoff with the BetterWorkspace maintainer.
2. Preserve the boundary as a plain JOSM-compatible OSM layer rather than a BetterWorkspace API dependency.
3. Keep QA metadata outside the OSM objects in a provenance manifest.

## Phase 2 — Contract definition

1. Define candidate semantics as review aids.
2. Export ways and their referenced nodes only for the first milestone.
3. Keep finding/task metadata in a versioned sidecar manifest.
4. Treat task IDs as optional because not every finding has a recoverable task association.
5. Omit review-priority automation from the handoff.

## Phase 3 — Implementation

1. Add a small standalone exporter that reads existing QA findings and the prepared OSM dataset.
2. Copy candidate ways and referenced nodes without changing their tags.
3. Generate the sidecar manifest with finding provenance and task IDs where available.
4. Add focused regression tests.
5. Document the Windows/JOSM/BetterWorkspace manual path.

## Phase 4 — Convergence

1. Compare the implementation against spec.md and tasks.md.
2. Run the focused exporter tests and the existing repository test suite.
3. Inspect the complete diff for speculative abstractions, duplicated logic, unrelated cleanup, and hidden BetterWorkspace coupling.
4. Perform the Windows/JOSM manual acceptance step when the local toolchain is available.
5. Keep human review and merge authority with the repository owner.

## Known limitation

The GitHub integration cannot perform the Windows/JOSM desktop acceptance step. That remains a local/manual verification item.
