from __future__ import annotations

import copy
import unittest

from scripts.adr0015_invalid_interval_implementation_review_check import (
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


class ADR0015ImplementationReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = build_document("2026-07-17T09:00:00Z")

    def test_exact_target_and_implementation_identity_are_bound(self) -> None:
        target = self.document["reviewed_target"]
        self.assertEqual(target["head_sha"], TARGET_HEAD)
        self.assertEqual(target["changed_file_list_sha256"], CHANGED_FILE_LIST_HASH)
        self.assertEqual(target["implementation_content_sha256"], IMPLEMENTATION_HASH)
        self.assertEqual(validate_document(self.document), [])

    def test_all_review_dimensions_pass(self) -> None:
        self.assertEqual(
            {item["dimension"] for item in self.document["review_dimensions"]},
            set(REVIEW_DIMENSIONS),
        )
        self.assertTrue(all(item["status"] == "pass" for item in self.document["review_dimensions"]))

    def test_approve_requires_zero_critical_and_high(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["remaining_findings"]["high"] = ["drift"]
        failures = validate_document(changed)
        self.assertIn("approve requires zero remaining critical/high findings", failures)
        self.assertIn("review evidence is not the deterministic exact-head document", failures)

    def test_only_exact_implementation_merge_is_authorized(self) -> None:
        self.assertEqual(self.document["authorization"], AUTHORIZATION)
        self.assertTrue(AUTHORIZATION["merge_exact_implementation_after_review_pr_merges"])
        for name, enabled in AUTHORIZATION.items():
            if name != "merge_exact_implementation_after_review_pr_merges":
                self.assertFalse(enabled, name)

    def test_generated_time_does_not_change_review_identity(self) -> None:
        first = build_document("2026-07-17T09:00:00Z")
        second = build_document("2030-01-01T00:00:00Z")
        self.assertEqual(first["review_content_sha256"], second["review_content_sha256"])

    def test_report_is_a_deterministic_json_render(self) -> None:
        report = render(self.document)
        self.assertEqual(report, render(self.document))
        self.assertIn("Remaining critical/high: `0 / 0`", report)
        self.assertIn("Public data read or executed: no", report)

    def test_all_contexts_record_the_review(self) -> None:
        self.assertEqual(validate_context(), [])

    def test_exact_target_static_review_passes_when_fetched(self) -> None:
        if not target_available():
            self.skipTest("exact implementation target is fetched by the review validator")
        self.assertEqual(validate_target(), [])


if __name__ == "__main__":
    unittest.main()
