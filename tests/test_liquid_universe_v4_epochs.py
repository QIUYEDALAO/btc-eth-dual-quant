import copy
import json
import unittest

from btc_eth_dual_quant.data.lifecycle_availability import (
    LifecycleEventRegistry,
    SymbolAvailabilityEpoch,
    validate_epochs,
)
from tests.v4_lifecycle_fixtures import REGISTRY_PATH, ms


class V4EpochTests(unittest.TestCase):
    def test_event_closes_old_identity_epoch_without_successor_splice(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        epochs = registry.build_epochs("KLAYUSDT", ms("2019-01-01T00:00:00Z"))
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].identity_version, "KLAY-v1")
        self.assertEqual(epochs[0].end_exclusive_ms, ms("2024-10-28T03:00:00Z"))

    def test_overlapping_epochs_are_blocked(self):
        first = SymbolAvailabilityEpoch("one", "ABC", "asset-v1", 0, 100, 0, 0, None, ())
        second = SymbolAvailabilityEpoch("two", "ABC", "asset-v2", 99, 200, 99, 99, None, ())
        with self.assertRaisesRegex(ValueError, "overlapping lifecycle epochs"):
            validate_epochs((first, second))

    def test_new_identity_epoch_does_not_inherit_history(self):
        epochs = validate_epochs((
            SymbolAvailabilityEpoch("old", "ABC", "asset-v1", 0, 100, 0, 0, "close-v1", ("a",)),
            SymbolAvailabilityEpoch("new", "ABC", "asset-v2", 200, None, 200, 200, "relist-v2", ("b",)),
        ))
        self.assertEqual(len(epochs), 2)
        self.assertEqual(epochs[1].inherited_history_days, 0)
        self.assertEqual(epochs[1].inherited_rank, None)

    def test_multiple_registry_events_cannot_auto_create_successor_epoch(self):
        document = json.loads(REGISTRY_PATH.read_text())
        second = copy.deepcopy(document["entries"][0])
        second["event_id"] = "KLAYUSDT-SECOND-LIFECYCLE-EVENT"
        second["identity_version"] = "KLAY-v2"
        for key in (
            "known_at",
            "publication_time",
            "effective_at",
            "last_valid_market_time",
            "availability_end_exclusive",
            "affected_interval_start",
            "affected_interval_end_exclusive",
            "resolution_approved_at",
        ):
            second[key] = {
                "known_at": "2025-01-01T00:00:00Z",
                "publication_time": "2025-01-01T00:00:00Z",
                "effective_at": "2025-02-01T00:00:00Z",
                "last_valid_market_time": "2025-01-31T23:59:59.999Z",
                "availability_end_exclusive": "2025-02-01T00:00:00Z",
                "affected_interval_start": "2025-01-31T00:00:00Z",
                "affected_interval_end_exclusive": "2025-02-02T00:00:00Z",
                "resolution_approved_at": "2026-07-16T00:00:00Z",
            }[key]
        second["affected_raw_rows"] = []
        document["entries"].append(second)
        document["reviewed_event_set_hash"] = LifecycleEventRegistry.compute_event_set_hash(document["entries"])
        document["canonical_hash"] = LifecycleEventRegistry.compute_hash(document)
        registry = LifecycleEventRegistry.from_document(document)
        with self.assertRaisesRegex(ValueError, "explicit epoch definitions"):
            registry.build_epochs("KLAYUSDT", ms("2019-01-01T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
