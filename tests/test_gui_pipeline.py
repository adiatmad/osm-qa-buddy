import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


VALIDATION_XML = """<?xml version='1.0' encoding='UTF-8'?>
<analysers generator='JOSM'>
  <analyser name='CrossingWays'>
    <class id='1' level='1'><classtext lang='en' title='Crossing ways'/></class>
    <error class='1'><location lat='0.5' lon='0.5'/><way id='200'/><text lang='en' value='Ways cross'/></error>
  </analyser>
</analysers>
"""


class GuiPipelineTests(unittest.TestCase):
    def test_finalizes_when_xml_is_already_in_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work_dir = root / "work"
            output_dir = root / "output"
            work_dir.mkdir()
            output_dir.mkdir()
            tasks_path = root / "tasks.geojson"
            tasks_path.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                    "properties": {"taskId": 1, "taskStatus": "VALIDATED"},
                }],
            }), encoding="utf-8")
            # The XML finding is a generic CrossingWays test. The prepared
            # object must be a highway so the thematic filter keeps it.
            (work_dir / "sample.osm").write_text(
                "<osm version='0.6'><way id='200'><tag k='highway' v='residential'/></way></osm>",
                encoding="utf-8",
            )
            (work_dir / "run_metadata.json").write_text(json.dumps({
                "validation_engine": "JOSM GUI Validator + native Validation errors XML export",
                "human_review_required": True,
            }), encoding="utf-8")
            xml_path = output_dir / "validation_errors.xml"
            xml_path.write_text(VALIDATION_XML, encoding="utf-8")

            sys.modules.pop("orchestrator", None)
            import gui_pipeline

            with patch.dict(os.environ, {"QABOT_WORK_DIR": str(work_dir)}):
                gui_pipeline.finalize_gui_run(tasks_path, xml_path, output_dir)

            self.assertEqual(xml_path.read_text(encoding="utf-8"), VALIDATION_XML)
            for name in (
                "qa_errors.geojson",
                "task_grid_qa_summary.geojson",
                "sample.osm",
                "report.html",
                "map.html",
                "run_metadata.json",
            ):
                self.assertTrue((output_dir / name).is_file(), name)
            errors = json.loads((output_dir / "qa_errors.geojson").read_text(encoding="utf-8"))
            self.assertEqual(errors["features"][0]["properties"]["severity"], "ERROR")

            xml_path.write_text("<analysers generator='JOSM'/>", encoding="utf-8")
            gui_pipeline.finalize_gui_run(tasks_path, xml_path, output_dir)
            empty_errors = json.loads((output_dir / "qa_errors.geojson").read_text(encoding="utf-8"))
            self.assertEqual(empty_errors["features"], [])

    def test_requires_metadata_from_prepare_before_writing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work_dir = root / "work"
            output_dir = root / "output"
            work_dir.mkdir()
            output_dir.mkdir()
            xml_path = output_dir / "validation_errors.xml"
            xml_path.write_text(VALIDATION_XML, encoding="utf-8")

            sys.modules.pop("orchestrator", None)
            import gui_pipeline

            with patch.dict(os.environ, {"QABOT_WORK_DIR": str(work_dir)}):
                with self.assertRaisesRegex(RuntimeError, "Run 'prepare' first"):
                    gui_pipeline.finalize_gui_run(root / "tasks.geojson", xml_path, output_dir)

            self.assertFalse((work_dir / "qa_errors.geojson").exists())


if __name__ == "__main__":
    unittest.main()
