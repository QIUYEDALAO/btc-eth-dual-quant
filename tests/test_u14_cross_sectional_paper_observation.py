from __future__ import annotations

import unittest
import copy
from decimal import Decimal

from scripts.u14_cross_sectional_paper_observation import cluster_events, evaluate_gates, select_events
from scripts.u14_cross_sectional_paper_observation_check import RUN, validate
from scripts.u04_cross_sectional_data_qualification import load_json


class U14PaperObservationCoreTests(unittest.TestCase):
    def setUp(self):
        self.run = load_json(RUN)

    def test_frozen_failed_result(self):
        self.assertEqual(validate(self.run), [])

    def test_result_or_authorization_tamper_fails(self):
        changed = copy.deepcopy(self.run); changed["metrics"]["complete_is_independent_episodes"] = 93
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.run); changed["authorizations"]["strategy"] = True
        self.assertTrue(validate(changed))
    def test_candidate_and_connected_cluster(self):
        symbols = tuple(f"S{i:02d}" for i in range(15)); membership = {"2020-01": symbols}
        values = {symbol: (Decimal("100"), Decimal("100.3"), Decimal("98.5"), Decimal("99")) for symbol in symbols}
        values[symbols[0]] = (Decimal("100"), Decimal("100.2"), Decimal("98"), Decimal("99.9"))
        first = 1_577_851_200_000
        events, _ = select_events({first: values, first + 14_400_000: values}, membership, "p", "q")
        self.assertEqual(len(events), 2); self.assertEqual(events[0]["symbol"], symbols[0]); self.assertEqual(len(cluster_events(events)), 1)

    def test_failed_empty_gates(self):
        metrics, checks = evaluate_gates([], {}, 0)
        self.assertEqual(metrics["complete_is_independent_episodes"], 0); self.assertFalse(all(checks.values()))


if __name__ == "__main__": unittest.main()
