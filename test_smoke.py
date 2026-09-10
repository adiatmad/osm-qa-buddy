import json
import tempfile
from pathlib import Path

from orchestrator import aggregate_errors_to_tasks
from report import generate_report


def feature(geometry, properties=None):
    return {"type": "Feature", "properties": properties or {}, "geometry": geometry}


def test_task_aggregation_and_report():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tasks = tmp_path / "tasks.geojson"
        errors = tmp_path / "qa_errors.geojson"
        report = tmp_path / "report.html"
        map_path = tmp_path / "map.html"
        metadata = tmp_path / "run_metadata.json"
        tasks_data = {"type": "FeatureCollection", "features": [
            feature({"type": "Polygon", "coordinates": [[[0,0],[2,0],[2,2],[0,2],[0,0]]]}, {"taskId": 56, "taskStatus": "VALIDATED"}),
            feature({"type": "Polygon", "coordinates": [[[2,0],[4,0],[4,2],[2,2],[2,0]]]}, {"taskId": 23, "taskStatus": "BADIMAGERY"}),
        ]}
        errors_data = {"type": "FeatureCollection", "features": [
            feature({"type":"Point","coordinates":[0.5,0.5]}, {"severity":"Errors","object_id":"way/1","rule":"MapCSS","message":"Example issue"}),
            feature({"type":"Point","coordinates":[0.5,0.5]}, {"severity":"Errors","object_id":"way/1","rule":"MapCSS","message":"Example issue"}),
            feature({"type":"Point","coordinates":[1,1]}, {"severity":"Warnings","object_id":"way/1","rule":"MapCSS","message":"Another issue"}),
            feature({"type":"Point","coordinates":[1.5,1.5]}, {"severity":"Warnings","object_id":"node/2","rule":"TagChecker","message":"Tag issue"}),
            feature({"type":"Point","coordinates":[10,10]}, {"severity":"Warnings","object_id":"way/99","rule":"MapCSS","message":"Outside task grid"}),
        ]}
        metadata_data = {
            "qa_buddy_version": "0.1.0",
            "project_id": "63564",
            "run_started_utc": "2026-09-09T00:00:00+00:00",
            "validation_engine": "JOSM headless validator",
            "toolchain": {"josm_tested_version": "19613", "jython_version": "2.7.3", "java_runtime": "OpenJDK", "osmium_version": "osmium-tool"},
            "inputs": {"project_boundary": {"filename": "project-aoi.geojson", "size_bytes": 123, "sha256": "abc123"}},
            "human_review_required": True,
        }
        tasks.write_text(json.dumps(tasks_data), encoding="utf-8")
        errors.write_text(json.dumps(errors_data), encoding="utf-8")
        metadata.write_text(json.dumps(metadata_data), encoding="utf-8")

        import orchestrator
        original_work_dir = orchestrator.WORK_DIR
        orchestrator.WORK_DIR = str(tmp_path)
        try:
            summary = aggregate_errors_to_tasks(str(tasks), str(errors))
            result = json.loads(Path(summary).read_text(encoding="utf-8"))
            props = result["features"][0]["properties"]
            bad_props = result["features"][1]["properties"]
            assert props["qa_finding_count"] == 4
            assert props["qa_unique_finding_count"] == 3
            assert props["qa_unique_osm_object_count"] == 2
            assert props["qa_rules_involved"] == ["MapCSS", "TagChecker"]
            assert props["qa_error_count"] == 2
            assert props["qa_warning_count"] == 2
            assert props["qa_task_status"] == "VALIDATED"
            assert props["qa_badimagery"] is False
            assert props["qa_priority"] == "MEDIUM"
            assert bad_props["qa_task_status"] == "BADIMAGERY"
            assert bad_props["qa_badimagery"] is True
            assert bad_props["qa_unique_finding_count"] == 0
            assert bad_props["qa_priority"] == "HIGH"
            assert result["qa_summary"]["raw_josm_finding_count"] == 5
            assert result["qa_summary"]["task_associated_finding_count"] == 4
            assert result["qa_summary"]["unassigned_finding_count"] == 1
            assert result["qa_summary"]["task_associated_unique_finding_count"] == 3
            generate_report(str(errors), str(summary), str(report), str(map_path), str(metadata))
            html = report.read_text(encoding="utf-8")
            map_html = map_path.read_text(encoding="utf-8")
            assert "Errors:</b> 2" in html
            assert "warning" in html.lower()
            assert "BADIMAGERY tasks</div>" in html
            assert "1 task marked BADIMAGERY" in html
            assert "Tasks requiring review" in html
            assert "Unique OSM objects" in html
            assert "Human review required" in html
            assert "JOSM tested version: 19613" in html
            assert "63564" in html
            assert "abc123" in html
            assert "BADIMAGERY" in map_html
            assert "qa_task_status" in map_html
            assert "Unique OSM objects:" in map_html
        finally:
            orchestrator.WORK_DIR = original_work_dir


if __name__ == "__main__":
    test_task_aggregation_and_report()
    print("Smoke tests passed.")
