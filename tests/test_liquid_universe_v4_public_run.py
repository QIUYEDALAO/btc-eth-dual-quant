from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.liquid_universe import MinuteBar
from btc_eth_dual_quant.data.liquid_universe_pipeline_v4 import validate_lifecycle_symbol_month_grid
from scripts.liquid_universe_v4_public_run import _validate_frozen_source_rows, run


UTC = timezone.utc


def bar(at: datetime) -> MinuteBar:
    return MinuteBar("KLAYUSDT", at, Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1"))


class LiquidUniverseV4PublicRunTests(unittest.TestCase):
    def test_consumed_source_inventory_is_exactly_frozen(self):
        bindings = {
            "data/spot/a.zip": {"canonical_key": "data/spot/a.zip", "sha256": "a" * 64, "byte_size": 1},
            "data/spot/b.zip": {"canonical_key": "data/spot/b.zip", "sha256": "b" * 64, "byte_size": 2},
        }
        rows = [
            {"canonical_key": "data/spot/a.zip", "sha256": "a" * 64, "byte_size": 1},
            {"canonical_key": "data/spot/b.zip", "sha256": "b" * 64, "byte_size": 2},
        ]
        _validate_frozen_source_rows(rows, bindings, require_complete=True)

        with self.assertRaisesRegex(ValueError, "unfrozen source consumed"):
            _validate_frozen_source_rows(
                rows + [{"canonical_key": "data/spot/extra.zip", "sha256": "c" * 64, "byte_size": 3}],
                bindings,
                require_complete=True,
            )
        with self.assertRaisesRegex(ValueError, "consumed source binding drift"):
            _validate_frozen_source_rows(
                [{**rows[0], "sha256": "0" * 64}, rows[1]], bindings, require_complete=True,
            )
        with self.assertRaisesRegex(ValueError, "frozen source not consumed"):
            _validate_frozen_source_rows(rows[:1], bindings, require_complete=True)

    def test_authority_run_rejects_download_or_remote_replacement_mode(self):
        arguments = {
            "raw_root": Path("unused"),
            "evidence_dir": Path("unused"),
            "end_month": "2026-06",
            "report_path": Path("unused"),
            "diff_report_path": Path("unused"),
        }
        with self.assertRaisesRegex(ValueError, "frozen local sources"):
            run(**arguments, offline=False, verify_remote_registry=False)
        with self.assertRaisesRegex(ValueError, "frozen local sources"):
            run(**arguments, offline=True, verify_remote_registry=True)

    def test_lifecycle_grid_stops_at_boundary_without_creating_gap(self):
        start = datetime(2024, 10, 1, tzinfo=UTC)
        boundary = datetime(2024, 10, 1, 1, tzinfo=UTC)
        bars = [bar(start + timedelta(minutes=5 * index)) for index in range(12)]
        result = validate_lifecycle_symbol_month_grid(
            "KLAYUSDT", "2024-10", bars,
            availability_end_exclusive_ms=int(boundary.timestamp() * 1_000),
        )
        self.assertTrue(result.complete)
        self.assertEqual((result.expected_count, result.actual_count), (12, 12))

    def test_post_lifecycle_row_blocks_instead_of_becoming_canonical(self):
        start = datetime(2024, 10, 1, tzinfo=UTC)
        boundary = start + timedelta(hours=1)
        bars = [bar(start + timedelta(minutes=5 * index)) for index in range(13)]
        result = validate_lifecycle_symbol_month_grid(
            "KLAYUSDT", "2024-10", bars,
            availability_end_exclusive_ms=int(boundary.timestamp() * 1_000),
        )
        self.assertFalse(result.complete)
        self.assertIn("unexpected post-lifecycle", result.errors[0])

    def test_pre_lifecycle_gap_remains_blocking(self):
        start = datetime(2024, 10, 1, tzinfo=UTC)
        boundary = start + timedelta(hours=1)
        bars = [bar(start + timedelta(minutes=5 * index)) for index in range(12) if index != 4]
        result = validate_lifecycle_symbol_month_grid(
            "KLAYUSDT", "2024-10", bars,
            availability_end_exclusive_ms=int(boundary.timestamp() * 1_000),
        )
        self.assertFalse(result.complete)
        self.assertEqual(len(result.missing), 1)


if __name__ == "__main__":
    unittest.main()
