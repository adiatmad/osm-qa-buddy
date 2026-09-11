import json
import tempfile
import unittest
from pathlib import Path

from preflight import normalize_aoi_for_osmium


class PreflightTests(unittest.TestCase):
    def test_normalize_aoi_preserves_osmium_first_feature_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "aoi.geojson"
            normalized = tmp_path / "normalized.geojson"
            first = {
                "type": "Feature",
                "properties": {"name": "first"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                },
            }
            second = {
                "type": "Feature",
                "properties": {"name": "second"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 10]]],
                },
            }
            source.write_text(json.dumps({"type": "FeatureCollection", "features": [first, second]}), encoding="utf-8")

            normalize_aoi_for_osmium(str(source), str(normalized))
            result = json.loads(normalized.read_text(encoding="utf-8"))

            self.assertEqual(result["geometry"], first["geometry"])
            self.assertEqual(result["properties"], first["properties"])
            self.assertNotIn("second", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
