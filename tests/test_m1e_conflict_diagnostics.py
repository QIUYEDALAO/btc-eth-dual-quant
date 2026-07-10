from __future__ import annotations

import unittest

from btc_eth_dual_quant.data.m1e_conflict_diagnostics import (
    calendar_budget,
    canonical_diagnostics_sha256,
    classify_aggregate_conflict,
    classify_monthly_daily_conflict,
    first_six_month_clean_suffix,
)


def row(timestamp: int = 0, volume: str = "10", close: str = "100") -> dict:
    return {
        "open_time": timestamp, "open": "99", "high": "101", "low": "98", "close": close,
        "volume": volume, "close_time": timestamp + 3_599_999, "quote_volume": volume,
        "trade_count": volume, "taker_buy_base_volume": volume, "taker_buy_quote_volume": volume,
    }


class M1EConflictDiagnosticTests(unittest.TestCase):
    def test_rest_confirmed_higher_timeframe_flow_revision_remains_contract_blocking(self) -> None:
        derived = row(volume="10")
        official = row(volume="11")
        result = classify_aggregate_conflict(symbol="BTCUSDT", month="2021-01", timeframe="4h", derived=derived, official=official, rest=official)
        self.assertEqual(result.classification, "higher_timeframe_flow_revision_confirmed_by_rest")
        self.assertFalse(result.resolved_for_contract)
        self.assertTrue(result.rest_matches_official)

    def test_price_difference_stays_unresolved(self) -> None:
        result = classify_aggregate_conflict(symbol="ETHUSDT", month="2021-04", timeframe="1h", derived=row(close="100"), official=row(close="101"), rest=None)
        self.assertEqual(result.classification, "unresolved_price_or_timestamp_conflict")
        self.assertFalse(result.resolved_for_contract)

    def test_monthly_daily_conflict_is_not_overridden_by_rest(self) -> None:
        monthly, daily = row(volume="10"), row(volume="12")
        result = classify_monthly_daily_conflict(symbol="BTCUSDT", month="2020-12", timeframe="5m", monthly=monthly, daily=daily, rest=monthly)
        self.assertEqual(result.classification, "monthly_daily_conflict_rest_supports_monthly")
        self.assertFalse(result.resolved_for_contract)

    def test_clean_suffix_and_calendar_are_diagnostic_only(self) -> None:
        states = [(f"2022-{month:02d}", "blocked" if month == 4 else "audit_complete") for month in range(1, 11)]
        self.assertEqual(first_six_month_clean_suffix(states), "2022-11-01")
        self.assertEqual(calendar_budget("2022-11-01", "2026-07-01"), (1338, 402))

    def test_hash_is_repeatable(self) -> None:
        item = classify_aggregate_conflict(symbol="BTCUSDT", month="2021-01", timeframe="4h", derived=row(volume="10"), official=row(volume="11"), rest=row(volume="11"))
        self.assertEqual(canonical_diagnostics_sha256([item]), canonical_diagnostics_sha256([item]))


if __name__ == "__main__":
    unittest.main()
