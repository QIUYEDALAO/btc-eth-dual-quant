from __future__ import annotations

import random
import unittest

from btc_eth_dual_quant.audit.completed_candle_derivation import (
    FIVE_MINUTE_MS,
    FiveMinuteCandle,
    canonical_candle_hash,
    derive_completed_candles,
    next_eligible_five_minute_open,
)


def fixture(count: int = 97):
    rows = tuple(
        FiveMinuteCandle("AAA", index * FIVE_MINUTE_MS, 100 + index, 102 + index, 99 + index, 101 + index, 10 + index)
        for index in range(count)
    )
    authority = {(row.symbol, row.open_time_ms): True for row in rows}
    return rows, authority


class CompletedCandleDerivationTests(unittest.TestCase):
    def test_exact_windows_and_three_order_hashes(self):
        rows, authority = fixture()
        shuffled = list(rows)
        random.Random(41).shuffle(shuffled)
        for timeframe, expected_count, constituents in (("15m", 32, 3), ("1h", 8, 12), ("4h", 2, 48)):
            normal = derive_completed_candles(rows, timeframe=timeframe, eligible_slots=authority)
            reverse = derive_completed_candles(reversed(rows), timeframe=timeframe, eligible_slots=authority)
            random_order = derive_completed_candles(shuffled, timeframe=timeframe, eligible_slots=authority)
            self.assertEqual(len(normal), expected_count)
            self.assertEqual({row.constituent_count for row in normal}, {constituents})
            self.assertEqual(canonical_candle_hash(normal), canonical_candle_hash(reverse))
            self.assertEqual(canonical_candle_hash(normal), canonical_candle_hash(random_order))

    def test_no_partial_fill_lifecycle_or_mask_crossing(self):
        rows, authority = fixture(49)
        missing = rows[:5] + rows[6:]
        derived = derive_completed_candles(missing, timeframe="15m", eligible_slots=authority)
        self.assertNotIn(3 * FIVE_MINUTE_MS, {row.open_time_ms for row in derived})
        masked = dict(authority)
        masked[("AAA", 13 * FIVE_MINUTE_MS)] = False
        one_hour = derive_completed_candles(rows, timeframe="1h", eligible_slots=masked)
        self.assertNotIn(12 * FIVE_MINUTE_MS, {row.open_time_ms for row in one_hour})
        missing_authority = dict(authority)
        missing_authority.pop(("AAA", 0))
        with self.assertRaisesRegex(ValueError, "authority"):
            derive_completed_candles(rows, timeframe="15m", eligible_slots=missing_authority)

    def test_next_open_is_strict_and_never_searches_forward(self):
        rows, authority = fixture(14)
        candle = derive_completed_candles(rows, timeframe="1h", eligible_slots=authority)[0]
        indexed = {(row.symbol, row.open_time_ms): row for row in rows}
        self.assertEqual(next_eligible_five_minute_open(completed=candle, five_minute_rows=indexed, eligible_slots=authority), rows[12])
        blocked = dict(authority)
        blocked[("AAA", 12 * FIVE_MINUTE_MS)] = False
        with self.assertRaisesRegex(ValueError, "not eligible"):
            next_eligible_five_minute_open(completed=candle, five_minute_rows=indexed, eligible_slots=blocked)
        without_next = dict(indexed)
        without_next.pop(("AAA", 12 * FIVE_MINUTE_MS))
        with self.assertRaisesRegex(ValueError, "missing"):
            next_eligible_five_minute_open(completed=candle, five_minute_rows=without_next, eligible_slots=authority)


if __name__ == "__main__":
    unittest.main()
