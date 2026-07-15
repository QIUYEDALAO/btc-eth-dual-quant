from __future__ import annotations

import json
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.kline_row_conflicts import RawKlineRow, ResolutionRegistry
from btc_eth_dual_quant.data.liquid_universe_pipeline_v3 import build_artifacts_v3, resolve_daily_key


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = json.loads(
    (ROOT / "reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json").read_text(encoding="utf-8")
)


def rows_from_archive(entry: dict, *, authority: str, fields: list[list[str]]) -> list[RawKlineRow]:
    return [
        RawKlineRow.from_fields(
            symbol=entry["symbol"], interval=entry["interval"], fields=row,
            line_number=index + 1,
            archive_key=entry[f"{authority}_archive"]["canonical_key"],
            archive_sha256=entry[f"{authority}_archive"]["sha256"],
            authority=f"official_{authority}_zip",
        )
        for index, row in enumerate(fields)
    ]


class V3ResolutionEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ResolutionRegistry.from_path(
            ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"
        )

    def test_invalid_monthly_row_uses_only_frozen_valid_daily_candidate(self):
        entry = next(item for item in self.registry.entries if item.approved_action.startswith("replace"))
        conflict = next(item for item in EVIDENCE["content"]["conflicts"] if item["conflict_id"] == entry.conflict_id)
        monthly_fields = next(
            row["raw_fields"] for row in conflict["affected_rows"]
            if row["row_sha256"] == entry.monthly_archive.raw_row_hashes[0]
        )
        daily_fields = [list(row) for row in entry.daily_archive.raw_rows]
        result = resolve_daily_key(
            rows_from_archive(entry.as_dict(), authority="monthly", fields=[monthly_fields]),
            rows_from_archive(entry.as_dict(), authority="daily", fields=daily_fields),
            self.registry,
        )
        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.canonical.resolution_id, entry.resolution_id)
        self.assertEqual(result.canonical.fields, tuple(daily_fields[0]))
        self.assertEqual(result.monthly_rows_quarantined, 1)
        self.assertEqual(result.daily_corrections_admitted, 1)
        self.assertEqual(result.synthetic_fills, 0)
        self.assertEqual(result.replacement_members, 0)

    def test_exact_duplicate_preserves_raw_multiplicity(self):
        entry = next(item for item in self.registry.entries if item.approved_action.startswith("collapse"))
        fields = [list(row) for row in entry.daily_archive.raw_rows]
        monthly = rows_from_archive(entry.as_dict(), authority="monthly", fields=fields)
        daily = rows_from_archive(entry.as_dict(), authority="daily", fields=fields)
        result = resolve_daily_key(monthly, daily, self.registry)
        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.canonical.raw_multiplicity, 2)
        self.assertEqual(result.canonical.raw_line_numbers, (1, 2))
        self.assertEqual(result.duplicate_collapses, 1)
        self.assertEqual(len(result.raw_row_quarantine), 2)

    def test_v3_manifests_bind_policy_and_keep_downstream_authorizations_false(self):
        contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v3.json").read_text(encoding="utf-8"))
        eligibility = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
        confirmed = json.loads((ROOT / "config/liquid_spot_confirmed_archive_gaps_v2.json").read_text(encoding="utf-8"))
        artifacts = build_artifacts_v3(
            contract=contract,
            eligibility_registry=eligibility,
            resolution_registry=self.registry,
            confirmed_gap_registry=confirmed,
            daily=[],
            bars_by_symbol_month={},
            source_rows=[],
            resolution_results=[],
        )
        self.assertEqual(set(artifacts), {
            "source_manifest", "conflict_resolution_manifest", "candidate_eligibility_manifest",
            "membership_manifest", "quarantine_manifest", "qualified_panel_manifest", "qualification_summary",
        })
        self.assertTrue(all(document["schema_version"] == 3 for document in artifacts.values()))
        summary = artifacts["qualification_summary"]["content"]
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["synthetic_fills"], 0)
        self.assertEqual(summary["replacement_members"], 0)
        self.assertFalse(any(
            value for key, value in summary["authorizations"].items()
            if key != "asset_data_qualification" and key != "u03e_v3_requalification"
        ))


if __name__ == "__main__":
    unittest.main()
