# Specification: BetterWorkspace Review Interoperability

## Goal

Define the smallest practical interoperability boundary between OSM QA Buddy and the BetterWorkspace JOSM plugin without coupling QA Buddy to BetterWorkspace's private implementation.

QA Buddy remains the QA analysis/orchestration layer. JOSM remains the validation engine. BetterWorkspace remains an optional JOSM-side review/navigation layer. A human mapper remains the final decision-maker.

## Evidence

Current repository evidence shows that QA Buddy's JOSM GUI Validation Bridge can preserve affected OSM primitives and task attribution in its existing outputs.

Current BetterWorkspace evidence shows that its multi-validation workflow hands selected JOSM Way primitives to the JOSM Todo plugin. Its current TodoBridge reaches the Todo plugin through reflection and private fields/methods, so those implementation details are not a suitable external contract for QA Buddy.

Therefore, this specification does not assume that QA Buddy can directly write to BetterWorkspace or the Todo plugin.

## Requirements

### R1 — Review-candidate semantics

Any interoperability output must represent **review candidates**, not authoritative mapping errors or decisions.

Each candidate should preserve, where available:

- OSM primitive identifier(s);
- finding source/type;
- HOT Tasking Manager task identifier;
- location sufficient for review;
- human-readable reason;
- provenance linking the candidate to the QA Buddy run/finding;
- optional review-priority metadata only when its semantics are explicitly defined.

### R2 — No private-plugin coupling

QA Buddy must not depend on BetterWorkspace private classes, fields, methods, reflection targets, package internals, or Todo plugin internals.

The interface must remain usable if BetterWorkspace changes its internal implementation while preserving the documented external behavior.

### R3 — No invented transport

Do not commit to GeoJSON, JSON, JOSM selection state, plugin API, clipboard automation, Remote Control, or another transport merely because it is convenient.

The first implementation may begin only after a practical input boundary is confirmed with the BetterWorkspace maintainer or documented by the plugin.

### R4 — Preserve existing QA Buddy behavior

The existing JOSM GUI Validation Bridge, task attribution, reports, maps, and headless validation behavior must remain unchanged unless a later accepted specification explicitly changes them.

### R5 — Human review remains authoritative

Interoperability must support navigation and review. It must not automatically resolve, suppress, rank as truth, modify, or upload OSM data.

### R6 — Minimal dependency footprint

The first implementation must not require a new service, hosted integration, or mandatory BetterWorkspace installation unless a later specification demonstrates that such a dependency is necessary.

### R7 — Reproducible provenance

An exported review candidate must be traceable to the QA Buddy run and source finding so that a reviewer can understand why the object was surfaced.

## Non-Goals

- Forking BetterWorkspace.
- Copying GPL-licensed BetterWorkspace implementation into QA Buddy.
- Reimplementing BetterWorkspace's Todo bridge.
- Replacing JOSM validation.
- Building a new JOSM workspace/plugin inside QA Buddy.
- Adding AI-based QA decisions or opaque scoring.
- Replacing existing QA Buddy output formats without evidence that the change is required.
- Supporting every JOSM/Todo/BetterWorkspace version in the first milestone.

## Acceptance Criteria

The specification is ready for implementation only when all of the following are true:

1. A documented, practical input boundary for review candidates is confirmed.
2. The boundary does not require BetterWorkspace private implementation details.
3. The smallest candidate payload needed for that boundary is documented.
4. A round-trip or end-to-end manual test path is identified on Windows/JOSM.
5. Existing QA Buddy behavior has regression coverage for any changed code.
6. The implementation can remain optional and human-reviewed.

## Open Questions

1. What is the smallest supported mechanism by which BetterWorkspace/JOSM can consume externally produced review candidates?
2. Does the BetterWorkspace maintainer want a stable external contract, or should interoperability target a lower-level JOSM/Todo mechanism?
3. Which candidate fields are actually required for the first review workflow?
4. Is task identity already recoverable from the JOSM data/session, making explicit task IDs unnecessary for the handoff?
5. Should review priority be omitted initially to avoid inventing semantics?

## Decision Gate

**No implementation is authorized by this specification until the input boundary is confirmed.**

If the maintainer confirms a boundary, update this specification and create the corresponding implementation plan/tasks before coding.

AI-assisted specification; human maintainer review and merge authority remain required.
