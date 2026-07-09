from __future__ import annotations

import json
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m1c_validate_design import CONTRACT_PATH, EVIDENCE_PATH, validate_design


class M1CRotationDesignTests(unittest.TestCase):
    def test_design_contract_is_fixed_and_valid(self) -> None:
        self.assertEqual(validate_design(), [])

    def test_sunday_signal_maps_to_next_daily_open(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        signal_open = datetime(2026, 7, 5, tzinfo=UTC)
        signal_close = signal_open + timedelta(days=1)
        fill_open = signal_close
        self.assertEqual(signal_open.weekday(), contract["decision_weekday"])
        self.assertEqual(contract["fill_rule"], "next_bar_open")
        self.assertEqual(fill_open, datetime(2026, 7, 6, tzinfo=UTC))

    def test_tie_breaker_and_cash_fallback_are_deterministic(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["tie_breaker"], "BTC/USDT")
        self.assertEqual(contract["missing_cross_pair_action"], "cash")

    def test_same_timestamp_rotation_requires_p2_runtime_fixture(self) -> None:
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        observations = evidence["observations"]
        self.assertTrue(observations["different_pair_can_enter_same_timestamp_after_exit"])
        self.assertTrue(observations["runtime_fixture_required_in_p2"])

    def test_p1_phase_does_not_implement_strategy(self) -> None:
        state = (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
        strategy = ROOT / "freqtrade_lab" / "user_data" / "strategies" / "BTCETHRelativeStrengthRotation.py"
        if "current_phase: P1 " in state:
            self.assertFalse(strategy.exists())


if __name__ == "__main__":
    unittest.main()
