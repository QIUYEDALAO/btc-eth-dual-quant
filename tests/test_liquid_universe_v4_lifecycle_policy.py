import copy
import json
import unittest

from btc_eth_dual_quant.data.lifecycle_availability import (
    AvailabilityMask,
    CompleteDayStatus,
    LifecycleEventQuarantine,
    LifecycleEventRegistry,
    LifecycleRawRowQuarantine,
    parse_utc,
    utc_epoch_ms,
)
from tests.v4_lifecycle_fixtures import REGISTRY_PATH


class V4LifecyclePolicyTests(unittest.TestCase):
    def test_required_immutable_policy_records_exist(self):
        self.assertTrue(AvailabilityMask("ABC", 1, "active_complete").expected)
        self.assertEqual(LifecycleRawRowQuarantine("event", "hash", "reason").raw_row_hash, "hash")
        self.assertEqual(LifecycleEventQuarantine("event", "reason").event_id, "event")
        self.assertFalse(CompleteDayStatus("active_partial", True, False, False, False).ranking_window_eligible)

    def test_times_are_timezone_aware_utc_and_integer_based(self):
        value = parse_utc("2024-10-28T03:00:00Z")
        self.assertEqual(utc_epoch_ms(value), 1730084400000)
        with self.assertRaises(ValueError):
            parse_utc("2024-10-28T03:00:00")
        with self.assertRaises(ValueError):
            parse_utc("2024-10-28T04:00:00+01:00")

    def test_knowledge_and_physical_availability_are_distinct(self):
        event = LifecycleEventRegistry.from_path(REGISTRY_PATH).events[0]
        self.assertLess(event.known_at, event.effective_at)
        self.assertEqual(event.physical_availability_time, event.effective_at)
        self.assertEqual(event.research_knowledge_time, event.known_at)
        self.assertFalse(event.retrospective_evidence_lag)

    def test_successor_inherits_nothing(self):
        event = LifecycleEventRegistry.from_path(REGISTRY_PATH).events[0]
        self.assertEqual(event.successor_inherits, ())
        self.assertFalse(event.automatic_successor_epoch)

    def test_late_evidence_is_explicitly_disclosed(self):
        document = json.loads(REGISTRY_PATH.read_text())
        changed = copy.deepcopy(document)
        changed["entries"][0]["known_at"] = "2024-11-01T00:00:00Z"
        changed["entries"][0]["publication_time"] = "2024-11-01T00:00:00Z"
        changed["reviewed_event_set_hash"] = LifecycleEventRegistry.compute_event_set_hash(changed["entries"])
        changed["canonical_hash"] = LifecycleEventRegistry.compute_hash(changed)
        event = LifecycleEventRegistry.from_document(changed).events[0]
        self.assertTrue(event.retrospective_evidence_lag)
        self.assertGreater(event.research_knowledge_time, event.physical_availability_time)


if __name__ == "__main__":
    unittest.main()
