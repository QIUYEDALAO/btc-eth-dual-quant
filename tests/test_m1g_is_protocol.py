from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1g_is_protocol_check", ROOT / "scripts/m1g_is_protocol_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1GISProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = MODULE.load()

    def test_repository_protocol_and_hashes_pass(self):
        self.assertEqual(MODULE.validate(self.protocol), [])

    def test_range_cost_or_gate_cannot_change(self):
        mutations = [
            ("range", "oos_opened", True),
            ("costs_per_side", "cost_x2", "0.0010"),
            ("is_gates", "complete_trades_minimum", 1),
            ("is_gates", "daily_mtm_sharpe_minimum", "0.5"),
            ("is_gates", "daily_mtm_psr_minimum", "0.5"),
            ("is_gates", "daily_mtm_max_drawdown_maximum", "0.50"),
        ]
        for section, key, value in mutations:
            changed = copy.deepcopy(self.protocol)
            changed[section][key] = value
            self.assertTrue(MODULE.validate(changed, verify_files=False), f"mutation passed: {section}.{key}")

    def test_audit_cannot_select_signals_or_relax_tolerance(self):
        changed = copy.deepcopy(self.protocol)
        changed["audit"]["signal_selection_allowed"] = True
        self.assertTrue(MODULE.validate(changed, verify_files=False))
        changed = copy.deepcopy(self.protocol)
        changed["audit"]["numeric_tolerance"] = "1e-2"
        self.assertTrue(MODULE.validate(changed, verify_files=False))

    def test_stress_is_diagnostic_and_oos_trading_remain_disabled(self):
        self.assertIsNone(self.protocol["diagnostics"]["stress_hard_gate"])
        for key in ("oos_access", "dry_run", "live", "m2"):
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            self.assertTrue(MODULE.validate(changed, verify_files=False))


if __name__ == "__main__":
    unittest.main()
