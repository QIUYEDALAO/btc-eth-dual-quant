from __future__ import annotations

import copy
import json
import unittest

from scripts.u11_cross_sectional_paper_protocol_review_check import EVIDENCE, REPORT, validate


class U11ProtocolReviewTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(EVIDENCE.read_text())
        self.report = REPORT.read_text()

    def test_exact_review(self):
        self.assertEqual(validate(self.document, self.report), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.document)
        changed["generated_utc"] = "2030"
        self.assertEqual(validate(changed, self.report), [])

    def test_target_or_verdict_tamper_fails(self):
        for key, value in (("target_commit", "0" * 40), ("remaining_high_findings", 1), ("target_modified", True)):
            changed = copy.deepcopy(self.document)
            changed[key] = value
            self.assertTrue(validate(changed, self.report), key)

    def test_permission_escalation_fails(self):
        changed = copy.deepcopy(self.document)
        changed["authorizations"]["event_scan"] = True
        self.assertTrue(validate(changed, self.report))


if __name__ == "__main__":
    unittest.main()
