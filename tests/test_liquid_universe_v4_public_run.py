from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.liquid_universe import MinuteBar
from btc_eth_dual_quant.data.liquid_universe_pipeline_v4 import validate_lifecycle_symbol_month_grid
from scripts.liquid_universe_v4_public_run import run


UTC = timezone.utc


def bar(at: datetime) -> MinuteBar:
    return MinuteBar("KLAYUSDT", at, Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1"))


class LiquidUniverseV4PublicRunTests(unittest.TestCase):
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
