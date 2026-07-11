from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1g_paper_protocol_check", ROOT / "scripts" / "m1g_paper_protocol_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1GPaperProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load()

    def test_repository_protocol_passes(self) -> None:
        self.assertEqual(MODULE.validate(self.protocol), [])

    def test_event_thresholds_cannot_change(self) -> None:
        for key, value in (("close_return_maximum", "-0.0200"), ("absolute_return_multiple_minimum", "2.0"), ("true_range_multiple_minimum", "2.0"), ("close_location_maximum", "0.50")):
            changed = copy.deepcopy(self.protocol)
            changed["diagnostic_event"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_common_sample_and_cost_coverage_gates_cannot_change(self) -> None:
        for key, value in (("projected_full_events_minimum", 80), ("projected_oos_events_minimum", 20), ("median_24h_mfe_minimum", "0.0120")):
            changed = copy.deepcopy(self.protocol)
            changed["paper_gates"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_current_task_cannot_run_or_backtest(self) -> None:
        for key in ("paper_diagnostic_run", "fixed_rule_contract", "strategy_code", "freqtrade_backtesting", "oos_access", "m2"):
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_protocol_has_no_fill_or_position_model(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["observation"]["entry_fill_model_used"] = True
        self.assertTrue(MODULE.validate(changed))


if __name__ == "__main__":
    unittest.main()
