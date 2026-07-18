from __future__ import annotations

import copy
import json
import unittest

from scripts.u20_cross_sectional_paper_protocol_review_check import EXPECTED, REVIEW, validate


class U20ReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(REVIEW.read_text())

    def test_exact(self):
        self.assertEqual(self.review["review_content_hash"], EXPECTED)
        self.assertEqual(validate(self.review, True), [])

    def test_generated_time_excluded(self):
        review = copy.deepcopy(self.review)
        review["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(review), [])

    def test_target_blob_or_dimension_tamper(self):
        review = copy.deepcopy(self.review)
        review["target"]["head_sha"] = "0" * 40
        self.assertTrue(validate(review))
        review = copy.deepcopy(self.review)
        review["target"]["files"]["config/u20_cross_sectional_paper_protocol_v1.json"] = "0" * 64
        self.assertTrue(validate(review, True))
        review = copy.deepcopy(self.review)
        review["review_dimensions"]["two_half_cross_sectional_bottom_quarter_persistence"] = "fail"
        self.assertTrue(validate(review))

    def test_verdict_or_escalation_tamper(self):
        review = copy.deepcopy(self.review)
        review["critical_findings"] = 1
        self.assertTrue(validate(review))
        for key in ("return_common_adjustment_coskewness_scan", "event_scan", "formal_returns", "oos", "m2"):
            review = copy.deepcopy(self.review)
            review["authorization_after_review"][key] = True
            self.assertTrue(validate(review), key)


if __name__ == "__main__":
    unittest.main()
