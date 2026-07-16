from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.backtest.funding_arbitrage import (
    FundingArbParams,
    annualize_funding_rate,
    build_funding_points,
    combine_funding_results,
    compute_payback_required_apr,
    compute_two_leg_pnl,
    infer_interval_from_funding_history,
    run_funding_arbitrage_backtest,
    should_enter_funding_arb,
    should_exit_funding_arb,
)
from btc_eth_dual_quant.backtest.trend_strategy import TrendBar
from scripts.m1b_run_funding_arbitrage_backtest import render_report


HOUR_MS = 3_600_000
DAY_MS = 24 * HOUR_MS


def hourly_bars(
    symbol: str,
    count: int,
    *,
    start: int = 0,
    base: float = 100.0,
    step: float = 0.01,
) -> list[TrendBar]:
    return [
        TrendBar(
            symbol=symbol,
            open_time_ms=start + idx * HOUR_MS,
            close_time_ms=start + (idx + 1) * HOUR_MS - 1,
            open=base + idx * step,
            high=(base + idx * step) * 1.01,
            low=(base + idx * step) * 0.99,
            close=base + idx * step,
            volume=1000.0,
        )
        for idx in range(count)
    ]


def daily_bars(symbol: str, count: int) -> list[TrendBar]:
    return [
        TrendBar(
            symbol=symbol,
            open_time_ms=idx * DAY_MS,
            close_time_ms=(idx + 1) * DAY_MS - 1,
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=1000.0,
        )
        for idx in range(count)
    ]


def market_inputs(symbol: str, count: int = 260) -> tuple[list[TrendBar], ...]:
    spot = hourly_bars(symbol, count, base=100.0)
    perp = hourly_bars(symbol, count, base=101.0)
    mark = hourly_bars(symbol, count, base=101.2)
    index = hourly_bars(symbol, count, base=100.2)
    premium = hourly_bars(symbol, count, base=0.001, step=0.0)
    return spot, perp, mark, index, premium


def cycle_history(symbol: str = "BTCUSDT", cycles: int = 3, start: int = 2 * HOUR_MS) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    time_ms = start
    for _ in range(cycles):
        for _high in range(6):
            rows.append({"symbol": symbol, "fundingTime": time_ms, "fundingRate": "0.0004"})
            time_ms += 12 * HOUR_MS
        for _negative in range(2):
            rows.append({"symbol": symbol, "fundingTime": time_ms, "fundingRate": "-0.0001"})
            time_ms += 12 * HOUR_MS
        for _sleep in range(2):
            rows.append({"symbol": symbol, "fundingTime": time_ms, "fundingRate": "0.00001"})
            time_ms += 12 * HOUR_MS
    return rows


def run_fixture(symbol: str = "BTCUSDT", cycles: int = 2, cost_multiplier: float = 1.0):
    bars = market_inputs(symbol, 300)
    return run_funding_arbitrage_backtest(
        symbol,
        bars[0],
        bars[1],
        cycle_history(symbol, cycles),
        bars[2],
        bars[3],
        bars[4],
        FundingArbParams(cost_multiplier=cost_multiplier),
    )


class M1BFundingArbitrageTests(unittest.TestCase):
    def test_funding_annualization_with_variable_interval(self) -> None:
        self.assertAlmostEqual(annualize_funding_rate(0.001, 12), 0.73)
        self.assertAlmostEqual(annualize_funding_rate(0.001, 6), 1.46)
        rows = [
            {"symbol": "BTCUSDT", "fundingTime": time_ms, "fundingRate": "0.001"}
            for time_ms in (0, 4 * HOUR_MS, 10 * HOUR_MS, 18 * HOUR_MS, 30 * HOUR_MS)
        ]
        points, _modal, warnings = build_funding_points("BTCUSDT", rows)
        self.assertEqual([point.interval_hours for point in points], [4.0, 4.0, 6.0, 8.0, 12.0])
        self.assertEqual(
            [round(point.annualized_rate, 3) for point in points],
            [2.19, 2.19, 1.46, 1.095, 0.73],
        )
        self.assertTrue(any("variable" in warning for warning in warnings))

    def test_no_hardcoded_interval_constant(self) -> None:
        source = inspect.getsource(__import__("btc_eth_dual_quant.backtest.funding_arbitrage", fromlist=["x"]))
        self.assertNotIn("28800000", source)
        self.assertNotIn("'8h'", source)
        self.assertNotIn('"8h"', source)

    def test_payback_threshold_and_eight_percent_rejection(self) -> None:
        params = FundingArbParams()
        self.assertAlmostEqual(compute_payback_required_apr(params), 0.2607142857, places=9)
        self.assertFalse(should_enter_funding_arb(0.08, 0.001, params))

    def test_entry_requires_positive_funding_and_payback(self) -> None:
        params = FundingArbParams()
        self.assertFalse(should_enter_funding_arb(0.30, -0.0001, params))
        self.assertFalse(should_enter_funding_arb(0.20, 0.0001, params))
        self.assertTrue(should_enter_funding_arb(0.30, 0.0001, params))

    def test_exit_on_low_funding_and_two_negative_periods(self) -> None:
        params = FundingArbParams()
        self.assertEqual(should_exit_funding_arb(0.01, 0, params), "low_funding_mean")
        self.assertIsNone(should_exit_funding_arb(0.01, 0, params, low_funding_days=2.99))
        self.assertEqual(should_exit_funding_arb(0.20, 2, params), "negative_funding_streak")
        self.assertIsNone(should_exit_funding_arb(0.20, 1, params))

    def test_two_leg_math_uses_settlement_mark_and_actual_fill_notionals(self) -> None:
        pnl = compute_two_leg_pnl(
            100.0,
            110.0,
            100.0,
            120.0,
            [0.001, 0.002],
            FundingArbParams(),
            funding_mark_prices=[120.0, 130.0],
        )
        self.assertAlmostEqual(pnl.spot_pnl, 0.10)
        self.assertAlmostEqual(pnl.perp_short_pnl, -0.20)
        self.assertAlmostEqual(pnl.funding_income, 0.0038)
        self.assertAlmostEqual(pnl.basis_pnl, -0.10)
        expected_fees = (1.0 + 1.1) * 0.001 + (1.0 + 1.2) * 0.0005
        expected_slippage = (1.0 + 1.0 + 1.1 + 1.2) * 0.0005
        self.assertAlmostEqual(pnl.fees, expected_fees)
        self.assertAlmostEqual(pnl.slippage, expected_slippage)

    def test_cost_x2_math(self) -> None:
        base = compute_two_leg_pnl(100, 110, 100, 120, [0.01], FundingArbParams())
        stressed = compute_two_leg_pnl(
            100, 110, 100, 120, [0.01], FundingArbParams(cost_multiplier=2.0)
        )
        self.assertAlmostEqual(stressed.fees, base.fees * 2)
        self.assertAlmostEqual(stressed.slippage, base.slippage * 2)

    def test_interval_inference_reports_anomaly(self) -> None:
        interval, warnings = infer_interval_from_funding_history(
            [
                {"symbol": "BTCUSDT", "fundingTime": 0, "fundingRate": "0.001"},
                {"symbol": "BTCUSDT", "fundingTime": 12 * HOUR_MS, "fundingRate": "0.001"},
                {"symbol": "BTCUSDT", "fundingTime": 18 * HOUR_MS, "fundingRate": "0.001"},
            ]
        )
        self.assertEqual(interval, 12)
        self.assertTrue(warnings)

    def test_unclosed_daily_close_is_rejected(self) -> None:
        rows = cycle_history(cycles=1)
        with self.assertRaisesRegex(ValueError, "completed 1h bars"):
            run_funding_arbitrage_backtest(
                "BTCUSDT",
                daily_bars("BTCUSDT", 10),
                daily_bars("BTCUSDT", 10),
                rows,
                daily_bars("BTCUSDT", 10),
                daily_bars("BTCUSDT", 10),
                daily_bars("BTCUSDT", 10),
            )

    def test_entry_is_next_hour_open_and_triggering_funding_is_not_income(self) -> None:
        result = run_fixture(cycles=1)
        cycle = result.cycles[0]
        self.assertGreater(cycle.entry_time_ms, cycle.entry_signal_time_ms)
        self.assertEqual(cycle.entry_time_ms, cycle.entry_signal_time_ms + HOUR_MS)
        contribution_times = [item.funding_time_ms for item in cycle.funding_contributions]
        self.assertNotIn(cycle.entry_signal_time_ms, contribution_times)
        self.assertTrue(all(item.valuation_bar_close_time_ms <= item.funding_time_ms for item in cycle.funding_contributions))

    def test_exit_triggering_funding_is_counted_before_next_hour_exit(self) -> None:
        result = run_fixture(cycles=1)
        cycle = result.cycles[0]
        self.assertGreater(cycle.exit_time_ms, cycle.exit_signal_time_ms)
        self.assertIn(cycle.exit_signal_time_ms, [item.funding_time_ms for item in cycle.funding_contributions])
        self.assertAlmostEqual(cycle.funding_income, sum(item.income for item in cycle.funding_contributions))

    def test_incomplete_end_position_is_not_complete_cycle(self) -> None:
        symbol = "BTCUSDT"
        bars = market_inputs(symbol, 80)
        rows = [
            {"symbol": symbol, "fundingTime": time_ms, "fundingRate": "0.001"}
            for time_ms in (2 * HOUR_MS, 14 * HOUR_MS, 26 * HOUR_MS, 38 * HOUR_MS)
        ]
        result = run_funding_arbitrage_backtest(symbol, *bars[:2], rows, *bars[2:])
        self.assertEqual(result.metrics["complete_cycles"], 0)
        self.assertEqual(len(result.incomplete_positions), 1)
        self.assertEqual(result.incomplete_positions[0].reason, "data_end_without_legal_exit")

    def test_oos_split_separates_carry_in_cycle(self) -> None:
        symbol = "BTCUSDT"
        bars = market_inputs(symbol, 140)
        times = [2 * HOUR_MS + idx * 12 * HOUR_MS for idx in range(10)]
        rates = ["0.001"] * 8 + ["-0.001", "-0.001"]
        rows = [
            {"symbol": symbol, "fundingTime": time_ms, "fundingRate": rate}
            for time_ms, rate in zip(times, rates)
        ]
        result = run_funding_arbitrage_backtest(symbol, *bars[:2], rows, *bars[2:])
        self.assertEqual(len(result.cycles), 1)
        self.assertEqual(len(result.oos_carry_in_cycles), 1)
        self.assertEqual(result.oos_metrics["complete_cycles"], 0)
        self.assertEqual(result.oos_metrics["carry_in_cycles"], 1)

    def test_btc_eth_portfolio_is_aligned_by_utc_timestamp(self) -> None:
        btc = run_fixture("BTCUSDT", cycles=1)
        eth = run_fixture("ETHUSDT", cycles=1)
        combined = combine_funding_results({"BTCUSDT": btc, "ETHUSDT": eth})
        self.assertTrue(combined.diagnostics["symbols_aligned_by_utc_timestamp"])
        self.assertEqual(combined.equity_times_ms, sorted(set(combined.equity_times_ms)))
        self.assertGreater(combined.diagnostics["utc_intersection_points"], 0)

    def test_mark_index_premium_are_used_for_diagnostics(self) -> None:
        result = run_fixture(cycles=1)
        self.assertEqual(result.basis_data_status, "available")
        self.assertEqual(result.diagnostics["missing_mark_events"], 0)
        self.assertIn("mean_mark_index_spread", result.diagnostics)
        self.assertIn("mean_abs_premium_consistency_error", result.diagnostics)

    def test_time_indexed_metrics_and_no_lookahead(self) -> None:
        result = run_fixture(cycles=2)
        self.assertEqual(result.metrics_basis, "funding-event time-indexed equity curve")
        self.assertTrue(result.no_lookahead)
        self.assertEqual(result.gates["No lookahead"], "pass")
        self.assertEqual(result.metrics["return_observations"], len(result.equity_curve) - 1)

    def test_graceful_sleep_when_funding_dries_up(self) -> None:
        symbol = "BTCUSDT"
        bars = market_inputs(symbol, 260)
        rows = [
            {"symbol": symbol, "fundingTime": 2 * HOUR_MS + idx * 12 * HOUR_MS, "fundingRate": "0.00001"}
            for idx in range(20)
        ]
        result = run_funding_arbitrage_backtest(symbol, *bars[:2], rows, *bars[2:])
        self.assertEqual(len(result.cycles), 0)
        self.assertEqual(result.gates["Funding dries up gracefully"], "pass")
        self.assertGreater(result.metrics["longest_sleep_days"], 0)

    def test_fully_passing_numerical_gates_cannot_auto_approve_m2(self) -> None:
        result = run_fixture(cycles=2)
        self.assertIn(result.final_status, {"under_review", "failed_validation"})
        self.assertNotEqual(result.final_status, "pass")

    def test_report_generation_from_fixtures(self) -> None:
        base_btc = run_fixture("BTCUSDT", cycles=1)
        base_eth = run_fixture("ETHUSDT", cycles=1)
        x2_btc = run_fixture("BTCUSDT", cycles=1, cost_multiplier=2.0)
        x2_eth = run_fixture("ETHUSDT", cycles=1, cost_multiplier=2.0)
        base = combine_funding_results({"BTCUSDT": base_btc, "ETHUSDT": base_eth})
        x2 = combine_funding_results(
            {"BTCUSDT": x2_btc, "ETHUSDT": x2_eth},
            FundingArbParams(cost_multiplier=2.0),
            "cost_x2",
        )
        report = render_report(
            base,
            x2,
            {"BTCUSDT": base_btc, "ETHUSDT": base_eth},
            {"BTCUSDT": x2_btc, "ETHUSDT": x2_eth},
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text(report, encoding="utf-8")
            text = path.read_text(encoding="utf-8")
        self.assertIn("# M1B Event-Time Revalidation Report", text)
        self.assertIn("triggering funding event is excluded", text)
        self.assertIn("OOS carry-in cycles", text)
        self.assertIn("does not approve M2", text)

    def test_no_trading_endpoint_implementation_and_no_execution_live(self) -> None:
        root = Path(__file__).resolve().parents[1]
        src_scripts = list((root / "src").rglob("*.py")) + list((root / "scripts").rglob("*.py"))
        text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in src_scripts
            if path.is_file()
        )
        forbidden = [
            "/api/v3/" + "order",
            "/fapi/v1/" + "order",
            "create_" + "order",
            "cancel_" + "order",
            "place_" + "order",
            "simulate_" + "fill",
            "matching_" + "engine",
        ]
        for item in forbidden:
            self.assertNotIn(item, text)
        self.assertFalse((root / "src" / "execution" / "live").exists())
        self.assertFalse((root / "execution" / "live").exists())


if __name__ == "__main__":
    unittest.main()
