# Specification: One-click Windows Runtime Bootstrap

## Goal

A Windows user with JOSM already installed can double-click `Launch_OSM_QA_Buddy.vbs` from an extracted repository ZIP on a fresh machine and reach a ready OSM QA Buddy GUI without manually installing Python, Java, Osmium Tool, or Conda.

## Problem

The previous VBS launcher only searched PATH for `pythonw.exe` and failed when Python was absent. Even when Python existed, the GUI could open without Shapely or Osmium Tool. The GUI bridge already uses the user's installed JOSM through Windows file association; bundling another JOSM and Java runtime is unnecessary. That is not a complete first-run experience.

## Requirements

### R1 — One-click bootstrap

The VBS launcher must invoke a visible PowerShell bootstrap script. It must not require Python to exist before setup begins.

### R2 — Private, reproducible runtime

Install Miniforge per-user and create a repository-local Conda environment under `.qabot-runtime\` containing Python 3.12 with Tkinter, Shapely 2.1.2, and Osmium Tool CLI. Do not register Python globally, modify user/machine PATH, or require administrator privileges.

### R3 — Verify installers and dependencies

Obtain the official Miniforge Windows x86-64 release asset and verify its GitHub-provided SHA-256 digest before execution. Verify Python/Tkinter/Shapely imports and `osmium.exe --version` before launching the GUI. Fail closed with a visible actionable error.

### R4 — Prepare JOSM for the GUI workflow

Download the repository-pinned JOSM JAR through the existing checksum-verifying setup code. The GUI must launch that JOSM JAR directly; it must not depend on a separately installed JOSM or Windows file association. The GUI bootstrap must not download the legacy Jython component that is not needed for the GUI bridge.

### R5 — Repair and reuse

Subsequent VBS launches must reuse a healthy runtime. If the environment is incomplete or a required command fails verification, use Conda to repair the existing environment before opening the GUI.

### R6 — Keep machine state untouched

All runtime files live under the checkout's ignored `.qabot-runtime\` directory. No global Python/Java install, global/user PATH mutation, registry registration, or admin elevation.

### R7 — Failure behavior

Show setup output in a visible PowerShell window. Do not launch a partially configured GUI. Keep the failure window open long enough for the user to read the error.

## Acceptance Criteria

- A clean Windows machine with PowerShell and internet access but without Python, Java, Osmium Tool, or Conda, but with JOSM installed and `.osm` files associated with it, can launch the VBS and reach the GUI.
- The runtime contains Python 3.12 with Tkinter, Shapely 2.1.2, and a working `osmium.exe`; it does not install Java.
- The GUI opens prepared samples using the user's installed JOSM through the Windows `.osm` file association; no JOSM or Java download occurs.
- A second launch reuses the environment and does not reinstall healthy packages.
- Removing a required package causes a repair before the GUI opens.
- Failed downloads, checksum mismatch, failed package installation, or failed dependency probes prevent GUI launch and show a useful error.
- The bootstrap does not modify global/user PATH or register Python.
- CI parses the PowerShell bootstrap and continues to run Python regression tests.
- Existing QA pipeline behavior and human review in JOSM remain unchanged.

## Non-Goals

- Installing Git or downloading the repository itself.
- Installing global software or changing Windows associations.
- Automatically running validation or making QA decisions on behalf of the human reviewer.
- Bundling large third-party binaries in Git.
