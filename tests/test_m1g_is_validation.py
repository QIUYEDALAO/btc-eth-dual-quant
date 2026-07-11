from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from btc_eth_dual_quant.audit.m1g_execution_repricing import DetailBar
from btc_eth_dual_quant.audit.m1g_is_validation import (
    INITIAL_EQUITY,
    IS_END_EXCLUSIVE,
    IS_START,
    STRATEGY,
    build_scenario_evidence,
    evaluate_is_gates,
    load_freqtrade_archive,
)


class M1GISValidationTests(unittest.TestCase):
    def archive(self, root: Path, *, note: str = "m1g-is:base", open_date: datetime | None = None) -> Path:
        opened = open_date or datetime(2020, 7, 2, tzinfo=timezone.utc)
        closed = opened + timedelta(minutes=5)
        trade = {
            "pair": "BTC/USDT",
            "open_date": opened.isoformat(),
            "close_date": closed.isoformat(),
            "open_rate": 100.0,
            "close_rate": 101.8,
            "stake_amount": 25_000.0,
            "profit_abs": 450.0,
            "profit_ratio": 0.018,
            "fee_open": 0.0015,
            "fee_close": 0.0015,
            "is_open": False,
        }
        result = {"strategy": {STRATEGY: {"trades": [trade], "profit_total": -0.01}}}
        path = root / "fixture.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("fixture.json", json.dumps(result))
            archive.writestr("fixture_config.json", "{}")
        path.with_suffix(".meta.json").write_text(
            json.dumps(
                {
                    STRATEGY: {
                        "notes": note,
                        "timeframe": "1h",
                        "timeframe_detail": "5m",
                        "backtest_end_ts": int(IS_END_EXCLUSIVE.timestamp()),
                    }
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_archive_enforces_note_and_sealed_oos_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.archive(root)
            strategy, digest = load_freqtrade_archive(path, "m1g-is:base")
            self.assertEqual(len(strategy["trades"]), 1)
            self.assertEqual(len(digest), 64)
            with self.assertRaisesRegex(ValueError, "note"):
                load_freqtrade_archive(path, "m1g-is:cost-x2")
            path = self.archive(root, open_date=IS_END_EXCLUSIVE)
            with self.assertRaisesRegex(ValueError, "IS boundary"):
                load_freqtrade_archive(path, "m1g-is:base")

    def test_fixture_evidence_is_repriced_without_selecting_signals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.archive(Path(directory))
            opened = datetime(2020, 7, 2, tzinfo=timezone.utc)
            detail = {
                opened: DetailBar(opened, 100.0, 102.0, 99.0, 101.0),
            }
            btc_open = {}
            btc_close = {}
            eth_open = {}
            eth_close = {}
            marks = {}
            day = IS_START.date()
            end = (IS_END_EXCLUSIVE - timedelta(days=1)).date()
            while day <= end:
                btc_open[day] = 100.0
                btc_close[day] = 100.0
                eth_open[day] = 100.0
                eth_close[day] = 100.0
                marks[("BTCUSDT", day)] = 100.0
                marks[("ETHUSDT", day)] = 100.0
                day += timedelta(days=1)
            evidence = build_scenario_evidence(
                scenario="base",
                archive_path=path,
                detail_by_symbol={"BTCUSDT": detail, "ETHUSDT": detail},
                daily_close=marks,
                benchmark_prices={"BTCUSDT": (btc_open, btc_close), "ETHUSDT": (eth_open, eth_close)},
            )
            self.assertEqual(len(evidence.native_trades), 1)
            self.assertEqual(len(evidence.audited_trades), 1)
            self.assertAlmostEqual(evidence.audited_trades[0].close_rate, 101.8)
            self.assertLess(evidence.native_total_return, 0)
            self.assertEqual(evidence.native_curve[0].equity, INITIAL_EQUITY)

    def test_frozen_gate_failure_does_not_authorize_oos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.archive(Path(directory))
            opened = datetime(2020, 7, 2, tzinfo=timezone.utc)
            detail = {opened: DetailBar(opened, 100.0, 102.0, 99.0, 101.0)}
            opens = {}
            closes = {}
            marks = {}
            day = date(2020, 7, 1)
            while day <= date(2024, 9, 10):
                opens[day] = closes[day] = 100.0
                marks[("BTCUSDT", day)] = marks[("ETHUSDT", day)] = 100.0
                day += timedelta(days=1)
            evidence = build_scenario_evidence(
                scenario="base",
                archive_path=path,
                detail_by_symbol={"BTCUSDT": detail, "ETHUSDT": detail},
                daily_close=marks,
                benchmark_prices={"BTCUSDT": (opens, closes), "ETHUSDT": (opens, closes)},
            )
            decision = evaluate_is_gates(evidence, evidence)
            self.assertEqual(decision.status, "failed_validation")
            self.assertFalse(decision.passed)
            self.assertIn(("Complete IS trades >= 56", False), decision.gates)

    def test_module_contains_no_signal_or_trading_implementation(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "src/btc_eth_dual_quant/audit/m1g_is_validation.py").read_text()
        for forbidden in ("populate_entry", "create_order", "cancel_order", "place_order", "execution/live"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
