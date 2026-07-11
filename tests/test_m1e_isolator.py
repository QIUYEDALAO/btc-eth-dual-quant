from __future__ import annotations

import unittest
import gzip
import importlib.util
import json
import tempfile
from pathlib import Path

from btc_eth_dual_quant.audit.m1e_isolator import (
    INTERVAL_MS,
    IS_END_EXCLUSIVE_MS,
    IS_START_MS,
    eligible_after_rewarm,
    isolate_bars,
)


def bar(timestamp: int, timeframe: str = "1h") -> dict:
    interval = INTERVAL_MS[timeframe]
    return {
        "open_time": timestamp, "open": "100", "high": "103", "low": "99", "close": "102",
        "volume": "10", "close_time": timestamp + interval - 1, "quote_volume": "1010",
        "trade_count": "12", "taker_buy_base_volume": "5", "taker_buy_quote_volume": "505",
    }


class M1EIsolatorTests(unittest.TestCase):
    def test_valid_is_rows_are_segmented_and_hashed_deterministically(self) -> None:
        rows = [bar(IS_START_MS), bar(IS_START_MS + INTERVAL_MS["1h"])]
        first = isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=rows)
        second = isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=rows)
        self.assertEqual(first.canonical_sha256, second.canonical_sha256)
        self.assertEqual((first.gap_count, first.segment_count), (0, 1))
        self.assertEqual(first.rows[-1].bars_since_segment_start, 2)

    def test_oos_and_pre_is_rows_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside sealed IS"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=[bar(IS_END_EXCLUSIVE_MS)])
        with self.assertRaisesRegex(ValueError, "outside sealed IS"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=[bar(IS_START_MS - INTERVAL_MS["1h"])])

    def test_incomplete_future_ordered_and_duplicate_rules(self) -> None:
        invalid = bar(IS_START_MS)
        invalid["close_time"] -= 1
        with self.assertRaisesRegex(ValueError, "incomplete"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=[invalid])
        duplicate = [bar(IS_START_MS), bar(IS_START_MS)]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=duplicate)

    def test_gap_starts_new_segment_and_requires_later_rewarm(self) -> None:
        interval = INTERVAL_MS["1h"]
        result = isolate_bars(symbol="ETHUSDT", timeframe="1h", rows=[bar(IS_START_MS), bar(IS_START_MS + 2 * interval)])
        self.assertEqual((result.gap_count, result.segment_count), (1, 2))
        self.assertFalse(eligible_after_rewarm(result.rows[-1], 2))
        self.assertTrue(eligible_after_rewarm(result.rows[-1], 1))

    def test_only_btc_eth_and_one_four_hour_are_supported(self) -> None:
        with self.assertRaises(ValueError):
            isolate_bars(symbol="SOLUSDT", timeframe="1h", rows=[])
        with self.assertRaises(ValueError):
            isolate_bars(symbol="BTCUSDT", timeframe="5m", rows=[])

    def test_illegal_ohlc_and_negative_flow_are_rejected(self) -> None:
        invalid = bar(IS_START_MS)
        invalid["high"] = "98"
        with self.assertRaisesRegex(ValueError, "OHLC"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=[invalid])

    def test_snapshot_builder_does_not_parse_oos_ohlc(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "m1e_build_is_snapshot", Path(__file__).resolve().parents[1] / "scripts/m1e_build_is_snapshot.py"
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                handle.write(json.dumps(bar(IS_START_MS)) + "\n")
                handle.write(f'{{"open_time":{IS_END_EXCLUSIVE_MS},"close":"must_not_parse" BROKEN}}\n')
            rows, oos_parsed = module.bounded_rows(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(oos_parsed, 0)
        invalid = bar(IS_START_MS)
        invalid["volume"] = "-1"
        with self.assertRaisesRegex(ValueError, "negative volume"):
            isolate_bars(symbol="BTCUSDT", timeframe="1h", rows=[invalid])


if __name__ == "__main__":
    unittest.main()
