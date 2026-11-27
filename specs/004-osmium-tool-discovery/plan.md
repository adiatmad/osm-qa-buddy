# Plan: One-click Windows Runtime Bootstrap

## Technical approach

1. Replace the Python-dependent VBS launcher with a visible PowerShell bootstrap entry point.
2. Download the official Miniforge Windows x86-64 installer from its GitHub release metadata; verify the asset's SHA-256 digest before running the silent per-user installer.
3. Install a private Conda environment in `.qabot-runtime\env` with Python 3.12, pinned Shapely 2.1.2, and `osmium-tool` from conda-forge.
4. Verify the Python/Tkinter/Shapely imports and `osmium.exe --version` before proceeding. Reuse a healthy environment and repair an unhealthy one.
5. Do not run the JOSM/Jython headless setup for the GUI bridge; the user already has JOSM installed.
6. Launch the GUI with the private environment's `pythonw.exe` and inherited environment. Pass `OSMIUM_EXE` and the runtime PATH into child processes.
7. Open sample OSM data through the Windows `.osm` file association so the user's installed JOSM opens it.
8. Ignore the local runtime and update README/spec/CI to match the actual user workflow.

## Validation strategy

- Run Python syntax checks and all repository regression tests.
- Parse `bootstrap.ps1` with the Windows PowerShell parser in CI.
- Inspect the VBS and bootstrap scripts for global PATH/registry mutation and ensure the GUI starts only after all probes pass.
- On Windows, test the actual VBS from an extracted ZIP with no Python/Java/Osmium/Conda installed and JOSM already installed; verify first install, GUI startup, opening the sample via file association, and second-launch reuse.
- Simulate an incomplete environment and verify repair; simulate a failed dependency probe and verify that the GUI is not launched.
- Manual Windows first-run acceptance remains mandatory; Linux CI cannot prove Windows installer behavior.

## Risks and mitigations

- GitHub release API may omit the installer digest: fail closed rather than execute an unverified installer.
- Conda-forge/network access may be blocked: keep the visible diagnostic and allow retry after connectivity is restored.
- Partial installer/runtime state: distinguish a missing environment from an incomplete Miniforge root and provide a safe recovery instruction.
- Windows `.osm` file associations vary by machine: verify the installed JOSM opens the sample during real acceptance.
