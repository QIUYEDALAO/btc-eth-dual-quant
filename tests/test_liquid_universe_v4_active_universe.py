import unittest

from btc_eth_dual_quant.data.lifecycle_availability import (
    LifecycleEventRegistry,
    SymbolAvailabilityEpoch,
    build_active_universe,
)
from tests.v4_lifecycle_fixtures import REGISTRY_PATH, ms


class V4ActiveUniverseTests(unittest.TestCase):
    def test_membership_stays_fixed_while_active_count_declines(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        membership = ("BTCUSDT", "KLAYUSDT")
        rows = build_active_universe(
            membership,
            (ms("2024-10-28T02:55:00Z"), ms("2024-10-28T03:00:00Z")),
            registry,
            {"BTCUSDT": ms("2017-01-01T00:00:00Z"), "KLAYUSDT": ms("2019-01-01T00:00:00Z")},
        )
        before, after = rows
        self.assertEqual(before.membership_count, 2)
        self.assertEqual(after.membership_count, 2)
        self.assertEqual(before.active_count, 2)
        self.assertEqual(after.active_count, 1)
        self.assertEqual(after.states["KLAYUSDT"], "lifecycle_terminated")
        self.assertNotIn("replacement", after.states)

    def test_explicit_relisting_epoch_is_independent_and_time_selected(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        epochs = (
            SymbolAvailabilityEpoch("ABC-v1", "ABCUSDT", "asset-v1", 0, 100, 0, 0, "close-v1", ("a",)),
            SymbolAvailabilityEpoch("ABC-v2", "ABCUSDT", "asset-v2", 200, None, 200, 200, "relist-v2", ("b",)),
        )
        rows = build_active_universe(
            ("ABCUSDT",),
            (50, 150, 200),
            registry,
            {"ABCUSDT": 0},
            explicit_epochs={"ABCUSDT": epochs},
        )
        self.assertEqual([row.states["ABCUSDT"] for row in rows], [
            "active_complete",
            "lifecycle_terminated",
            "active_complete",
        ])
        self.assertEqual(epochs[1].inherited_history_days, 0)
        self.assertIsNone(epochs[1].inherited_rank)


if __name__ == "__main__":
    unittest.main()
