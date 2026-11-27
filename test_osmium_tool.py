import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import osmium_tool
from osmium_tool import OsmiumToolError, resolve_osmium


class OsmiumDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def _executable(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test executable", encoding="utf-8")
        return path

    @staticmethod
    def _success(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="osmium version 1.16.0", stderr="")

    def test_prefers_and_verifies_path_executable(self):
        executable = self._executable(self.root / "bin" / "osmium.exe")
        with patch.dict(os.environ, {}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=str(executable)
        ), patch.object(osmium_tool.subprocess, "run", side_effect=self._success):
            self.assertEqual(resolve_osmium(), str(executable.resolve()))

    def test_discovers_active_conda_environment_without_path(self):
        executable = self._executable(self.root / "env" / "Library" / "bin" / "osmium.exe")
        with patch.dict(os.environ, {"CONDA_PREFIX": str(self.root / "env")}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ), patch.object(osmium_tool.subprocess, "run", side_effect=self._success):
            self.assertEqual(resolve_osmium(), str(executable.resolve()))

    def test_discovers_environment_under_conda_envs_path(self):
        envs_dir = self.root / "conda-envs"
        executable = self._executable(envs_dir / "mapping" / "Library" / "bin" / "osmium.exe")
        with patch.dict(os.environ, {"CONDA_ENVS_PATH": str(envs_dir)}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ), patch.object(osmium_tool.subprocess, "run", side_effect=self._success):
            self.assertEqual(resolve_osmium(), str(executable.resolve()))

    def test_discovers_miniforge_environment_without_conda_activation(self):
        executable = self._executable(
            self.root / "miniforge3" / "envs" / "mapping" / "Library" / "bin" / "osmium.exe"
        )
        with patch.dict(os.environ, {"USERPROFILE": str(self.root)}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ), patch.object(osmium_tool.subprocess, "run", side_effect=self._success):
            self.assertEqual(resolve_osmium(), str(executable.resolve()))

    def test_discovers_conda_environment_from_user_registry(self):
        executable = self._executable(
            self.root / "custom-conda" / "envs" / "mapping" / "Library" / "bin" / "osmium.exe"
        )
        registry = self.root / ".conda" / "environments.txt"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(str(executable.parents[2]), encoding="utf-8")
        with patch.dict(os.environ, {"USERPROFILE": str(self.root)}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ), patch.object(osmium_tool.subprocess, "run", side_effect=self._success):
            self.assertEqual(resolve_osmium(), str(executable.resolve()))

    def test_explicit_override_is_authoritative_and_must_work(self):
        executable = self._executable(self.root / "broken" / "osmium.exe")
        failed = subprocess.CompletedProcess([str(executable), "--version"], 1, stdout="", stderr="missing DLL")
        with patch.dict(os.environ, {"OSMIUM_EXE": str(executable)}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ), patch.object(osmium_tool.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(OsmiumToolError, "missing DLL"):
                resolve_osmium()

    def test_reports_missing_cli_not_python_package(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            osmium_tool.shutil, "which", return_value=None
        ):
            with self.assertRaisesRegex(OsmiumToolError, "Python package named 'osmium'"):
                resolve_osmium()

    def test_rejects_empty_version_probe(self):
        executable = self._executable(self.root / "osmium.exe")
        result = subprocess.CompletedProcess([str(executable), "--version"], 0, stdout="", stderr="")
        with patch.dict(os.environ, {"OSMIUM_EXE": str(executable)}, clear=True), patch.object(
            osmium_tool.subprocess, "run", return_value=result
        ):
            with self.assertRaisesRegex(OsmiumToolError, "no version information"):
                resolve_osmium()


if __name__ == "__main__":
    unittest.main()
