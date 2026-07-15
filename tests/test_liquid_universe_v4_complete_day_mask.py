import unittest

from btc_eth_dual_quant.data.lifecycle_availability import (
    LifecycleEventRegistry,
    classify_complete_day,
)
from tests.v4_lifecycle_fixtures import REGISTRY_PATH, ms


class V4CompleteDayMaskTests(unittest.TestCase):
    def setUp(self):
        self.epoch = LifecycleEventRegistry.from_path(REGISTRY_PATH).build_epochs(
            "KLAYUSDT", ms("2019-01-01T00:00:00Z")
        )[0]

    def test_cessation_day_is_partial_and_excluded_from_windows(self):
        status = classify_complete_day(ms("2024-10-28T00:00:00Z"), self.epoch, complete_slots=36)
        self.assertEqual(status.status, "active_partial")
        self.assertFalse(status.ranking_window_eligible)
        self.assertFalse(status.history_window_eligible)

    def test_post_cessation_day_is_not_expected_or_gap(self):
        status = classify_complete_day(ms("2024-10-29T00:00:00Z"), self.epoch, complete_slots=0)
        self.assertEqual(status.status, "lifecycle_terminated")
        self.assertFalse(status.expected)
        self.assertFalse(status.gap)

    def test_pre_boundary_missing_slot_remains_gap(self):
        status = classify_complete_day(ms("2024-10-27T00:00:00Z"), self.epoch, complete_slots=287)
        self.assertEqual(status.status, "data_quarantined")
        self.assertTrue(status.gap)


if __name__ == "__main__":
    unittest.main()
