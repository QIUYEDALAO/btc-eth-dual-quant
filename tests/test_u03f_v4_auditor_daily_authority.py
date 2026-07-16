import unittest

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import KlineRow, reconcile_daily_authority


def row(ts="1704067200000", volume="10"):
    close = str(int(ts) + 86_399_999)
    return KlineRow.from_fields([ts, "1", "2", "0.5", "1.5", volume, close, "20", "3", "4", "5", "0"])


class DailyAuthorityTests(unittest.TestCase):
    def test_daily_fills_missing_but_cannot_override_monthly(self):
        first = row()
        extra = row("1704153600000")
        merged, conflicts = reconcile_daily_authority([first], [first, extra])
        self.assertEqual(len(merged), 2)
        self.assertEqual(conflicts, [])
        changed = row(volume="11")
        _, conflicts = reconcile_daily_authority([first], [changed])
        self.assertEqual(len(conflicts), 1)

    def test_unknown_duplicates_and_negative_values_fail(self):
        with self.assertRaises(ValueError):
            reconcile_daily_authority([row(), row()], [])
        with self.assertRaises(ValueError):
            row(volume="-1")
