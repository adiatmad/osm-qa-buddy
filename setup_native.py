import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from osmium_tool import OsmiumToolError, resolve_osmium

JOSM_VERSION = "tested"
JYTHON_VERSION = "2.7.3"
TOOLS_DIR = Path(__file__).resolve().parent / "tools"
REQUIREMENTS_FILE = Path(__file__).resolve().parent / "requirements.txt"
JOSM_URL = "https://josm.openstreetmap.de/download/josm-tested.jar"
JYTHON_URL = f"https://repo1.maven.org/maven2/org/python/jython-standalone/{JYTHON_VERSION}/jython-standalone-{JYTHON_VERSION}.jar"


def download(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 100000:
        print(f"OK: {destination.name} already exists")
        return
    print(f"Downloading {destination.name}...")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, open(destination, "wb") as output:
            shutil.copyfileobj(response, output)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if expected_sha256 and sha256(destination) != expected_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 verification failed for {destination.name}.")


def is_valid_josm_jar(path):
    """Return whether the file is a readable JOSM application JAR."""
    try:
        with zipfile.ZipFile(path) as archive:
            return "org/openstreetmap/josm/gui/MainApplication.class" in archive.namelist()
    except (OSError, zipfile.BadZipFile):
        return False


def command_exists(name):
    return shutil.which(name) is not None


def ensure_python_dependencies():
    """Install the small native-Python runtime dependency set when needed."""
    if not REQUIREMENTS_FILE.is_file():
        raise SystemExit("requirements.txt is missing from the QA Buddy repository.")

    try:
        import shapely
        print(f"OK: Shapely {shapely.__version__} already installed")
        return
    except ImportError:
        pass

    print("Installing native Python dependencies...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=False)
    if result.returncode != 0:
        raise SystemExit("Python dependency installation failed. Check the pip output above and try again.")

    try:
        import shapely
        print(f"OK: Shapely {shapely.__version__} installed")
    except ImportError as exc:
        raise SystemExit("Shapely is still unavailable after dependency installation.") from exc


def main():
    parser = argparse.ArgumentParser(description="Prepare OSM QA Buddy native dependencies.")
    parser.add_argument(
        "--gui-only",
        action="store_true",
        help="Prepare the verified JOSM GUI runtime without downloading the legacy Jython component.",
    )
    args = parser.parse_args()

    print("OSM QA Buddy — native Windows setup")
    print("====================================")
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")
    ensure_python_dependencies()
    if not command_exists("java"):
        raise SystemExit("Java was not found on PATH. Install a 64-bit Java runtime, then reopen PowerShell.")
    try:
        osmium_path = resolve_osmium()
    except OsmiumToolError as exc:
        raise SystemExit(str(exc)) from exc
    java = subprocess.run(["java", "-version"], capture_output=True, text=True)
    print((java.stderr or java.stdout).splitlines()[0] if (java.stderr or java.stdout) else "Java detected")
    print(f"Osmium Tool: {osmium_path} (verified with --version)")
    josm_jar = TOOLS_DIR / "josm-tested.jar"
    if josm_jar.exists() and not is_valid_josm_jar(josm_jar):
        josm_jar.unlink()
    download(JOSM_URL, josm_jar)
    if not is_valid_josm_jar(josm_jar):
        josm_jar.unlink(missing_ok=True)
        raise RuntimeError("The official JOSM download is not a valid JOSM application JAR.")
    if not args.gui_only:
        download(JYTHON_URL, TOOLS_DIR / f"jython-{JYTHON_VERSION}.jar")
    print(f"\nReady. The current tested JOSM release is prepared in {TOOLS_DIR}.")
    if not args.gui_only:
        print(f"Jython {JYTHON_VERSION} is also prepared in {TOOLS_DIR}.")


if __name__ == "__main__":
    main()
