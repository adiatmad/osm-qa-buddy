# Specification: BetterWorkspace Review Interoperability

## Goal

Provide the smallest practical interoperability path between OSM QA Buddy and the BetterWorkspace JOSM plugin without coupling QA Buddy to BetterWorkspace's private implementation.

QA Buddy remains the QA analysis/orchestration layer. JOSM remains the validation engine. BetterWorkspace remains an optional JOSM-side review/navigation layer. A human mapper remains the final decision-maker.

## Confirmed boundary

The first milestone uses a plain OSM XML review-candidate layer as the handoff boundary:

1. QA Buddy exports candidate **ways** from an existing JOSM dataset into a separate OSM layer.
2. The candidate layer contains the original OSM way and its referenced nodes, without QA Buddy tags or other edits to the objects.
3. A sidecar JSON manifest carries QA provenance, finding details, and optional HOT Tasking Manager task IDs.
4. The candidate layer is opened in JOSM.
5. BetterWorkspace's existing multi-validation workflow can operate on the candidate Way layer and hand the ways to the JOSM Todo workflow.
6. Human review in JOSM remains authoritative.

This boundary does not require QA Buddy to call BetterWorkspace, Todo plugin internals, reflection targets, or private APIs.

## Requirements

### R1 — Review-candidate semantics

The exported OSM layer represents **review candidates**, not authoritative mapping errors or decisions.

Each manifest candidate preserves, where available:

- OSM primitive identifier;
- finding source/type;
- HOT Tasking Manager task identifier;
- finding location;
- human-readable reason;
- provenance linking the candidate to the QA Buddy finding;
- severity as source metadata, not as an automatic review decision.

### R2 — Way-first interoperability

The first milestone exports only OSM ways because BetterWorkspace's existing multi-validation workflow operates on JOSM Way primitives.

Node-only and relation-only findings remain in the normal QA Buddy outputs and are not silently discarded from QA Buddy itself.

### R3 — No private-plugin coupling

QA Buddy must not depend on BetterWorkspace private classes, fields, methods, reflection targets, package internals, or Todo plugin internals.

### R4 — Unmodified OSM candidates

The exported OSM objects must be copied from the source dataset without injecting QA Buddy tags or changing mapping content. QA metadata belongs in the sidecar manifest.

### R5 — Preserve existing QA Buddy behavior

The existing JOSM GUI Validation Bridge, task attribution, reports, maps, and headless validation behavior remain unchanged.

### R6 — Human review remains authoritative

The interoperability path supports navigation and review. It must not automatically resolve, suppress, modify, or upload OSM data.

### R7 — Reproducible provenance

The sidecar manifest must identify the source findings and candidate OSM objects and retain enough finding information for a reviewer to understand why each object was surfaced.

### R8 — Minimal dependency footprint

The export path uses the repository's existing Python runtime and Shapely dependency. No BetterWorkspace runtime dependency or hosted service is introduced.

## Non-Goals

- Forking BetterWorkspace.
- Copying GPL-licensed BetterWorkspace implementation into QA Buddy.
- Reimplementing BetterWorkspace's Todo bridge.
- Replacing JOSM validation.
- Building a new JOSM workspace/plugin inside QA Buddy.
- Adding AI-based QA decisions or opaque scoring.
- Replacing existing QA Buddy output formats.
- Supporting every JOSM/Todo/BetterWorkspace version in the first milestone.
- Exporting node-only or relation-only candidates into the BetterWorkspace layer in the first milestone.

## Acceptance Criteria

1. QA Buddy can export a plain OSM candidate layer containing only candidate ways and their referenced nodes.
2. Candidate OSM objects are copied without QA-specific tags or mapping changes.
3. A sidecar manifest records candidate object IDs, finding details, provenance, and task IDs when recoverable.
4. The export does not import or depend on BetterWorkspace/Todo private implementation details.
5. Existing QA Buddy findings and task attribution outputs remain available unchanged.
6. Focused regression tests cover candidate extraction, referenced-node retention, and task attribution.
7. A Windows/JOSM manual path is documented.
8. Human review remains required.

## Manual acceptance path

On Windows:

1. Run the normal GUI validation workflow through finalization.
2. Export the BetterWorkspace candidate layer from qa_errors.geojson and the prepared sample.osm.
3. Open the candidate OSM file as a separate layer in JOSM.
4. Use BetterWorkspace's existing multi-validation preparation workflow on the candidate layer.
5. Confirm the candidate ways appear in the JOSM Todo workflow.
6. Review the candidates manually; do not treat the manifest or candidate list as an automatic mapping decision.

## Implementation notes

The first implementation lives in betterworkspace_export.py and is intentionally a standalone producer. It can be used from the command line without requiring BetterWorkspace to be installed.

The sidecar manifest is versioned as:

osm-qa-buddy/betterworkspace-review-candidates/v1

The export fails rather than producing a misleading empty handoff when candidate ways cannot be found in the source OSM dataset.

AI-assisted implementation; human maintainer review and merge authority remain required.
