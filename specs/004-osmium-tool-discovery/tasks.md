# Tasks: One-click Windows Runtime Bootstrap

## 1. Specification and inspection
- [x] Record the desired fresh-machine, one-click acceptance behavior.
- [x] Inspect the VBS, GUI, setup script, runtime dependencies, and existing Osmium resolver.

## 2. Bootstrap implementation
- [x] Add a visible PowerShell first-run bootstrapper.
- [x] Verify the official Miniforge installer SHA-256 before execution.
- [x] Create/repair a private Python 3.12 + Shapely + Osmium Tool environment.
- [x] Verify Python/Tkinter/Shapely and Osmium Tool before launching the GUI.
- [x] Remove JOSM/Java preparation from the GUI bootstrap; use the installed JOSM through the Windows `.osm` association.
- [x] Launch the GUI with the private runtime and open samples through the installed JOSM file association.
- [x] Keep all runtime state inside the ignored checkout-local directory.

## 3. Documentation and CI
- [x] Make the VBS invoke the bootstrapper rather than searching for system Python.
- [x] Document the first-run and subsequent-launch behavior.
- [x] Add Windows PowerShell 5.1 parser validation to CI.
- [ ] Run Python syntax and regression tests against the final commit.

## 4. Acceptance
- [ ] Test first launch from an extracted ZIP on Windows without Python, Java, Osmium Tool, or Conda, with JOSM already installed.
- [ ] Verify Windows opens the prepared sample in the installed JOSM.
- [ ] Verify second launch reuses the runtime.
- [ ] Verify a damaged environment is repaired before the GUI opens.

## Definition of done

A Windows user with JOSM installed can extract the ZIP, double-click the VBS, wait for setup, and reach a GUI with verified private Python, Shapely, and Osmium Tool. Automated CI and real Windows first-run acceptance both pass.
