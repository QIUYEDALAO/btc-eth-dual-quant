from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"


class ResolutionRegistryTests(unittest.TestCase):
    def test_repository_registry_is_hash_bound_and_complete(self):
        registry = ResolutionRegistry.from_path(REGISTRY)
        self.assertEqual(len(registry.entries), 6)
        self.assertEqual(
            registry.adjudication_evidence_hash,
            "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b",
        )
        self.assertEqual(
            {entry.approved_action for entry in registry.entries},
            {"replace_invalid_monthly_with_daily", "collapse_byte_identical_duplicate"},
        )

    def test_registry_hash_and_evidence_drift_fail_closed(self):
        document = json.loads(REGISTRY.read_text(encoding="utf-8"))
        changed = copy.deepcopy(document)
        changed["entries"][0]["daily_archive"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "registry canonical hash mismatch"):
            ResolutionRegistry.from_document(changed)

        changed = copy.deepcopy(document)
        changed["entries"][0]["adjudication_evidence_hash"] = "f" * 64
        changed["canonical_hash"] = ResolutionRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "adjudication evidence hash mismatch"):
            ResolutionRegistry.from_document(changed)

    def test_missing_or_duplicate_key_is_rejected(self):
        document = json.loads(REGISTRY.read_text(encoding="utf-8"))
        changed = copy.deepcopy(document)
        changed["entries"].append(copy.deepcopy(changed["entries"][0]))
        changed["canonical_hash"] = ResolutionRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "duplicate resolution key"):
            ResolutionRegistry.from_document(changed)


if __name__ == "__main__":
    unittest.main()
