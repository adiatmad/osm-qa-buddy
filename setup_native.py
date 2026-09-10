import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

JOSM_VERSION = "19613"
JYTHON_VERSION = "2.7.3"
TOOLS_DIR = Path(__file__).resolve().parent / "tools"
JOSM_URL = f"https://josm.openstreetmap.de/download/josm-{JOSM_VERSION}.jar"
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


def command_exists(name):
    return shutil.which(name) is not None


def main():
    print("OSM QA Buddy — native Windows setup")
    print("====================================")
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")
    if not command_exists("java"):
        raise SystemExit("Java was not found on PATH. Install a current 64-bit JDK/JRE, then reopen PowerShell.")
    if not command_exists("osmium"):
        raise SystemExit("Osmium was not found on PATH. Install osmium-tool, then reopen PowerShell.")

    java = subprocess.run(["java", "-version"], capture_output=True, text=True)
    print((java.stderr or java.stdout).splitlines()[0] if (java.stderr or java.stdout) else "Java detected")
    print("Osmium detected")
    download(JOSM_URL, TOOLS_DIR / f"josm-{JOSM_VERSION}.jar")
    download(JYTHON_URL, TOOLS_DIR / f"jython-{JYTHON_VERSION}.jar")
    print(f"\nReady. Pinned JOSM {JOSM_VERSION} and Jython {JYTHON_VERSION} are in {TOOLS_DIR}.")


if __name__ == "__main__":
    main()
