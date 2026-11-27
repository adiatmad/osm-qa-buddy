"""Resolve and verify the Osmium Tool executable for every QA Buddy entry point."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


class OsmiumToolError(RuntimeError):
    """Raised when an Osmium Tool executable cannot be found or run."""


def _as_executable(value: str | Path) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    if path.is_dir():
        path = path / "osmium.exe"
    return path


def _candidate_paths():
    """Yield likely Windows Osmium Tool locations in deterministic precedence."""
    active_prefixes: list[Path] = []
    for value in (os.environ.get("CONDA_PREFIX"), sys.prefix):
        if value:
            active_prefixes.append(Path(value))

    env_roots: list[Path] = []
    for value in os.environ.get("CONDA_ENVS_PATH", "").split(os.pathsep):
        if value.strip():
            env_roots.append(Path(os.path.expandvars(value.strip())).expanduser())

    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    registry = home / ".conda" / "environments.txt"
    if registry.is_file():
        try:
            active_prefixes.extend(
                Path(line.strip())
                for line in registry.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except OSError:
            pass
    env_roots.append(home / ".conda" / "envs")

    local_app_data = os.environ.get("LOCALAPPDATA")
    install_roots = [home / name for name in ("miniforge3", "mambaforge", "miniconda3", "anaconda3")]
    if local_app_data:
        programs = Path(local_app_data) / "Programs"
        install_roots.extend(
            programs / name
            for name in ("Miniforge3", "Mambaforge", "Miniconda3", "Anaconda3")
        )

    for root in install_roots:
        active_prefixes.append(root)
        env_roots.append(root / "envs")

    seen: set[str] = set()
    for prefix in active_prefixes:
        key = os.path.normcase(os.path.abspath(prefix))
        if key not in seen:
            seen.add(key)
            yield prefix / "Library" / "bin" / "osmium.exe"

    for env_root in env_roots:
        # CONDA_ENVS_PATH may name either an environment prefix or an envs directory.
        key = os.path.normcase(os.path.abspath(env_root))
        if key not in seen:
            seen.add(key)
            yield env_root / "Library" / "bin" / "osmium.exe"
        if env_root.is_dir():
            try:
                prefixes = sorted(env_root.iterdir(), key=lambda item: item.name.casefold())
            except OSError:
                continue
            for prefix in prefixes:
                if prefix.is_dir():
                    key = os.path.normcase(os.path.abspath(prefix))
                    if key not in seen:
                        seen.add(key)
                        yield prefix / "Library" / "bin" / "osmium.exe"


def _verify_executable(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "file does not exist"
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return False, output or f"process exited with code {result.returncode}"
    if not output:
        return False, "the --version command returned no version information"
    return True, output.splitlines()[0]


def resolve_osmium() -> str:
    """Return a verified absolute path to osmium.exe or raise a useful error.

    OSMIUM_EXE is an explicit override. If it is set but invalid, fail closed
    instead of silently choosing a different installation.
    """
    override = os.environ.get("OSMIUM_EXE", "").strip()
    if override:
        path = _as_executable(override)
        ok, detail = _verify_executable(path)
        if ok:
            return str(path.resolve())
        raise OsmiumToolError(
            f"OSMIUM_EXE points to an unusable Osmium Tool executable: {path} ({detail}). "
            "Correct OSMIUM_EXE or remove it to use automatic discovery."
        )

    candidates: list[Path] = []
    on_path = shutil.which("osmium")
    if on_path:
        candidates.append(Path(on_path))
    candidates.extend(_candidate_paths())

    seen: set[str] = set()
    failures: list[str] = []
    for candidate in candidates:
        key = os.path.normcase(os.path.abspath(candidate))
        if key in seen:
            continue
        seen.add(key)
        if not candidate.is_file():
            continue
        ok, detail = _verify_executable(candidate)
        if ok:
            return str(candidate.resolve())
        failures.append(f"{candidate}: {detail}")

    if failures:
        details = "; ".join(failures[:3])
        raise OsmiumToolError(
            "Osmium Tool was found but could not be executed. "
            f"Checked: {details}. Restore the complete Osmium distribution (including its DLLs), "
            "or set OSMIUM_EXE to a working osmium.exe."
        )
    raise OsmiumToolError(
        "Osmium Tool (osmium.exe) was not found. Install the osmium-tool package in a Conda "
        "environment, add its Library\\bin directory to PATH, or set OSMIUM_EXE to the full "
        "path of osmium.exe. The Python package named 'osmium' is not a replacement."
    )


def main() -> int:
    if sys.argv[1:] != ["--print-path"]:
        print("Usage: python osmium_tool.py --print-path", file=sys.stderr)
        return 2
    try:
        print(resolve_osmium())
    except OsmiumToolError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
