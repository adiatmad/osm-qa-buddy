# Plan: Reliable Osmium Tool Discovery

## Technical approach

1. Add osmium_tool.py as the sole resolver and verification boundary.
2. Keep discovery deterministic and bounded: inspect PATH, active prefixes, CONDA_ENVS_PATH, the per-user .conda/environments.txt registry, and known per-user Conda installation roots; do not recursively scan the entire disk.
3. Treat OSMIUM_EXE as an explicit override and verify every candidate by executing --version.
4. Update the GUI, batch launcher, setup script, and orchestrator to consume the resolver. Pass the absolute executable path to pipeline subprocesses and prepend its directory to the child PATH where the launcher owns the environment.
5. Document Conda discovery and the override without adding automatic downloads, installers, or PATH mutation.
6. Add standard-library unit tests and a CI step for discovery, precedence, and failure cases.

## Validation strategy

- Run python -m unittest test_osmium_tool.py.
- Run the repository CI test commands and Python syntax checks.
- Inspect all Osmium subprocess call sites to confirm none invoke a bare osmium command.
- On Windows, manually launch the VBS from Explorer with Osmium installed only in an inactive Conda environment; confirm the GUI reports the resolved executable and completes preflight.
- Confirm the batch launcher and native setup resolve the same executable.
- Windows Explorer/Conda integration is a manual acceptance item; Linux CI only verifies the resolver logic using mocked executable probes.

## Risks and mitigations

- Stale explicit override: fail closed and explain how to correct or remove it.
- Broken/incomplete Osmium distribution: execute --version before declaring it ready and report DLL/startup errors.
- Slow or unbounded search: search only known roots and one level of Conda environments.
- Different environments across launchers: pass the verified absolute path through OSMIUM_EXE and subprocess arguments.
