from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from scripts.u20_cross_sectional_data_qualification import COMMON, NEGATIVE_HISTORY, NEUTRAL_HISTORY
from scripts.u20_cross_sectional_paper_observation import ONE_HOUR_MS, evaluate_gates, main, observe_paths, select_events


def path(decision: int, symbol: str, relative: str = "0.020", absolute: str = "0.020") -> dict:
    return {
        "decision_time_ms": decision,
        "symbol": symbol,
        "relative_negative_coskewness_risk_premium": {"24": relative},
        "candidate_absolute_close_displacement": {"24": absolute},
    }


class U20ObservationPreflightTests(unittest.TestCase):
    def test_complete_prior_history_selects_cross_sectional_representative(self) -> None:
        import datetime
        import math

        decision = int(datetime.datetime(2020, 2, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
        symbols = tuple(f"S{index:02d}USDT" for index in range(15))
        membership = {"2020-01": symbols, "2020-02": symbols}
        closes = {}
        for symbol_index, symbol in enumerate(symbols):
            history = NEGATIVE_HISTORY if symbol_index < 4 else NEUTRAL_HISTORY
            value = 100.0
            closes[(symbol, decision - 336 * ONE_HOUR_MS)] = Decimal(str(value))
            for index, log_return in enumerate(history, start=1):
                value *= math.exp(log_return)
                closes[(symbol, decision - (336 - index) * ONE_HOUR_MS)] = Decimal(str(value))
        events, accounting = select_events(closes, membership, decision, decision + 4 * ONE_HOUR_MS, "p")
        self.assertEqual(accounting["candidate_events"], 1)
        self.assertEqual(events[0]["symbol"], "S00USDT")

    def test_frozen_economic_gates(self) -> None:
        rows = []
        for year in range(2020, 2025):
            base = int(__import__("datetime").datetime(year, 1, 1, tzinfo=__import__("datetime").timezone.utc).timestamp() * 1000)
            rows.extend(path(base + index * 18 * 86_400_000, f"S{index % 10:02d}USDT") for index in range(20))
        metrics, checks = evaluate_gates(rows, 0)
        self.assertEqual(metrics["complete_is_independent_episodes"], 100)
        self.assertTrue(all(checks.values()))

    def test_failed_economic_gate_does_not_authorize(self) -> None:
        rows = [path(1_600_000_000_000 + index * 86_400_000, f"S{index % 10:02d}USDT", "-0.001", "-0.001") for index in range(100)]
        _, checks = evaluate_gates(rows, 0)
        self.assertFalse(checks["median_24h_relative_negative_coskewness_risk_premium"])
        self.assertFalse(checks["median_24h_candidate_absolute_close_displacement"])

    def test_observation_path_uses_reference_open_and_all_peers(self) -> None:
        episode = {"episode_id": "e", "event_id": "v", "symbol": "A", "active_members": ["A", "B"], "decision_time_ms": 1, "reference_open_time_ms": 0}
        captured = {}
        for index in range(288):
            opened = index * 300_000
            captured[("A", opened)] = (Decimal("100"), Decimal("103"), Decimal("97"), Decimal("102"))
            captured[("B", opened)] = (Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100"))
        paths, censored = observe_paths([episode], captured, {})
        self.assertFalse(censored)
        self.assertEqual(paths[0]["relative_negative_coskewness_risk_premium"]["24"], "0.02")

    def test_missing_peer_right_censors(self) -> None:
        episode = {"episode_id": "e", "event_id": "v", "symbol": "A", "active_members": ["A", "B"], "decision_time_ms": 1, "reference_open_time_ms": 0}
        paths, censored = observe_paths([episode], {}, {})
        self.assertEqual(paths, [])
        self.assertEqual(censored["missing_or_quarantined_5m"], 1)

    def test_second_run_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "run_manifest.json").write_text("{}")
            import sys
            original = sys.argv
            try:
                sys.argv = ["u20", "--evidence-dir", str(evidence), "--report", str(evidence / "report.md")]
                self.assertEqual(main(), 2)
            finally:
                sys.argv = original


if __name__ == "__main__":
    unittest.main()
