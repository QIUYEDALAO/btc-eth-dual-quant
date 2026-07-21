from __future__ import annotations

import copy
import unittest

from scripts.u04_cross_sectional_design_check import (
    EXPECTED_CONTENT_HASH,
    SCOPE_PATH,
    load_json,
    validate_bound_repository_evidence,
    validate_ledger,
    validate_scope,
)


class U04CrossSectionalDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = load_json(SCOPE_PATH)

    def test_repository_design_ledger_and_authorities_are_exact(self) -> None:
        self.assertEqual(self.scope["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertEqual(validate_scope(self.scope), [])
        self.assertEqual(validate_ledger(), [])
        self.assertEqual(validate_bound_repository_evidence(), [])

    def test_generated_time_does_not_change_content_identity(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_scope(changed), [])

    def test_audit_membership_lifecycle_or_policy_binding_tamper_fails(self) -> None:
        for key in (
            "adr0015_audit_summary_hash", "membership_manifest_hash",
            "membership_authority_hash", "lifecycle_registry_hash",
            "invalid_interval_runtime_policy_hash",
        ):
            changed = copy.deepcopy(self.scope)
            changed["bindings"][key] = "0" * 64
            with self.subTest(key=key):
                self.assertTrue(validate_scope(changed))

    def test_outcome_or_authorization_escalation_fails(self) -> None:
        for key in ("event_scan", "signals", "returns", "fixed_rule_contract", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.scope)
            changed["authorizations"][key] = True
            with self.subTest(key=key):
                self.assertTrue(validate_scope(changed))

    def test_timeframe_threshold_exit_or_position_selection_fails(self) -> None:
        for key in ("timeframe", "threshold", "target", "stop", "position_cap", "holding_period", "return"):
            changed = copy.deepcopy(self.scope)
            changed[key] = "selected_too_early"
            with self.subTest(key=key):
                self.assertTrue(validate_scope(changed))

    def test_point_in_time_and_prior_only_guards_cannot_be_disabled(self) -> None:
        for key in (
            "prior_only_inputs", "exact_active_member_set_required",
            "complete_active_member_rows_required", "current_membership_hindsight_prohibited",
            "replacement_members_prohibited", "survivorship_rewrite_prohibited",
            "lifecycle_crossing_assumption_prohibited",
        ):
            changed = copy.deepcopy(self.scope)
            changed["causal_and_membership_invariants"][key] = False
            with self.subTest(key=key):
                self.assertTrue(validate_scope(changed))

    def test_failure_regime_and_nonduplication_removal_fails(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["non_duplication"]["m1g_absolute_single_asset_panic_trigger_reuse_prohibited"] = False
        self.assertTrue(validate_scope(changed))

    def test_only_protocol_design_is_enabled(self) -> None:
        enabled = [key for key, value in self.scope["authorizations"].items() if value]
        self.assertEqual(enabled, ["u04_paper_protocol_design"])


if __name__ == "__main__":
    unittest.main()
