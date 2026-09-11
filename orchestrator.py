import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point, shape

from preflight import normalize_aoi_for_osmium, validate_inputs
from report import generate_report

QA_BUDDY_VERSION = "0.1.0"
JOSM_VERSION = "19613"
JYTHON_VERSION = "2.7.3"
HOT_RULES_URL = "https://josm.openstreetmap.de/josmfile?page=Rules/ValidatingBuildingsInHOTTMProjects&zip=1"
REPO_DIR = Path(__file__).resolve().parent
TOOLS_DIR = REPO_DIR / "tools"
JOSM_JAR = TOOLS_DIR / f"josm-{JOSM_VERSION}.jar"
JYTHON_JAR = TOOLS_DIR / f"jython-{JYTHON_VERSION}.jar"
WORK_DIR = os.environ.get("QABOT_WORK_DIR", str(REPO_DIR / "work"))


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


def _check_native_toolchain():
    missing = []
    if shutil.which("java") is None: missing.append("Java")
    if shutil.which("osmium") is None: missing.append("Osmium")
    if not JOSM_JAR.is_file(): missing.append(f"tools/{JOSM_JAR.name}")
    if not JYTHON_JAR.is_file(): missing.append(f"tools/{JYTHON_JAR.name}")
    if missing: raise RuntimeError("Native prerequisites missing: " + ", ".join(missing) + ". Run setup_native.py first.")


def write_run_metadata(aoi_path, tasks_path, pbf_path, output_path, run_started_utc, ram_gb, project_id=None):
    inputs = {}
    for label, path in (("project_boundary", aoi_path), ("task_grid", tasks_path), ("geofabrik_pbf", pbf_path)):
        stat = os.stat(path)
        inputs[label] = {"filename": os.path.basename(path), "size_bytes": stat.st_size, "sha256": _sha256(path)}
    resolved_project_id = str(project_id).strip() if project_id is not None else os.environ.get("QABOT_PROJECT_ID") or None
    metadata = {"qa_buddy_version": QA_BUDDY_VERSION, "project_id": resolved_project_id, "run_started_utc": run_started_utc, "validation_engine": "JOSM headless validator", "java_xmx_gb": ram_gb, "toolchain": {"josm_tested_version": JOSM_VERSION, "jython_version": JYTHON_VERSION, "java_runtime": _command_version(["java", "-version"]), "osmium_version": _command_version(["osmium", "--version"])}, "inputs": inputs, "human_review_required": True}
    Path(output_path).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"  -> Run metadata saved to: {output_path}")
    return output_path


def _update_run_metadata(path, **updates):
    try:
        metadata = json.loads(Path(path).read_text(encoding="utf-8"))
        metadata.update(updates)
        Path(path).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"  -> Warning: could not update run metadata: {exc}")


def prepare_hot_rules():
    extract_path = os.path.join(WORK_DIR, "hot_rules")
    if os.path.isdir(extract_path) and any(filename.endswith(".mapcss") for _, _, files in os.walk(extract_path) for filename in files):
        print("[*] HOT TM MapCSS rules already prepared.")
        return extract_path
    os.makedirs(extract_path, exist_ok=True)
    zip_path = os.path.join(WORK_DIR, "hot_building_rules.zip")
    print("[*] Downloading HOT TM MapCSS rules with Python 3...")
    try:
        with urllib.request.urlopen(HOT_RULES_URL, timeout=60) as response, open(zip_path, "wb") as output: shutil.copyfileobj(response, output)
        with zipfile.ZipFile(zip_path, "r") as zip_ref: zip_ref.extractall(extract_path)
    except Exception as exc:
        raise RuntimeError(f"Could not prepare HOT TM MapCSS rules:\n{exc}") from exc
    if not any(filename.endswith(".mapcss") for _, _, files in os.walk(extract_path) for filename in files): raise RuntimeError("HOT TM MapCSS rules ZIP was downloaded, but no .mapcss rule file was found.")
    print(f"  -> HOT TM MapCSS rules prepared in {extract_path}")
    return extract_path


def _osmium_fileinfo(path):
    result = subprocess.run(["osmium", "fileinfo", "-e", path], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Osmium could not inspect the extracted dataset:\n{result.stderr or result.stdout}")
    return result.stdout or result.stderr


def clip_pbf_with_osmium(aoi_geojson_path, regional_pbf_path):
    output_osm_path = os.path.join(WORK_DIR, "sample.osm")
    normalized_aoi_path = os.path.join(WORK_DIR, "osmium_aoi.geojson")
    normalize_aoi_for_osmium(aoi_geojson_path, normalized_aoi_path)
    print(f"[*] Clipping PBF ({os.path.basename(regional_pbf_path)}) using native Osmium...")
    result = subprocess.run(["osmium", "extract", "-p", normalized_aoi_path, regional_pbf_path, "-o", output_osm_path, "--overwrite"], capture_output=True, text=True)
    if result.returncode != 0: raise RuntimeError(f"Osmium extraction failed:\n{result.stderr or result.stdout}")
    print("  -> Extracted project dataset:")
    print(_osmium_fileinfo(output_osm_path))
    print(f"  -> Saved to {output_osm_path}")
    return output_osm_path


def run_josm_qa_bot(ram_gb):
    classpath = os.pathsep.join((str(JOSM_JAR), str(JYTHON_JAR)))
    print(f"[*] Executing native JOSM {JOSM_VERSION} + Jython {JYTHON_VERSION} with -Xmx{ram_gb}g...")
    print("    JOSM CrossingWays is a full-dataset spatial test; long periods without new log lines are expected.")
    started = time.monotonic()
    process = subprocess.Popen(["java", f"-Xmx{ram_gb}g", "-cp", classpath, "org.python.util.jython", str(REPO_DIR / "bot.py")], cwd=WORK_DIR)
    last_heartbeat = started
    while process.poll() is None:
        time.sleep(30)
        elapsed = int(time.monotonic() - started)
        if elapsed - int(last_heartbeat - started) >= 30:
            minutes, seconds = divmod(elapsed, 60)
            print(f"    JOSM still running — elapsed {minutes}m {seconds:02d}s. Waiting for validator completion...")
            last_heartbeat = time.monotonic()
    if process.returncode != 0: raise RuntimeError("bot.py execution failed. Check the live log for the failing validator.")


def _normalize_severity(value):
    value = str(value or "UNKNOWN").upper()
    if value in {"ERROR", "ERRORS"}: return "ERROR"
    if value in {"WARNING", "WARN", "WARNINGS"}: return "WARNING"
    return value


def _finding_key(finding):
    return (str(finding.get("severity") or "UNKNOWN"), str(finding.get("rule") or "Unknown"), str(finding.get("message") or ""), str(finding.get("object_id") or ""), tuple(finding.get("coordinates") or ()))


def _priority_for_task(finding_count, unique_finding_count, unique_object_count, badimagery):
    if badimagery or unique_object_count >= 5 or unique_finding_count >= 5: return "HIGH"
    if unique_object_count >= 2 or unique_finding_count >= 2: return "MEDIUM"
    if finding_count >= 1: return "LOW"
    return "NONE"


def aggregate_errors_to_tasks(tasks_geojson_path, errors_geojson_path):
    with open(tasks_geojson_path, "r", encoding="utf-8") as f: tasks_data = json.load(f)
    with open(errors_geojson_path, "r", encoding="utf-8") as f: errors_data = json.load(f)
    error_points = []
    for feature in errors_data.get("features", []):
        coords = feature.get("geometry", {}).get("coordinates")
        if not coords: continue
        props = feature.get("properties", {})
        error_points.append({"point": Point(coords[0], coords[1]), "coordinates": coords, "severity": props.get("severity", "UNKNOWN"), "object_id": props.get("object_id", ""), "rule": props.get("rule", "Unknown"), "message": props.get("message", "")})
    assigned_count = 0; unassigned = []; task_geometries = []
    for task_feat in tasks_data.get("features", []):
        task_poly = shape(task_feat["geometry"]); task_geometries.append(task_poly)
        findings = [error for error in error_points if task_poly.covers(error["point"])]
        assigned_count += len(findings)
        error_count = sum(1 for x in findings if _normalize_severity(x["severity"]) == "ERROR")
        warning_count = sum(1 for x in findings if _normalize_severity(x["severity"]) == "WARNING")
        unique_objects = {x["object_id"] for x in findings if x["object_id"]}; rules = {x["rule"] for x in findings if x["rule"]}; unique_findings = {_finding_key(x) for x in findings}
        props = task_feat.setdefault("properties", {}); task_status = str(props.get("taskStatus") or "").strip().upper(); badimagery = task_status == "BADIMAGERY"
        props.update({"qa_task_status": task_status or "UNKNOWN", "qa_badimagery": badimagery, "qa_finding_count": len(findings), "qa_unique_finding_count": len(unique_findings), "qa_unique_osm_object_count": len(unique_objects), "qa_rules_involved": sorted(rules), "qa_error_count": error_count, "qa_warning_count": warning_count, "qa_unknown_severity_count": len(findings) - error_count - warning_count, "qa_total_issues": len(findings), "qa_priority": _priority_for_task(len(findings), len(unique_findings), len(unique_objects), badimagery)})
    for error in error_points:
        if not any(poly.covers(error["point"]) for poly in task_geometries): unassigned.append(error)
    tasks_data["qa_summary"] = {"raw_josm_finding_count": len(error_points), "task_associated_finding_count": assigned_count, "unassigned_finding_count": len(unassigned), "task_associated_unique_finding_count": len({_finding_key(error) for poly in task_geometries for error in error_points if poly.covers(error["point"])}), "priority_definition": {"HIGH": "BADIMAGERY or at least 5 unique findings or 5 unique OSM objects", "MEDIUM": "2-4 unique findings or 2-4 unique OSM objects", "LOW": "1 raw finding with no HIGH/MEDIUM signal", "NONE": "No QA finding signal and not BADIMAGERY"}, "human_review_required": True}
    summary_path = os.path.join(WORK_DIR, "task_grid_qa_summary.geojson")
    with open(summary_path, "w", encoding="utf-8") as f: json.dump(tasks_data, f, indent=2)
    badimagery_count = sum(1 for feature in tasks_data.get("features", []) if feature.get("properties", {}).get("qa_badimagery"))
    print(f"  -> BADIMAGERY tasks detected: {badimagery_count}"); print(f"  -> Raw JOSM findings: {len(error_points)}"); print(f"  -> Task-associated findings: {assigned_count}"); print(f"  -> Unassigned findings: {len(unassigned)}"); print(f"  -> Final Task Grid QA Summary saved to: {summary_path}")
    return summary_path


def run_local_pipeline(pbf_path, aoi_path, tasks_path, output_dir=None, ram_gb=24, project_id=None):
    os.makedirs(WORK_DIR, exist_ok=True)
    if output_dir: os.makedirs(output_dir, exist_ok=True)
    _check_native_toolchain(); run_started_utc = datetime.now(timezone.utc).isoformat()
    print("==================================================\n Starting OSM QA Buddy — 3rd Pass Validation\n==================================================")
    preflight = validate_inputs(aoi_path, tasks_path, pbf_path, check_pbf=True)
    for check in preflight["checks"]: print(("PASS: " if check["ok"] else "FAIL: ") + check["message"])
    if not preflight["ok"]: raise RuntimeError("Pre-flight validation failed. Fix the selected input files and try again.")
    metadata_path = os.path.join(WORK_DIR, "run_metadata.json"); write_run_metadata(aoi_path, tasks_path, pbf_path, metadata_path, run_started_utc, ram_gb, project_id=project_id)
    for src, name in ((aoi_path, "project_aoi.geojson"), (tasks_path, "project_tasks.geojson"), (pbf_path, "region.osm.pbf")):
        dst = os.path.join(WORK_DIR, name)
        if os.path.abspath(src) != os.path.abspath(dst): shutil.copy2(src, dst)
    aoi, tasks, pbf = (os.path.join(WORK_DIR, x) for x in ("project_aoi.geojson", "project_tasks.geojson", "region.osm.pbf"))
    sample_path = clip_pbf_with_osmium(aoi, pbf); _update_run_metadata(metadata_path, extracted_dataset={"path": sample_path, "size_bytes": os.path.getsize(sample_path), "osmium_fileinfo": _osmium_fileinfo(sample_path)})
    prepare_hot_rules(); run_josm_qa_bot(ram_gb)
    errors = os.path.join(WORK_DIR, "qa_errors.geojson"); summary = aggregate_errors_to_tasks(tasks, errors)
    report_path, map_path = os.path.join(WORK_DIR, "report.html"), os.path.join(WORK_DIR, "map.html")
    generate_report(errors, summary, report_path, map_path, metadata_path)
    if output_dir:
        for name in ("qa_errors.geojson", "task_grid_qa_summary.geojson", "sample.osm", "report.html", "map.html", "run_metadata.json"):
            src = os.path.join(WORK_DIR, name)
            if os.path.exists(src): shutil.copy2(src, os.path.join(output_dir, name))
    print(f"[+] REPORT: {report_path}\n[+] MAP: {map_path}\n[+] METADATA: {metadata_path}\n[+] PIPELINE SUCCEEDED")


def main():
    parser = argparse.ArgumentParser(description="OSM QA Buddy native Windows pipeline")
    parser.add_argument("pbf"); parser.add_argument("aoi"); parser.add_argument("tasks"); parser.add_argument("output_dir"); parser.add_argument("--ram-gb", type=int, default=24); parser.add_argument("--project-id", default=None)
    args = parser.parse_args()
    if not 1 <= args.ram_gb <= 128: parser.error("--ram-gb must be between 1 and 128")
    if args.project_id is not None and not str(args.project_id).isdigit(): parser.error("--project-id must be numeric")
    run_local_pipeline(args.pbf, args.aoi, args.tasks, args.output_dir, args.ram_gb, project_id=args.project_id)


if __name__ == "__main__":
    main()
