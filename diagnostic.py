import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
OLD_DIR = REPO_DIR / "Working Code"
CURRENT_WORK_DIR = Path(os.environ.get("QABOT_WORK_DIR", str(REPO_DIR / "work")))
OLD_RUNTIME_DIR = Path(r"C:\JOSM_Headless")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_info(path):
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "size_bytes": stat.st_size,
        "mtime": stat.st_mtime,
        "sha256": sha256(path),
    }


def command_output(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = (result.stdout or result.stderr).strip()
        return {"returncode": result.returncode, "output": output}
    except Exception as exc:
        return {"returncode": None, "output": f"unavailable: {exc}"}


def osmium_fileinfo(path):
    if not path.exists() or shutil.which("osmium") is None:
        return None
    return command_output(["osmium", "fileinfo", "-e", str(path)])


def main():
    print("OSM QA Buddy forensic diagnostic")
    print("================================")
    print(f"Python: {sys.version.replace(chr(10), ' ')}")
    print(f"Platform: {platform.platform()}")
    print(f"Repository: {REPO_DIR}")
    print()

    print("[Toolchain]")
    for label, command in (("Java", ["java", "-version"]), ("Osmium", ["osmium", "--version"])):
        print(f"{label}: {json.dumps(command_output(command), ensure_ascii=False)}")

    print("\n[Source comparison]")
    for name in ("bot.py", "orchestrator.py", "size_rule.mapcss"):
        current = REPO_DIR / name
        old = OLD_DIR / name
        print(f"{name}: current={file_info(current)}")
        print(f"{name}: working_code={file_info(old)}")

    print("\n[Old runtime artifacts]")
    for name in ("sample.osm", "josm-tested.jar", "jython.jar", "qa_errors.geojson", "task_grid_qa_summary.geojson"):
        path = OLD_RUNTIME_DIR / name
        print(f"{path}: {file_info(path)}")
        if name == "sample.osm":
            print(f"{path} fileinfo: {osmium_fileinfo(path)}")

    print("\n[Current runtime artifacts]")
    for name in ("sample.osm", "qa_errors.geojson", "run_metadata.json", "task_grid_qa_summary.geojson"):
        path = CURRENT_WORK_DIR / name
        print(f"{path}: {file_info(path)}")
        if name == "sample.osm":
            print(f"{path} fileinfo: {osmium_fileinfo(path)}")

    print("\n[Repository Working Code outputs]")
    for name in ("qa_errors.geojson", "task_grid_qa_summary.geojson"):
        path = OLD_DIR / name
        print(f"{path}: {file_info(path)}")


if __name__ == "__main__":
    main()
