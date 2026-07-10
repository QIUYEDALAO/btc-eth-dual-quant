from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from btc_eth_dual_quant.data.minute_archive import (
    MINUTE_MS,
    MinuteArchiveManifest,
    MinuteMonthEvidence,
    analyze_month,
    compare_rest_sample,
    determine_research_start,
    deterministic_rest_sample_months,
    expected_minute_rows,
    month_bounds_ms,
    render_minute_archive_report,
)


def row(timestamp: int, close: str = "100") -> dict[str, object]:
    return {
        "open_time": timestamp,
        "open": "100",
        "high": "100.01",
        "low": "99.99",
        "close": close,
        "volume": "10",
        "close_time": timestamp + MINUTE_MS - 1,
        "quote_volume": "1000",
        "trade_count": 5,
        "taker_buy_base_volume": "4",
        "taker_buy_quote_volume": "400",
    }


def qualifying(symbol: str, month: str) -> MinuteMonthEvidence:
    return MinuteMonthEvidence(
        symbol=symbol,
        month=month,
        expected_rows=1,
        observed_rows=1,
        first_open_ms=0,
        last_open_ms=0,
        monthly_zip_rows=1,
        daily_supplement_rows=0,
        daily_fetch_failures=0,
        duplicate_rows=0,
        invalid_rows=0,
        missing_rows=0,
        max_contiguous_gap=0,
        completeness="1.0000000000",
        p95_spread_proxy="0.0001000000",
        monthly_zip_sha256="a" * 64,
        daily_bundle_sha256="",
        rest_evidence_complete=True,
        rest_sampled=False,
        rest_sample_passed=True,
        audit_state="audit_complete",
        qualifies=True,
    )


class MinuteArchiveTests(unittest.TestCase):
    def test_expected_rows_and_daily_supplement_fill_without_overwrite(self) -> None:
        month = "2020-02"
        start, end = month_bounds_ms(month)
        missing = start + 10 * MINUTE_MS
        monthly = [row(timestamp) for timestamp in range(start, end, MINUTE_MS) if timestamp != missing]
        supplement = [row(missing), row(start, close="999")]
        evidence = analyze_month(
            symbol="BTCUSDT",
            month=month,
            monthly_rows=monthly,
            supplemental_rows=supplement,
            monthly_zip_sha256="a" * 64,
            daily_bundle_sha256="b" * 64,
            rest_evidence_complete=True,
        )
        self.assertEqual(expected_minute_rows(month), 29 * 24 * 60)
        self.assertEqual(evidence.observed_rows, evidence.expected_rows)
        self.assertLessEqual(float(evidence.completeness), 1.0)
        self.assertEqual(evidence.daily_supplement_rows, 1)
        self.assertEqual(evidence.missing_rows, 0)
        self.assertEqual(evidence.audit_state, "audit_complete")

    def test_off_grid_monthly_rows_are_invalid_and_do_not_raise_completeness_above_one(self) -> None:
        month = "2020-01"
        start, end = month_bounds_ms(month)
        monthly = [row(timestamp) for timestamp in range(start, end, MINUTE_MS)]
        monthly.extend(row(timestamp + 20_799) for timestamp in range(start, start + 20 * MINUTE_MS, MINUTE_MS))
        evidence = analyze_month(
            symbol="BTCUSDT",
            month=month,
            monthly_rows=monthly,
            monthly_zip_sha256="a" * 64,
            rest_evidence_complete=True,
        )
        self.assertEqual(evidence.observed_rows, evidence.expected_rows)
        self.assertEqual(evidence.completeness, "1.0000000000")
        self.assertEqual(evidence.invalid_rows, 20)
        self.assertEqual(evidence.audit_state, "blocked")

    def test_missing_or_invalid_rows_block_month(self) -> None:
        month = "2020-01"
        start, end = month_bounds_ms(month)
        rows = [row(timestamp) for timestamp in range(start, end, MINUTE_MS)]
        rows.pop(10)
        rows[20]["high"] = "90"
        evidence = analyze_month(
            symbol="ETHUSDT",
            month=month,
            monthly_rows=rows,
            monthly_zip_sha256="a" * 64,
            rest_evidence_complete=True,
        )
        self.assertEqual(evidence.missing_rows, 1)
        self.assertEqual(evidence.invalid_rows, 1)
        self.assertEqual(evidence.audit_state, "blocked")
        self.assertFalse(evidence.qualifies)

    def test_listing_month_does_not_treat_pre_listing_minutes_as_gaps(self) -> None:
        month = "2017-08"
        start, end = month_bounds_ms(month)
        listing = start + 16 * 24 * 60 * MINUTE_MS
        rows = [row(timestamp) for timestamp in range(listing, end, MINUTE_MS)]
        evidence = analyze_month(
            symbol="BTCUSDT",
            month=month,
            monthly_rows=rows,
            monthly_zip_sha256="a" * 64,
            rest_evidence_complete=True,
            allow_inception_partial=True,
        )
        self.assertEqual(evidence.expected_rows, len(rows))
        self.assertEqual(evidence.missing_rows, 0)
        self.assertEqual(evidence.audit_state, "audit_complete")

    def test_rest_sample_exact_match_passes_and_difference_blocks(self) -> None:
        archive = [row(0), row(MINUTE_MS)]
        matching = compare_rest_sample(
            month="2020-01",
            reason="first",
            start_ms=0,
            archive_rows=archive,
            rest_rows=[dict(item) for item in archive],
        )
        self.assertTrue(matching.passed)
        changed = [dict(item) for item in archive]
        changed[1]["close"] = "101"
        mismatch = compare_rest_sample(
            month="2020-01",
            reason="first",
            start_ms=0,
            archive_rows=archive,
            rest_rows=changed,
        )
        self.assertFalse(mismatch.passed)
        self.assertEqual(mismatch.field_differences, 1)

    def test_rest_sample_plan_is_deterministic_and_has_required_scopes(self) -> None:
        months = [f"2020-{month:02d}" for month in range(1, 13)]
        first = deterministic_rest_sample_months(months, "BTCUSDT", random_count=2)
        second = deterministic_rest_sample_months(months, "BTCUSDT", random_count=2)
        self.assertEqual(first, second)
        self.assertIn("first", first["2020-01"])
        self.assertIn("middle", first["2020-07"])
        self.assertIn("latest_complete", first["2020-12"])
        self.assertIn("stress", first["2020-03"])

    def test_research_start_requires_both_symbols_for_six_consecutive_months(self) -> None:
        months = [f"2018-{month:02d}" for month in range(1, 7)]
        evidence = [qualifying(symbol, month) for symbol in ("BTCUSDT", "ETHUSDT") for month in months]
        self.assertEqual(determine_research_start(evidence), "2019-01-01")
        blocked = [
            replace(item, qualifies=False, audit_state="blocked")
            if item.symbol == "ETHUSDT" and item.month == "2018-04"
            else item
            for item in evidence
        ]
        self.assertIsNone(determine_research_start(blocked))

    def test_report_is_sanitized_and_does_not_approve_strategy(self) -> None:
        evidence = tuple(qualifying(symbol, "2020-01") for symbol in ("BTCUSDT", "ETHUSDT"))
        sample = compare_rest_sample(
            month="2020-01",
            reason="first",
            start_ms=0,
            archive_rows=[row(0)],
            rest_rows=[row(0)],
        )
        manifest = MinuteArchiveManifest(
            generated_utc="2026-07-10T00:00:00Z",
            requested_start="2020-01-01T00:00:00+00:00",
            requested_end="2020-01-31T23:59:59.999000+00:00",
            symbols=("BTCUSDT", "ETHUSDT"),
            months=evidence,
            rest_samples=(sample,),
            research_start="2020-02-01",
        )
        report = render_minute_archive_report(manifest)
        self.assertIn("Strategy returns computed: no", report)
        self.assertIn("M1D strategy code authorized: no", report)
        self.assertIn("M2 authorized: no", report)
        self.assertNotIn("BINANCE_API_KEY", report)

    def test_t1_script_contains_no_private_or_trading_entry(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "scripts" / "t1_build_minute_archive.py").read_text(
            encoding="utf-8"
        )
        for forbidden in ("BINANCE_API_KEY", "BINANCE_API_SECRET", "create_order", "cancel_order", "place_order"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
