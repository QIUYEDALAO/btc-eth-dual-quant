from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1g_is_design_check", ROOT / "scripts" / "m1g_is_design_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1GISDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = MODULE.load_scope()

    def test_repository_scope_and_ledger_pass(self) -> None:
        self.assertEqual(MODULE.validate_scope(self.scope), [])
        self.assertEqual(MODULE.validate_ledger(), [])

    def test_oos_boundary_and_price_only_contract_are_fixed(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["research_scope"]["oos_opened"] = True
        self.assertTrue(MODULE.validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["research_scope"]["canonical_fields"].append("volume")
        self.assertTrue(MODULE.validate_scope(changed))

    def test_rule_selection_is_deferred(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["unresolved_until_later_gates"].remove("risk_invalidation_stop")
        changed["risk_invalidation_stop"] = "selected_too_early"
        self.assertTrue(MODULE.validate_scope(changed))

    def test_non_duplication_guards_cannot_be_disabled(self) -> None:
        for key in (
            "m1e_protocol_reuse_prohibited", "m1e_outcome_derived_rule_prohibited",
            "m1d_15m_timeframe_rescue_prohibited", "daily_panic_threshold_rescaling_prohibited",
            "m1a_combined_bundle_prohibited",
        ):
            changed = copy.deepcopy(self.scope)
            changed["non_duplication"][key] = False
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_scope(changed))

    def test_only_paper_protocol_design_is_authorized(self) -> None:
        for key in ("m1g_paper_diagnostic_run", "fixed_rule_contract", "strategy_code", "freqtrade_backtesting", "oos_access", "m2"):
            changed = copy.deepcopy(self.scope)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_scope(changed))

    def test_failure_regimes_cannot_be_removed(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(MODULE.validate_scope(changed))


if __name__ == "__main__":
    unittest.main()
