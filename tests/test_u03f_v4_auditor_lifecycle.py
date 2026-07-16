import unittest

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import LifecycleEvent, availability_state


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.event = LifecycleEvent.from_mapping({
            "event_id": "event", "symbol": "KLAYUSDT",
            "known_at": "2024-10-16T08:00:03.464000Z",
            "effective_at": "2024-10-28T03:00:00Z",
            "availability_end_exclusive": "2024-10-28T03:00:00Z",
            "last_valid_market_time": "2024-10-28T02:59:59.999000Z",
            "successor_authority": "provenance_only",
        })

    def test_boundary_is_start_inclusive_end_exclusive(self):
        self.assertEqual(availability_state(self.event, 1730084399999), "active_partial")
        self.assertEqual(availability_state(self.event, 1730084400000), "lifecycle_terminated")

    def test_successor_and_overlap_fail_closed(self):
        with self.assertRaises(ValueError):
            LifecycleEvent.from_mapping({**self.event.source, "successor_authority": "inherits_history"})
