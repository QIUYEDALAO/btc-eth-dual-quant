from __future__ import annotations

import copy
import unittest

from scripts.adr0015_independent_auditor_review_check import (
    DIMENSIONS, IMPLEMENTATION_HASH, PROTOCOL_HASH, TARGET_COMMIT,
    build_document, render, validate_document, validate_target,
)


class Adr0015IndependentAuditorReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = build_document("2026-07-18T00:00:00Z")

    def test_exact_target_and_all_hashes_are_bound(self):
        self.assertEqual(self.document["target_commit"], TARGET_COMMIT)
        self.assertEqual(self.document["protocol_content_hash"], PROTOCOL_HASH)
        self.assertEqual(self.document["implementation_content_hash"], IMPLEMENTATION_HASH)
        self.assertEqual(validate_target(), [])

    def test_all_review_dimensions_pass(self):
        self.assertEqual(len(self.document["review_dimensions"]), len(DIMENSIONS))
        self.assertTrue(all(item["status"] == "pass" for item in self.document["review_dimensions"]))

    def test_approve_requires_zero_critical_and_high(self):
        changed = copy.deepcopy(self.document)
        changed["remaining_high_findings"] = 1
        self.assertIn("approve requires zero remaining critical/high findings", validate_document(changed))

    def test_only_real_audit_is_authorized(self):
        self.assertTrue(self.document["full_independent_audit_run_authorized"])
        enabled = [name for name, value in self.document["authorizations"].items() if value]
        self.assertEqual(enabled, ["full_independent_audit_run"])

    def test_generated_time_does_not_change_review_identity(self):
        other = build_document("2030-01-01T00:00:00Z")
        self.assertEqual(self.document["review_content_hash"], other["review_content_hash"])

    def test_report_is_deterministic(self):
        self.assertEqual(render(self.document), render(self.document))
        self.assertIn("Remaining critical/high: `0 / 0`", render(self.document))


if __name__ == "__main__":
    unittest.main()
