import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Benchmark the official JOSM headless ValidatorCLI.")
    parser.add_argument("--input", required=True, help="Project-clipped .osm file")
    parser.add_argument("--josm-jar", required=True, help="JOSM jar, e.g. tools/josm-19613.jar")
    parser.add_argument("--output", required=True, help="ValidatorCLI GeoJSON output path")
    parser.add_argument("--report", required=True, help="Benchmark JSON report path")
    parser.add_argument("--xmx-gb", type=int, default=24)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    josm_jar = Path(args.josm_jar).resolve()
    output_path = Path(args.output).resolve()
    report_path = Path(args.report).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.is_file():
        raise SystemExit(f"Input OSM file not found: {input_path}")
    if not josm_jar.is_file():
        raise SystemExit(f"JOSM jar not found: {josm_jar}")

    command = ["java", f"-Xmx{args.xmx_gb}g", "-jar", str(josm_jar), "validate", "--input", str(input_path), "--output", str(output_path)]
    started = datetime.now(timezone.utc)
    start_monotonic = time.monotonic()
    print("Official JOSM ValidatorCLI benchmark")
    print("====================================")
    print("Input : " + str(input_path))
    print("JOSM  : " + str(josm_jar))
    print("Output: " + str(output_path))
    print("Xmx   : " + str(args.xmx_gb) + " GB")
    print("")
    print("Running: " + " ".join(command))
    print("")

    process = subprocess.run(command, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - start_monotonic
    finished = datetime.now(timezone.utc)
    stdout = process.stdout or ""
    stderr = process.stderr or ""
    print(stdout, end="")
    if stderr:
        print(stderr, end="")

    finding_count = None
    if output_path.is_file():
        try:
            text = output_path.read_text(encoding="utf-8")
            finding_count = sum(1 for line in text.splitlines() if line.startswith("\x1e"))
        except Exception:
            finding_count = None

    report = {
        "benchmark": "JOSM official ValidatorCLI",
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": process.returncode,
        "xmx_gb": args.xmx_gb,
        "input": {"path": str(input_path), "size_bytes": input_path.stat().st_size, "sha256": sha256(input_path)},
        "josm_jar": {"path": str(josm_jar), "size_bytes": josm_jar.stat().st_size, "sha256": sha256(josm_jar)},
        "output": {"path": str(output_path), "exists": output_path.is_file(), "size_bytes": output_path.stat().st_size if output_path.is_file() else 0, "finding_count": finding_count},
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("")
    print("Benchmark report: " + str(report_path))
    print("Elapsed seconds: " + str(round(elapsed, 3)))
    print("Exit code: " + str(process.returncode))
    if finding_count is not None:
        print("GeoJSON records: " + str(finding_count))
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
