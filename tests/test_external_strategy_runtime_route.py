from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "external_strategy_is_boundary_qualification",
    ROOT / "scripts/external_strategy_is_boundary_qualification.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ExternalStrategyRuntimeRouteTests(unittest.TestCase):
    def test_runtime_and_causal_evidence_is_exact_and_oos_sealed(self):
        runtime = json.loads((ROOT / "reports/m1/evidence/external_strategy_runtime/runtime_identity.json").read_text())
        causal = json.loads((ROOT / "reports/m1/evidence/external_strategy_runtime/causal_summary.json").read_text())
        self.assertEqual(runtime["status"], "pass")
        self.assertEqual(runtime["image_id"], "sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6")
        self.assertEqual(runtime["network"], "none")
        self.assertFalse(runtime["secrets_mounted"])
        self.assertFalse(runtime["dry_run_or_trading_used"])
        self.assertEqual(causal["pass_count"], causal["causal_validations"])
        self.assertEqual(causal["pass_count"], 6)
        self.assertEqual(causal["minimum_required_before_is"], 5)
        self.assertEqual(causal["oos_rows_decoded"], 0)
        self.assertTrue(all(row["status"] == "PASS" and not row["failures"] for row in causal["results"]))

    def test_membership_exit_preflight_is_truthfully_blocked_and_deterministic(self):
        evidence = json.loads(MODULE.EVIDENCE.read_text())
        self.assertEqual(MODULE.validate(ROOT, evidence), [])
        self.assertEqual(evidence["boundary_transition_count"], 92)
        self.assertEqual(evidence["missing_frozen_boundary_archive_count"], 92)
        self.assertEqual(evidence["frozen_boundary_archive_count"], 0)
        self.assertFalse(evidence["is_authorized"])
        self.assertEqual(evidence["is_trials_materialized"], 0)
        self.assertEqual(evidence["oos_rows_decoded"], 0)

    def test_membership_exit_preflight_rejects_tampering(self):
        evidence = json.loads(MODULE.EVIDENCE.read_text())
        for field, value in (
            ("missing_frozen_boundary_archive_count", 91),
            ("is_authorized", True),
            ("oos_rows_decoded", 1),
        ):
            changed = copy.deepcopy(evidence)
            changed[field] = value
            changed["content_hash"] = MODULE.canonical_hash(changed)
            self.assertTrue(MODULE.validate(ROOT, changed))
        changed = copy.deepcopy(evidence)
        changed["transitions"][0]["frozen_boundary_archive"] = True
        changed["content_hash"] = MODULE.canonical_hash(changed)
        self.assertTrue(MODULE.validate(ROOT, changed))

    def test_materialization_identity_and_zero_oos_are_hash_bound(self):
        evidence = json.loads(MODULE.EVIDENCE.read_text())
        changed = copy.deepcopy(evidence)
        changed["is_materialization"]["content_hash"] = "0" * 64
        changed["content_hash"] = MODULE.canonical_hash(changed)
        self.assertIn("IS materialization identity drift", MODULE.validate(ROOT, changed))
        changed = copy.deepcopy(evidence)
        changed["is_materialization"]["oos_rows_decoded"] = 1
        changed["content_hash"] = MODULE.canonical_hash(changed)
        self.assertIn("IS materialization isolation failed", MODULE.validate(ROOT, changed))


if __name__ == "__main__":
    unittest.main()
