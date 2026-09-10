import os
import sys
import json
import subprocess
from shapely.geometry import shape, Point

# ============================================================
# LOCAL CONFIGURATION
# ============================================================
WORK_DIR = r"C:\JOSM_Headless"

# Uses standard system Java binary path or custom installation path
JAVA_BIN = "java"


def resolve_path(file_path):
    """Ensures the file path is absolute, relative to WORK_DIR if needed."""
    if not file_path:
        return None
    if not os.path.isabs(file_path):
        return os.path.join(WORK_DIR, file_path)
    return file_path


def auto_detect_pbf():
    """Automatically searches for an .osm.pbf file in the working folder if none is specified."""
    for file in os.listdir(WORK_DIR):
        if file.endswith(".pbf"):
            return os.path.join(WORK_DIR, file)

    cache_dir = os.path.join(WORK_DIR, "pbf_cache")
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            if file.endswith(".pbf"):
                return os.path.join(cache_dir, file)

    return None


def clip_pbf_with_osmium(aoi_geojson_path, regional_pbf_path):
    """Clips the local PBF file to the project AOI, producing sample.osm."""
    output_osm_path = os.path.join(WORK_DIR, "sample.osm")
    print(f"[*] Clipping PBF ({os.path.basename(regional_pbf_path)}) using Osmium...")

    cmd = [
        "osmium", "extract",
        "-p", aoi_geojson_path,
        regional_pbf_path,
        "-o", output_osm_path,
        "--overwrite"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Osmium extraction failed:\n{result.stderr}")

    print(f"  -> Extracted project dataset saved to {output_osm_path}")
    return output_osm_path


def run_josm_qa_bot():
    """Runs bot.py using Jython & JOSM Headless core with 16 GB RAM allocation."""
    print("[*] Executing JOSM Headless QA Bot (bot.py)...")
    cmd = [
        JAVA_BIN,
        "-Xmx24g",  # Allocated 24 GB RAM for high-performance spatial processing on 32GB RAM PC
        "-cp", "josm-tested.jar;jython.jar",
        "org.python.util.jython",
        "bot.py"
    ]

    result = subprocess.run(cmd, cwd=WORK_DIR)
    if result.returncode != 0:
        raise Exception("bot.py execution failed.")


def aggregate_errors_to_tasks(tasks_geojson_path, errors_geojson_path):
    """Spatial join: counts total errors/warnings inside each task grid polygon."""
    if not tasks_geojson_path or not os.path.exists(tasks_geojson_path):
        filename = os.path.basename(tasks_geojson_path) if tasks_geojson_path else "tasks grid"
        print(f"  [*] Note: Task grid file '{filename}' not found. Grid aggregation skipped.")
        return

    if not os.path.exists(errors_geojson_path):
        print("  [!] Skipping grid aggregation due to missing qa_errors.geojson.")
        return

    print(f"[*] Aggregating errors into Task Grid '{os.path.basename(tasks_geojson_path)}' (Spatial Join)...")

    with open(tasks_geojson_path, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)

    with open(errors_geojson_path, "r", encoding="utf-8") as f:
        errors_data = json.load(f)

    error_points = []
    for feat in errors_data.get("features", []):
        coords = feat["geometry"]["coordinates"]
        error_points.append({
            "point": Point(coords[0], coords[1]),
            "severity": feat["properties"].get("severity", "UNKNOWN")
        })

    total_issues_joined = 0
    for task_feat in tasks_data.get("features", []):
        task_poly = shape(task_feat["geometry"])
        error_count = 0
        warning_count = 0

        for err in error_points:
            if task_poly.contains(err["point"]):
                if err["severity"] == "ERROR":
                    error_count += 1
                else:
                    warning_count += 1

        task_feat["properties"]["qa_error_count"] = error_count
        task_feat["properties"]["qa_warning_count"] = warning_count
        task_feat["properties"]["qa_total_issues"] = error_count + warning_count
        total_issues_joined += (error_count + warning_count)

    summary_path = os.path.join(WORK_DIR, "task_grid_qa_summary.geojson")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(tasks_data, f, indent=2)

    print(f"  -> Final Task Grid QA Summary saved to: {summary_path}")


def run_local_pipeline(pbf_path=None, aoi_path=None, tasks_path=None):
    """Main entrypoint for the local pipeline."""
    print("==================================================")
    print(" Starting Standalone Offline QA Pipeline")
    print("==================================================")

    pbf_path = resolve_path(pbf_path)
    aoi_path = resolve_path(aoi_path)
    tasks_path = resolve_path(tasks_path)

    if not pbf_path:
        pbf_path = auto_detect_pbf()

    if not pbf_path or not os.path.exists(pbf_path):
        raise Exception("No .osm.pbf file found.")

    if not aoi_path:
        aoi_path = os.path.join(WORK_DIR, "project_aoi.geojson")

    if not os.path.exists(aoi_path):
        raise Exception("AOI GeoJSON file not found.")

    if not tasks_path:
        tasks_path = os.path.join(WORK_DIR, "project_tasks.geojson")

    print(f"  -> PBF File : {os.path.basename(pbf_path)}")
    print(f"  -> AOI File : {os.path.basename(aoi_path)}")
    if os.path.exists(tasks_path):
        print(f"  -> Grid File: {os.path.basename(tasks_path)}")

    clip_pbf_with_osmium(aoi_path, pbf_path)
    run_josm_qa_bot()

    errors_path = os.path.join(WORK_DIR, "qa_errors.geojson")
    aggregate_errors_to_tasks(tasks_path, errors_path)

    print("\n[+] LOCAL PIPELINE COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    pbf_arg = sys.argv[1] if len(sys.argv) > 1 else None
    aoi_arg = sys.argv[2] if len(sys.argv) > 2 else None
    tasks_arg = sys.argv[3] if len(sys.argv) > 3 else None

    run_local_pipeline(pbf_arg, aoi_arg, tasks_arg)