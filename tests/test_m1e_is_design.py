from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1e_is_design_check", ROOT / "scripts" / "m1e_is_design_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1EISDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = MODULE.load_scope()

    def changed(self, *path: str, value: object) -> list[str]:
        scope = copy.deepcopy(self.scope)
        target = scope
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return MODULE.validate_scope(scope)

    def test_repository_scope_and_ledger_pass(self) -> None:
        self.assertEqual(MODULE.validate_scope(self.scope), [])
        self.assertEqual(MODULE.validate_ledger(), [])

    def test_is_boundary_and_oos_seal_are_fixed(self) -> None:
        self.assertTrue(self.changed("research_scope", "is_end_exclusive", value="2026-07-01T00:00:00Z"))
        self.assertTrue(self.changed("research_scope", "oos_opened", value=True))

    def test_m1a_bundle_and_timeframe_rescue_remain_forbidden(self) -> None:
        scope = copy.deepcopy(self.scope)
        scope["non_duplication"]["forbidden_combined_bundle"].pop()
        self.assertTrue(MODULE.validate_scope(scope))
        self.assertTrue(self.changed("non_duplication", "m1a_timeframe_rescue_prohibited", value=False))

    def test_rule_parameters_cannot_be_selected_in_m1e_04(self) -> None:
        scope = copy.deepcopy(self.scope)
        scope["unresolved_until_later_gates"].remove("risk_stop")
        scope["risk_stop"] = "chosen_too_early"
        self.assertTrue(MODULE.validate_scope(scope))

    def test_only_isolator_is_authorized(self) -> None:
        for key in ("m1e_06_paper_diagnostics", "m1e_07_fixed_rule_contract", "strategy_code", "freqtrade_backtesting", "oos_access", "m2"):
            self.assertTrue(self.changed("authorization", key, value=True))

    def test_failure_regimes_cannot_be_removed_after_registration(self) -> None:
        scope = copy.deepcopy(self.scope)
        scope["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(MODULE.validate_scope(scope))


if __name__ == "__main__":
    unittest.main()
