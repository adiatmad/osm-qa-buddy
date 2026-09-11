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
- [x] Exclude PR #9's misleading `Ways` object-batch progress implementation.

## 5. Long-running validation
- [x] Use a 30-second JOSM heartbeat while the native validator runs.
- [x] Explain that CrossingWays is a full-dataset spatial test.
- [x] Preserve the existing validator lifecycle and test set.

## 6. CI and regression protection
- [x] Install dependencies from `requirements.txt` in CI.
- [x] Run smoke tests in CI.
- [x] Run preflight regression tests in CI.
- [ ] Add deterministic HOT rule discovery regression coverage where practical.
- [ ] Verify the known Nepal benchmark after the consolidated implementation.

## 7. Documentation and acceptance
- [x] Verify that the native workflow documentation already describes the PM workflow and safety checks.
- [ ] Verify generated report/map/metadata outputs remain usable after the consolidated run.
- [ ] Run the final real-project acceptance test without developer-only intervention.

## Definition of done
The native PM workflow preserves the known-good extraction scope and validator semantics, fails loudly when inputs are invalid, records enough information to audit the dataset passed to JOSM, handles fresh Python setup reproducibly, discovers HOT rules reliably, and reports long-running validation honestly.
