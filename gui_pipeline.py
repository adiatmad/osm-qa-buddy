"""Interactive JOSM GUI validation bridge.

This module deliberately does not run JOSM's validator. Normal JOSM GUI owns
validation and its rule configuration. QA Buddy prepares the clipped dataset,
then consumes JOSM's native Validation errors XML export.
"""

from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _load_components():
    # orchestrator reads WORK_DIR at import time, so the caller must set it first.
    from orchestrator import (
        WORK_DIR,
        aggregate_errors_to_tasks,
        clip_pbf_with_osmium,
        generate_report,
        _osmium_fileinfo,
        _update_run_metadata,
        validate_inputs,
        write_run_metadata,
    )
    from josm_validation_xml import parse_josm_validation_xml, write_geojson

    return {
        "WORK_DIR": WORK_DIR,
        "aggregate_errors_to_tasks": aggregate_errors_to_tasks,
        "clip_pbf_with_osmium": clip_pbf_with_osmium,
        "generate_report": generate_report,
        "osmium_fileinfo": _osmium_fileinfo,
        "update_run_metadata": _update_run_metadata,
        "validate_inputs": validate_inputs,
        "write_run_metadata": write_run_metadata,
        "parse_josm_validation_xml": parse_josm_validation_xml,
        "write_geojson": write_geojson,
    }


def prepare_gui_run(pbf_path, tasks_path, output_dir, project_id=None):
    c = _load_components()
    work_dir = c["WORK_DIR"]
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    preflight = c["validate_inputs"](tasks_path, pbf_path, check_pbf=True)
    for check in preflight["checks"]:
        print(("PASS: " if check["ok"] else "FAIL: ") + check["message"])
    if not preflight["ok"]:
        raise RuntimeError("Pre-flight validation failed. Fix the selected input files and try again.")

    run_started_utc = datetime.now(timezone.utc).isoformat()
    metadata_path = os.path.join(work_dir, "run_metadata.json")
    c["write_run_metadata"](
        tasks_path,
        pbf_path,
        metadata_path,
        run_started_utc,
        ram_gb=None,
        project_id=project_id,
    )
    c["update_run_metadata"](
        metadata_path,
        validation_engine="JOSM GUI Validator + native Validation errors XML export",
        workflow_mode="interactive_gui",
        human_validation_required=True,
    )

    for src, name in ((tasks_path, "project_tasks.geojson"), (pbf_path, "region.osm.pbf")):
        dst = os.path.join(work_dir, name)
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copy2(src, dst)

    tasks = os.path.join(work_dir, "project_tasks.geojson")
    pbf = os.path.join(work_dir, "region.osm.pbf")
    sample_path = c["clip_pbf_with_osmium"](tasks, pbf)
    c["update_run_metadata"](
        metadata_path,
        extracted_dataset={
            "path": sample_path,
            "size_bytes": os.path.getsize(sample_path),
            "osmium_fileinfo": c["osmium_fileinfo"](sample_path),
        },
        validation_status="awaiting_josm_gui_export",
    )

    output_sample = os.path.join(output_dir, "sample.osm")
    shutil.copy2(sample_path, output_sample)
    shutil.copy2(metadata_path, os.path.join(output_dir, "run_metadata.json"))
    print("[+] GUI VALIDATION PREPARED")
    print(f"[+] JOSM DATASET: {output_sample}")
    print("[+] NEXT: Open the dataset in normal JOSM, run Validator, then save the Validation errors layer as XML.")
    return output_sample


def finalize_gui_run(tasks_path, validation_xml_path, output_dir):
    c = _load_components()
    work_dir = c["WORK_DIR"]
    os.makedirs(work_dir, exist_ok=True)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    xml_path = Path(validation_xml_path)
    if not xml_path.is_file():
        raise FileNotFoundError(f"JOSM validation XML not found: {xml_path}")

    findings = c["parse_josm_validation_xml"](xml_path)
    errors_path = os.path.join(work_dir, "qa_errors.geojson")
    c["write_geojson"](findings, errors_path)

    summary_path = c["aggregate_errors_to_tasks"](tasks_path, errors_path)
    report_path = os.path.join(work_dir, "report.html")
    map_path = os.path.join(work_dir, "map.html")
    metadata_path = os.path.join(work_dir, "run_metadata.json")
    c["update_run_metadata"](
        metadata_path,
        validation_status="completed",
        validation_xml={
            "filename": xml_path.name,
            "path": str(xml_path.resolve()),
            "size_bytes": xml_path.stat().st_size,
        },
        josm_finding_count=len(findings),
    )
    c["generate_report"](errors_path, summary_path, report_path, map_path, metadata_path)

    for name in (
        "qa_errors.geojson",
        "task_grid_qa_summary.geojson",
        "sample.osm",
        "sample.osm.ready.json",
        "report.html",
        "map.html",
        "run_metadata.json",
    ):
        src = os.path.join(work_dir, name)
        destination = os.path.join(output_dir, name)
        if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(destination):
            shutil.copy2(src, destination)
    destination_xml = os.path.join(output_dir, "validation_errors.xml")
    if xml_path.resolve() != Path(destination_xml).resolve():
        shutil.copy2(xml_path, destination_xml)

    print(f"[+] JOSM FINDINGS: {len(findings)}")
    print(f"[+] SUMMARY: {summary_path}")
    print(f"[+] REPORT: {report_path}")
    print(f"[+] MAP: {map_path}")
    print("[+] GUI PIPELINE SUCCEEDED")
    return errors_path, summary_path, report_path, map_path


def main():
    parser = argparse.ArgumentParser(description="OSM QA Buddy interactive JOSM GUI bridge")
    parser.add_argument("mode", choices=("prepare", "finalize"))
    parser.add_argument("pbf_or_tasks")
    parser.add_argument("tasks_or_xml")
    parser.add_argument("output_dir")
    parser.add_argument("--project-id", default=None)
    args = parser.parse_args()

    if args.mode == "prepare":
        prepare_gui_run(args.pbf_or_tasks, args.tasks_or_xml, args.output_dir, project_id=args.project_id)
    else:
        finalize_gui_run(args.pbf_or_tasks, args.tasks_or_xml, args.output_dir)


if __name__ == "__main__":
    main()
