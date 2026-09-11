# Plan: Native Reliability Hardening

## Technical approach

1. Keep the current native Windows pipeline as the baseline: Python GUI/orchestrator → native Osmium extraction → JOSM 19613 + Jython 2.7.3 → report/map outputs.
2. Make AOI normalization preserve Osmium's actual first-feature behavior. Preflight may inspect the full task grid, but extraction must not silently union AOI features.
3. Persist extraction diagnostics after Osmium completes so the dataset entering JOSM is observable and auditable.
4. Make setup self-contained for the native Python dependency set through `requirements.txt` and `setup_native.py`.
5. Make HOT TM MapCSS discovery deterministic for the current flat ZIP layout, with recursive fallback for future ZIP layouts.
6. Keep long-running validator reporting honest: emit a heartbeat while JOSM runs, but do not fabricate incremental completion for CrossingWays.
7. Preserve the existing validator list and JOSM lifecycle. Do not partition data or alter CrossingWays behavior.

## Validation strategy

- Unit regression: multi-feature AOI normalization must retain only the first feature and its properties.
- CI regression: install `requirements.txt`, run smoke tests, preflight tests, and native workflow checks.
- Large regression: rerun the known Nepal dataset and verify extraction remains approximately 259k objects and the Ways validator remains in the known ~30-minute range.
- Operational acceptance: run the native PM workflow on real HOT TM inputs and confirm outputs, metadata, task association, and failure messages remain usable.

## Risks and mitigations

- **AOI semantics drift:** keep a dedicated first-feature regression test and extraction diagnostics.
- **HOT ZIP layout changes:** direct listing is preferred for current behavior; recursive fallback remains available.
- **Long validator appears frozen:** 30-second heartbeat explains that CrossingWays is a full-dataset operation.
- **Fresh-machine dependency failure:** setup installs from the pinned repository dependency file before native execution.
- **False performance optimization:** explicitly avoid PR #9's object-batch progress because the expensive CrossingWays work occurs after object visitation.

## Out of scope

AI scoring, automatic Geofabrik download/source selection, CrossingWays rewrites, dataset partitioning, and Docker removal remain outside this pass.
