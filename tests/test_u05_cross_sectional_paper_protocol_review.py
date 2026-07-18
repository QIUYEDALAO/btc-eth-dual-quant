from __future__ import annotations

import copy
import unittest

from scripts.u05_cross_sectional_paper_protocol_review_check import (
    EXPECTED_REVIEW_HASH,
    REVIEW_PATH,
    load,
    validate,
    validate_report,
)


class U05CrossSectionalPaperProtocolReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.review = load(REVIEW_PATH)

    def test_repository_review_is_exact_and_approve(self) -> None:
        self.assertEqual(self.review["review_content_hash"], EXPECTED_REVIEW_HASH)
        self.assertEqual(validate(self.review), [])
        self.assertEqual(validate_report(), [])

    def test_generated_time_does_not_change_review_identity(self) -> None:
        changed = copy.deepcopy(self.review)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, verify_git=False), [])

    def test_target_protocol_or_file_tamper_fails(self) -> None:
        changed = copy.deepcopy(self.review)
        changed["target"]["head_commit"] = "0" * 40
        self.assertTrue(validate(changed, verify_git=False))
        for rel_path in self.review["target_files"]:
            changed = copy.deepcopy(self.review)
            changed["target_files"][rel_path] = "0" * 64
            with self.subTest(rel_path=rel_path):
                self.assertTrue(validate(changed, verify_git=False))

    def test_missing_or_failed_dimension_blocks_approve(self) -> None:
        changed = copy.deepcopy(self.review)
        changed["review_dimensions"].pop()
        self.assertTrue(validate(changed, verify_git=False))
        changed = copy.deepcopy(self.review)
        changed["review_dimensions"][0]["result"] = "fail"
        self.assertTrue(validate(changed, verify_git=False))

    def test_approve_requires_zero_critical_and_high(self) -> None:
        for key in ("remaining_critical_findings", "remaining_high_findings"):
            changed = copy.deepcopy(self.review)
            changed[key] = 1
            with self.subTest(key=key):
                self.assertTrue(validate(changed, verify_git=False))

    def test_only_data_qualification_is_authorized(self) -> None:
        enabled = {key for key, value in self.review["authorizations"].items() if value}
        self.assertEqual(enabled, {"data_qualification"})
        for key in set(self.review["authorizations"]) - enabled:
            changed = copy.deepcopy(self.review)
            changed["authorizations"][key] = True
            with self.subTest(key=key):
                self.assertTrue(validate(changed, verify_git=False))

    def test_target_mutation_claim_fails(self) -> None:
        changed = copy.deepcopy(self.review)
        changed["target_modified_by_review"] = True
        self.assertTrue(validate(changed, verify_git=False))


if __name__ == "__main__":
    unittest.main()
