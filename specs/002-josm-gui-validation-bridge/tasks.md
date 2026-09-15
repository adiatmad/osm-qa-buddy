# Tasks: JOSM GUI Validation Bridge

- [x] Inspect the existing native pipeline, README, GUI-bridge branch, and
  JOSM native exporter format.
- [x] Specify the bridge boundary, compatibility contract, and non-goals.
- [x] Plan the minimal implementation and complete the pre-implementation
  analysis quality gate.
- [x] Reject malformed, foreign, and incomplete TestErrors without silent loss.
- [x] Deduplicate exact repeated TestErrors while retaining all primitives.
- [x] Add parser regressions for severity, empty output, duplicate errors, and
  invalid input.
- [x] Add finalization regression coverage for an XML file already in the
  destination directory.
- [x] Run the repository's syntax and CI test commands.
- [x] Perform an Anti-Slop/diff review and record the remaining human JOSM
  acceptance test.

## Review result

The final code change uses only the Python standard library, preserves the
existing aggregation/reporting path, and adds no integration, service, rule,
or ranking abstraction. The remaining acceptance work is a real JOSM GUI
export on Windows; automated coverage cannot establish that environment's
native exporter behavior.

