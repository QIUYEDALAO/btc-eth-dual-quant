from __future__ import annotations

import inspect
import math
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.backtest.funding_arbitrage import (
    FundingArbParams,
    annualize_funding_rate,
    compute_payback_required_apr,
    compute_two_leg_pnl,
    infer_interval_from_funding_history,
    run_funding_arbitrage_backtest,
    should_enter_funding_arb,
    should_exit_funding_arb,
)
from btc_eth_dual_quant.backtest.trend_strategy import TrendBar

from scripts.m1b_run_funding_arbitrage_backtest import render_report


MS_PER_DAY = 86_400_000
HALF_DAY_MS = MS_PER_DAY // 2


def bars(symbol: str, count: int, start: int = 0, base: float = 100.0) -> list[TrendBar]:
    out: list[TrendBar] = []
    for idx in range(count):
        open_time = start + idx * MS_PER_DAY
        price = base + idx * 0.2
        out.append(
            TrendBar(
                symbol=symbol,
                open_time_ms=open_time,
                close_time_ms=open_time + MS_PER_DAY - 1,
                open=price,
                high=price * 1.02,
                low=price * 0.98,
                close=price,
                volume=1000.0,
            )
        )
    return out


def funding_history(cycles: int = 4, start: int = 0) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    time_ms = start
    for _ in range(cycles):
        for _high in range(6):
            rows.append({"symbol": "BTCUSDT", "fundingTime": time_ms, "fundingRate": "0.0004"})
            time_ms += HALF_DAY_MS
        for _negative in range(2):
            rows.append({"symbol": "BTCUSDT", "fundingTime": time_ms, "fundingRate": "-0.0001"})
            time_ms += HALF_DAY_MS
        for _sleep in range(2):
            rows.append({"symbol": "BTCUSDT", "fundingTime": time_ms, "fundingRate": "0.00001"})
            time_ms += HALF_DAY_MS
    return rows


class M1BFundingArbitrageTests(unittest.TestCase):
    def test_funding_annualization_with_variable_interval(self) -> None:
        self.assertAlmostEqual(annualize_funding_rate(0.001, 12), 0.73)
        self.assertAlmostEqual(annualize_funding_rate(0.001, 6), 1.46)

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
        self.assertEqual(should_exit_funding_arb(0.20, 2, params), "negative_funding_streak")
        self.assertIsNone(should_exit_funding_arb(0.20, 1, params))

    def test_two_leg_direction_neutral_pnl_math(self) -> None:
        pnl = compute_two_leg_pnl(
            entry_spot_price=100.0,
            exit_spot_price=110.0,
            entry_perp_price=101.0,
            exit_perp_price=111.0,
            funding_rates=[0.001, 0.002],
            params=FundingArbParams(cost_multiplier=1.0),
        )
        self.assertAlmostEqual(pnl.spot_pnl, 0.10)
        self.assertAlmostEqual(pnl.perp_short_pnl, -10 / 101)
        self.assertAlmostEqual(pnl.funding_income, 0.003)
        self.assertAlmostEqual(pnl.basis_pnl, pnl.spot_pnl + pnl.perp_short_pnl)
        self.assertAlmostEqual(pnl.fees, 0.003)
        self.assertAlmostEqual(pnl.slippage, 0.002)

    def test_cost_x2_math(self) -> None:
        base = compute_two_leg_pnl(100, 100, 100, 100, [0.01], FundingArbParams(cost_multiplier=1.0))
        stressed = compute_two_leg_pnl(100, 100, 100, 100, [0.01], FundingArbParams(cost_multiplier=2.0))
        self.assertAlmostEqual(stressed.fees, base.fees * 2)
        self.assertAlmostEqual(stressed.slippage, base.slippage * 2)

    def test_interval_inference_reports_anomaly(self) -> None:
        interval, warnings = infer_interval_from_funding_history(
            [
                {"fundingTime": 0, "fundingRate": "0.001"},
                {"fundingTime": HALF_DAY_MS, "fundingRate": "0.001"},
                {"fundingTime": HALF_DAY_MS + HALF_DAY_MS // 2, "fundingRate": "0.001"},
            ]
        )
        self.assertEqual(interval, 12)
        self.assertTrue(warnings)

    def test_interval_inference_ignores_timestamp_jitter(self) -> None:
        interval, warnings = infer_interval_from_funding_history(
            [
                {"fundingTime": 0, "fundingRate": "0.001"},
                {"fundingTime": HALF_DAY_MS + 5, "fundingRate": "0.001"},
                {"fundingTime": HALF_DAY_MS * 2 + 10, "fundingRate": "0.001"},
            ]
        )
        self.assertEqual(interval, 12)
        self.assertEqual(warnings, [])

    def test_run_backtest_cycles_oos_sleep_and_no_lookahead(self) -> None:
        rows = funding_history(cycles=5)
        result = run_funding_arbitrage_backtest(
            "BTCUSDT",
            bars("BTCUSDT", 30, base=100.0),
            bars("BTCUSDT", 30, base=101.0),
            rows,
            bars("BTCUSDT", 30, base=101.0),
            bars("BTCUSDT", 30, base=100.5),
            bars("BTCUSDT", 30, base=0.0),
            FundingArbParams(),
        )
        self.assertGreaterEqual(len(result.cycles), 1)
        self.assertEqual(result.no_lookahead, True)
        self.assertLessEqual(result.oos_start_ms or 0, result.oos_end_ms or 0)
        self.assertGreaterEqual(result.metrics["longest_sleep_days"], 0.0)
        for cycle in result.cycles:
            self.assertLessEqual(cycle.entry_time_ms, cycle.exit_time_ms)

    def test_graceful_sleep_when_funding_dries_up(self) -> None:
        rows = [
            {"symbol": "BTCUSDT", "fundingTime": idx * HALF_DAY_MS, "fundingRate": "0.00001"}
            for idx in range(20)
        ]
        result = run_funding_arbitrage_backtest(
            "BTCUSDT",
            bars("BTCUSDT", 12),
            bars("BTCUSDT", 12, base=101.0),
            rows,
            params=FundingArbParams(),
        )
        self.assertEqual(len(result.cycles), 0)
        self.assertEqual(result.gates["Funding dries up gracefully"], "pass")
        self.assertGreater(result.metrics["longest_sleep_days"], 0)

    def test_report_generation_from_fixtures(self) -> None:
        rows = funding_history(cycles=3)
        base = run_funding_arbitrage_backtest(
            "BTCUSDT",
            bars("BTCUSDT", 20),
            bars("BTCUSDT", 20, base=101.0),
            rows,
            params=FundingArbParams(),
        )
        x2 = run_funding_arbitrage_backtest(
            "BTCUSDT",
            bars("BTCUSDT", 20),
            bars("BTCUSDT", 20, base=101.0),
            rows,
            params=FundingArbParams(cost_multiplier=2.0),
        )
        report = render_report(base, x2, {"BTCUSDT": base, "ETHUSDT": base}, {"BTCUSDT": x2, "ETHUSDT": x2})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            path.write_text(report, encoding="utf-8")
            text = path.read_text(encoding="utf-8")
        self.assertIn("# M1B Funding Arbitrage Backtest Report", text)
        self.assertIn("M1B Gate Status", text)

    def test_no_trading_endpoint_implementation_and_no_execution_live(self) -> None:
        root = Path(__file__).resolve().parents[1]
        src_scripts = list((root / "src").rglob("*")) + list((root / "scripts").rglob("*"))
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in src_scripts if path.is_file())
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
