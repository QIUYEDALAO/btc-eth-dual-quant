from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1g_freqtrade_capability_check", ROOT / "scripts" / "m1g_freqtrade_capability_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1GFreqtradeCapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapping = MODULE.load()

    def test_repository_mapping_passes(self) -> None:
        self.assertEqual(MODULE.validate(self.mapping), [])

    def test_native_gap_differences_cannot_be_hidden(self) -> None:
        changed = copy.deepcopy(self.mapping)
        changed["native_execution_differences"]["material"] = False
        self.assertTrue(MODULE.validate(changed))

    def test_audit_cannot_recompute_signals_or_become_second_backtest(self) -> None:
        for key in ("signal_or_trade_selection_recomputed", "full_second_strategy_backtest"):
            changed = copy.deepcopy(self.mapping)
            changed["mandatory_independent_audit"][key] = True
            self.assertTrue(MODULE.validate(changed))

    def test_both_native_and_conservative_audit_are_required(self) -> None:
        changed = copy.deepcopy(self.mapping)
        changed["mandatory_independent_audit"]["approval_requires_freqtrade_and_contract_audit_gates"] = False
        self.assertTrue(MODULE.validate(changed))

    def test_performance_oos_and_trading_remain_disabled(self) -> None:
        for key in ("performance_backtesting", "oos_access", "dry_run", "live", "m2"):
            changed = copy.deepcopy(self.mapping)
            changed["authorization"][key] = True
            self.assertTrue(MODULE.validate(changed))


if __name__ == "__main__":
    unittest.main()
