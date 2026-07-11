from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1g_fixed_rule_check", ROOT / "scripts" / "m1g_fixed_rule_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1GFixedRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load()

    def changed(self, section: str, key: str, value: object) -> list[str]:
        contract = copy.deepcopy(self.contract)
        contract[section][key] = value
        return MODULE.validate(contract)

    def test_repository_contract_passes(self) -> None:
        self.assertEqual(MODULE.validate(self.contract), [])

    def test_target_stop_timeout_and_cooldown_are_single_fixed_values(self) -> None:
        self.assertTrue(self.changed("exit", "profit_target_from_entry", "0.0240"))
        self.assertTrue(self.changed("exit", "invalidation_stop_from_entry", "-0.0600"))
        self.assertTrue(self.changed("exit", "maximum_holding_hours", 12))
        self.assertTrue(self.changed("risk", "global_cooldown_hours_after_exit", 24))

    def test_conservative_intrabar_and_gap_rules_cannot_change(self) -> None:
        self.assertTrue(self.changed("exit", "same_5m_target_and_stop_priority", "target_first"))
        self.assertTrue(self.changed("exit", "stop_gap_fill", "stop_threshold"))

    def test_position_and_one_trade_cap_are_fixed(self) -> None:
        self.assertTrue(self.changed("risk", "maximum_position_fraction_of_equity", "0.50"))
        self.assertTrue(self.changed("market", "maximum_open_trades", 2))

    def test_oos_backtest_and_trading_remain_disabled(self) -> None:
        for key in ("strategy_code", "freqtrade_backtesting", "oos_access", "dry_run", "live", "m2"):
            self.assertTrue(self.changed("authorization", key, True))

    def test_parameter_search_cannot_be_reintroduced(self) -> None:
        self.assertTrue(self.changed("derivation", "parameter_search_used", True))
        self.assertTrue(self.changed("derivation", "alternatives_evaluated", True))


if __name__ == "__main__":
    unittest.main()
