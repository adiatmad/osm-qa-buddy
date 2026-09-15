import json
import tempfile
import unittest
from pathlib import Path

from preflight import normalize_task_grid_for_osmium, validate_task_grid_input


class PreflightTests(unittest.TestCase):
    def test_normalize_task_grid_unions_all_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "tasks.geojson"
            normalized = tmp_path / "normalized.geojson"
            first = {
                "type": "Feature",
                "properties": {"taskId": 1},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                },
            }
            second = {
                "type": "Feature",
                "properties": {"taskId": 2},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 10]]],
                },
            }
            source.write_text(json.dumps({"type": "FeatureCollection", "features": [first, second]}), encoding="utf-8")

            normalize_task_grid_for_osmium(str(source), str(normalized))
            result = json.loads(normalized.read_text(encoding="utf-8"))

            self.assertEqual(result["properties"]["feature_count"], 2)
            self.assertEqual(result["geometry"]["type"], "MultiPolygon")
            self.assertEqual(len(result["geometry"]["coordinates"]), 2)

    def test_validate_task_grid_requires_polygon_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tasks.geojson"
            source.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                }],
            }), encoding="utf-8")

            result = validate_task_grid_input(str(source))
            self.assertFalse(result["ok"])
            self.assertIn("Polygon/MultiPolygon", result["checks"][-1]["message"])


if __name__ == "__main__":
    unittest.main()
