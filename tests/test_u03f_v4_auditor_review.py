import copy
import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "u03f_review", "scripts/u03f_v4_auditor_review_check.py"
)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class U03FV4AuditorReviewTests(unittest.TestCase):
    def test_repository_review_passes(self):
        self.assertEqual(review.validate(), [])

    def test_exact_target_and_hashes_are_bound(self):
        document = review.build_document("2026-07-16T00:00:00Z")
        target = document["reviewed_target"]
        self.assertEqual(target["head_sha"], review.TARGET_HEAD)
        self.assertEqual(target["audit_algorithm_sha256"], review.ALGORITHM_HASH)
        self.assertEqual(target["changed_file_list_sha256"], review.CHANGED_FILE_LIST_HASH)
        if review.target_available():
            self.assertEqual(review.algorithm_hash(), review.ALGORITHM_HASH)

    def test_approve_requires_zero_critical_and_high(self):
        document = review.build_document("2026-07-16T00:00:00Z")
        self.assertEqual(document["verdict"], "approve")
        self.assertEqual(document["implementation_findings"]["critical"], [])
        self.assertEqual(document["implementation_findings"]["high"], [])
        tampered = copy.deepcopy(document)
        tampered["implementation_findings"]["high"].append("hidden")
        self.assertNotEqual(tampered, review.build_document("2026-07-16T00:00:00Z"))

    def test_independence_and_fixture_coverage_are_real(self):
        document = review.build_document("2026-07-16T00:00:00Z")
        self.assertEqual(document["validation_evidence"]["auditor_test_count"], 34)
        self.assertTrue(all(item["status"] == "pass" for item in document["review_dimensions"]))
        if review.target_available():
            self.assertEqual(review.independence_findings(), [])
            self.assertEqual(review.auditor_test_count(), 34)

    def test_required_exact_head_fails_closed_when_unavailable(self):
        if review.target_available():
            self.assertEqual(review.validate(require_target=True), [])
        else:
            self.assertIn("exact target head is unavailable", review.validate(require_target=True))

    def test_production_time_risks_are_deferred_not_hidden(self):
        document = review.build_document("2026-07-16T00:00:00Z")
        self.assertEqual(
            document["deferred_real_audit_gate"]["production_integer_time_risks"],
            review.PRODUCTION_TIME_RISKS,
        )
        self.assertEqual(len(review.PRODUCTION_TIME_RISKS), 6)

    def test_authorization_is_narrow(self):
        authorization = review.build_document("2026-07-16T00:00:00Z")["authorization"]
        permitted = {"merge_review_pr", "merge_auditor_after_exact_head_recheck"}
        self.assertTrue(all(value is False for key, value in authorization.items() if key not in permitted))


if __name__ == "__main__":
    unittest.main()
