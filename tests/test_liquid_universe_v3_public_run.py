from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry
from scripts.liquid_universe_v3_public_run import (
    assert_registered_archive_bindings,
    build_daily_canonical_evidence,
    raw_rows_from_archive,
)


ROOT = Path(__file__).resolve().parents[1]


def write_archive(path: Path, rows: list[list[str]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(path.with_suffix(".csv").name, "\n".join(",".join(row) for row in rows) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class V3PublicRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ResolutionRegistry.from_path(
            ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"
        )
        cls.adjudication = json.loads(
            (ROOT / "reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json").read_text()
        )

    def monthly_rows(self, entry):
        conflict = next(
            item for item in self.adjudication["content"]["conflicts"]
            if item["conflict_id"] == entry.conflict_id
        )
        by_hash = {row["row_sha256"]: row["raw_fields"] for row in conflict["affected_rows"]}
        return [by_hash[digest] for digest in entry.monthly_archive.raw_row_hashes]

    def test_registered_sources_are_required_and_remote_checksum_drift_stops(self):
        entry = self.registry.entries[0]
        registry = ResolutionRegistry(self.registry.document, (entry,))
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory)
            monthly = raw_root / Path(entry.monthly_archive.canonical_key).relative_to("data/spot")
            daily = raw_root / Path(entry.daily_archive.canonical_key).relative_to("data/spot")
            write_archive(monthly, self.monthly_rows(entry))
            write_archive(daily, [list(row) for row in entry.daily_archive.raw_rows])

            observed = {
                entry.monthly_archive.canonical_key: entry.monthly_archive.sha256,
                entry.daily_archive.canonical_key: entry.daily_archive.sha256,
            }
            expected_local = {
                monthly: entry.monthly_archive.sha256,
                daily: entry.daily_archive.sha256,
            }
            assert_registered_archive_bindings(
                raw_root,
                registry,
                observed.__getitem__,
                file_hasher=expected_local.__getitem__,
            )

            observed[entry.daily_archive.canonical_key] = "f" * 64
            with self.assertRaisesRegex(ValueError, "remote checksum drift"):
                assert_registered_archive_bindings(
                    raw_root,
                    registry,
                    observed.__getitem__,
                    file_hasher=expected_local.__getitem__,
                )

            daily.unlink()
            with self.assertRaisesRegex(ValueError, "registered archive missing"):
                assert_registered_archive_bindings(
                    raw_root,
                    registry,
                    observed.__getitem__,
                    file_hasher=expected_local.__getitem__,
                )

    def test_registered_btt_and_axs_rows_use_generic_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory)
            monthly_groups = {}
            daily_groups = {}
            for entry in self.registry.entries:
                monthly_path = raw_root / Path(entry.monthly_archive.canonical_key).relative_to("data/spot")
                daily_path = raw_root / Path(entry.daily_archive.canonical_key).relative_to("data/spot")
                monthly_fields = self.monthly_rows(entry)
                write_archive(monthly_path, monthly_fields)
                write_archive(daily_path, [list(row) for row in entry.daily_archive.raw_rows])
                monthly_groups[entry.key] = raw_rows_from_archive(
                    monthly_path,
                    symbol=entry.symbol,
                    interval=entry.interval,
                    archive_key=entry.monthly_archive.canonical_key,
                    archive_sha256=entry.monthly_archive.sha256,
                    authority="official_monthly_zip",
                )
                daily_groups[entry.key] = raw_rows_from_archive(
                    daily_path,
                    symbol=entry.symbol,
                    interval=entry.interval,
                    archive_key=entry.daily_archive.canonical_key,
                    archive_sha256=entry.daily_archive.sha256,
                    authority="official_daily_zip",
                )

            daily, outcomes = build_daily_canonical_evidence(
                monthly_groups=monthly_groups,
                daily_groups=daily_groups,
                registry=self.registry,
                contract=json.loads((ROOT / "config/liquid_spot_universe_contract_v3.json").read_text()),
                eligibility_registry=json.loads(
                    (ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text()
                ),
            )

        self.assertEqual(len(daily), 6)
        self.assertEqual(sum(item.monthly_rows_quarantined for item in outcomes), 5)
        self.assertEqual(sum(item.daily_corrections_admitted for item in outcomes), 5)
        self.assertEqual(sum(item.duplicate_collapses for item in outcomes), 1)
        self.assertEqual(sum(item.unresolved_row_conflicts for item in outcomes), 0)
        self.assertTrue(all(item.canonical and item.canonical.resolution_id for item in outcomes))


if __name__ == "__main__":
    unittest.main()
