# Specification: JOSM GUI Validation Bridge

## Goal

Let a user run JOSM's normal GUI Validator on the existing Osmium-clipped
dataset, then turn JOSM's native Validation errors XML into QA Buddy's existing
task-level outputs. JOSM remains the validation engine.

## Requirements

1. `prepare` must reuse the existing task-grid clipping path and expose a
   JOSM-openable `sample.osm`.
2. `finalize` must accept only JOSM Validation errors XML and preserve each
   exported TestError's severity, location, and affected primitives in
   `qa_errors.geojson`.
3. A valid empty JOSM export must produce empty, usable downstream outputs.
4. Missing, malformed, or incomplete XML must fail clearly; findings must not
   be silently discarded or fabricated.
5. Exact repeated XML errors must produce one normalized finding. The
   compatibility `object_id` remains the first affected primitive, while
   `object_ids` retains every affected primitive.
6. Existing task attribution, report, map, and headless validation behavior
   must remain unchanged.
7. Finalization must safely handle an export already named
   `validation_errors.xml` in its destination directory and must retain run
   metadata created by `prepare`.

## Non-goals

- Calling JOSM, Remote Control, browser/UI automation, a JOSM plugin, or a
  second validator/rule set.
- Reinterpreting validator findings or changing task attribution/ranking.
- New runtime dependencies or unrelated refactoring.

## Acceptance boundary

Automated tests can establish code correctness. A native Windows/JOSM run with
a real Validator export remains necessary before the bridge is
production-validated.

