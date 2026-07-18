from __future__ import annotations

import copy
import unittest

from scripts.u13_cross_sectional_design_check import CONTENT_HASH, SCOPE, load, validate_scope


class U13DesignTests(unittest.TestCase):
    def setUp(self):
        self.document = load(SCOPE)

    def test_exact_design(self):
        self.assertEqual(self.document["content_hash"], CONTENT_HASH)
        self.assertEqual(validate_scope(self.document), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.document); changed["generated_utc"] = "2030"
        self.assertEqual(validate_scope(changed), [])

    def test_permission_escalation_fails(self):
        for key in ("public_data_read", "event_scan", "returns", "fixed_rule_contract", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.document); changed["authorizations"][key] = True
            self.assertTrue(validate_scope(changed), key)

    def test_removing_invariant_or_failure_fails(self):
        changed = copy.deepcopy(self.document); changed["causal_and_membership_invariants"].pop("prior_only_lag_relationship_estimation")
        self.assertTrue(validate_scope(changed))
        changed = copy.deepcopy(self.document); changed["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(validate_scope(changed))

    def test_resolving_parameter_prematurely_fails(self):
        changed = copy.deepcopy(self.document); changed["unresolved_until_separate_protocol"].pop()
        self.assertTrue(validate_scope(changed))


if __name__ == "__main__":
    unittest.main()
