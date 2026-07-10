from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1e_contract_check", ROOT / "scripts" / "m1e_contract_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1EContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_contract()

    def failures_after(self, path: tuple[str, ...], value: object) -> list[str]:
        changed = copy.deepcopy(self.contract)
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return MODULE.validate_contract(changed)

    def test_repository_contract_and_trial_identity_pass(self) -> None:
        self.assertEqual(MODULE.validate_contract(self.contract), [])
        self.assertEqual(MODULE.validate_ledger_identity(), [])

    def test_fixed_timeframes_and_range_cannot_change(self) -> None:
        self.assertTrue(self.failures_after(("timeframes", "signal_authority"), "4h"))
        self.assertTrue(self.failures_after(("range", "start"), "2023-10-01"))

    def test_liquidity_threshold_cannot_be_overridden(self) -> None:
        self.assertTrue(self.failures_after(("liquidity", "maximum"), "0.0040"))
        self.assertTrue(self.failures_after(("liquidity", "callers_may_override"), True))

    def test_monthly_zip_precedence_and_no_synthetic_bars_are_fixed(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["source_precedence"].reverse()
        self.assertTrue(MODULE.validate_contract(changed))
        self.assertTrue(self.failures_after(("aggregation", "fill_or_interpolate"), True))

    def test_oos_strategy_backtest_and_m2_remain_prohibited(self) -> None:
        for key in ("candidate_oos_returns", "strategy_code", "freqtrade_backtesting", "m2"):
            self.assertTrue(self.failures_after(("authorization", key), True))

    def test_m1a_combined_rule_bundle_must_remain_forbidden(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["m1a_non_reuse"]["forbidden_rule_bundle"].pop()
        self.assertTrue(MODULE.validate_contract(changed))


if __name__ == "__main__":
    unittest.main()
