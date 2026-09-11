# Specification: Native Reliability Hardening

## Goal
Make the PM-facing native Windows workflow reliable and auditable for large HOT Tasking Manager projects without changing JOSM validation semantics.

## Problem
The investigation found that the same JOSM/Jython validator can complete a ~259k-object dataset in about 30 minutes, while an accidentally expanded ~578k-object dataset becomes impractically slow. QA Buddy must therefore prevent silent changes to the dataset handed to JOSM and make the extraction scope observable before expensive validation starts.

## Requirements

### R1 — Preserve extraction semantics
The AOI passed to Osmium must preserve the semantics expected by the current workflow. In particular, a multi-feature AOI must not be silently unioned when Osmium's configured GeoJSON behavior consumes the first feature.

### R2 — Preflight before JOSM
Before starting JOSM, the workflow must validate the selected inputs and produce extraction diagnostics sufficient to identify the actual dataset: file path, size, bounding box, and object counts.

### R3 — Reproducible Python runtime
Native setup must ensure required Python runtime dependencies, including Shapely, are available without requiring the PM to discover and install them manually.

### R4 — Honest long-running progress
The GUI/log output must distinguish cheap object collection from the expensive CrossingWays validation phase. A 100% object-collection message must not imply that the validator itself is 100% complete.

### R5 — Preserve validator semantics
Do not remove CrossingWays, partition the dataset, replace JOSM validation, or otherwise change validation semantics as part of this hardening pass.

### R6 — Large-area regression evidence
The known-good Nepal dataset (~259k JOSM objects, ~30-minute Ways validation) is the large-area regression benchmark.

## Success Criteria
- A fresh native setup can prepare the Python runtime without manual Shapely installation.
- A Nepal run using the known AOI produces approximately 259k objects before JOSM starts.
- Extraction diagnostics are persisted for audit/debugging.
- Long CrossingWays execution reports an honest heartbeat rather than misleading percentage completion.
- Existing validator outputs and lifecycle remain unchanged apart from reliability/observability metadata.

## Non-Goals
- Optimizing or rewriting JOSM CrossingWays.
- AI-based QA scoring or prioritization.
- Automatic Geofabrik source selection/download.
- Removing Docker from the repository.
