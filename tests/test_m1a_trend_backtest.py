from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.backtest.indicators import atr, donchian_high, donchian_low, realized_volatility, sma
from btc_eth_dual_quant.backtest.metrics import Trade
from btc_eth_dual_quant.backtest.m0_data import load_funding_records, load_spot_bars
from btc_eth_dual_quant.backtest.skeleton import LookaheadBiasError
from btc_eth_dual_quant.backtest.trend_engine import (
    Segment,
    parameter_neighborhood,
    position_size,
    remove_best_trades_effect,
    run_trend_backtest,
    segment_result,
    split_in_sample_oos,
)
from btc_eth_dual_quant.backtest.trend_strategy import (
    FundingRecord,
    TrendBar,
    TrendParams,
    assert_no_same_bar_fill,
    generate_trend_signals,
)
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m1a_run_trend_backtest import evaluate_m1a_gates, render_report


DAY_MS = 86_400_000


def make_bars(symbol: str = "BTCUSDT", count: int = 80) -> list[TrendBar]:
    bars: list[TrendBar] = []
    price = 100.0
    for idx in range(count):
        if idx < 20:
            close = price + 0.5
        elif idx < 45:
            close = price + 2.0
        elif idx < 60:
            close = price - 1.5
        else:
            close = price + 1.0
        open_price = price
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        bars.append(
            TrendBar(
                symbol=symbol,
                open_time_ms=idx * DAY_MS,
                close_time_ms=(idx + 1) * DAY_MS - 1,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=1000.0 + idx,
            )
        )
        price = close
    return bars


class M1AIndicatorTests(unittest.TestCase):
    def test_indicator_correctness_and_no_future_change(self) -> None:
        values = [1.0, 2.0, 3.0, 100.0]
        self.assertEqual(sma(values, 3)[:3], [None, None, 2.0])
        changed_future = [1.0, 2.0, 3.0, 999.0]
        self.assertEqual(sma(values, 3)[:3], sma(changed_future, 3)[:3])

    def test_donchian_excludes_current_bar(self) -> None:
        highs = [10.0, 11.0, 12.0, 99.0]
        lows = [10.0, 9.0, 8.0, 1.0]
        self.assertEqual(donchian_high(highs, 3)[3], 12.0)
        self.assertEqual(donchian_low(lows, 3)[3], 8.0)

    def test_atr_and_realized_volatility(self) -> None:
        highs = [12.0, 14.0, 13.0]
        lows = [9.0, 10.0, 11.0]
        closes = [10.0, 12.0, 12.0]
        self.assertEqual(atr(highs, lows, closes, 2), [None, 3.5, 3.0])
        self.assertIsNone(realized_volatility(closes, 2)[1])
        self.assertIsNotNone(realized_volatility(closes, 2)[2])


class M1ATrendStrategyTests(unittest.TestCase):
    def test_signal_after_close_and_next_open_fill(self) -> None:
        bars = make_bars(count=30)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        signals = [signal for signal in generate_trend_signals(bars, [], params) if signal.action == "enter_long"]
        self.assertTrue(signals)
        signal = signals[0]
        self.assertEqual(signal.decision_time_ms, bars[signal.decision_bar_index].close_time_ms)
        self.assertEqual(signal.earliest_fill_time_ms, bars[signal.decision_bar_index + 1].open_time_ms)

    def test_same_bar_close_fill_rejected(self) -> None:
        bars = make_bars(count=30)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        signal = [item for item in generate_trend_signals(bars, [], params) if item.action == "enter_long"][0]
        bad_signal = type(signal)(
            **{**signal.__dict__, "earliest_fill_time_ms": bars[signal.decision_bar_index].close_time_ms}
        )
        with self.assertRaises(LookaheadBiasError):
            assert_no_same_bar_fill(bad_signal, bars)

    def test_final_bar_signal_is_ignored(self) -> None:
        bars = make_bars(count=10)
        final = bars[-1]
        bars[-1] = TrendBar(
            symbol=final.symbol,
            open_time_ms=final.open_time_ms,
            close_time_ms=final.close_time_ms,
            open=final.open,
            high=final.high + 100,
            low=final.low,
            close=final.close + 100,
            volume=final.volume,
        )
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        signals = generate_trend_signals(bars, [], params)
        self.assertTrue(any(signal.ignored_reason == "final_bar_no_next_open" for signal in signals))


class M1ATrendEngineTests(unittest.TestCase):
    def test_position_sizing_respects_risk_and_cash_cap(self) -> None:
        params = TrendParams()
        qty = position_size(10_000.0, 1_000.0, 100.0, 10.0, 0.10, params)
        self.assertLessEqual(qty * 100.0, 1_000.0)
        risk_limited = position_size(10_000.0, 10_000.0, 100.0, 10.0, None, params)
        self.assertAlmostEqual(risk_limited, 5.0)

    def test_cost_model_base_and_x2(self) -> None:
        bars = make_bars(count=80)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        base = run_trend_backtest("BTCUSDT", bars, [], params, cost_multiplier=1)
        doubled = run_trend_backtest("BTCUSDT", bars, [], params, cost_multiplier=2)
        self.assertLessEqual(doubled.equity_curve[-1], base.equity_curve[-1])

    def test_oos_split_keeps_last_30_percent(self) -> None:
        items = list(range(10))
        is_items, oos_items = split_in_sample_oos(items, 0.30)
        self.assertEqual(is_items, list(range(7)))
        self.assertEqual(oos_items, [7, 8, 9])

    def test_parameter_neighborhood_has_no_best_selection(self) -> None:
        params = parameter_neighborhood()
        self.assertEqual(len(params), 81)
        self.assertIn(TrendParams(), params)

    def test_delete_best_three_trades(self) -> None:
        bars = make_bars(count=80)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        result = run_trend_backtest("BTCUSDT", bars, [], params)
        adjusted = remove_best_trades_effect(result, 3)
        self.assertIn("total_return", adjusted)
        self.assertIn("breakeven_or_better", adjusted)

    def test_segment_report_boundaries(self) -> None:
        bars = make_bars(count=80)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        result = run_trend_backtest("BTCUSDT", bars, [], params)
        row = segment_result(result, bars, Segment("fixture", 0, 20 * DAY_MS, "fixture segment"))
        self.assertEqual(row["note"], "fixture segment")
        self.assertIn("trade_count", row)


class M1ADataAndReportTests(unittest.TestCase):
    def test_m1a_gate_fails_when_delete_best_3_portfolio_below_breakeven(self) -> None:
        gates = evaluate_m1a_gates(
            cost_x2_total_return=0.10,
            parameter_neighborhood_rows=[(TrendParams(), {"total_return": 0.0})],
            delete_best_rows=[
                ("BTCUSDT", {"breakeven_or_better": 1.0}),
                ("ETHUSDT", {"breakeven_or_better": 1.0}),
                ("BTC+ETH equal-weight portfolio", {"breakeven_or_better": 0.0}),
            ],
            oos_sharpe=1.2,
            combined_trade_count=100,
        )
        self.assertFalse(gates["delete_best_3_trades"])
        self.assertEqual(gates["final_status"], "failed_validation")

    def test_m1a_gate_fails_when_oos_sharpe_below_one(self) -> None:
        gates = evaluate_m1a_gates(
            cost_x2_total_return=0.10,
            parameter_neighborhood_rows=[(TrendParams(), {"total_return": 0.0})],
            delete_best_rows=[("BTC+ETH equal-weight portfolio", {"breakeven_or_better": 1.0})],
            oos_sharpe=0.99,
            combined_trade_count=100,
        )
        self.assertFalse(gates["oos_sharpe_ge_1"])
        self.assertEqual(gates["final_status"], "failed_validation")

    def test_m1a_gate_fails_when_trade_count_below_80(self) -> None:
        gates = evaluate_m1a_gates(
            cost_x2_total_return=0.10,
            parameter_neighborhood_rows=[(TrendParams(), {"total_return": 0.0})],
            delete_best_rows=[("BTC+ETH equal-weight portfolio", {"breakeven_or_better": 1.0})],
            oos_sharpe=1.2,
            combined_trade_count=79,
        )
        self.assertFalse(gates["trade_count_ge_80"])
        self.assertEqual(gates["final_status"], "failed_validation")

    def test_m1a_final_status_failed_validation_when_any_gate_fails(self) -> None:
        gates = evaluate_m1a_gates(
            cost_x2_total_return=-0.01,
            parameter_neighborhood_rows=[(TrendParams(), {"total_return": 0.0})],
            delete_best_rows=[("BTC+ETH equal-weight portfolio", {"breakeven_or_better": 1.0})],
            oos_sharpe=1.2,
            combined_trade_count=100,
        )
        self.assertFalse(gates["cost_x2"])
        self.assertEqual(gates["final_status"], "failed_validation")

    def test_loads_m0_raw_fixtures_and_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AppendOnlyRawStore(Path(tmp) / "raw")
            rows = []
            for bar in make_bars(count=80):
                rows.append(
                    [
                        bar.open_time_ms,
                        str(bar.open),
                        str(bar.high),
                        str(bar.low),
                        str(bar.close),
                        str(bar.volume),
                        bar.close_time_ms,
                    ]
                )
            store.append("spot_klines", "fixture", "GET /api/v3/klines", {"symbol": "BTCUSDT", "interval": "1d"}, rows)
            store.append(
                "funding_rate_history",
                "fixture",
                "GET /fapi/v1/fundingRate",
                {"symbol": "BTCUSDT"},
                [
                    {"symbol": "BTCUSDT", "fundingTime": 0, "fundingRate": "0.0001"},
                    {"symbol": "BTCUSDT", "fundingTime": 8 * 3_600_000, "fundingRate": "0.0001"},
                ],
            )
            bars = load_spot_bars("BTCUSDT", Path(tmp) / "raw", Path(tmp) / "missing.duckdb")
            funding = load_funding_records("BTCUSDT", Path(tmp) / "raw", Path(tmp) / "missing.duckdb")
            self.assertEqual(len(bars), 80)
            self.assertEqual(len(funding), 2)
            params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
            result = run_trend_backtest("BTCUSDT", bars, funding, params)
            report = render_report(
                {"BTCUSDT": bars, "ETHUSDT": bars},
                {"BTCUSDT": funding, "ETHUSDT": funding},
                {"BTCUSDT": result, "ETHUSDT": result},
                {"BTCUSDT": result, "ETHUSDT": result},
                {"BTCUSDT": result, "ETHUSDT": result},
                [(params, {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "trade_count": 0.0})],
                [
                    ("BTCUSDT", {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "breakeven_or_better": 1.0}),
                    ("BTC+ETH equal-weight portfolio", {"total_return": -0.1, "sharpe": 0.0, "max_drawdown": -0.2, "breakeven_or_better": 0.0}),
                ],
                [("BTCUSDT", "fixture", {"return": 0.0, "max_drawdown": 0.0, "trade_count": 0.0, "exposure_days": 0.0, "note": "fixture"})],
                "ignored.md",
            )
            self.assertIn("Status: failed_validation", report)
            self.assertIn("M1A Gate Status", report)

    def test_m1a_report_contains_do_not_advance_to_m2_when_failed(self) -> None:
        bars = make_bars(count=80)
        params = TrendParams(regime_ma=3, entry_channel=3, exit_channel=2, atr_period=3)
        result = run_trend_backtest("BTCUSDT", bars, [], params)
        report = render_report(
            {"BTCUSDT": bars, "ETHUSDT": bars},
            {"BTCUSDT": [], "ETHUSDT": []},
            {"BTCUSDT": result, "ETHUSDT": result},
            {"BTCUSDT": result, "ETHUSDT": result},
            {"BTCUSDT": result, "ETHUSDT": result},
            [(params, {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "trade_count": 0.0})],
            [("BTC+ETH equal-weight portfolio", {"total_return": -0.1, "sharpe": 0.0, "max_drawdown": -0.2, "breakeven_or_better": 0.0})],
            [("BTCUSDT", "fixture", {"return": 0.0, "max_drawdown": 0.0, "trade_count": 0.0, "exposure_days": 0.0, "note": "fixture"})],
            "ignored.md",
        )
        self.assertIn("Decision: do not advance trend leg to M2", report)
        self.assertIn("Final M1A status: failed_validation", report)

    def test_no_trading_endpoint_implementation_in_m1a_modules(self) -> None:
        root = ROOT / "src" / "btc_eth_dual_quant" / "backtest"
        text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("trend*.py"))
        forbidden = ["/api/v3/order", "/fapi/v1/order", "create_order", "cancel_order", "place_order"]
        for item in forbidden:
            self.assertNotIn(item, text)


if __name__ == "__main__":
    unittest.main()
