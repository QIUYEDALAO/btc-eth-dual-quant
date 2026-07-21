from __future__ import annotations

import copy
import json
import unittest

from scripts.u18_cross_sectional_paper_protocol_review_check import EXPECTED, REVIEW, validate


class U18ReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(REVIEW.read_text())

    def test_exact(self):
        self.assertEqual(self.review["review_content_hash"], EXPECTED)
        self.assertEqual(validate(self.review, True), [])

    def test_generated_time_excluded(self):
        review = copy.deepcopy(self.review)
        review["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(review), [])

    def test_target_or_dimension_tamper(self):
        review = copy.deepcopy(self.review)
        review["target"]["head_sha"] = "0" * 40
        self.assertTrue(validate(review))
        review = copy.deepcopy(self.review)
        review["review_dimensions"]["tail_energy_and_single_point_dominance"] = "fail"
        self.assertTrue(validate(review))

    def test_escalation(self):
        review = copy.deepcopy(self.review)
        review["authorization_after_review"]["event_scan"] = True
        self.assertTrue(validate(review))


if __name__ == "__main__":
    unittest.main()
