from __future__ import annotations

import copy
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1h_paper_protocol_check", ROOT / "scripts/m1h_paper_protocol_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1HPaperProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = MODULE.load()

    def test_repository_protocol_ledger_and_report_pass(self) -> None:
        self.assertEqual(MODULE.validate(self.protocol), [])
        self.assertEqual(MODULE.validate_ledger(), [])
        self.assertEqual(MODULE.validate_report(), [])

    def test_funding_extreme_is_frozen_and_not_a_strategy_parameter(self) -> None:
        changes = {
            "lower_tail_percentile": "0.10",
            "history_window_utc_days": 180,
            "percentile_interpolation": "nearest",
            "same_symbol_cluster_hours": 12,
            "hardcoded_default_interval_allowed": True,
            "spot_price_trigger_allowed": True,
        }
        for key, value in changes.items():
            changed = copy.deepcopy(self.protocol)
            changed["funding_extreme_event"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_horizons_are_market_observations_and_cannot_change(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["observation_contract"]["fixed_horizon_hours"] = [1, 4, 24]
        self.assertTrue(MODULE.validate(changed))
        changed = copy.deepcopy(self.protocol)
        changed["observation_contract"]["purpose"] = "strategy_holding_period"
        self.assertTrue(MODULE.validate(changed))

    def test_mfe_is_not_a_gate_and_all_path_diagnostics_are_required(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["paper_gates"]["mfe_standalone_gate"] = True
        self.assertTrue(MODULE.validate(changed))
        for diagnostic in self.protocol["observation_contract"]["required_diagnostics"]:
            changed = copy.deepcopy(self.protocol)
            changed["observation_contract"]["required_diagnostics"].remove(diagnostic)
            with self.subTest(diagnostic=diagnostic):
                self.assertTrue(MODULE.validate(changed))

    def test_close_displacement_and_sample_gates_cannot_be_lowered(self) -> None:
        changes = {
            "projected_full_independent_episodes_minimum": 80,
            "projected_sealed_oos_episodes_minimum": 20,
            "combined_median_24h_close_displacement_minimum": "0.0100",
            "each_symbol_median_24h_close_displacement_minimum": "0.0100",
        }
        for key, value in changes.items():
            changed = copy.deepcopy(self.protocol)
            changed["paper_gates"][key] = value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_reference_is_exact_next_5m_open(self) -> None:
        funding = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        reference = funding + timedelta(minutes=5)
        self.assertEqual(MODULE.validate_timing(funding, funding, reference), [])
        self.assertTrue(MODULE.validate_timing(funding, funding, funding))
        self.assertTrue(MODULE.validate_timing(funding, funding, funding + timedelta(minutes=10)))
        self.assertTrue(MODULE.validate_timing(funding, funding - timedelta(seconds=1), reference))

    def test_off_grid_funding_time_uses_first_strict_grid_open(self) -> None:
        funding = datetime(2025, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        self.assertEqual(MODULE.expected_reference_time(funding), datetime(2025, 1, 1, 0, 5, tzinfo=timezone.utc))

    def test_research_leakage_guards_cannot_be_enabled(self) -> None:
        for key, value in self.protocol["research_leakage_prevention"].items():
            changed = copy.deepcopy(self.protocol)
            changed["research_leakage_prevention"][key] = not value
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_m1b_and_m1g_semantics_remain_prohibited(self) -> None:
        for key, value in self.protocol["non_duplication"].items():
            if isinstance(value, bool):
                changed = copy.deepcopy(self.protocol)
                changed["non_duplication"][key] = not value
                with self.subTest(key=key):
                    self.assertTrue(MODULE.validate(changed))

    def test_only_protocol_freeze_is_authorized(self) -> None:
        for key in self.protocol["authorization"]:
            if key == "paper_protocol_frozen":
                continue
            changed = copy.deepcopy(self.protocol)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_data_qualification_cannot_scan_or_decide(self) -> None:
        for key in ("event_scan_allowed", "event_count_allowed", "path_diagnostics_allowed", "returns_allowed", "feasibility_decision_allowed"):
            changed = copy.deepcopy(self.protocol)
            changed["next_task_data_qualification"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate(changed))

    def test_no_strategy_or_trading_implementation(self) -> None:
        sources = MODULE.PROTOCOL_PATH.read_text(encoding="utf-8") + (ROOT / "scripts/m1h_paper_protocol_check.py").read_text(encoding="utf-8")
        for forbidden in ("populate_entry", "populate_exit", "create_order", "cancel_order", "place_order", "execution/live"):
            self.assertNotIn(forbidden, sources)


if __name__ == "__main__":
    unittest.main()
