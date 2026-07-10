from __future__ import annotations

import csv
import math
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from btc_eth_dual_quant.audit.unified_metrics import (
    AuditTrade,
    EquityPoint,
    build_daily_mtm_equity,
    build_policy_benchmark,
    compare_granularity,
    concentration_diagnostics,
    cost_attribution,
    daily_returns,
    deflated_sharpe_ratio,
    frequency_diagnostics,
    metrics_from_equity,
    probabilistic_sharpe_ratio,
    trade_from_freqtrade,
)


ROOT = Path(__file__).resolve().parents[1]


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def trade(**overrides) -> AuditTrade:
    values = {
        "pair": "BTC/USDT",
        "open_time": utc("2024-01-01T00:00:00"),
        "close_time": utc("2024-01-03T00:00:00"),
        "stake_amount": 500.0,
        "open_rate": 100.0,
        "close_rate": 110.0,
        "profit_abs": 48.0,
        "fee_open_rate": 0.001,
        "fee_close_rate": 0.001,
    }
    values.update(overrides)
    return AuditTrade(**values)


class UnifiedMetricTests(unittest.TestCase):
    def test_daily_metrics_use_flat_days_ddof_one_and_positive_drawdown(self) -> None:
        points = [
            EquityPoint(date(2024, 1, 1), 100.0),
            EquityPoint(date(2024, 1, 2), 110.0),
            EquityPoint(date(2024, 1, 3), 110.0),
            EquityPoint(date(2024, 1, 4), 99.0),
        ]
        returns = daily_returns(points)
        expected_std = math.sqrt(sum((value - sum(returns) / 3) ** 2 for value in returns) / 2)
        metrics = metrics_from_equity(points)
        self.assertAlmostEqual(metrics.sharpe, sum(returns) / 3 / expected_std * math.sqrt(365))
        self.assertAlmostEqual(metrics.max_drawdown, 0.1)
        self.assertEqual(metrics.observations, 4)

    def test_missing_calendar_day_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "consecutive UTC day"):
            metrics_from_equity(
                [EquityPoint(date(2024, 1, 1), 100.0), EquityPoint(date(2024, 1, 3), 101.0)]
            )

    def test_psr_and_dsr_are_probabilities_and_dsr_penalizes_trials(self) -> None:
        returns = [0.01, -0.005, 0.008, 0.0, 0.004, -0.002] * 20
        psr = probabilistic_sharpe_ratio(returns)
        dsr = deflated_sharpe_ratio(returns, [0.2, 0.7, 1.1, 1.4])
        self.assertGreater(psr, dsr)
        self.assertTrue(0.0 <= dsr <= 1.0)


class EquityBuilderTests(unittest.TestCase):
    def test_freqtrade_adapter_and_daily_mtm_reconcile_realized_endpoint(self) -> None:
        parsed = trade_from_freqtrade(
            {
                "pair": "BTC/USDT",
                "open_date": "2024-01-01T00:00:00Z",
                "close_date": "2024-01-03T00:00:00Z",
                "stake_amount": 500,
                "open_rate": 100,
                "close_rate": 110,
                "profit_abs": 48,
                "fee_open": 0.001,
                "fee_close": 0.001,
            }
        )
        points = build_daily_mtm_equity(
            trades=[parsed],
            daily_close={
                ("BTCUSDT", date(2024, 1, 1)): 102,
                ("BTCUSDT", date(2024, 1, 2)): 108,
            },
            start=date(2024, 1, 1),
            end=date(2024, 1, 4),
            initial_equity=1000,
        )
        self.assertGreater(points[1].equity, points[0].equity)
        self.assertEqual(points[2].equity, 1048.0)
        self.assertEqual(points[3].equity, 1048.0)

    def test_intraday_completed_trade_is_realized_on_same_day(self) -> None:
        intraday = trade(close_time=utc("2024-01-01T12:00:00"), profit_abs=10.0)
        points = build_daily_mtm_equity(
            trades=[intraday], daily_close={}, start=date(2024, 1, 1), end=date(2024, 1, 2), initial_equity=1000
        )
        self.assertEqual([point.equity for point in points], [1010.0, 1010.0])

    def test_overlapping_trades_are_rejected(self) -> None:
        second = trade(
            pair="ETH/USDT",
            open_time=utc("2024-01-02T00:00:00"),
            close_time=utc("2024-01-04T00:00:00"),
        )
        with self.assertRaisesRegex(ValueError, "overlapping"):
            build_daily_mtm_equity(
                trades=[trade(), second], daily_close={}, start=date(2024, 1, 1), end=date(2024, 1, 4), initial_equity=1000
            )

    def test_policy_benchmark_waits_for_monday_and_charges_rebalance_cost(self) -> None:
        start, end = date(2024, 1, 3), date(2024, 1, 9)
        days = [(start.fromordinal(start.toordinal() + offset)) for offset in range(7)]
        opens = {day: 100.0 for day in days}
        closes = {day: 100.0 for day in days}
        curve = build_policy_benchmark(
            btc_open=opens,
            btc_close=closes,
            eth_open=opens,
            eth_close=closes,
            start=start,
            end=end,
            initial_equity=1000,
            cost_per_side=0.0015,
        )
        self.assertEqual(curve[5].day.weekday(), 0)
        self.assertEqual([point.equity for point in curve[:5]], [1000.0] * 5)
        self.assertAlmostEqual(curve[5].equity, 999.25)


class DiagnosticTests(unittest.TestCase):
    def test_cost_frequency_and_concentration(self) -> None:
        trades = [trade(), trade(open_time=utc("2024-01-10T00:00:00"), close_time=utc("2024-01-12T00:00:00"), profit_abs=20)]
        costs = cost_attribution(trades)
        self.assertGreater(costs.total, 0)
        frequency = frequency_diagnostics(trades, date(2024, 1, 1), date(2024, 1, 30), 1000)
        self.assertEqual(frequency.complete_trades, 2)
        self.assertEqual(frequency.longest_sleep_days, 18)
        self.assertGreaterEqual(frequency.p999_daily_order_events, frequency.p95_daily_order_events)
        concentration = concentration_diagnostics(trades)
        self.assertAlmostEqual(concentration.best_three_share, 1.0)

    def test_granularity_gate_reversal_always_blocks(self) -> None:
        points = [EquityPoint(date(2024, 1, 1), 100), EquityPoint(date(2024, 1, 2), 101), EquityPoint(date(2024, 1, 3), 102)]
        metrics = metrics_from_equity(points)
        result = compare_granularity(
            reference_metrics=metrics,
            candidate_metrics=metrics,
            reference_trades=100,
            candidate_trades=100,
            reference_gate=True,
            candidate_gate=False,
        )
        self.assertFalse(result.passed)
        self.assertFalse(result.gate_consistent)


class ExpertRegressionTests(unittest.TestCase):
    def test_m1c_expert_daily_equity_regression(self) -> None:
        path = ROOT / "reports" / "expert" / "m1c_oos_daily_equity.csv"
        base: list[EquityPoint] = []
        x2: list[EquityPoint] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                day = date.fromisoformat(row["date_utc"])
                base.append(EquityPoint(day, float(row["equity_base"])))
                x2.append(EquityPoint(day, float(row["equity_x2"])))
        base_metrics = metrics_from_equity(base)
        x2_metrics = metrics_from_equity(x2)
        self.assertAlmostEqual(base_metrics.sharpe, 0.7882, places=4)
        self.assertAlmostEqual(base_metrics.max_drawdown, 0.234729, places=5)
        self.assertAlmostEqual(base_metrics.psr, 0.9024, places=4)
        self.assertAlmostEqual(x2_metrics.sharpe, 0.7528, places=4)
        self.assertAlmostEqual(x2_metrics.max_drawdown, 0.244688, places=5)
        self.assertAlmostEqual(x2_metrics.psr, 0.8920, places=4)

    def test_t3_has_no_strategy_or_trading_implementation(self) -> None:
        source = (ROOT / "src" / "btc_eth_dual_quant" / "audit" / "unified_metrics.py").read_text(encoding="utf-8")
        for forbidden in ("populate_entry", "populate_exit", "create_order", "cancel_order", "place_order", "execution/live"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
