from __future__ import annotations

import copy
import json
import unittest

from scripts.adr0015_independent_review_check import (
    AUTHORIZATION,
    CHANGED_FILE_LIST_HASH,
    EVIDENCE,
    MODEL_CONTENT_HASH,
    REVIEW_DIMENSIONS,
    TARGET_HEAD,
    build_document,
    render,
    target_available,
    validate_context,
    validate_document,
    validate_frozen_evidence,
    validate_target,
)


class ADR0015IndependentReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = build_document("2026-07-17T02:20:00Z")

    def test_exact_target_and_review_dimensions_are_bound(self) -> None:
        target = self.document["reviewed_target"]
        self.assertEqual(target["head_sha"], TARGET_HEAD)
        self.assertEqual(target["model_content_sha256"], MODEL_CONTENT_HASH)
        self.assertEqual(target["changed_file_list_sha256"], CHANGED_FILE_LIST_HASH)
        self.assertEqual(
            {item["dimension"] for item in self.document["review_dimensions"]},
            set(REVIEW_DIMENSIONS),
        )

    def test_approve_requires_zero_critical_high_and_all_dimensions_pass(self) -> None:
        self.assertEqual(validate_document(self.document), [])
        changed = copy.deepcopy(self.document)
        changed["remaining_findings"]["high"] = ["drift"]
        self.assertIn("approve requires zero remaining critical/high findings", validate_document(changed))
        changed = copy.deepcopy(self.document)
        changed["review_dimensions"][0]["status"] = "fail"
        self.assertIn("approve requires every review dimension to pass", validate_document(changed))

    def test_only_separate_adoption_consideration_is_authorized(self) -> None:
        self.assertEqual(self.document["authorization"], AUTHORIZATION)
        self.assertTrue(AUTHORIZATION["separate_conditional_adoption_consideration"])
        self.assertFalse(any(value for key, value in AUTHORIZATION.items() if key != "separate_conditional_adoption_consideration"))

    def test_frozen_threshold_and_window_evidence_pass(self) -> None:
        self.assertEqual(validate_frozen_evidence(), [])
        evidence = self.document["validation_evidence"]
        self.assertEqual(evidence["minimum_invalid_active_members"], 2)
        self.assertEqual(evidence["minimum_invalid_active_fraction"], 0.8)
        self.assertEqual(evidence["minimum_observed_window_fraction"], "0.933333333333")
        self.assertEqual(evidence["full_active_windows"], 7)
        self.assertEqual(evidence["valid_minority_windows"], 1)

    def test_report_is_deterministic_and_preserves_zero_authority(self) -> None:
        report = render(self.document)
        self.assertEqual(report, render(self.document))
        self.assertIn("Remaining critical/high: `0 / 0`", report)
        self.assertIn("Approval does not adopt ADR-0015", report)
        self.assertIn("valid minority", report)

    def test_checked_in_evidence_is_the_deterministic_document(self) -> None:
        checked_in = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(checked_in, build_document(checked_in["generated_utc"]))

    def test_all_six_context_files_record_the_review(self) -> None:
        self.assertEqual(validate_context(), [])

    def test_exact_target_static_review_passes_when_fetched(self) -> None:
        if not target_available():
            self.skipTest("exact Draft target is fetched by the review workflow")
        self.assertEqual(validate_target(), [])


if __name__ == "__main__":
    unittest.main()
