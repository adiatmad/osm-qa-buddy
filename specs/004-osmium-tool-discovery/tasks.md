# Tasks: One-click Windows Runtime Bootstrap

## 1. Specification and inspection
- [x] Record the desired fresh-machine, one-click acceptance behavior.
- [x] Inspect the VBS, GUI, setup script, runtime dependencies, and existing Osmium resolver.

## 2. Bootstrap implementation
- [x] Add a visible PowerShell first-run bootstrapper.
- [x] Verify the official Miniforge installer SHA-256 before execution.
- [x] Create/repair a private Python 3.12 + Shapely + Osmium Tool + OpenJDK environment.
- [x] Verify each runtime dependency before launching the GUI.
- [x] Prepare the pinned JOSM JAR without downloading unused Jython.
- [x] Launch the GUI with the private runtime and launch JOSM directly from its bundled JAR.
- [x] Keep all runtime state inside the ignored checkout-local directory.

## 3. Documentation and CI
- [x] Make the VBS invoke the bootstrapper rather than searching for system Python.
- [x] Document the first-run and subsequent-launch behavior.
- [ ] Add Windows PowerShell parser validation to CI.
- [ ] Run Python syntax and regression tests against the final commit.

## 4. Acceptance
- [ ] Test first launch from a clean Windows machine without Python, Java, Osmium Tool, Conda, or JOSM.
- [ ] Verify JOSM opens the prepared sample from the GUI.
- [ ] Verify second launch reuses the runtime.
- [ ] Verify a damaged environment is repaired before the GUI opens.

## Definition of done

A clean Windows user can double-click the VBS, wait for setup, and reach a GUI with verified Python, Shapely, Osmium Tool, Java, and bundled JOSM. Automated CI and real Windows first-run acceptance both pass.
