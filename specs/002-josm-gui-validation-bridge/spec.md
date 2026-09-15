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

Automated tests establish parser and pipeline behavior. The production acceptance boundary also requires a real native Windows/JOSM run because automated tests cannot establish the behavior of the installed JOSM GUI exporter.

## Acceptance evidence

A real Windows acceptance run was completed on 2026-09-15 using JOSM 19613 and the Nepal test dataset. The workflow successfully:

1. prepared an Osmium-clipped `sample.osm`;
2. opened that dataset in normal JOSM;
3. ran the normal JOSM Validator;
4. exported the native Validation errors XML;
5. finalized that XML through QA Buddy; and
6. produced the established downstream GeoJSON, HTML report, and map outputs.

Observed result:

- 17,202 raw JOSM findings parsed;
- 15,768 findings associated with Task Grid polygons;
- 1,435 findings remained unassigned;
- 1 BADIMAGERY task was detected.

The unassigned findings are preserved rather than forcibly attributed to tasks. Their presence is not by itself evidence of a parser or attribution failure and should be investigated from the underlying geometry/task boundaries when needed.

The acceptance run establishes the GUI bridge as **field-validated for this workflow**, while not claiming universal correctness for every JOSM version, dataset, validator configuration, or task-grid geometry.
