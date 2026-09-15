import tempfile
import unittest
from pathlib import Path

from josm_validation_filter import filter_josm_findings, is_target_josm_finding, load_osm_feature_tags


def finding(analyser, title, message="", object_ids=None):
    object_ids = object_ids or ["way/1"]
    return {
        "analyser": analyser,
        "rule": analyser,
        "rule_detail": title,
        "message": message,
        "object_id": object_ids[0],
        "object_ids": object_ids,
    }


class JosmValidationFilterTests(unittest.TestCase):
    def test_keeps_building_findings(self):
        self.assertTrue(is_target_josm_finding(finding("RightAngleBuildingTest", "Building has an unusual angle")))
        self.assertTrue(is_target_josm_finding(finding("MapCSSTagChecker", "Building has an unusual shape")))
        self.assertTrue(is_target_josm_finding(finding("MapCSSTagChecker", "Custom Bot Rule (Oversize)", "This building is too large")))

    def test_keeps_highway_findings(self):
        self.assertTrue(is_target_josm_finding(finding("CrossingWays", "Crossing highway", "Highway crosses another way")))
        self.assertTrue(is_target_josm_finding(finding("Highways", "Highway validation", "Highway has a problem")))
        self.assertTrue(is_target_josm_finding(finding("SharpAngles", "Sharp angles on roads", "Sharp angle")))

    def test_uses_affected_object_tags_for_generic_geometry_rules(self):
        osm = """<osm version='0.6'>
          <way id='10'><tag k='highway' v='residential'/></way>
          <way id='20'><tag k='waterway' v='stream'/></way>
          <way id='30'><tag k='building' v='yes'/></way>
        </osm>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.osm"
            path.write_text(osm, encoding="utf-8")
            tags, members = load_osm_feature_tags(path)
            self.assertTrue(is_target_josm_finding(finding("CrossingWays", "Crossing ways", "Ways cross", ["way/10"]), tags, members))
            self.assertFalse(is_target_josm_finding(finding("CrossingWays", "Crossing ways", "Ways cross", ["way/20"]), tags, members))
            self.assertTrue(is_target_josm_finding(finding("SelfIntersectingWay", "Self-intersecting way", "Geometry problem", ["way/30"]), tags, members))

    def test_relation_members_can_identify_building(self):
        osm = """<osm version='0.6'>
          <way id='30'><tag k='building' v='yes'/></way>
          <relation id='40'><member type='way' ref='30' role='outer'/><tag k='type' v='multipolygon'/></relation>
        </osm>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.osm"
            path.write_text(osm, encoding="utf-8")
            tags, members = load_osm_feature_tags(path)
            self.assertTrue(is_target_josm_finding(finding("SelfIntersectingWay", "Geometry problem", "Geometry problem", ["relation/40"]), tags, members))

    def test_keeps_requested_generic_rules(self):
        self.assertTrue(is_target_josm_finding(finding("TagChecker", "Missing tag")))
        self.assertTrue(is_target_josm_finding(finding("DuplicateNode", "Duplicate nodes")))
        self.assertTrue(is_target_josm_finding(finding("TagChecker", "Address tagging issue", "addr:street missing")))

    def test_excludes_address_rule(self):
        self.assertFalse(is_target_josm_finding(finding("Addresses", "House number without street", "Address is incomplete")))
        self.assertFalse(is_target_josm_finding(finding("MapCSSTagChecker", "Address rule", "Address is incomplete", ["way/1"])))

    def test_excludes_unrelated_feature_rules(self):
        self.assertFalse(is_target_josm_finding(finding("CrossingWays", "Crossing waterways", "Waterway crosses another way")))
        self.assertFalse(is_target_josm_finding(finding("PowerLines", "Power line crossing", "Power line problem")))

    def test_ambiguous_words_do_not_keep_unrelated_rules_without_tags(self):
        self.assertFalse(is_target_josm_finding(finding("SomeTest", "Street geometry problem")))
        self.assertFalse(is_target_josm_finding(finding("SomeTest", "Path geometry problem")))

    def test_filter_reports_removed_count(self):
        findings = [
            finding("RightAngleBuildingTest", "Building has an unusual angle"),
            finding("Addresses", "Building address problem", "Address is incomplete"),
            finding("DuplicateNode", "Duplicate nodes"),
            finding("CrossingWays", "Crossing waterways", "Waterway crosses another way"),
        ]
        kept, removed = filter_josm_findings(findings)
        self.assertEqual(len(kept), 2)
        self.assertEqual(removed, 2)


if __name__ == "__main__":
    unittest.main()
