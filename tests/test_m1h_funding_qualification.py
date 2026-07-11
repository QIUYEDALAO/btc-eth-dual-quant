from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from btc_eth_dual_quant.audit.m1h_paper import (
    IS_END_EXCLUSIVE_MS,
    qualify_funding_rows,
    validate_research_scope_text,
)


ROOT = Path(__file__).resolve().parents[1]


def row(symbol: str, time_ms: int, rate: str, interval: str, source: str = "a" * 64) -> dict:
    return {
        "symbol": symbol,
        "fundingTime": time_ms,
        "fundingRate": rate,
        "fundingIntervalHours": interval,
        "source_sha256": source,
    }


class FundingQualificationTests(unittest.TestCase):
    def test_variable_per_event_intervals_are_inferred_without_default(self) -> None:
        start = 1_600_000_000_000
        rows = [
            row("BTCUSDT", start, "0.001", "4"),
            row("BTCUSDT", start + 4 * 3_600_000, "0.001", "4"),
            row("BTCUSDT", start + 10 * 3_600_000, "0.001", "6"),
            row("BTCUSDT", start + 18 * 3_600_000, "0.001", "8"),
            row("BTCUSDT", start + 30 * 3_600_000, "0.001", "12"),
        ]
        result = qualify_funding_rows(symbol="BTCUSDT", rows=rows, source_hashes=["a" * 64])
        self.assertTrue(result.passed)
        self.assertEqual([point.interval_hours for point in result.points], ["4", "4", "6", "8", "12"])
        source = inspect.getsource(qualify_funding_rows)
        self.assertNotIn("interval_hours = 8", source)
        self.assertNotIn("or 8", source)

    def test_future_funding_value_is_rejected(self) -> None:
        start = IS_END_EXCLUSIVE_MS - 16 * 3_600_000
        rows = [
            row("ETHUSDT", start, "0.001", "8"),
            row("ETHUSDT", start + 8 * 3_600_000, "0.001", "8"),
            row("ETHUSDT", IS_END_EXCLUSIVE_MS, "-9", "8"),
        ]
        result = qualify_funding_rows(symbol="ETHUSDT", rows=rows, source_hashes=["a" * 64])
        self.assertFalse(result.passed)
        self.assertEqual(result.invalid_rows, 1)

    def test_identical_append_only_duplicates_do_not_override_or_conflict(self) -> None:
        start = 1_600_000_000_000
        original = row("BTCUSDT", start, "0.001", "8", "a" * 64)
        duplicate = row("BTCUSDT", start, "0.001", "8", "b" * 64)
        rows = [original, duplicate, row("BTCUSDT", start + 8 * 3_600_000, "0.002", "8")]
        result = qualify_funding_rows(symbol="BTCUSDT", rows=rows, source_hashes=["a" * 64, "b" * 64])
        self.assertTrue(result.passed)
        self.assertEqual(result.identical_duplicates, 1)
        self.assertEqual(result.conflicting_duplicates, 0)

    def test_conflicting_duplicate_and_missing_settlement_block(self) -> None:
        start = 1_600_000_000_000
        rows = [
            row("BTCUSDT", start, "0.001", "8"),
            row("BTCUSDT", start, "0.002", "8", "b" * 64),
            row("BTCUSDT", start + 16 * 3_600_000, "0.001", "8"),
        ]
        result = qualify_funding_rows(symbol="BTCUSDT", rows=rows, source_hashes=["a" * 64, "b" * 64])
        self.assertFalse(result.passed)
        self.assertEqual(result.conflicting_duplicates, 1)
        self.assertEqual(result.missing_settlements, 2)

    def test_m1b_and_m1g_semantics_are_blocked(self) -> None:
        self.assertIn("funding arbitrage", validate_research_scope_text("Funding arbitrage research"))
        self.assertIn("basis trade", validate_research_scope_text("Basis trade"))
        self.assertIn("panic trigger", validate_research_scope_text("Panic trigger"))
        self.assertEqual(validate_research_scope_text("settled funding sentiment and spot path"), [])

    def test_qualification_script_has_no_api_or_strategy_entry(self) -> None:
        text = (ROOT / "scripts/m1h_qualify_funding_data.py").read_text(encoding="utf-8").lower()
        for prohibited in ("binance_api_key", "create_order", "cancel_order", "place_order", "freqtrade trade"):
            self.assertNotIn(prohibited, text)


if __name__ == "__main__":
    unittest.main()
