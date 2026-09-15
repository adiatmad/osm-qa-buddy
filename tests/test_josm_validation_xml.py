import tempfile
import unittest
from pathlib import Path

from josm_validation_xml import parse_josm_validation_xml, write_geojson


FIXTURE = """<?xml version='1.0' encoding='UTF-8'?>
<analysers generator='JOSM' timestamp='2026-09-15T00:00:00Z'>
  <analyser timestamp='2026-09-15T00:00:00Z' name='CrossingWays'>
    <class id='1' level='1'>
      <classtext lang='en' title='Crossing ways'/>
    </class>
    <class id='2' level='2'>
      <classtext lang='en' title='Crossing buildings'/>
    </class>
    <class id='3' level='3'>
      <classtext lang='en' title='Potentially disconnected way'/>
    </class>
    <error class='1'>
      <location lat='-6.2000' lon='106.8000'/>
      <node id='100' lat='-6.2000' lon='106.8000'/>
      <way id='200'>
        <nd ref='100'/>
        <nd ref='101'/>
      </way>
      <text lang='en' value='Ways cross'/>
    </error>
    <error class='2'>
      <location lat='-6.2010' lon='106.8010'/>
      <way id='300'>
        <nd ref='102'/>
        <nd ref='103'/>
      </way>
      <text lang='en' value='Building crosses highway'/>
    </error>
    <error class='3'>
      <location lat='-6.2020' lon='106.8020'/>
      <relation id='400'>
        <member type='way' ref='300' role=''/>
      </relation>
      <text lang='en' value='Check connection'/>
    </error>
  </analyser>
</analysers>
"""

DUPLICATE_FIXTURE = """<?xml version='1.0' encoding='UTF-8'?>
<analysers generator='JOSM'>
  <analyser name='CrossingWays'>
    <class id='1' level='1'><classtext lang='en' title='Crossing ways'/></class>
    <error class='1'><location lat='-6.2' lon='106.8'/><way id='200'/><text lang='en' value='Ways cross'/></error>
    <error class='1'><location lat='-6.2' lon='106.8'/><way id='200'/><text lang='en' value='Ways cross'/></error>
  </analyser>
</analysers>
"""

INCOMPLETE_FIXTURE = """<?xml version='1.0' encoding='UTF-8'?>
<analysers generator='JOSM'>
  <analyser name='CrossingWays'>
    <class id='1' level='1'><classtext lang='en' title='Crossing ways'/></class>
    <error class='1'><way id='200'/><text lang='en' value='Ways cross'/></error>
  </analyser>
</analysers>
"""


class JosmValidationXmlTests(unittest.TestCase):
    def test_parses_severity_location_and_all_affected_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "validation_errors.xml"
            path.write_text(FIXTURE, encoding="utf-8")
            findings = parse_josm_validation_xml(path)

        self.assertEqual(len(findings), 3)
        self.assertEqual(findings[0]["severity"], "ERROR")
        self.assertEqual(findings[0]["rule"], "CrossingWays")
        self.assertEqual(findings[0]["rule_detail"], "Crossing ways")
        self.assertEqual(findings[0]["message"], "Ways cross")
        self.assertEqual(findings[0]["coordinates"], [106.8, -6.2])
        self.assertEqual(findings[0]["object_id"], "node/100")
        self.assertEqual(findings[0]["object_ids"], ["node/100", "way/200"])
        self.assertEqual(findings[1]["severity"], "WARNING")
        self.assertEqual(findings[1]["object_ids"], ["way/300"])
        self.assertEqual(findings[2]["severity"], "OTHER")
        self.assertEqual(findings[2]["object_ids"], ["relation/400"])

    def test_writes_existing_geojson_finding_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "validation_errors.xml"
            geojson_path = Path(directory) / "qa_errors.geojson"
            xml_path.write_text(FIXTURE, encoding="utf-8")
            findings = parse_josm_validation_xml(xml_path)
            write_geojson(findings, geojson_path)
            text = geojson_path.read_text(encoding="utf-8")

        self.assertIn('"FeatureCollection"', text)
        self.assertIn('"object_ids"', text)
        self.assertIn('"severity": "ERROR"', text)
        self.assertIn('"rule_detail": "Crossing ways"', text)

    def test_rejects_non_josm_root(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not_josm.xml"
            path.write_text("<osm/>", encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_josm_validation_xml(path)

    def test_empty_josm_export_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "validation_errors.xml"
            path.write_text("<analysers generator='JOSM'/>", encoding="utf-8")
            self.assertEqual(parse_josm_validation_xml(path), [])

    def test_deduplicates_exact_repeated_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "validation_errors.xml"
            path.write_text(DUPLICATE_FIXTURE, encoding="utf-8")
            findings = parse_josm_validation_xml(path)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["object_ids"], ["way/200"])

    def test_rejects_malformed_or_incomplete_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            malformed = directory_path / "malformed.xml"
            incomplete = directory_path / "incomplete.xml"
            malformed.write_text("<analysers generator='JOSM'>", encoding="utf-8")
            incomplete.write_text(INCOMPLETE_FIXTURE, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JOSM Validation errors XML"):
                parse_josm_validation_xml(malformed)
            with self.assertRaisesRegex(ValueError, "missing a valid location"):
                parse_josm_validation_xml(incomplete)
            with self.assertRaises(FileNotFoundError):
                parse_josm_validation_xml(directory_path / "missing.xml")


if __name__ == "__main__":
    unittest.main()

