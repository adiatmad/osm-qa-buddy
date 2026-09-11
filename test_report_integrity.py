import json
import tempfile
import unittest
from pathlib import Path

from report import generate_report


class ReportIntegrityTest(unittest.TestCase):
    def test_report_counts_raw_unique_findings_including_unassigned(self):
        point = lambda x, y: {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [x, y]},
            "properties": {
                "severity": "Warnings",
                "rule": "Test rule",
                "message": "Same issue",
                "object_id": "way/1",
            },
        }
        errors = {"type": "FeatureCollection", "features": [point(0, 0), point(0, 0), point(2, 2)]}
        task = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[ -1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
            },
            "properties": {
                "taskId": 1,
                "taskStatus": "VALIDATED",
            },
        }
        tasks = {"type": "FeatureCollection", "features": [task]}

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            errors_path = tmp / "qa_errors.geojson"
            tasks_path = tmp / "tasks.geojson"
            report_path = tmp / "report.html"
            map_path = tmp / "map.html"
            errors_path.write_text(json.dumps(errors), encoding="utf-8")
            tasks_path.write_text(json.dumps(tasks), encoding="utf-8")

            generate_report(errors_path, tasks_path, report_path, map_path)
            html = report_path.read_text(encoding="utf-8")

            self.assertIn("Raw QA findings</div><div class=\"value\">3", html)
            self.assertIn("Unique findings</div><div class=\"value\">2", html)
            self.assertIn("1 are exact duplicates", html)


if __name__ == "__main__":
    unittest.main()
