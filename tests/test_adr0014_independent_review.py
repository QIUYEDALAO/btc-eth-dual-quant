import copy
import unittest

from scripts.adr0014_independent_review_check import (
    EXPECTED_CHANGED_FILES,
    EXPECTED_MANDATORY_CHANGE_IDS,
    EXPECTED_REVIEW_QUESTION_IDS,
    build_review_document,
    content_identity,
    render_report,
    verify_review_document,
)


class Adr0014IndependentReviewTests(unittest.TestCase):
    def test_review_binds_exact_pr_and_returns_unambiguous_verdict(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        reviewed = document["reviewed_artifacts"]
        self.assertEqual(reviewed["reviewed_pr_number"], 81)
        self.assertEqual(reviewed["reviewed_pr_head"], "cd4a1d8fb53870cdf8a3a683a4942a2c81b58f44")
        self.assertEqual(reviewed["reviewed_base_sha"], "d2d876af192a23ff1879d6a09cb2737c3f12133f")
        self.assertEqual(reviewed["changed_files"], EXPECTED_CHANGED_FILES)
        self.assertEqual(document["content"]["verdict"], "approve_with_required_changes")
        self.assertEqual(verify_review_document(document), [])

    def test_questions_and_machine_verifiable_mandatory_changes_are_complete(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        questions = document["content"]["questions"]
        mandatory = document["content"]["mandatory_changes"]
        self.assertEqual({item["review_id"] for item in questions}, EXPECTED_REVIEW_QUESTION_IDS)
        self.assertEqual({item["id"] for item in mandatory}, EXPECTED_MANDATORY_CHANGE_IDS)
        self.assertTrue(all(item["blocks_adoption"] for item in mandatory))
        self.assertTrue(all(item["acceptance"] and item["tests"] for item in mandatory))
        self.assertEqual(document["content"]["severity_counts"]["critical"], 0)
        self.assertEqual(document["content"]["severity_counts"]["high"], 10)

    def test_review_time_is_excluded_from_content_identity(self):
        first = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        second = build_review_document(generated_utc="2026-07-15T13:00:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(content_identity(first), content_identity(second))

    def test_all_downstream_authorizations_remain_false(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        self.assertFalse(any(document["content"]["authorization_matrix"].values()))
        changed = copy.deepcopy(document)
        changed["content"]["authorization_matrix"]["v4_implementation"] = True
        self.assertIn("authorization matrix changed", verify_review_document(changed))

    def test_approve_is_rejected_while_high_findings_exist(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        changed = copy.deepcopy(document)
        changed["content"]["verdict"] = "approve"
        self.assertIn("verdict is incompatible with unresolved high findings", verify_review_document(changed))

    def test_report_is_rendered_from_machine_evidence_and_exposes_boundary_risks(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        report = render_report(document)
        self.assertEqual(report, render_report(document))
        self.assertIn("Verdict: `approve_with_required_changes`", report)
        self.assertIn("2024-10-29", report)
        self.assertIn("availability_end_exclusive", report)
        self.assertIn("announced_successor_symbol", report)
        self.assertIn("Archive absence is not lifecycle proof", report)
        self.assertIn("V4 implementation authorized: no", report)

    def test_tampering_with_target_or_required_change_is_rejected(self):
        document = build_review_document(generated_utc="2026-07-15T12:00:00Z")
        changed = copy.deepcopy(document)
        changed["reviewed_artifacts"]["adr_content_sha256"] = "0" * 64
        self.assertIn("reviewed artifact binding changed: adr_content_sha256", verify_review_document(changed))
        changed = copy.deepcopy(document)
        changed["content"]["mandatory_changes"] = changed["content"]["mandatory_changes"][:-1]
        self.assertIn("mandatory change set mismatch", verify_review_document(changed))


if __name__ == "__main__":
    unittest.main()
