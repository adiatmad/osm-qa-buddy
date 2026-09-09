import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Point, shape

from preflight import normalize_aoi_for_osmium, validate_inputs
from report import generate_report

WORK_DIR = os.environ.get("QABOT_WORK_DIR", "/data/work")


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
    print("[*] Executing JOSM Headless QA Bot (bot.py)...")
    cmd = ["java", "-Xmx10g", "-cp", "/app/josm-tested.jar:/app/jython.jar", "org.python.util.jython", "/app/bot.py"]
    result = subprocess.run(cmd, cwd=WORK_DIR)
    if result.returncode != 0:
        raise RuntimeError("bot.py execution failed. Check the Docker console output for the failing validator.")


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
            "severity": props.get("severity", "UNKNOWN"),
            "object_id": props.get("object_id", ""),
            "rule": props.get("rule", "Unknown"),
        })

    for task_feat in tasks_data.get("features", []):
        task_poly = shape(task_feat["geometry"])
        findings = [error for error in error_points if task_poly.covers(error["point"])]
        error_count = sum(1 for finding in findings if str(finding["severity"]).upper() == "ERROR")
        warning_count = sum(1 for finding in findings if str(finding["severity"]).upper() in {"WARNING", "WARN", "WARNINGS"})
        unknown_count = len(findings) - error_count - warning_count
        unique_objects = {finding["object_id"] for finding in findings if finding["object_id"]}
        rules = {finding["rule"] for finding in findings if finding["rule"]}

        props = task_feat.setdefault("properties", {})
        props["qa_finding_count"] = len(findings)
        props["qa_unique_osm_object_count"] = len(unique_objects)
        props["qa_rules_involved"] = sorted(rules)
        props["qa_error_count"] = error_count
        props["qa_warning_count"] = warning_count
        props["qa_unknown_severity_count"] = unknown_count
        props["qa_total_issues"] = len(findings)

    summary_path = os.path.join(WORK_DIR, "task_grid_qa_summary.geojson")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(tasks_data, f, indent=2)
    print(f"  -> Final Task Grid QA Summary saved to: {summary_path}")
    return summary_path


def run_local_pipeline(pbf_path, aoi_path, tasks_path, output_dir=None):
    os.makedirs(WORK_DIR, exist_ok=True)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
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
    generate_report(errors, summary, report_path, map_path)

    if output_dir:
        for name in ("qa_errors.geojson", "task_grid_qa_summary.geojson", "sample.osm", "report.html", "map.html"):
            src = os.path.join(WORK_DIR, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(output_dir, name))

    print(f"[+] REPORT: {report_path}")
    print(f"[+] MAP: {map_path}")
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
