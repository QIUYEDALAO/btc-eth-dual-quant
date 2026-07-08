from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from btc_eth_dual_quant.backtest.skeleton import (
    LookaheadBiasError,
    MarketBar,
    assert_feature_available,
    schedule_next_open,
)
from btc_eth_dual_quant.data import binance
from btc_eth_dual_quant.data.binance import BinanceClientError, BinanceReadOnlyRestClient
from btc_eth_dual_quant.data.costs import (
    compute_roundtrip_cost,
    funding_payback_threshold,
    parse_futures_commission,
    parse_spot_commission,
)
from btc_eth_dual_quant.data.funding import annualize_funding_rate, infer_funding_interval_hours
from btc_eth_dual_quant.data.quality import (
    compare_zip_rest_klines,
    detect_kline_gaps,
    flag_kline_anomalies,
    missing_archive_days,
)
from btc_eth_dual_quant.data.registry import load_registry
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore


ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_registry_covers_all_v1_1_table_9_items(self) -> None:
        registry = load_registry(ROOT / "data_registry.yaml")
        self.assertEqual(len(registry.datasets), 20)
        required = {
            "name",
            "source",
            "endpoint",
            "fields",
            "granularity",
            "history_start",
            "retention_limit",
            "update_freq",
            "table",
            "validations",
            "fallback",
            "consumers",
        }
        for record in registry.datasets:
            dumped = record.model_dump()
            self.assertTrue(required.issubset(dumped.keys()))

    def test_m0_enabled_records_match_requested_collectors(self) -> None:
        enabled = {record.name for record in load_registry(ROOT / "data_registry.yaml").enabled_records()}
        self.assertEqual(
            enabled,
            {
                "spot_klines",
                "um_futures_klines",
                "funding_rate_history",
                "premium_index",
                "funding_info",
                "mark_price_klines",
                "index_price_klines",
                "premium_index_klines",
                "open_interest",
                "order_book_depth",
                "funding_income",
                "commissions",
                "exchange_rules",
            },
        )


class StorageAndCollectorTests(unittest.TestCase):
    def test_raw_store_is_append_only_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AppendOnlyRawStore(tmp)
            store.append("spot_klines", "test", "GET /api/v3/klines", {"symbol": "BTCUSDT"}, [[1]])
            store.append("spot_klines", "test", "GET /api/v3/klines", {"symbol": "BTCUSDT"}, [[2]])
            records = store.iter_envelopes("spot_klines")
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].payload, [[1]])
            self.assertEqual(records[1].payload, [[2]])

    def test_client_rejects_trading_paths(self) -> None:
        with self.assertRaises(BinanceClientError):
            BinanceReadOnlyRestClient._assert_read_only("/api/v3/order")
        with self.assertRaises(BinanceClientError):
            BinanceReadOnlyRestClient._assert_read_only("/fapi/v1/countdownCancelAll")


class FundingTests(unittest.TestCase):
    def test_funding_info_has_priority_when_consistent(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            funding_info={"symbol": "BTCUSDT", "fundingIntervalHours": 4},
            premium_index={"symbol": "BTCUSDT", "time": 0, "nextFundingTime": 14_400_000},
            funding_rate_history=[
                {"symbol": "BTCUSDT", "fundingTime": 0},
                {"symbol": "BTCUSDT", "fundingTime": 14_400_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "fundingInfo.fundingIntervalHours")
        self.assertEqual(result.warnings, [])

    def test_conflict_uses_shorter_interval_and_warns(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            funding_info={"symbol": "BTCUSDT", "fundingIntervalHours": 8},
            premium_index={"symbol": "BTCUSDT", "time": 0, "nextFundingTime": 14_400_000},
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "conflict_shorter_interval")
        self.assertTrue(result.warnings)

    def test_premium_index_fallback(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            premium_index={"symbol": "BTCUSDT", "time": 1000, "nextFundingTime": 14_401_000},
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "premiumIndex.nextFundingTime")

    def test_history_fallback_and_annualization(self) -> None:
        result = infer_funding_interval_hours(
            "ETHUSDT",
            funding_rate_history=[
                {"symbol": "ETHUSDT", "fundingTime": 0},
                {"symbol": "ETHUSDT", "fundingTime": 21_600_000},
                {"symbol": "ETHUSDT", "fundingTime": 43_200_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("6"))
        self.assertEqual(annualize_funding_rate("0.001", result.hours), Decimal("1.460"))


class CostTests(unittest.TestCase):
    def test_parse_commissions_and_roundtrip_cost(self) -> None:
        spot = parse_spot_commission(
            {"standardCommission": {"maker": "0.001", "taker": "0.001"}, "discount": {"discount": "0.25"}}
        )
        futures = parse_futures_commission({"makerCommissionRate": "0.0002", "takerCommissionRate": "0.0005"})
        cost = compute_roundtrip_cost(spot.taker, futures.taker, "0.0005")
        self.assertEqual(futures.taker, Decimal("0.0005"))
        self.assertEqual(cost.total_rate, Decimal("0.0050"))

    def test_payback_threshold(self) -> None:
        result = funding_payback_threshold("0.20", 14, "0.005", "2.0")
        self.assertEqual(result.expected_funding_income_rate, Decimal("0.007671232876712328767123287672"))
        self.assertFalse(result.passes)
        self.assertTrue(funding_payback_threshold("0.40", 14, "0.005", "2.0").passes)


class QualityTests(unittest.TestCase):
    def test_gap_detection_blocks_only_over_three_missing_bars(self) -> None:
        rows = [{"open_time": 0}, {"open_time": 60_000}, {"open_time": 5 * 60_000}]
        report = detect_kline_gaps(rows, "1m")
        self.assertEqual(report.gaps[0].missing_count, 3)
        self.assertFalse(report.blocks_backtest)
        rows.append({"open_time": 10 * 60_000})
        self.assertTrue(detect_kline_gaps(rows, "1m").blocks_backtest)

    def test_zip_rest_compare_and_anomaly_flags(self) -> None:
        left = [{"open_time": 1, "open": "100", "high": "110", "low": "90", "close": "100", "volume": "10", "quote_volume": "1000"}]
        right = [{"open_time": 1, "open": "100.2", "high": "110", "low": "90", "close": "100", "volume": "10", "quote_volume": "1000"}]
        self.assertEqual(compare_zip_rest_klines(left, right)[0].field, "open")
        anomalies = flag_kline_anomalies(
            [{"open_time": 1, "open": "100", "high": "140", "low": "90", "close": "100", "volume": "0"}]
        )
        self.assertEqual({item.reason for item in anomalies}, {"amplitude_gt_30pct", "zero_volume"})

    def test_archive_completeness_missing_days(self) -> None:
        records = [{"time": 0}, {"time": 2 * 24 * 60 * 60 * 1000}]
        self.assertEqual(missing_archive_days(records, "time", "1970-01-01", "1970-01-03"), ["1970-01-02"])


class BacktestTimeSemanticsTests(unittest.TestCase):
    def test_decision_schedules_next_bar_open(self) -> None:
        bars = [
            MarketBar(0, 59_999, "1", "2", "1", "2"),
            MarketBar(60_000, 119_999, "2", "3", "2", "3"),
        ]
        decision = schedule_next_open(bars, 0, "signal_after_close")
        self.assertEqual(decision.decision_time_ms, 59_999)
        self.assertEqual(decision.earliest_effective_time_ms, 60_000)

    def test_feature_after_decision_is_lookahead(self) -> None:
        with self.assertRaises(LookaheadBiasError):
            assert_feature_available(100, 99)
        with self.assertRaises(LookaheadBiasError):
            schedule_next_open([MarketBar(0, 1, "1", "1", "1", "1")], 0, "no_next_bar")

    def test_current_bar_close_fill_is_rejected(self) -> None:
        bars = [
            MarketBar(0, 59_999, "1", "2", "1", "2"),
            MarketBar(59_999, 119_999, "2", "3", "2", "3"),
        ]
        with self.assertRaises(LookaheadBiasError):
            schedule_next_open(bars, 0, "same_close_fill")


class M0GuardrailTests(unittest.TestCase):
    def test_no_execution_live_tree_created(self) -> None:
        self.assertFalse((ROOT / "execution" / "live").exists())
        self.assertFalse((ROOT / "src" / "execution" / "live").exists())
        self.assertFalse((ROOT / "src" / "btc_eth_dual_quant" / "execution").exists())

    def test_no_trading_endpoint_implementation(self) -> None:
        source = inspect.getsource(binance)
        forbidden_literals = [
            '"/api/v3/order"',
            '"/fapi/v1/order"',
            "POST",
            "DELETE",
            "place_order",
            "cancel_order",
            "simulate_fill",
            "matching_engine",
        ]
        for literal in forbidden_literals:
            self.assertNotIn(literal, source)


if __name__ == "__main__":
    unittest.main()
