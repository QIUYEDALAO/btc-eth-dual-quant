import copy
import unittest

from scripts.adr0013_independent_review_check import (
    EXPECTED_MANDATORY_CHANGE_IDS,
    EXPECTED_REVIEW_QUESTION_IDS,
    build_review_document,
    render_report,
    verify_review_document,
)


class Adr0013IndependentReviewTests(unittest.TestCase):
    def test_frozen_review_is_complete_and_fail_closed(self):
        document = build_review_document()
        self.assertEqual(document["content"]["verdict"], "approve_with_required_changes")
        self.assertEqual(
            {item["id"] for item in document["content"]["review_questions"]},
            EXPECTED_REVIEW_QUESTION_IDS,
        )
        self.assertEqual(
            {item["id"] for item in document["content"]["mandatory_changes"]},
            EXPECTED_MANDATORY_CHANGE_IDS,
        )
        self.assertFalse(any(document["content"]["authorizations"].values()))
        self.assertEqual(verify_review_document(document), [])

    def test_every_mandatory_change_blocks_adoption_until_completed(self):
        document = build_review_document()
        self.assertTrue(all(item["required"] for item in document["content"]["mandatory_changes"]))
        self.assertTrue(all(item["draft_status"] == "missing_or_incomplete" for item in document["content"]["mandatory_changes"]))
        changed = copy.deepcopy(document)
        changed["content"]["mandatory_changes"] = changed["content"]["mandatory_changes"][:-1]
        self.assertIn("mandatory change set mismatch", verify_review_document(changed))

    def test_review_identity_and_evidence_are_hash_bound(self):
        document = build_review_document()
        changed = copy.deepcopy(document)
        changed["reviewed_artifacts"]["adr_draft_content_sha256"] = "0" * 64
        self.assertIn("reviewed artifact binding changed: adr_draft_content_sha256", verify_review_document(changed))
        self.assertIn("content hash mismatch", verify_review_document(changed))

    def test_authorization_escalation_is_rejected(self):
        document = build_review_document()
        changed = copy.deepcopy(document)
        changed["content"]["authorizations"]["v3_implementation"] = True
        self.assertIn("authorization matrix changed", verify_review_document(changed))

    def test_report_is_deterministic_and_states_no_implementation_authority(self):
        report = render_report(build_review_document())
        self.assertEqual(report, render_report(build_review_document()))
        self.assertIn("Verdict: `approve_with_required_changes`", report)
        self.assertIn("V3 implementation authorized: no", report)
        self.assertIn("U-03E V3 rerun authorized: no", report)
        self.assertIn("U-03F authorized: no", report)
        self.assertIn("U-04 authorized: no", report)


if __name__ == "__main__":
    unittest.main()
