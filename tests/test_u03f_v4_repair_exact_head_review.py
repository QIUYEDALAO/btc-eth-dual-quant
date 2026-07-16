from __future__ import annotations

import copy
import unittest

from scripts.u03f_v4_repair_exact_head_review_check import (
    AUTHORIZATION,
    CHANGED_FILE_LIST_HASH,
    IMPLEMENTATION_HASH,
    REVIEW_DIMENSIONS,
    TARGET_HEAD,
    build_document,
    render,
    target_available,
    validate_context,
    validate_document,
    validate_target,
)


class U03FV4RepairExactHeadReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = build_document("2026-07-16T15:10:00Z")

    def test_exact_target_and_all_review_dimensions_are_bound(self) -> None:
        target = self.document["reviewed_target"]
        self.assertEqual(target["head_sha"], TARGET_HEAD)
        self.assertEqual(target["changed_file_list_sha256"], CHANGED_FILE_LIST_HASH)
        self.assertEqual(target["repair_implementation_sha256"], IMPLEMENTATION_HASH)
        self.assertEqual(
            {item["dimension"] for item in self.document["review_dimensions"]},
            set(REVIEW_DIMENSIONS),
        )
        self.assertEqual(validate_document(self.document), [])

    def test_approve_requires_zero_critical_high_and_all_checks_pass(self) -> None:
        self.assertEqual(self.document["verdict"], "approve")
        self.assertEqual(self.document["remaining_findings"]["critical"], [])
        self.assertEqual(self.document["remaining_findings"]["high"], [])
        changed = copy.deepcopy(self.document)
        changed["remaining_findings"]["high"] = ["drift"]
        self.assertIn("review evidence is not the deterministic exact-head document", validate_document(changed))
        self.assertIn("approve requires zero remaining critical/high findings", validate_document(changed))

    def test_three_review_findings_are_resolved_not_waived(self) -> None:
        resolved = self.document["resolved_during_review"]
        self.assertEqual([item["id"] for item in resolved], ["U03F-RR-H01", "U03F-RR-H02", "U03F-RR-H03"])
        self.assertTrue(all(item["severity"] == "high" and item["resolution"] for item in resolved))

    def test_downstream_authorizations_remain_false(self) -> None:
        self.assertEqual(self.document["authorization"], AUTHORIZATION)
        for key, value in AUTHORIZATION.items():
            if key != "merge_exact_implementation_after_review":
                self.assertFalse(value, key)

    def test_report_is_a_deterministic_evidence_render(self) -> None:
        report = render(self.document)
        self.assertEqual(report, render(self.document))
        self.assertIn("Remaining critical/high: `0 / 0`", report)
        self.assertIn("GitHub exact-head checks: 110/110", report)
        self.assertIn("Public requalification executed: no", report)

    def test_all_six_context_files_record_the_review(self) -> None:
        self.assertEqual(validate_context(), [])

    def test_exact_target_static_review_passes_when_fetched(self) -> None:
        if not target_available():
            self.skipTest("exact implementation target is fetched by the review workflow")
        self.assertEqual(validate_target(), [])


if __name__ == "__main__":
    unittest.main()
