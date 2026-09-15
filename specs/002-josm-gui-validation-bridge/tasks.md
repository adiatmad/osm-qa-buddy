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
- [x] Perform an Anti-Slop/diff review.
- [x] Perform the real Windows/JOSM acceptance test with a native Validation
  errors XML export.
- [x] Record the field-validation evidence and update user-facing workflow
  documentation.

## Review result

The final code change uses only the Python standard library, preserves the
existing aggregation/reporting path, and adds no integration, service, rule,
or ranking abstraction. The real Windows/JOSM acceptance run completed
successfully on 2026-09-15 with 17,202 raw findings, 15,768 task-associated
findings, 1,435 unassigned findings, and 1 BADIMAGERY task.

The unassigned findings are preserved rather than forcibly attributed. This is
an attribution result to investigate from geometry/task boundaries when needed,
not a reason to change the bridge contract without evidence.

## Convergence status

**PASS for the implemented GUI bridge workflow.** Automated and native
acceptance evidence now cover the intended bridge boundary. The acceptance is
not a universal guarantee across arbitrary JOSM versions, validator
configurations, datasets, or task-grid geometries.
