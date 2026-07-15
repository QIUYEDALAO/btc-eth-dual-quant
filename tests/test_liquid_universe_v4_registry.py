import copy
import json
import unittest

from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry
from tests.v4_lifecycle_fixtures import REGISTRY_PATH


class V4LifecycleRegistryTests(unittest.TestCase):
    def test_klay_event_is_fully_evidence_bound(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        event = registry.events[0]
        self.assertEqual(event.event_id, "KLAYUSDT-SPOT-2024-10-28-PERMANENT-CESSATION")
        self.assertEqual(event.availability_end_exclusive.isoformat(), "2024-10-28T03:00:00+00:00")
        self.assertEqual(event.last_valid_market_time.isoformat(), "2024-10-28T02:59:59.999000+00:00")
        self.assertEqual(event.adjudication_hash, "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a")
        self.assertEqual([row.classification for row in event.affected_raw_rows], [
            "cessation_day_partial_row",
            "post_cessation_normal_duration_placeholder",
            "post_cessation_malformed_placeholder",
        ])
        self.assertEqual(event.announced_successor_symbol, "KAIAUSDT")
        self.assertEqual(event.successor_authority, "provenance_only")

    def test_hash_change_overlap_or_unknown_event_fails_closed(self):
        document = json.loads(REGISTRY_PATH.read_text())
        changed = copy.deepcopy(document)
        changed["entries"][0]["affected_raw_rows"][0]["raw_row_sha256"] = "0" * 64
        changed["canonical_hash"] = LifecycleEventRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "reviewed lifecycle evidence"):
            LifecycleEventRegistry.from_document(changed)

        changed = copy.deepcopy(document)
        changed["entries"].append(copy.deepcopy(changed["entries"][0]))
        changed["entries"][1]["event_id"] = "overlap"
        changed["canonical_hash"] = LifecycleEventRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "overlapping lifecycle epochs"):
            LifecycleEventRegistry.from_document(changed)

    def test_new_post_event_row_requires_readjudication(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        claim = registry.claim_row("KLAYUSDT", "1d", 1730332800000, "1" * 64)
        self.assertEqual(claim.status, "unresolved_blocked")
        self.assertEqual(claim.reason, "new_post_event_row_readjudication_required")

    def test_all_reviewed_klay_rows_are_claimed_with_frozen_semantics(self):
        registry = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        expected = (
            (1730073600000, "692aa865b2c8924b0b2e64a9128346ac77b1db3d0f1b82fdf7cd79fe0cb96319", "active_partial", "cessation_day_partial_row"),
            (1730160000000, "fde7b4044554dff07cc39570082938a67e4c6763d2106e2b94809dd7d85695b7", "lifecycle_terminated", "post_cessation_normal_duration_placeholder"),
            (1730246400000, "8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1", "lifecycle_terminated", "post_cessation_malformed_placeholder"),
        )
        for open_time_ms, raw_hash, status, classification in expected:
            claim = registry.claim_row("KLAYUSDT", "1d", open_time_ms, raw_hash)
            self.assertEqual(claim.status, status)
            self.assertEqual(claim.row_classification, classification)


if __name__ == "__main__":
    unittest.main()
