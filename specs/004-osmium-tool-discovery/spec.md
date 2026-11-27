# Specification: Reliable Osmium Tool Discovery

## Goal

Make every supported Windows QA Buddy entry point find and verify the same Osmium Tool executable without depending on the launching shell's Conda activation state or a hardcoded environment name.

## Problem

Osmium discovery is duplicated and inconsistent across the GUI, batch launcher, native setup, and pipeline. The GUI searches PATH, CONDA_PREFIX, and two hardcoded environment paths; the batch launcher has a separate copy; setup and the native orchestrator only use PATH. Launching the VBS from Explorer does not activate a Conda environment, so an installed Osmium executable can be reported as missing.

The Python package named osmium (pyosmium) is not the Osmium Tool command-line executable.

## Requirements

### R1 — One discovery implementation

All GUI, batch, setup, and native pipeline paths must use one shared resolver. Remove duplicated hardcoded environment checks.

### R2 — Supported discovery locations

Resolve Osmium Tool in this order:
1. Explicit OSMIUM_EXE override.
2. Executable available on PATH.
3. Active CONDA_PREFIX and current Python environment.
4. Conda environment directories from CONDA_ENVS_PATH and the per-user Conda environments registry.
5. Common per-user Miniforge, Mambaforge, Miniconda, and Anaconda installation roots.

An explicit override is authoritative: if it is set but invalid, report the problem rather than silently selecting another binary.

### R3 — Verify the executable

A candidate is valid only when it is a file and osmium.exe --version exits successfully with version output. Distinguish missing executables from found-but-unusable executables and provide actionable diagnostics.

### R4 — Use the resolved executable consistently

Pass the resolved absolute executable path to every Osmium subprocess call. Ensure the executable directory is available on PATH for Windows DLL resolution and child processes where the GUI/batch launcher starts the pipeline.

### R5 — No implicit machine mutation

Do not download or install Osmium automatically and do not edit system PATH. Support a documented user-level OSMIUM_EXE override for nonstandard installations.

### R6 — Regression coverage

Test PATH discovery, active Conda discovery, Conda environment-root discovery, explicit override behavior, missing executable, and broken version probe. Run the tests in CI.

## Acceptance Criteria

- Launching QA Buddy without an activated Conda shell can discover Osmium in a supported Conda/Miniforge environment.
- GUI, batch, setup, and orchestrator all call the shared resolver.
- Pipeline subprocesses use the verified absolute executable, not a bare osmium command.
- A missing executable and a broken executable produce different actionable errors.
- A configured invalid OSMIUM_EXE fails closed.
- CI runs focused Osmium resolver tests.
- Existing JOSM validation behavior and human-review workflow remain unchanged.

## Non-Goals

- Installing or updating Osmium automatically.
- Bundling Osmium binaries or DLLs into the repository.
- Changing Osmium extraction semantics or JOSM validation behavior.
- Modifying global or user PATH automatically.
