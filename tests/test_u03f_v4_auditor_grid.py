import unittest
from decimal import Decimal

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import FiveMinuteBar, aggregate_one_hour, expected_slots


class GridTests(unittest.TestCase):
    def test_integer_expected_grid_and_exact_twelve_bar_aggregation(self):
        slots = expected_slots(0, 3_600_000, 300_000)
        self.assertEqual(len(slots), 12)
        bars = [FiveMinuteBar(t, Decimal("1"), Decimal("2"), Decimal("0.5"), Decimal("1.5"), Decimal("1")) for t in slots]
        result = aggregate_one_hour(bars)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["volume"], "12")

    def test_missing_slot_or_post_boundary_slot_is_not_filled(self):
        slots = expected_slots(0, 3_600_000, 300_000)
        bars = [FiveMinuteBar(t, Decimal("1"), Decimal("2"), Decimal("0.5"), Decimal("1.5"), Decimal("1")) for t in slots[:-1]]
        self.assertEqual(aggregate_one_hour(bars), [])
        self.assertEqual(expected_slots(0, 600_000, 300_000, availability_end_exclusive=300_000), (0,))
