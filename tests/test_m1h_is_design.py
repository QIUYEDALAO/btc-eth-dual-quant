from __future__ import annotations

import copy
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m1h_is_design_check", ROOT / "scripts/m1h_is_design_check.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class M1HISDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = MODULE.load_json(MODULE.SCOPE_PATH)

    def test_repository_scope_ledger_and_registry_pass(self) -> None:
        self.assertEqual(MODULE.validate_scope(self.scope), [])
        self.assertEqual(MODULE.validate_ledger(), [])
        self.assertEqual(MODULE.validate_registry(), [])

    def test_settlement_timing_is_strictly_causal(self) -> None:
        funding_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(
            MODULE.validate_timing(funding_time, funding_time, funding_time + timedelta(minutes=5)),
            [],
        )
        self.assertTrue(MODULE.validate_timing(funding_time, funding_time - timedelta(seconds=1), funding_time + timedelta(minutes=5)))
        self.assertTrue(MODULE.validate_timing(funding_time, funding_time, funding_time))
        self.assertTrue(MODULE.validate_timing(funding_time, funding_time + timedelta(minutes=10), funding_time + timedelta(minutes=5)))

    def test_naive_timestamps_are_rejected(self) -> None:
        value = datetime(2025, 1, 1)
        self.assertEqual(MODULE.validate_timing(value, value, value), ["all M1H timestamps must be timezone-aware"])

    def test_funding_is_signal_only_and_positions_remain_spot_only(self) -> None:
        for key in ("futures_position", "funding_cashflow_return", "two_leg_execution"):
            changed = copy.deepcopy(self.scope)
            changed["research_scope"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_scope(changed))

    def test_interval_policy_cannot_hardcode_or_use_one_snapshot(self) -> None:
        for key in ("single_premium_snapshot_is_complete_interval", "hardcoded_default_interval"):
            changed = copy.deepcopy(self.scope)
            changed["data_lineage"]["interval_metadata"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["data_lineage"]["interval_metadata"]["per_event_interval_required"] = False
        self.assertTrue(MODULE.validate_scope(changed))

    def test_m1b_and_m1g_non_duplication_guards_cannot_be_disabled(self) -> None:
        for key, value in self.scope["non_duplication"].items():
            if isinstance(value, bool):
                changed = copy.deepcopy(self.scope)
                changed["non_duplication"][key] = False
                with self.subTest(key=key):
                    self.assertTrue(MODULE.validate_scope(changed))

    def test_execution_representability_is_required_before_implementation(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["execution_representability"]["exit_family_selected"] = True
        self.assertTrue(MODULE.validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["execution_representability"]["zero_mismatch_fixture_required_before_implementation"] = False
        self.assertTrue(MODULE.validate_scope(changed))

    def test_rule_selection_remains_deferred(self) -> None:
        changed = copy.deepcopy(self.scope)
        changed["unresolved_until_later_gates"].remove("negative_funding_extreme_definition")
        changed["negative_funding_extreme_definition"] = "selected_too_early"
        self.assertTrue(MODULE.validate_scope(changed))

    def test_only_paper_protocol_design_is_authorized(self) -> None:
        for key in (
            "m1h_paper_diagnostic_run",
            "fixed_rule_contract",
            "strategy_code",
            "freqtrade_backtesting",
            "oos_access",
            "private_data",
            "dry_run",
            "live",
            "m2",
        ):
            changed = copy.deepcopy(self.scope)
            changed["authorization"][key] = True
            with self.subTest(key=key):
                self.assertTrue(MODULE.validate_scope(changed))

    def test_design_files_contain_no_strategy_or_execution_module(self) -> None:
        source = MODULE.SCOPE_PATH.read_text(encoding="utf-8") + (ROOT / "scripts/m1h_is_design_check.py").read_text(encoding="utf-8")
        for forbidden in ("populate_entry", "populate_exit", "create_order", "cancel_order", "place_order", "execution/live"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
