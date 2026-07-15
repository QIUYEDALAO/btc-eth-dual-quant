from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.kline_row_conflicts import RawKlineRow, ResolutionRegistry
from btc_eth_dual_quant.data.liquid_universe_pipeline_v3 import resolve_daily_key


ROOT = Path(__file__).resolve().parents[1]


class V3FaultInjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ResolutionRegistry.from_path(
            ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"
        )
        cls.registry_document = json.loads(
            (ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json").read_text(encoding="utf-8")
        )

    def _rows(self, entry, source, fields):
        archive = getattr(entry, f"{source}_archive")
        return [RawKlineRow.from_fields(
            symbol=entry.symbol, interval=entry.interval, fields=list(row), line_number=index + 1,
            archive_key=archive.canonical_key, archive_sha256=archive.sha256,
            authority=f"official_{source}_zip",
        ) for index, row in enumerate(fields)]

    def test_unknown_conflict_and_source_checksum_drift_block(self):
        entry = next(item for item in self.registry.entries if item.approved_action.startswith("collapse"))
        fields = entry.daily_archive.raw_rows
        monthly = self._rows(entry, "monthly", fields)
        daily = self._rows(entry, "daily", fields)

        unknown = copy.copy(monthly[0])
        object.__setattr__(unknown, "symbol", "NEWUSDT")
        result = resolve_daily_key([unknown, unknown], [], self.registry)
        self.assertEqual(result.status, "blocked_pending_adjudication")

        drifted = copy.copy(monthly[0])
        object.__setattr__(drifted, "archive_sha256", "f" * 64)
        result = resolve_daily_key([drifted, drifted], daily, self.registry)
        self.assertEqual(result.status, "blocked_pending_adjudication")

    def test_daily_invalid_duplicate_rest_mismatch_and_missing_evidence_block(self):
        entry = next(item for item in self.registry.entries if item.approved_action.startswith("replace"))
        monthly_fields = list(entry.rest_comparators[0].normalized_rows[0])
        monthly_fields[5] = "-1"
        monthly = self._rows(entry, "monthly", [monthly_fields])

        invalid_daily = [list(entry.daily_archive.raw_rows[0])]
        invalid_daily[0][5] = "-1"
        self.assertNotEqual(resolve_daily_key(monthly, self._rows(entry, "daily", invalid_daily), self.registry).status, "resolved")

        conflicting_daily = [list(entry.daily_archive.raw_rows[0]), list(entry.daily_archive.raw_rows[0])]
        conflicting_daily[1][4] = "999"
        self.assertNotEqual(resolve_daily_key(monthly, self._rows(entry, "daily", conflicting_daily), self.registry).status, "resolved")

        exact_duplicate = [list(entry.daily_archive.raw_rows[0]), list(entry.daily_archive.raw_rows[0])]
        self.assertNotEqual(resolve_daily_key(monthly, self._rows(entry, "daily", exact_duplicate), self.registry).status, "resolved")

        changed = copy.deepcopy(self.registry_document)
        target = next(item for item in changed["entries"] if item["resolution_id"] == entry.resolution_id)
        target["rest_comparators"][0]["normalized_rows"][0][4] = "999"
        changed["canonical_hash"] = ResolutionRegistry.compute_hash(changed)
        mismatched_registry = ResolutionRegistry.from_document(changed)
        self.assertNotEqual(
            resolve_daily_key(monthly, self._rows(entry, "daily", entry.daily_archive.raw_rows), mismatched_registry).status,
            "resolved",
        )

        changed = copy.deepcopy(self.registry_document)
        target = next(item for item in changed["entries"] if item["resolution_id"] == entry.resolution_id)
        target["rest_comparators"].pop()
        changed["canonical_hash"] = ResolutionRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "two frozen REST comparators"):
            ResolutionRegistry.from_document(changed)

        self.assertTrue(all(item.endpoint_identity for item in entry.rest_comparators))
        self.assertEqual(len(entry.rest_comparators), 2)

    def test_live_rest_is_not_part_of_the_resolution_api(self):
        import inspect

        source = inspect.getsource(resolve_daily_key)
        for forbidden in ("urlopen", "requests", "api.binance.com", "data-api.binance.vision"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
