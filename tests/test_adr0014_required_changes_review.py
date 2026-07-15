import copy
import unittest

from scripts.adr0014_required_changes_review_check import (
    EXPECTED_MANDATORY_CHANGE_IDS,
    EXPECTED_TARGET,
    build_review_document,
    content_identity,
    render_report,
    verify_review_document,
)


class ADR0014RequiredChangesReviewTests(unittest.TestCase):
    def test_exact_revised_pr_head_is_bound(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        self.assertEqual(document["reviewed_artifacts"], EXPECTED_TARGET)
        self.assertEqual(document["content"]["verdict"], "approve")
        self.assertEqual(verify_review_document(document), [])

    def test_every_mandatory_change_passes_with_required_fields(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        reviews = document["content"]["mandatory_change_reviews"]
        self.assertEqual({item["mandatory_change_id"] for item in reviews}, EXPECTED_MANDATORY_CHANGE_IDS)
        for item in reviews:
            self.assertEqual(
                set(item),
                {
                    "review_id",
                    "mandatory_change_id",
                    "evidence",
                    "acceptance_result",
                    "test_mapping",
                    "severity",
                    "remaining_gap",
                    "pass",
                },
            )
            self.assertTrue(item["pass"])
            self.assertEqual(item["acceptance_result"], "pass")
            self.assertEqual(item["remaining_gap"], "none")

    def test_approve_requires_zero_critical_and_high(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        self.assertEqual(document["content"]["severity_counts"]["critical"], 0)
        self.assertEqual(document["content"]["severity_counts"]["high"], 0)
        changed = copy.deepcopy(document)
        changed["content"]["mandatory_change_reviews"][0]["pass"] = False
        self.assertIn("approve verdict requires every mandatory change to pass", verify_review_document(changed))

    def test_all_authorizations_are_false(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        self.assertFalse(any(document["content"]["authorization_matrix"].values()))
        changed = copy.deepcopy(document)
        changed["content"]["authorization_matrix"]["v4_implementation"] = True
        self.assertIn("authorization matrix changed", verify_review_document(changed))

    def test_hash_or_target_tampering_is_rejected(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        for key in (
            "reviewed_pr_head",
            "adr_content_sha256",
            "policy_model_hash",
            "fault_matrix_hash",
            "mc_conformance_hash",
            "changed_file_list_sha256",
            "prior_review_content_hash",
            "klay_adjudication_evidence_hash",
        ):
            changed = copy.deepcopy(document)
            changed["reviewed_artifacts"][key] = "0" * 64
            self.assertIn(f"reviewed artifact binding changed: {key}", verify_review_document(changed))

    def test_review_time_does_not_change_content_identity(self):
        first = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        second = build_review_document(generated_utc="2026-07-15T19:30:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(content_identity(first), content_identity(second))

    def test_markdown_is_exact_deterministic_render(self):
        document = build_review_document(generated_utc="2026-07-15T18:30:00Z")
        report = render_report(document)
        self.assertEqual(report, render_report(document))
        self.assertIn("Verdict: `approve`", report)
        self.assertIn("Remaining critical/high: `0 / 0`", report)
        self.assertIn("PR #81 remains Draft", report)
        self.assertIn("Policy adoption authorized: no", report)


if __name__ == "__main__":
    unittest.main()
