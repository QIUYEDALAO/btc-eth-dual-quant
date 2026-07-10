from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m1c_p3_ranges import build_ranges
from m1c_p3_report import build_report, load_run, profile_data


def trade(index: int, profit_abs: float = 100.0, force_exit: bool = False) -> dict:
    opened = datetime(2020, 1, 6, tzinfo=UTC) + timedelta(days=index * 7)
    closed = opened + timedelta(days=7)
    return {
        "pair": "BTC/USDT" if index % 2 == 0 else "ETH/USDT",
        "open_date": opened.isoformat(sep=" "),
        "close_date": closed.isoformat(sep=" "),
        "trade_duration": 10_080,
        "profit_abs": profit_abs,
        "profit_ratio": profit_abs / 50_000.0,
        "exit_reason": "force_exit" if force_exit else "exit_signal",
    }


def stats(trades: list[dict], profit_total: float, sharpe: float = 1.5) -> dict:
    starting = 100_000.0
    absolute = profit_total * starting
    return {
        "trades": trades,
        "profit_total": profit_total,
        "profit_total_abs": absolute,
        "starting_balance": starting,
        "final_balance": starting + absolute,
        "sharpe": sharpe,
        "max_drawdown_account": 0.05,
        "backtest_start": "2020-01-01 00:00:00",
        "backtest_end": "2020-12-31 00:00:00",
        "periodic_breakdown": {"year": [{"date": "01/01/2020", "trades": len(trades), "profit_abs": absolute}]},
    }


def write_run(root: Path, label: str, run_stats: dict) -> Path:
    directory = root / label
    directory.mkdir()
    payload = {"strategy": {"BTCETHRelativeStrengthRotation": run_stats}}
    with ZipFile(directory / f"{label}.zip", "w", ZIP_DEFLATED) as archive:
        archive.writestr(f"{label}.json", json.dumps(payload))
        archive.writestr(f"{label}_config.json", "{}")
    (directory / f"{label}.meta.json").write_text(
        json.dumps({"BTCETHRelativeStrengthRotation": {"notes": f"m1c-p3:{label}"}}),
        encoding="utf-8",
    )
    return directory


class M1CP3RangeTests(unittest.TestCase):
    def test_ranges_are_time_based_sealed_70_30_and_four_contiguous_segments(self) -> None:
        ranges = build_ranges(date(2020, 1, 1), date(2021, 1, 1))
        self.assertEqual(ranges["M1C_FULL_RANGE"], "20200101-20210101")
        self.assertEqual(ranges["M1C_OOS_START"], "2020-09-13")
        segments = [ranges[f"M1C_SEGMENT_{index}_RANGE"] for index in range(1, 5)]
        self.assertEqual(segments[0].split("-")[0], "20200101")
        self.assertEqual(segments[-1].split("-")[1], "20200913")
        for previous, current in zip(segments, segments[1:]):
            self.assertEqual(previous.split("-")[1], current.split("-")[0])


class M1CP3ReportTests(unittest.TestCase):
    def _fixtures(self, root: Path, complete_count: int) -> tuple[dict, list, Path, Path]:
        base_trades = [trade(index, 100.0) for index in range(complete_count)]
        oos_trades = [trade(index, 100.0) for index in range(min(complete_count, 20))]
        mappings = {
            "base-full": stats(base_trades, 0.20),
            "x2-full": stats(base_trades, 0.12),
            "base-oos": stats(oos_trades, 0.08, sharpe=1.2),
            "x2-oos": stats(oos_trades, 0.04, sharpe=1.0),
            **{f"segment-{index}": stats(base_trades[:5], 0.02) for index in range(1, 5)},
        }
        runs = {label: load_run(label, write_run(root, label, value)) for label, value in mappings.items()}

        data_dir = root / "data"
        data_dir.mkdir()
        start = date(2020, 1, 1)
        rows = []
        for index in range(366):
            timestamp = int(datetime.combine(start + timedelta(days=index), datetime.min.time(), tzinfo=UTC).timestamp() * 1000)
            rows.append([timestamp, 1, 1, 1, 1, 1])
        profiles = []
        for symbol in ("BTC/USDT", "ETH/USDT"):
            path = data_dir / f"{symbol.replace('/', '_')}-1d.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            profiles.append(profile_data(data_dir, symbol, start, date(2021, 1, 1)))

        lookahead = root / "lookahead.csv"
        lookahead.write_text(
            "filename,strategy,has_bias,total_signals,biased_entry_signals,biased_exit_signals,biased_indicators\n"
            "strategy.py,BTCETHRelativeStrengthRotation,False,20,0,0,\n",
            encoding="utf-8",
        )
        recursive = root / "recursive.log"
        recursive.write_text(
            "No variance on indicator(s) found due to recursive formula.\nNo lookahead bias on indicators found.\n",
            encoding="utf-8",
        )
        return runs, profiles, lookahead, recursive

    def test_report_is_under_review_only_when_every_gate_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs, profiles, lookahead, recursive = self._fixtures(Path(tmp), 80)
            report = build_report(
                runs, profiles, lookahead, recursive, date(2020, 1, 1), date(2021, 1, 1), date(2020, 9, 13)
            )
        self.assertIn("- Status: under_review", report)
        self.assertIn("| Complete trades >= 80 | pass |", report)
        self.assertNotIn("Status: pass", report)

    def test_low_trade_count_fails_without_threshold_rescue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs, profiles, lookahead, recursive = self._fixtures(Path(tmp), 12)
            report = build_report(
                runs, profiles, lookahead, recursive, date(2020, 1, 1), date(2021, 1, 1), date(2020, 9, 13)
            )
        self.assertIn("- Status: failed_validation", report)
        self.assertIn("| Complete trades >= 80 | fail |", report)
        self.assertIn("parameter rescue", report)


if __name__ == "__main__":
    unittest.main()
