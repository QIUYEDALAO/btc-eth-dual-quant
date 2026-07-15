import unittest

from btc_eth_dual_quant.data.lifecycle_availability import (
    LifecycleEventRegistry,
    aggregate_complete_hour,
    apply_availability_mask,
    build_expected_grid,
)
from tests.v4_lifecycle_fixtures import REGISTRY_PATH, five_minute_bar, ms


class V4ExpectedGridTests(unittest.TestCase):
    def setUp(self):
        self.epoch = LifecycleEventRegistry.from_path(REGISTRY_PATH).build_epochs(
            "KLAYUSDT", ms("2019-01-01T00:00:00Z")
        )[0]

    def test_mask_is_applied_before_expected_grid(self):
        grid = build_expected_grid(
            self.epoch,
            ms("2024-10-28T02:50:00Z"),
            ms("2024-10-28T03:10:00Z"),
            300_000,
        )
        self.assertEqual(grid, (ms("2024-10-28T02:50:00Z"), ms("2024-10-28T02:55:00Z")))
        self.assertNotIn(ms("2024-10-28T03:00:00Z"), grid)

    def test_crossing_bar_is_partial_and_post_boundary_is_not_expected(self):
        crossing = five_minute_bar(ms("2024-10-28T02:59:00Z"))
        post = five_minute_bar(ms("2024-10-28T03:00:00Z"))
        self.assertEqual(apply_availability_mask(crossing, self.epoch), "active_partial")
        self.assertEqual(apply_availability_mask(post, self.epoch), "lifecycle_terminated")

    def test_hour_requires_twelve_contiguous_children_in_one_epoch(self):
        start = ms("2024-10-28T02:00:00Z")
        children = tuple(five_minute_bar(start + index * 300_000) for index in range(12))
        hour = aggregate_complete_hour(children, self.epoch)
        self.assertEqual(hour["open_time_ms"], start)
        with self.assertRaisesRegex(ValueError, "12 contiguous"):
            aggregate_complete_hour(children[:-1], self.epoch)


if __name__ == "__main__":
    unittest.main()
