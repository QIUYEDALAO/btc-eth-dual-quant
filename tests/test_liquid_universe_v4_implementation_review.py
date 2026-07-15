import copy
import subprocess
import unittest

from scripts.liquid_universe_v4_implementation_review_check import (
    EXPECTED,
    EXPECTED_AUTHORIZATIONS,
    EXPECTED_REVIEW_IDS,
    TARGET_HEAD,
    build_review_document,
    render_report,
    verify_review_document,
    verify_target,
)


class LiquidUniverseV4ImplementationReviewTests(unittest.TestCase):
    def test_exact_target_and_all_review_dimensions_are_bound(self):
        document = build_review_document("2026-07-16T01:00:00Z")
        self.assertEqual(document["reviewed_target"]["implementation_head"], TARGET_HEAD)
        self.assertEqual(document["reviewed_target"]["changed_file_list_sha256"], EXPECTED["changed_file_list_sha256"])
        self.assertEqual({item["review_id"] for item in document["content"]["checks"]}, EXPECTED_REVIEW_IDS)
        self.assertEqual(verify_review_document(document), [])

    def test_approve_requires_zero_critical_high_and_all_checks_pass(self):
        document = build_review_document("2026-07-16T01:00:00Z")
        self.assertEqual(document["content"]["verdict"], "approve")
        self.assertEqual(document["content"]["severity_counts"]["critical"], 0)
        self.assertEqual(document["content"]["severity_counts"]["high"], 0)
        changed = copy.deepcopy(document)
        changed["content"]["checks"][0]["result"] = "fail"
        self.assertIn("approve requires every review check to pass", verify_review_document(changed))

    def test_downstream_authorizations_remain_false(self):
        document = build_review_document("2026-07-16T01:00:00Z")
        self.assertEqual(document["content"]["authorization_matrix"], EXPECTED_AUTHORIZATIONS)
        for key in ("u03f", "u04", "hypothesis", "strategy", "events", "returns", "oos", "api_trading", "execution_live", "m2"):
            self.assertFalse(document["content"]["authorization_matrix"][key])

    def test_tampering_with_target_or_authority_hash_is_rejected(self):
        for key in ("implementation_head", "changed_file_list_sha256", "contract_canonical_hash", "policy_canonical_hash", "registry_canonical_hash", "klay_adjudication_hash", "fault_matrix_hash"):
            document = build_review_document("2026-07-16T01:00:00Z")
            document["reviewed_target"][key] = "0" * 64
            self.assertIn("review target binding changed", verify_review_document(document))

    def test_report_is_exact_deterministic_render(self):
        document = build_review_document("2026-07-16T01:00:00Z")
        report = render_report(document)
        self.assertEqual(report, render_report(document))
        self.assertIn("Verdict: `approve`", report)
        self.assertIn("Remaining critical/high: `0 / 0`", report)
        self.assertIn("Real public requalification run: `not run`", report)

    def test_exact_target_static_review_passes(self):
        if subprocess.run(
            ["git", "cat-file", "-e", f"{TARGET_HEAD}^{{commit}}"],
            capture_output=True,
            check=False,
        ).returncode:
            self.skipTest("exact implementation target is fetched by the dedicated review workflow")
        self.assertEqual(verify_target(TARGET_HEAD), [])


if __name__ == "__main__":
    unittest.main()
