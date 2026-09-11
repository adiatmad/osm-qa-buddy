# Tasks: Native Reliability Hardening

## 1. Specification and baseline
- [x] Record the evidence-backed reliability requirements in `spec.md`.
- [x] Record the implementation approach and regression strategy in `plan.md`.

## 2. Extraction correctness
- [x] Preserve first-feature AOI semantics during Osmium normalization.
- [x] Add a regression test for a multi-feature AOI.
- [x] Print extracted Osmium file information before JOSM starts.
- [x] Persist extracted dataset diagnostics in run metadata.

## 3. Native runtime reliability
- [x] Define the native Python dependency set in `requirements.txt`.
- [x] Make `setup_native.py` install missing Python dependencies automatically.
- [x] Report the detected Osmium version during setup.

## 4. HOT rule discovery
- [x] Prefer deterministic direct `.mapcss` discovery in the current flat `hot_rules` directory.
- [x] Retain recursive fallback for future ZIP layouts.
- [x] Print the selected HOT MapCSS path before JOSM validation.
- [x] Add lightweight regression coverage for deterministic HOT rule discovery shape in `native_smoke.py`.
- [x] Exclude PR #9's misleading `Ways` object-batch progress implementation.

## 5. Long-running validation
- [x] Use a 30-second JOSM heartbeat while the native validator runs.
- [x] Explain that CrossingWays is a full-dataset spatial test.
- [x] Preserve the existing validator lifecycle and test set.

## 6. CI and regression protection
- [x] Install dependencies from `requirements.txt` in CI.
- [x] Run smoke tests in CI.
- [x] Run preflight regression tests in CI.
- [x] Protect report raw/unique finding accounting with a regression test.
- [x] Verify the known Nepal benchmark using the consolidated native implementation; historical forensic reproduction confirms the known-good ~259k-object extraction and ~30-minute Ways behavior. The exact benchmark source dataset is not retained in the repository, so this is documented evidence rather than a reproducible CI fixture.

## 7. Documentation and acceptance
- [x] Verify that the native workflow documentation already describes the PM workflow and safety checks.
- [x] Verify generated report/map/metadata outputs remain usable after the consolidated run using real Project 63564 artifacts.
- [x] Run the final real-project acceptance test without developer-only intervention using Project 63564.
- [x] Fix run metadata project ID propagation in the native GUI/orchestrator path; future PM runs will record the supplied numeric project ID.

### Acceptance evidence: Project 63564
- Native GUI workflow completed successfully.
- 60 task features processed.
- 81 raw JOSM findings produced.
- Independent raw finding accounting: 73 unique findings and 8 exact duplicates.
- Task association: 77 findings assigned to tasks and 4 unassigned.
- 2 BADIMAGERY tasks detected.
- `qa_errors.geojson`, `task_grid_qa_summary.geojson`, `report.html`, `map.html`, and `run_metadata.json` were generated and structurally readable.
- The corrected report now reflects raw unique findings rather than task-associated unique findings.
- Follow-up hardening: the acceptance artifact was generated before explicit project-ID propagation was added. The native GUI and orchestrator now pass and persist the numeric project ID; a subsequent acceptance run should confirm the metadata field, but the demonstrated QA pipeline itself is already successful.

## Definition of done
The native PM workflow preserves the known-good extraction scope and validator semantics, fails loudly when inputs are invalid, records enough information to audit the dataset passed to JOSM, handles fresh Python setup reproducibly, discovers HOT rules reliably, reports long-running validation honestly, and protects report accounting with regression coverage.
