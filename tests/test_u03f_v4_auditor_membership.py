import unittest
from decimal import Decimal

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import rank_membership


class MembershipTests(unittest.TestCase):
    def test_decimal_median_and_symbol_tie_break_are_deterministic(self):
        daily = {
            "ETHUSDT": [Decimal("10")] * 90,
            "BTCUSDT": [Decimal("10")] * 90,
            "XRPUSDT": [Decimal("9")] * 90,
        }
        rows = rank_membership("2024-01", daily, target_size=2)
        self.assertEqual([(r["rank"], r["symbol"]) for r in rows], [(1, "BTCUSDT"), (2, "ETHUSDT")])

    def test_incomplete_rank_window_and_future_data_are_rejected(self):
        with self.assertRaises(ValueError):
            rank_membership("2024-01", {"BTCUSDT": [Decimal("1")] * 89})
