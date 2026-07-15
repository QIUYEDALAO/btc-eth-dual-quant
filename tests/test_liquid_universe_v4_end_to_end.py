import json
import unittest

from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry
from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry
from btc_eth_dual_quant.data.liquid_universe_pipeline_v4 import (
    V4_MANIFEST_TYPES,
    build_fixture_artifacts_v4,
    dispatch_daily_rows,
)
from tests.v4_lifecycle_fixtures import CONTRACT_PATH, REGISTRY_PATH, ROOT, daily_row


class V4EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text())
        self.lifecycle = LifecycleEventRegistry.from_path(REGISTRY_PATH)
        self.rows = ResolutionRegistry.from_path(ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json")

    def test_lifecycle_rows_are_quarantined_without_repair_or_gap(self):
        row = daily_row("1730246400000000", "1730084399999000", "7" * 64)
        result = dispatch_daily_rows((row,), (), self.rows, self.lifecycle)
        self.assertEqual(result.status, "lifecycle_terminated")
        self.assertIsNone(result.canonical)
        self.assertEqual(result.raw_row_quarantine[0]["raw_row_hash"], "8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1")
        self.assertFalse(result.count_as_gap)
        self.assertFalse(result.close_time_rewritten)

    def test_policy_overlap_fails_instead_of_first_match_wins(self):
        row = daily_row("1730246400000000", "1730084399999000", "7" * 64)
        class OverlappingRegistry:
            def get(self, key):
                if key == row.canonical_key:
                    return object()
                return self.rows.get(key)

        fake_rows = OverlappingRegistry()
        fake_rows.rows = self.rows
        result = dispatch_daily_rows((row,), (), fake_rows, self.lifecycle)
        self.assertEqual(result.status, "blocked_policy_overlap")

    def test_fixture_build_emits_every_hash_bound_v4_artifact(self):
        first = build_fixture_artifacts_v4(self.contract, self.lifecycle)
        second = build_fixture_artifacts_v4(self.contract, self.lifecycle, reverse_inputs=True)
        self.assertEqual(set(first), V4_MANIFEST_TYPES)
        self.assertEqual(first, second)
        self.assertEqual(first["qualification_summary"]["content"]["status"], "implementation_fixture_pass")
        self.assertFalse(any(first["qualification_summary"]["content"]["authorizations"].values()))


if __name__ == "__main__":
    unittest.main()
