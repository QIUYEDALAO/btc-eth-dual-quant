from __future__ import annotations

import copy
import unittest

from scripts.adr0015_independent_audit_result_check import (
    ARTIFACT_SET, SUMMARY_HASH, load, validate_documents,
)


class Adr0015IndependentAuditResultTests(unittest.TestCase):
    def setUp(self):
        self.summary = load("audit_summary.json")
        self.comparison = load("production_comparison.json")
        self.hashes = load("independent_manifest_hashes.json")
        self.traversal = load("traversal_identity.json")

    def validate(self, **changed):
        return validate_documents(
            changed.get("summary", self.summary), changed.get("comparison", self.comparison),
            changed.get("hashes", self.hashes), changed.get("traversal", self.traversal),
        )

    def test_repository_result_is_exact(self):
        self.assertEqual(self.summary["audit_summary_hash"], SUMMARY_HASH)
        self.assertEqual(self.summary["independent_artifact_set_hash"], ARTIFACT_SET)
        self.assertEqual(self.validate(), [])

    def test_summary_gate_tamper_fails(self):
        changed = copy.deepcopy(self.summary); changed["manifests_exact"] = 18
        self.assertTrue(self.validate(summary=changed))

    def test_any_manifest_mismatch_fails(self):
        changed = copy.deepcopy(self.comparison)
        changed["comparisons"][next(iter(changed["comparisons"]))]["exact_content_match"] = False
        self.assertTrue(self.validate(comparison=changed))

    def test_traversal_identity_or_order_tamper_fails(self):
        changed = copy.deepcopy(self.traversal); changed[1]["artifact_set_hash"] = "0" * 64
        self.assertTrue(self.validate(traversal=changed))

    def test_downstream_authorization_fails(self):
        changed = copy.deepcopy(self.summary); changed["authorization"]["u04"] = True
        self.assertTrue(self.validate(summary=changed))


if __name__ == "__main__":
    unittest.main()
