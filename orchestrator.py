import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape

from preflight import normalize_aoi_for_osmium, validate_inputs
from report import generate_report

WORK_DIR = os.environ.get("QABOT_WORK_DIR", "/data/work")
QA_BUDDY_VERSION = "0.1.0"
JOSM_VERSION = "19613"
JYTHON_VERSION = "2.7.3"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        output = (result.stdout or result.stderr).strip()
        return output.splitlines()[0] if output else "unknown"
    except Exception as exc:
        return f"unavailable: {exc}"


def write_run_metadata(aoi_path, tasks_path, pbf_path, output_path, run_started_utc):
    inputs = {}
    for label, path in (("project_boundary", aoi_path), ("task_grid", tasks_path), ("geofabrik_pbf", pbf_path)):
        stat = os.stat(path)
        inputs[label] = {
            "filename": os.path.basename(path),
            "size_bytes": stat.st_size,
            "sha256": _sha256(path),
        }

    metadata = {
        "qa_buddy_version": QA_BUDDY_VERSION,
        "project_id": os.environ.get("QABOT_PROJECT_ID") or None,
        "run_started_utc": run_started_utc,
        "validation_engine": "JOSM headless validator",
        "toolchain": {
            "josm_tested_version": JOSM_VERSION,
            "jython_version": JYTHON_VERSION,
            "java_runtime": _command_version(["java", "-version"]),
            "osmium_version": _command_version(["osmium", "--version"]),
        },
        "inputs": inputs,
        "validation_scope": [
            "HOT TM project boundary preflight",
            "HOT TM task grid preflight",
            "Geofabrik regional PBF preflight",
            "OSM data clipped to project boundary",
            "JOSM validator checks",
            "task-level finding aggregation",
        ],
        "human_review_required": True,
    }
    Path(output_path).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"  -> Run metadata saved to: {output_path}")
    return output_path


def clip_pbf_with_osmium(aoi_geojson_path, regional_pbf_path):
    output_osm_path = os.path.join(WORK_DIR, "sample.osm")
    normalized_aoi_path = os.path.join(WORK_DIR, "osmium_aoi.geojson")
    normalize_aoi_for_osmium(aoi_geojson_path, normalized_aoi_path)
    print(f"[*] Clipping PBF ({os.path.basename(regional_pbf_path)}) using Osmium...")
    print("  -> Normalized AOI written in Osmium-compatible Feature format.")
    cmd = ["osmium", "extract", "-p", normalized_aoi_path, regional_pbf_path, "-o", output_osm_path, "--overwrite"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Osmium extraction failed:\n{result.stderr or result.stdout}")
    print(f"  -> Extracted project dataset saved to {output_osm_path}")
    return output_osm_path


def run_josm_qa_bot():
    print(f"[*] Executing JOSM {JOSM_VERSION} Headless QA Bot (bot.py)...")
    cmd = ["java", "-Xmx10g", "-cp", "/app/josm-tested.jar:/app/jython.jar", "org.python.util.jython", "/app/bot.py"]
    result = subprocess.run(cmd, cwd=WORK_DIR)
    if result.returncode != 0:
        raise RuntimeError("bot.py execution failed. Check the Docker console output for the failing validator.")


def _normalize_severity(value):
    value = str(value or "UNKNOWN").upper()
    if value in {"ERROR", "ERRORS"}:
        return "ERROR"
    if value in {"WARNING", "WARN", "WARNINGS"}:
        return "WARNING"
    return value


def _finding_key(finding):
    """Identity for exact duplicate reporting; raw findings remain untouched."""
    return (
        str(finding.get("severity") or "UNKNOWN"),
        str(finding.get("rule") or "Unknown"),
        str(finding.get("message") or ""),
        str(finding.get("object_id") or ""),
        tuple(finding.get("coordinates") or ()),
    )


def _priority_for_task(finding_count, unique_finding_count, unique_object_count, badimagery):
    """Explainable PM triage signal; this is prioritization, not a quality score."""
    if badimagery or unique_object_count >= 5 or unique_finding_count >= 5:
        return "HIGH"
    if unique_object_count >= 2 or unique_finding_count >= 2:
        return "MEDIUM"
    if finding_count >= 1:
        return "LOW"
    return "NONE"


def aggregate_errors_to_tasks(tasks_geojson_path, errors_geojson_path):
    if not os.path.exists(tasks_geojson_path) or not os.path.exists(errors_geojson_path):
        raise FileNotFoundError("Task grid or QA errors output is missing, so task-level summary cannot be generated.")

    with open(tasks_geojson_path, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)
    with open(errors_geojson_path, "r", encoding="utf-8") as f:
        errors_data = json.load(f)

    error_points = []
    for feature in errors_data.get("features", []):
        coords = feature.get("geometry", {}).get("coordinates")
        if not coords:
            continue
        props = feature.get("properties", {})
        error_points.append({
            "point": Point(coords[0], coords[1]),
            "coordinates": coords,
            "severity": props.get("severity", "UNKNOWN"),
            "object_id": props.get("object_id", ""),
            "rule": props.get("rule", "Unknown"),
            "message": props.get("message", ""),
        })

    assigned_count = 0
    unassigned_findings = []

    for task_feat in tasks_data.get("features", []):
        task_poly = shape(task_feat["geometry"])
        findings = [error for error in error_points if task_poly.covers(error["point"])]
        assigned_count += len(findings)
        error_count = sum(1 for finding in findings if _normalize_severity(finding["severity"]) == "ERROR")
        warning_count = sum(1 for finding in findings if _normalize_severity(finding["severity"]) == "WARNING")
        unknown_count = len(findings) - error_count - warning_count
        unique_objects = {finding["object_id"] for finding in findings if finding["object_id"]}
        rules = {finding["rule"] for finding in findings if finding["rule"]}
        unique_findings = {_finding_key(finding) for finding in findings}

        props = task_feat.setdefault("properties", {})
        task_status = str(props.get("taskStatus") or "").strip().upper()
        badimagery = task_status == "BADIMAGERY"
        props["qa_task_status"] = task_status or "UNKNOWN"
        props["qa_badimagery"] = badimagery
        props["qa_finding_count"] = len(findings)
        props["qa_unique_finding_count"] = len(unique_findings)
        props["qa_unique_osm_object_count"] = len(unique_objects)
        props["qa_rules_involved"] = sorted(rules)
        props["qa_error_count"] = error_count
        props["qa_warning_count"] = warning_count
        props["qa_unknown_severity_count"] = unknown_count
        props["qa_total_issues"] = len(findings)
        props["qa_priority"] = _priority_for_task(
            len(findings), len(unique_findings), len(unique_objects), badimagery
        )

    # Do not silently force a finding into a task when its representative point
    # does not fall inside any task polygon. Keep the raw finding in qa_errors.geojson
    # and expose the accounting gap for auditability.
    for error in error_points:
        if not any(shape(task_feat["geometry"]).covers(error["point"]) for task_feat in tasks_data.get("features", [])):
            unassigned_findings.append(error)

    tasks_data["qa_summary"] = {
        "raw_josm_finding_count": len(error_points),
        "task_associated_finding_count": assigned_count,
        "unassigned_finding_count": len(unassigned_findings),
        "task_associated_unique_finding_count": len({
            _finding_key(error)
            for task_feat in tasks_data.get("features", [])
            for error in error_points
            if shape(task_feat["geometry"]).covers(error["point"])
        }),
        "priority_definition": {
            "HIGH": "BADIMAGERY or at least 5 unique findings or 5 unique OSM objects",
            "MEDIUM": "2-4 unique findings or 2-4 unique OSM objects",
            "LOW": "1 raw finding with no HIGH/MEDIUM signal",
            "NONE": "No QA finding signal and not BADIMAGERY",
        },
        "human_review_required": True,
    }

    summary_path = os.path.join(WORK_DIR, "task_grid_qa_summary.geojson")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(tasks_data, f, indent=2)
    badimagery_count = sum(
        1 for feature in tasks_data.get("features", [])
        if feature.get("properties", {}).get("qa_badimagery")
    )
    print(f"  -> BADIMAGERY tasks detected: {badimagery_count}")
    print(f"  -> Raw JOSM findings: {len(error_points)}")
    print(f"  -> Task-associated findings: {assigned_count}")
    print(f"  -> Unassigned findings: {len(unassigned_findings)}")
    print(f"  -> Final Task Grid QA Summary saved to: {summary_path}")
    return summary_path


def run_local_pipeline(pbf_path, aoi_path, tasks_path, output_dir=None):
    os.makedirs(WORK_DIR, exist_ok=True)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    run_started_utc = datetime.now(timezone.utc).isoformat()
    for path, label in ((pbf_path, "PBF"), (aoi_path, "Project Boundary"), (tasks_path, "Task Grid")):
        if not path or not os.path.isfile(path):
            raise FileNotFoundError(f"{label} file not found: {path}")

    print("==================================================")
    print(" Starting OSM QA Buddy — 3rd Pass Validation")
    print("==================================================")
    preflight = validate_inputs(aoi_path, tasks_path, pbf_path, check_pbf=True)
    for check in preflight["checks"]:
        print(("PASS: " if check["ok"] else "FAIL: ") + check["message"])
    if not preflight["ok"]:
        raise RuntimeError("Pre-flight validation failed. Fix the selected input files and try again.")

    metadata_path = os.path.join(WORK_DIR, "run_metadata.json")
    write_run_metadata(aoi_path, tasks_path, pbf_path, metadata_path, run_started_utc)
    if output_dir:
        shutil.copy2(metadata_path, os.path.join(output_dir, "run_metadata.json"))

    for src, name in ((aoi_path, "project_aoi.geojson"), (tasks_path, "project_tasks.geojson"), (pbf_path, "region.osm.pbf")):
        dst = os.path.join(WORK_DIR, name)
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst)

    aoi = os.path.join(WORK_DIR, "project_aoi.geojson")
    tasks = os.path.join(WORK_DIR, "project_tasks.geojson")
    pbf = os.path.join(WORK_DIR, "region.osm.pbf")
    clip_pbf_with_osmium(aoi, pbf)
    run_josm_qa_bot()
    errors = os.path.join(WORK_DIR, "qa_errors.geojson")
    summary = aggregate_errors_to_tasks(tasks, errors)
    report_path = os.path.join(WORK_DIR, "report.html")
    map_path = os.path.join(WORK_DIR, "map.html")
    generate_report(errors, summary, report_path, map_path, metadata_path)

    if output_dir:
        for name in ("qa_errors.geojson", "task_grid_qa_summary.geojson", "sample.osm", "report.html", "map.html", "run_metadata.json"):
            src = os.path.join(WORK_DIR, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(output_dir, name))

    print(f"[+] REPORT: {report_path}")
    print(f"[+] MAP: {map_path}")
    print(f"[+] METADATA: {metadata_path}")
    print("[+] PIPELINE SUCCEEDED")


def main():
    parser = argparse.ArgumentParser(description="OSM QA Buddy Docker pipeline")
    parser.add_argument("pbf", nargs="?")
    parser.add_argument("aoi", nargs="?")
    parser.add_argument("tasks", nargs="?")
    parser.add_argument("output_dir", nargs="?")
    parser.add_argument("--preflight", action="store_true", help="Run input preflight only")
    args = parser.parse_args()
    if not args.pbf or not args.aoi or not args.tasks:
        parser.error("pbf, aoi and tasks are required")
    if args.preflight:
        result = validate_inputs(args.aoi, args.tasks, args.pbf, check_pbf=True)
        for check in result["checks"]:
            print(("PASS: " if check["ok"] else "FAIL: ") + check["message"])
        sys.exit(0 if result["ok"] else 1)
    run_local_pipeline(args.pbf, args.aoi, args.tasks, args.output_dir)


if __name__ == "__main__":
    main()
