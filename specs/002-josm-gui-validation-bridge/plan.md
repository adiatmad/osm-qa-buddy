# Plan: JOSM GUI Validation Bridge

1. Reuse `clip_pbf_with_osmium` in a thin prepare command; store metadata that
   identifies the interactive JOSM workflow.
2. Parse the native `ValidatorErrorWriter` shape with the standard library and
   translate it to the established point GeoJSON contract.
3. Fail closed for non-JOSM, malformed, or incomplete TestErrors so findings
   cannot disappear silently. Deduplicate only exact normalized errors.
4. Reuse `aggregate_errors_to_tasks` and `generate_report`; do not add a
   bridge-specific ranking or output format.
5. Add parser and finalization regressions, then run syntax and all existing
   CI test commands.

## Analysis quality gate

The JOSM `ValidatorErrorWriter` source was checked before implementation. It
writes an `analysers` root with `generator='JOSM'`, analyser-local severity
classes, a location, serialized OSM primitives, and text for each TestError.
The initial bridge audit found silent skips for malformed/incomplete errors and
no exact-error de-duplication. The implementation is limited to correcting
those gaps and testing the existing destination-copy guard.

