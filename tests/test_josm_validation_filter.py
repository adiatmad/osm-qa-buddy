import unittest

from josm_validation_filter import filter_josm_findings, is_target_josm_finding


def finding(analyser, title, message=""):
    return {
        "analyser": analyser,
        "rule": analyser,
        "rule_detail": title,
        "message": message,
    }


class JosmValidationFilterTests(unittest.TestCase):
    def test_keeps_building_findings(self):
        self.assertTrue(is_target_josm_finding(finding("RightAngleBuildingTest", "Building has an unusual angle")))
        self.assertTrue(is_target_josm_finding(finding("MapCSSTagChecker", "Building has an unusual shape")))
        self.assertTrue(is_target_josm_finding(finding("MapCSSTagChecker", "Custom Bot Rule (Oversize)", "This building is too large")))

    def test_keeps_highway_findings(self):
        self.assertTrue(is_target_josm_finding(finding("CrossingWays", "Crossing highway", "Highway crosses another way")))
        self.assertTrue(is_target_josm_finding(finding("MapCSSTagChecker", "Highway validation", "Road has a tagging problem")))

    def test_keeps_requested_generic_rules(self):
        self.assertTrue(is_target_josm_finding(finding("TagChecker", "Missing tag")))
        self.assertTrue(is_target_josm_finding(finding("DuplicateNode", "Duplicate nodes")))

    def test_excludes_address_even_when_building_is_mentioned(self):
        self.assertFalse(is_target_josm_finding(finding("Addresses", "Building address problem", "Address is incomplete")))

    def test_excludes_unrelated_feature_rules(self):
        self.assertFalse(is_target_josm_finding(finding("CrossingWays", "Crossing waterways", "Waterway crosses another way")))
        self.assertFalse(is_target_josm_finding(finding("PowerLines", "Power line crossing", "Power line problem")))

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
