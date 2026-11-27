# Tasks: Reliable Osmium Tool Discovery

## 1. Specification and baseline
- [x] Record the duplicated-discovery failure mode and acceptance criteria.
- [x] Inspect all supported launchers, setup, pipeline call sites, and current CI.

## 2. Shared discovery
- [x] Add the shared resolver with explicit override, PATH, active prefix, configured Conda roots, and common installation roots.
- [x] Verify candidates by executing --version and report missing versus unusable binaries.
- [x] Add focused regression tests for discovery precedence and failure cases.

## 3. Integrate all entry points
- [x] Replace GUI hardcoded discovery with the shared resolver.
- [x] Replace batch launcher duplicate discovery with the shared resolver.
- [x] Make native setup use the same verified resolver.
- [x] Make every orchestrator Osmium subprocess use the resolved absolute path.

## 4. Documentation and CI
- [x] Document Osmium Tool versus pyosmium and the OSMIUM_EXE override.
- [x] Add resolver tests and syntax checks to CI.
- [x] Inspect the final diff and all Osmium call sites.
- [x] Run focused and repository-native tests where execution is available.

## 5. Acceptance
- [ ] Verify Windows VBS launch with Osmium installed only in an inactive Conda environment.
- [ ] Verify batch launcher and native setup discover the same executable.

## Definition of done

All entry points share one bounded, tested resolver; all pipeline calls use the verified executable; missing and broken installations produce actionable diagnostics; no machine-level configuration is silently changed; and CI protects the behavior.
