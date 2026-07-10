from __future__ import annotations

import unittest
from decimal import Decimal

from btc_eth_dual_quant.data.m1e_qualification import (
    INTERVAL_MS,
    LIQUIDITY_P95_MAXIMUM,
    aggregate_bars,
    build_canonical_5m,
    classify_audit_parity,
    compare_parity,
    determine_research_start,
    merge_archive_month,
    qualify_pair_month,
)
from btc_eth_dual_quant.data.minute_archive import month_bounds_ms


def row(timestamp: int, interval: str, value: str = "10", volume: str = "1") -> dict:
    return {
        "open_time": timestamp, "open": value, "high": str(Decimal(value) + 1),
        "low": str(Decimal(value) - 1), "close": value, "volume": volume,
        "close_time": timestamp + INTERVAL_MS[interval] - 1, "quote_volume": volume,
        "trade_count": "1", "taker_buy_base_volume": volume, "taker_buy_quote_volume": volume,
    }


class M1EDataQualificationTests(unittest.TestCase):
    def test_daily_only_fills_missing_and_never_overwrites_monthly(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        monthly = [row(start, "5m", "10")]
        daily = [row(start, "5m", "11"), row(start + INTERVAL_MS["5m"], "5m", "12")]
        result = merge_archive_month(symbol="BTCUSDT", month="2020-01", timeframe="5m", monthly_rows=monthly, daily_rows=daily)
        self.assertEqual(result.rows[0]["open"], "10")
        self.assertEqual(result.daily_fill_rows, 1)
        self.assertEqual(result.conflict_rows, 1)

    def test_canonical_5m_patches_only_rest_confirmed_daily_revision(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        monthly = [row(start, "5m", "10"), row(start + INTERVAL_MS["5m"], "5m", "20")]
        daily = [row(start, "5m", "11"), row(start + INTERVAL_MS["5m"], "5m", "21")]
        result = build_canonical_5m(
            monthly_rows=monthly, daily_rows=daily, rest_supported_daily_timestamps=[start]
        )
        self.assertEqual(result.rows[0]["open"], "11")
        self.assertEqual(result.rows[1]["open"], "20")
        self.assertEqual(result.patched_timestamps, (start,))
        self.assertEqual(result.unresolved_timestamps, (start + INTERVAL_MS["5m"],))
        self.assertIn("monthly_sha256", result.decisions[0])

    def test_higher_timeframe_flow_revision_is_audit_only(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        derived = row(start, "1h", "10", "1")
        official = dict(derived, volume="2", quote_volume="2", trade_count="2")
        evidence = classify_audit_parity([derived], [official])
        self.assertEqual(evidence.price_differences, 0)
        self.assertGreater(evidence.flow_differences, 0)
        self.assertEqual(evidence.classification, "audit_flow_revision_quarantined")

    def test_higher_timeframe_price_revision_is_quarantined_not_canonical(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        derived = row(start, "1h", "10")
        official = dict(derived, close="11")
        evidence = classify_audit_parity([derived], [official])
        self.assertGreater(evidence.price_differences, 0)
        self.assertEqual(evidence.classification, "audit_price_revision_quarantined")

    def test_canonical_hash_is_deterministic_after_confirmed_patch(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        monthly = [row(start, "5m", "10")]
        daily = [row(start, "5m", "11")]
        left = build_canonical_5m(
            monthly_rows=monthly, daily_rows=daily, rest_supported_daily_timestamps=[start]
        )
        right = build_canonical_5m(
            monthly_rows=reversed(monthly), daily_rows=reversed(daily),
            rest_supported_daily_timestamps=[start],
        )
        self.assertEqual(left.canonical_sha256, right.canonical_sha256)

    def test_twelve_5m_and_four_1h_aggregate_exactly(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        five = [row(start + index * INTERVAL_MS["5m"], "5m", str(10 + index), "0.1") for index in range(12)]
        one = aggregate_bars(five, "5m", "1h", "2020-01")
        self.assertEqual(len(one.rows), 1)
        self.assertEqual(one.rows[0]["open"], "10")
        self.assertEqual(one.rows[0]["close"], "21")
        self.assertEqual(one.rows[0]["volume"], "1.2")
        hours = [row(start + index * INTERVAL_MS["1h"], "1h", str(20 + index), "0.2") for index in range(4)]
        four = aggregate_bars(hours, "1h", "4h", "2020-01")
        self.assertEqual(len(four.rows), 1)
        self.assertEqual(four.rows[0]["volume"], "0.8")

    def test_missing_child_rejects_derived_bar(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        five = [row(start + index * INTERVAL_MS["5m"], "5m") for index in range(12) if index != 4]
        result = aggregate_bars(five, "5m", "1h", "2020-01")
        self.assertNotIn(start, {item["open_time"] for item in result.rows})
        self.assertIn(start, result.incomplete_buckets)

    def test_numeric_difference_blocks_but_format_only_does_not(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        base = row(start, "1h", "10")
        formatted = dict(base, open="10.0")
        evidence = compare_parity(symbol="BTCUSDT", month="2020-01", timeframe="1h", derived=[base], official=[formatted])
        self.assertEqual(evidence.numeric_differences, 0)
        self.assertGreater(evidence.format_only_fields, 0)
        changed = dict(base, close="12")
        self.assertGreater(compare_parity(symbol="BTCUSDT", month="2020-01", timeframe="1h", derived=[base], official=[changed]).numeric_differences, 0)

    def test_common_outage_is_quarantined_and_single_symbol_gap_blocks(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        full5 = [row(start + index * INTERVAL_MS["5m"], "5m") for index in range(12)]
        missing5 = full5[1:]
        official1 = [row(start, "1h")]
        official4 = [row(start, "4h")]
        archives = {}
        p1 = {}
        p4 = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            archives[(symbol, "5m")] = merge_archive_month(symbol=symbol, month="2020-01", timeframe="5m", monthly_rows=missing5)
            archives[(symbol, "1h")] = merge_archive_month(symbol=symbol, month="2020-01", timeframe="1h", monthly_rows=official1)
            archives[(symbol, "4h")] = merge_archive_month(symbol=symbol, month="2020-01", timeframe="4h", monthly_rows=official4)
            derived1 = aggregate_bars(missing5, "5m", "1h", "2020-01")
            derived4 = aggregate_bars(derived1.rows, "1h", "4h", "2020-01")
            p1[symbol] = compare_parity(symbol=symbol, month="2020-01", timeframe="1h", derived=derived1.rows, official=official1)
            p4[symbol] = compare_parity(symbol=symbol, month="2020-01", timeframe="4h", derived=derived4.rows, official=official4)
        result = qualify_pair_month(month="2020-01", archives=archives, one_hour_parity=p1, four_hour_parity=p4)
        self.assertEqual(result.state, "audit_complete_with_confirmed_outage")
        btc = archives[("BTCUSDT", "5m")]
        archives[("BTCUSDT", "5m")] = merge_archive_month(symbol="BTCUSDT", month="2020-01", timeframe="5m", monthly_rows=full5)
        blocked = qualify_pair_month(month="2020-01", archives=archives, one_hour_parity=p1, four_hour_parity=p4)
        self.assertEqual(blocked.state, "blocked")
        archives[("BTCUSDT", "5m")] = btc

    def test_aligned_early_close_is_outage_candidate_but_illegal_ohlc_blocks(self) -> None:
        start, _ = month_bounds_ms("2020-01")
        partial = row(start, "5m")
        partial["close_time"] = start + 30_000
        left = merge_archive_month(symbol="BTCUSDT", month="2020-01", timeframe="5m", monthly_rows=[partial])
        self.assertEqual(left.outage_candidate_timestamps, (start,))
        self.assertEqual(left.invalid_rows, 0)
        illegal = row(start, "5m")
        illegal["high"] = "1"
        right = merge_archive_month(symbol="BTCUSDT", month="2020-01", timeframe="5m", monthly_rows=[illegal])
        self.assertEqual(right.outage_candidate_timestamps, ())
        self.assertEqual(right.invalid_rows, 1)

    def test_research_start_uses_six_months_and_fixed_liquidity_only(self) -> None:
        from btc_eth_dual_quant.data.m1e_qualification import PairMonthQualification
        months = [f"2020-{month:02d}" for month in range(1, 7)]
        qualifications = [PairMonthQualification(month, "audit_complete", (), (), (), ()) for month in months]
        liquidity = {(symbol, month): Decimal("0.0029") for symbol in ("BTCUSDT", "ETHUSDT") for month in months}
        self.assertEqual(determine_research_start(qualifications, liquidity), "2020-07-01")
        liquidity[("ETHUSDT", "2020-03")] = Decimal("0.0031")
        self.assertIsNone(determine_research_start(qualifications, liquidity))
        self.assertEqual(LIQUIDITY_P95_MAXIMUM, Decimal("0.0030"))

    def test_qualification_source_has_no_strategy_or_trading_command(self) -> None:
        root = __import__("pathlib").Path(__file__).resolve().parents[1]
        source = "\n".join(
            (root / path).read_text(encoding="utf-8")
            for path in ("scripts/m1e_qualify_public_data.py", "scripts/m1e_requalify_canonical_5m.py")
        )
        forbidden = ("create_" + "order", "cancel_" + "order", "place_" + "order", "freqtrade " + "trade", "backtesting\"")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
