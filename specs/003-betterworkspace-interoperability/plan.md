# Plan: BetterWorkspace Review Interoperability

## Phase 1 — Evidence and boundary confirmation

1. Keep the current BetterWorkspace evidence recorded in the specification.
2. Contact the BetterWorkspace maintainer through an available public project channel.
3. Ask only for the smallest supported input boundary for externally generated review candidates.
4. Record the maintainer's answer and any version/platform constraints.

## Phase 2 — Contract definition

1. Define only the fields required by the confirmed boundary.
2. Separate required fields from optional metadata.
3. Define provenance and failure behavior.
4. Explicitly document that candidates are review aids, not authoritative errors.

## Phase 3 — Implementation planning

1. Identify the smallest QA Buddy component that can produce the contract.
2. Reuse existing finding/task attribution data where possible.
3. Add focused tests for serialization/normalization and provenance.
4. Avoid new runtime dependencies unless the confirmed boundary requires one.
5. Define a Windows/JOSM manual acceptance path.

## Phase 4 — Convergence

1. Compare implementation against the accepted specification and tasks.
2. Run focused tests and the existing repository test suite.
3. Perform the manual JOSM acceptance step when applicable.
4. Review the diff for speculative abstractions, duplicated logic, unrelated cleanup, and hidden coupling.
