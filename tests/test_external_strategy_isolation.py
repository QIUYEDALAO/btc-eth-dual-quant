from __future__ import annotations

import copy
import random
import unittest

from btc_eth_dual_quant.audit.completed_candle_derivation import FIVE_MINUTE_MS, FiveMinuteCandle
from btc_eth_dual_quant.audit.external_strategy_isolation import (
    IS_END_MS,
    ActiveInterval,
    boundary_lookup_from_authority,
    build_candidate_segments,
    exact_forced_exit,
    isolation_hash,
    strict_next_entry_open,
)


def candle(symbol: str, timestamp: int, price: float = 100.0) -> FiveMinuteCandle:
    return FiveMinuteCandle(
        symbol=symbol,
        open_time_ms=timestamp,
        open=price,
        high=price + 1,
        low=price - 1,
        close=price + 0.25,
        volume=10.0,
    )


def rows(symbol: str, start: int, count: int) -> list[FiveMinuteCandle]:
    return [candle(symbol, start + index * FIVE_MINUTE_MS, 100 + index / 1000) for index in range(count)]


def boundary_record(symbol: str, timestamp: int, price: float = 50.0) -> dict:
    return {
        "symbol": symbol,
        "row": {
            "symbol": symbol,
            "open_time_ms": timestamp,
            "close_time_ms": timestamp + FIVE_MINUTE_MS - 1,
            "raw_fields": [
                str(timestamp),
                str(price),
                str(price + 1),
                str(price - 1),
                str(price + 0.25),
                "10",
                str(timestamp + FIVE_MINUTE_MS - 1),
            ],
            "raw_line_sha256": "a" * 64,
        },
    }


class ExternalStrategyIsolationTests(unittest.TestCase):
    def test_normal_reverse_shuffled_are_identical_and_inactive_gap_resets_age(self) -> None:
        start_a = 0
        count = 80
        start_b = (count + 12) * FIVE_MINUTE_MS
        intervals = [
            ActiveInterval("BTCUSDT", start_a, start_a + count * FIVE_MINUTE_MS),
            ActiveInterval("BTCUSDT", start_b, start_b + count * FIVE_MINUTE_MS),
        ]
        source = rows("BTCUSDT", start_a, count) + rows("BTCUSDT", start_b, count)
        shuffled = list(source)
        random.Random(20260722).shuffle(shuffled)
        outputs = [
            build_candidate_segments(source, intervals, timeframe="5m", startup_candle_count=30),
            build_candidate_segments(reversed(source), reversed(intervals), timeframe="5m", startup_candle_count=30),
            build_candidate_segments(shuffled, [intervals[1], intervals[0]], timeframe="5m", startup_candle_count=30),
        ]
        self.assertEqual(len({isolation_hash(value) for value in outputs}), 1)
        first, second = outputs[0]
        self.assertEqual(first.entry_eligible_candles[0].open_time_ms, start_a + 30 * FIVE_MINUTE_MS)
        self.assertEqual(second.entry_eligible_candles[0].open_time_ms, start_b + 30 * FIVE_MINUTE_MS)
        self.assertGreater(second.entry_eligible_candles[0].open_time_ms, first.completed_candles[-1].open_time_ms)

    def test_all_six_runtime_timeframes_rewarm_before_entry_and_use_strict_next_open(self) -> None:
        cases = {
            "Supertrend": ("1h", 199, 12),
            "Strategy001": ("5m", 100, 1),
            "UniversalMACD": ("5m", 30, 1),
            "Bandtastic": ("15m", 999, 3),
            "Diamond": ("5m", 12, 1),
            "Heracles": ("4h", 40, 48),
        }
        for candidate, (timeframe, startup, width) in cases.items():
            with self.subTest(candidate=candidate):
                count = (startup + 3) * width
                interval = ActiveInterval("ETHUSDT", 0, count * FIVE_MINUTE_MS)
                segments = build_candidate_segments(
                    rows("ETHUSDT", 0, count),
                    [interval],
                    timeframe=timeframe,
                    startup_candle_count=startup,
                )
                segment = segments[0]
                self.assertEqual(len(segment.completed_candles), startup + 3)
                self.assertEqual(len(segment.entry_eligible_candles), 3)
                decision = segment.entry_eligible_candles[0]
                next_open = strict_next_entry_open(segment, decision)
                self.assertEqual(next_open.open_time_ms, decision.close_time_ms + 1)

    def test_boundary_lookup_is_exact_separate_and_never_searches_forward(self) -> None:
        boundary = 12 * FIVE_MINUTE_MS
        lookup = boundary_lookup_from_authority(
            [boundary_record("BTCUSDT", boundary)], required_count=1, is_end_ms=IS_END_MS
        )
        row = exact_forced_exit(
            lookup, symbol="BTCUSDT", membership_end_exclusive_ms=boundary
        )
        self.assertEqual(row.open, 50.0)
        with self.assertRaisesRegex(ValueError, "exact forced-exit"):
            exact_forced_exit(
                lookup,
                symbol="BTCUSDT",
                membership_end_exclusive_ms=boundary - FIVE_MINUTE_MS,
            )

        active = ActiveInterval("BTCUSDT", 0, boundary)
        segment = build_candidate_segments(
            rows("BTCUSDT", 0, 12), [active], timeframe="5m", startup_candle_count=1
        )[0]
        self.assertNotIn(boundary, {item.open_time_ms for item in segment.five_minute_rows})
        self.assertNotIn(boundary, {item.open_time_ms for item in segment.completed_candles})
        with self.assertRaisesRegex(ValueError, "active-interval authority"):
            build_candidate_segments(
                rows("BTCUSDT", 0, 12) + [candle("BTCUSDT", boundary)],
                [active],
                timeframe="5m",
                startup_candle_count=1,
            )

    def test_missing_duplicate_wrong_time_and_oos_boundary_fail_closed(self) -> None:
        timestamp = FIVE_MINUTE_MS
        with self.assertRaisesRegex(ValueError, "coverage"):
            boundary_lookup_from_authority([], required_count=1)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            boundary_lookup_from_authority(
                [boundary_record("BTCUSDT", timestamp), boundary_record("BTCUSDT", timestamp)],
                required_count=2,
            )
        wrong = boundary_record("BTCUSDT", timestamp)
        wrong["row"]["close_time_ms"] += 1
        with self.assertRaisesRegex(ValueError, "time mismatch"):
            boundary_lookup_from_authority([wrong], required_count=1)
        with self.assertRaisesRegex(ValueError, "OOS"):
            boundary_lookup_from_authority(
                [boundary_record("BTCUSDT", IS_END_MS)], required_count=1
            )

    def test_gaps_overlaps_duplicates_and_oos_rows_fail_closed(self) -> None:
        interval = ActiveInterval("BTCUSDT", 0, 3 * FIVE_MINUTE_MS)
        with self.assertRaisesRegex(ValueError, "gap"):
            build_candidate_segments(
                [candle("BTCUSDT", 0), candle("BTCUSDT", 2 * FIVE_MINUTE_MS)],
                [interval],
                timeframe="5m",
                startup_candle_count=0,
            )
        duplicated = [candle("BTCUSDT", 0), candle("BTCUSDT", 0)]
        with self.assertRaisesRegex(ValueError, "duplicate 5m"):
            build_candidate_segments(
                duplicated,
                [ActiveInterval("BTCUSDT", 0, FIVE_MINUTE_MS)],
                timeframe="5m",
                startup_candle_count=0,
            )
        with self.assertRaisesRegex(ValueError, "overlapping"):
            build_candidate_segments(
                rows("BTCUSDT", 0, 3),
                [
                    ActiveInterval("BTCUSDT", 0, 2 * FIVE_MINUTE_MS),
                    ActiveInterval("BTCUSDT", FIVE_MINUTE_MS, 3 * FIVE_MINUTE_MS),
                ],
                timeframe="5m",
                startup_candle_count=0,
            )
        with self.assertRaisesRegex(ValueError, "OOS"):
            build_candidate_segments(
                [candle("BTCUSDT", IS_END_MS)],
                [ActiveInterval("BTCUSDT", IS_END_MS, IS_END_MS + FIVE_MINUTE_MS)],
                timeframe="5m",
                startup_candle_count=0,
            )

    def test_boundary_raw_hash_symbol_and_ohlcv_tamper_fail(self) -> None:
        base = boundary_record("BTCUSDT", FIVE_MINUTE_MS)
        cases = []
        wrong_symbol = copy.deepcopy(base)
        wrong_symbol["row"]["symbol"] = "ETHUSDT"
        cases.append(wrong_symbol)
        wrong_hash = copy.deepcopy(base)
        wrong_hash["row"]["raw_line_sha256"] = "short"
        cases.append(wrong_hash)
        wrong_ohlcv = copy.deepcopy(base)
        wrong_ohlcv["row"]["raw_fields"][2] = "1"
        cases.append(wrong_ohlcv)
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    boundary_lookup_from_authority([value], required_count=1)


if __name__ == "__main__":
    unittest.main()
