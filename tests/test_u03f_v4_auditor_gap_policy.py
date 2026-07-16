import unittest

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import attribute_gap


class GapPolicyTests(unittest.TestCase):
    def test_global_outage_requires_all_members(self):
        self.assertEqual(attribute_gap({"A", "B"}, {"A", "B"}), "global_outage")
        self.assertEqual(attribute_gap({"A", "B"}, {"A"}), "symbol_month_quarantine")
        self.assertEqual(attribute_gap({"A", "B"}, set()), "clean")
