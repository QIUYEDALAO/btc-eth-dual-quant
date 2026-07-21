from __future__ import annotations

import unittest
import copy
from decimal import Decimal

from scripts import u11_cross_sectional_paper_observation as observation
from scripts.u11_cross_sectional_paper_observation import LOOKBACK, PATH_MS, capture, cluster_events, window_stats
from scripts.u11_cross_sectional_paper_observation_check import ADJ,E,HASHES,validate
from scripts.u04_cross_sectional_data_qualification import load_json


class U11PaperObservationCoreTests(unittest.TestCase):
    def test_rerun_entrypoint_is_disabled(self):
        self.assertEqual(observation.main(), 2)

    def test_invalid_attempt_is_frozen(self):
        summary=load_json(E/"run_manifest.json");manifests={n:load_json(E/f"{n}.json") for n in HASHES}
        self.assertEqual(validate(summary,manifests,ADJ.read_text()),[])
        changed=copy.deepcopy(summary);changed["second_run_executed"]=True
        self.assertTrue(validate(changed,manifests,ADJ.read_text()))
    def test_zero_intercept_capture(self):
        common = [Decimal("0.01"), Decimal("-0.01")]
        asset = [Decimal("0.012"), Decimal("-0.005")]
        self.assertEqual(capture(common, asset, True), Decimal("1.2"))
        self.assertEqual(capture(common, asset, False), Decimal("0.5"))

    def test_state_sample_gate(self):
        common = [Decimal("0.01") if index % 2 else Decimal("-0.01") for index in range(LOOKBACK)]
        asset = [value for value in common]
        stats = window_stats(common, asset)
        self.assertIsNotNone(stats)
        self.assertEqual(stats["score"], Decimal(0))
        self.assertIsNone(window_stats([Decimal("0.01")] * LOOKBACK, [Decimal("0.01")] * LOOKBACK))

    def test_connected_cluster(self):
        base = {"symbol": "A"}
        events = [{**base, "decision_time_ms": value, "event_id": str(index)} for index, value in enumerate((0, PATH_MS, 2 * PATH_MS, 3 * PATH_MS + 1))]
        self.assertEqual([row["event_id"] for row in cluster_events(events)], ["0", "3"])


if __name__ == "__main__":
    unittest.main()
