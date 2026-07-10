from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.data.golden_data import (
    aggregate_klines,
    build_golden_month,
    compare_official_klines,
    quarantine_sha256,
    parse_freqtrade_list_data,
    validate_freqtrade_runtime_evidence,
    write_freqtrade_jsongz,
)
from btc_eth_dual_quant.data.minute_archive import MINUTE_MS, month_bounds_ms


def row(timestamp: int, *, opened: str = "100.0", high: str = "101.0", low: str = "99.0", close: str = "100.5", volume: str = "1.1") -> dict:
    return {
        "open_time": timestamp,
        "open": opened,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "close_time": timestamp + MINUTE_MS - 1,
        "quote_volume": "110.0",
        "trade_count": "2",
        "taker_buy_base_volume": "0.4",
        "taker_buy_quote_volume": "40.0",
    }


class GoldenMonthTests(unittest.TestCase):
    def test_daily_fills_missing_but_never_overwrites_monthly(self) -> None:
        start, end = month_bounds_ms("2024-01")
        monthly = [row(timestamp) for timestamp in range(start, end, MINUTE_MS)]
        missing = monthly.pop(10)
        daily = [row(missing["open_time"], close="101.0"), row(start, close="999.0", high="999.0")]
        result = build_golden_month(symbol="BTCUSDT", month="2024-01", monthly_rows=monthly, daily_rows=daily)
        indexed = {item["open_time"]: item for item in result.rows}
        self.assertEqual(indexed[start]["close"], "100.5")
        self.assertEqual(indexed[missing["open_time"]]["close"], "101.0")
        self.assertEqual(result.state, "blocked")
        self.assertEqual(result.conflict_rows, 1)

    def test_off_grid_monthly_row_is_quarantined(self) -> None:
        start, end = month_bounds_ms("2024-01")
        monthly = [row(timestamp) for timestamp in range(start, end, MINUTE_MS)]
        monthly.append(row(start + 20_799))
        result = build_golden_month(symbol="ETHUSDT", month="2024-01", monthly_rows=monthly)
        self.assertEqual(result.invalid_rows, 1)
        self.assertIn("invalid_or_off_grid_monthly_row", {item.reason for item in result.quarantine})
        self.assertEqual(result.state, "blocked")

    def test_malformed_timestamp_and_duplicate_daily_row_are_quarantined(self) -> None:
        start, _ = month_bounds_ms("2024-01")
        malformed = row(start)
        malformed["open_time"] = "not-a-timestamp"
        daily = [row(start), row(start)]
        result = build_golden_month(
            symbol="ETHUSDT",
            month="2024-01",
            monthly_rows=[malformed],
            daily_rows=daily,
            enforce_complete_month=False,
        )
        reasons = {item.reason for item in result.quarantine}
        self.assertIn("invalid_or_off_grid_monthly_row", reasons)
        self.assertIn("duplicate_daily_timestamp", reasons)

    def test_hash_is_repeatable(self) -> None:
        start, end = month_bounds_ms("2024-01")
        monthly = [row(timestamp) for timestamp in range(start, end, MINUTE_MS)]
        first = build_golden_month(symbol="BTCUSDT", month="2024-01", monthly_rows=monthly)
        second = build_golden_month(symbol="BTCUSDT", month="2024-01", monthly_rows=reversed(monthly))
        self.assertEqual(first.canonical_sha256, second.canonical_sha256)
        self.assertEqual(quarantine_sha256(first.quarantine), quarantine_sha256(second.quarantine))


class AggregateTests(unittest.TestCase):
    def test_decimal_aggregation_for_five_and_fifteen_minutes(self) -> None:
        rows = [row(index * MINUTE_MS, volume="0.1") for index in range(15)]
        five = aggregate_klines(rows, "5m")
        fifteen = aggregate_klines(rows, "15m")
        self.assertEqual(len(five.rows), 3)
        self.assertEqual(len(fifteen.rows), 1)
        self.assertEqual(fifteen.rows[0]["volume"], "1.5")
        self.assertEqual(fifteen.rows[0]["trade_count"], "30")
        self.assertEqual(fifteen.rows[0]["close_time"], 15 * MINUTE_MS - 1)

    def test_missing_minute_rejects_bucket(self) -> None:
        rows = [row(index * MINUTE_MS) for index in range(15) if index != 7]
        result = aggregate_klines(rows, "15m")
        self.assertEqual(result.rows, ())
        self.assertEqual(result.incomplete_buckets, (0,))


class OfficialComparisonTests(unittest.TestCase):
    def test_format_only_is_nonblocking(self) -> None:
        derived = aggregate_klines([row(index * MINUTE_MS) for index in range(15)], "15m").rows
        official = [dict(derived[0], open="100.000", volume="16.5000")]
        comparison = compare_official_klines(symbol="BTCUSDT", month="2024-01", derived_rows=derived, official_rows=official)
        self.assertTrue(comparison.passed)
        self.assertGreater(comparison.format_only_fields, 0)
        self.assertEqual(comparison.numeric_differences, 0)

    def test_numeric_or_timestamp_difference_blocks(self) -> None:
        derived = aggregate_klines([row(index * MINUTE_MS) for index in range(15)], "15m").rows
        changed = [dict(derived[0], close="102")]
        numeric = compare_official_klines(symbol="BTCUSDT", month="2024-01", derived_rows=derived, official_rows=changed)
        self.assertFalse(numeric.passed)
        shifted = [dict(derived[0], open_time=15 * MINUTE_MS)]
        timestamp = compare_official_klines(symbol="BTCUSDT", month="2024-01", derived_rows=derived, official_rows=shifted)
        self.assertFalse(timestamp.passed)
        self.assertEqual(timestamp.derived_only_rows, 1)
        self.assertEqual(timestamp.official_only_rows, 1)

    def test_duplicate_official_timestamp_blocks(self) -> None:
        derived = aggregate_klines([row(index * MINUTE_MS) for index in range(15)], "15m").rows
        comparison = compare_official_klines(
            symbol="ETHUSDT", month="2024-01", derived_rows=derived, official_rows=[derived[0], derived[0]]
        )
        self.assertFalse(comparison.passed)
        self.assertEqual(comparison.invalid_official_rows, 1)


class FreqtradeCacheTests(unittest.TestCase):
    def test_jsongz_schema_and_hash_are_deterministic(self) -> None:
        rows = [row(0), row(MINUTE_MS)]
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json.gz"
            second = Path(directory) / "second.json.gz"
            first_hash = write_freqtrade_jsongz(first, rows)
            second_hash = write_freqtrade_jsongz(second, rows)
            self.assertEqual(first_hash, second_hash)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with gzip.open(first, "rt", encoding="utf-8") as source:
                payload = json.load(source)
        self.assertEqual(len(payload[0]), 6)
        self.assertEqual(payload[0][0], 0)

    def test_runtime_evidence_requires_all_six_exact_cache_entries(self) -> None:
        rows = []
        expected = (
            ("BTC/USDT", "1m", "2026-06-30 23:59:00", 1445760),
            ("BTC/USDT", "5m", "2026-06-30 23:55:00", 289152),
            ("BTC/USDT", "15m", "2026-06-30 23:45:00", 96384),
            ("ETH/USDT", "1m", "2026-06-30 23:59:00", 1445760),
            ("ETH/USDT", "5m", "2026-06-30 23:55:00", 289152),
            ("ETH/USDT", "15m", "2026-06-30 23:45:00", 96384),
        )
        for pair, timeframe, end, count in expected:
            rows.append(
                f"│ {pair} │ {timeframe} │ spot │ 2023-10-01 00:00:00 │ {end} │ {count} │"
            )
        entries = parse_freqtrade_list_data("freqtrade 2026.6\n" + "\n".join(rows))
        evidence = {
            "status": "pass",
            "image_ref": "freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6",
            "version": "freqtrade 2026.6",
            "command": "list-data",
            "api_key_used": False,
            "entries": [item.__dict__ for item in entries],
        }
        self.assertTrue(validate_freqtrade_runtime_evidence(evidence))
        evidence["entries"] = evidence["entries"][:-1]
        self.assertFalse(validate_freqtrade_runtime_evidence(evidence))

    def test_t2_source_has_no_private_or_trading_logic(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts" / "t2_build_golden_data.py").read_text(encoding="utf-8")
        for forbidden in ("BINANCE_API_KEY", "BINANCE_API_SECRET", "create_order", "cancel_order", "place_order", "freqtrade trade"):
            self.assertNotIn(forbidden, source)

    def test_freqtrade_research_configs_pin_jsongz(self) -> None:
        root = Path(__file__).resolve().parents[1]
        config_root = root / "freqtrade_lab" / "user_data" / "configs"
        for path in config_root.glob("*.json"):
            config = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(config.get("dataformat_ohlcv"), "jsongz", path.name)


if __name__ == "__main__":
    unittest.main()
