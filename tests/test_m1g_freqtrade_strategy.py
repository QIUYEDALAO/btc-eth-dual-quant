from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from btc_eth_dual_quant.audit.m1g_execution_repricing import (
    DetailBar,
    ExportedTrade,
    reprice_exported_trade,
    trade_from_export,
    validate_entry_timing,
)


ROOT = Path(__file__).resolve().parents[1]
STRATEGY_PATH = ROOT / "freqtrade_lab/user_data/strategies/M1GPanicDislocationMeanReversion.py"


class FakeTradeModel:
    closed = []

    @classmethod
    def get_trades_proxy(cls, **kwargs):
        del kwargs
        return cls.closed


def load_strategy_class():
    strategy_module = types.ModuleType("freqtrade.strategy")
    strategy_module.IStrategy = object
    persistence_module = types.ModuleType("freqtrade.persistence")
    persistence_module.Trade = FakeTradeModel
    freqtrade_module = types.ModuleType("freqtrade")
    freqtrade_module.strategy = strategy_module
    freqtrade_module.persistence = persistence_module
    sys.modules["freqtrade"] = freqtrade_module
    sys.modules["freqtrade.strategy"] = strategy_module
    sys.modules["freqtrade.persistence"] = persistence_module
    spec = importlib.util.spec_from_file_location("m1g_strategy", STRATEGY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.M1GPanicDislocationMeanReversion


class FakeDataProvider:
    def __init__(self, frames):
        self.frames = frames

    def get_pair_dataframe(self, pair: str, timeframe: str):
        if timeframe != "1h":
            raise AssertionError(timeframe)
        return self.frames[pair].copy()


def market_frame(*, event_indices=(), start="2024-01-01", periods=240):
    dates = pd.date_range(start=start, periods=periods, freq="1h", tz="UTC")
    closes = [100.0 + (0.05 if index % 2 else -0.05) for index in range(periods)]
    opens = list(closes)
    highs = [value + 0.1 for value in closes]
    lows = [value - 0.1 for value in closes]
    for index in event_indices:
        previous = closes[index - 1]
        opens[index] = previous
        closes[index] = previous * 0.97
        highs[index] = previous * 1.001
        lows[index] = previous * 0.968
    return pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": 100.0})


class M1GStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy_class = load_strategy_class()
        FakeTradeModel.closed = []

    def strategy(self, btc, eth):
        strategy = self.strategy_class()
        strategy.dp = FakeDataProvider({"BTC/USDT": btc, "ETH/USDT": eth})
        return strategy

    def test_fixed_lifecycle_and_research_config(self):
        strategy = self.strategy_class()
        self.assertFalse(strategy.can_short)
        self.assertEqual(strategy.stoploss, -0.04)
        self.assertEqual(strategy.minimal_roi, {"0": 0.018, "1440": -1})
        self.assertEqual(strategy.max_open_trades, 1)
        self.assertFalse(strategy.trailing_stop)
        self.assertFalse(strategy.position_adjustment_enable)
        config = json.loads((ROOT / "freqtrade_lab/user_data/configs/config.m1g-research.json").read_text())
        self.assertEqual(config["tradable_balance_ratio"], 0.25)
        self.assertEqual(config["max_open_trades"], 1)
        self.assertFalse(config["api_server"]["enabled"])
        self.assertNotIn("key", config["exchange"])
        self.assertNotIn("secret", config["exchange"])

    def test_exact_event_and_btc_tie_breaker(self):
        btc = market_frame(event_indices=(169,))
        eth = market_frame(event_indices=(169,))
        strategy = self.strategy(btc, eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        self.assertEqual(analyzed.iloc[169]["event_target"], "BTC/USDT")
        btc_entries = strategy.populate_entry_trend(analyzed, {"pair": "BTC/USDT"})
        eth_entries = strategy.populate_entry_trend(analyzed, {"pair": "ETH/USDT"})
        self.assertEqual(int(btc_entries["enter_long"].sum()), 1)
        self.assertEqual(int(eth_entries["enter_long"].sum()), 0)

    def test_stronger_eth_is_unique_winner(self):
        btc = market_frame(event_indices=(169,))
        eth = market_frame(event_indices=(169,))
        eth.loc[169, "close"] = eth.loc[168, "close"] * 0.965
        eth.loc[169, "low"] = eth.loc[168, "close"] * 0.963
        strategy = self.strategy(btc, eth)
        analyzed = strategy.populate_indicators(btc, {"pair": "BTC/USDT"})
        self.assertEqual(analyzed.iloc[169]["event_target"], "ETH/USDT")

    def test_connected_24h_cluster_keeps_only_first_raw_event(self):
        features = self.strategy_class._event_features(market_frame(event_indices=(169, 189, 209)), "btc")
        self.assertTrue(bool(features.iloc[169]["btc_cluster_event"]))
        self.assertFalse(bool(features.iloc[189]["btc_cluster_event"]))
        self.assertFalse(bool(features.iloc[209]["btc_cluster_event"]))

    def test_gap_resets_169_bar_warmup(self):
        frame = market_frame(event_indices=(200,))
        frame = frame.drop(index=100).reset_index(drop=True)
        features = self.strategy_class._event_features(frame, "btc")
        event_row = features.loc[features["date"] == pd.Timestamp("2024-01-09 08:00:00+00:00")].iloc[0]
        self.assertFalse(bool(event_row["btc_cluster_event"]))

    def test_future_row_does_not_change_existing_features(self):
        base = market_frame(event_indices=(169,))
        first = self.strategy_class._event_features(base, "btc")
        future = market_frame(start="2024-01-11", periods=1)
        future.loc[0, ["open", "high", "low", "close"]] = [1.0, 2.0, 0.5, 1.5]
        extended = self.strategy_class._event_features(pd.concat([base, future], ignore_index=True), "btc")
        pd.testing.assert_frame_equal(first, extended.iloc[:-1].reset_index(drop=True))

    def test_global_cooldown_uses_all_pairs(self):
        strategy = self.strategy_class()
        now = datetime(2026, 1, 4, tzinfo=UTC)
        FakeTradeModel.closed = [types.SimpleNamespace(close_date_utc=now - timedelta(hours=71), pair="ETH/USDT")]
        self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 1, "gtc", now, None, "long"))
        FakeTradeModel.closed = [types.SimpleNamespace(close_date_utc=now - timedelta(hours=73), pair="ETH/USDT")]
        self.assertTrue(strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 1, "gtc", now, None, "long"))

    def test_entry_time_is_after_completed_event(self):
        event = datetime(2025, 1, 1, 12, tzinfo=UTC)
        self.assertTrue(validate_entry_timing(event, event))
        self.assertEqual(validate_entry_timing(event, event + timedelta(hours=1)), [])


class M1GExecutionRepricingTests(unittest.TestCase):
    def trade(self, close_time=None, close_rate=101.8):
        opened = datetime(2025, 1, 1, tzinfo=UTC)
        return ExportedTrade("BTC/USDT", opened, close_time or opened + timedelta(minutes=5), 100.0, close_rate, 250.0)

    def bars(self, values):
        opened = datetime(2025, 1, 1, tzinfo=UTC)
        return [DetailBar(opened + timedelta(minutes=5 * i), *value) for i, value in enumerate(values)]

    def test_same_bar_target_and_stop_resolves_to_worse_stop_open(self):
        result = reprice_exported_trade(self.trade(), self.bars([(95.0, 102.0, 94.0, 100.0), (100, 100, 100, 100)]))
        self.assertEqual(result.audited_exit_reason, "stop")
        self.assertEqual(result.audited_close_rate, 95.0)
        self.assertFalse(result.native_exit_bar_matches)

    def test_target_gap_receives_exact_target(self):
        result = reprice_exported_trade(self.trade(close_time=datetime(2025, 1, 1, tzinfo=UTC)), self.bars([(103.0, 104.0, 102.0, 103.0)]))
        self.assertEqual(result.audited_exit_reason, "target")
        self.assertAlmostEqual(result.audited_close_rate, 101.8)
        self.assertTrue(result.native_exit_bar_matches)

    def test_timeout_uses_first_5m_open_at_or_after_24h(self):
        values = [(100.0, 101.0, 99.0, 100.0)] * 289
        close_time = datetime(2025, 1, 2, tzinfo=UTC)
        result = reprice_exported_trade(self.trade(close_time=close_time, close_rate=100.0), self.bars(values))
        self.assertEqual(result.audited_exit_reason, "timeout")
        self.assertEqual(result.audited_close_time, close_time)

    def test_cost_returns_are_monotonic_and_hash_is_repeatable(self):
        bars = self.bars([(100.0, 102.0, 99.0, 101.8)])
        first = reprice_exported_trade(self.trade(close_time=datetime(2025, 1, 1, tzinfo=UTC)), bars)
        second = reprice_exported_trade(self.trade(close_time=datetime(2025, 1, 1, tzinfo=UTC)), bars)
        values = [value for _, value in first.net_returns]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(first.canonical_sha256, second.canonical_sha256)

    def test_input_rejects_signal_selection_fields_and_discontinuous_bars(self):
        payload = {"pair": "BTC/USDT", "open_date": "2025-01-01T00:00:00Z", "close_date": "2025-01-01T00:05:00Z", "open_rate": 100, "close_rate": 101, "stake_amount": 250, "signal": "x"}
        with self.assertRaises(ValueError):
            trade_from_export(payload)
        with self.assertRaisesRegex(ValueError, "continuous"):
            reprice_exported_trade(self.trade(), [
                DetailBar(datetime(2025, 1, 1, tzinfo=UTC), 100, 101, 99, 100),
                DetailBar(datetime(2025, 1, 1, 0, 10, tzinfo=UTC), 100, 102, 99, 101),
            ])


if __name__ == "__main__":
    unittest.main()
