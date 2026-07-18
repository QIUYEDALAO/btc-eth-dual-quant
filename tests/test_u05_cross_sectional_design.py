from __future__ import annotations

import copy
import json
import unittest

from scripts.u05_cross_sectional_design_check import SCOPE_PATH, validate_scope, validate_ledger, validate_bound_evidence


class U05CrossSectionalDesignTests(unittest.TestCase):
    def setUp(self):
        self.scope = json.loads(SCOPE_PATH.read_text())

    def test_repository_design_ledger_and_authorities_are_exact(self):
        self.assertEqual(validate_scope(self.scope), [])
        self.assertEqual(validate_ledger(), [])
        self.assertEqual(validate_bound_evidence(), [])

    def test_generated_time_does_not_change_content_identity(self):
        changed = copy.deepcopy(self.scope); changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_scope(changed), [])

    def test_authority_or_u04_binding_tamper_fails(self):
        for key in ("u05_design_authorization_hash", "u04_closed_run_hash", "source_freeze_hash"):
            changed = copy.deepcopy(self.scope); changed["bindings"][key] = "0" * 64
            self.assertTrue(validate_scope(changed), key)

    def test_failure_regime_or_nonduplication_removal_fails(self):
        changed = copy.deepcopy(self.scope); changed["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(validate_scope(changed))
        changed = copy.deepcopy(self.scope); changed["non_duplication"].pop("u04_residual_reversal_or_observed_sign_inversion_prohibited")
        self.assertTrue(validate_scope(changed))

    def test_causal_guards_cannot_be_disabled(self):
        for key in ("prior_only_inputs", "exact_active_member_set_required", "u04_outcome_inversion_prohibited"):
            changed = copy.deepcopy(self.scope); changed["causal_and_membership_invariants"][key] = False
            self.assertTrue(validate_scope(changed), key)

    def test_parameter_or_permission_escalation_fails(self):
        changed = copy.deepcopy(self.scope); changed["selected_timeframe"] = "1h"
        self.assertTrue(validate_scope(changed))
        for key in ("event_scan", "returns", "fixed_rule_contract", "freqtrade_strategy_code", "oos", "api_trading", "m2"):
            changed = copy.deepcopy(self.scope); changed["authorizations"][key] = True
            self.assertTrue(validate_scope(changed), key)


if __name__ == "__main__":
    unittest.main()
