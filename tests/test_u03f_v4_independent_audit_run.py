from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_run import (
    _boundary_differential,
    _source_order,
    parse_archive_identity,
    render_report,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "u03f_result_check", ROOT / "scripts/u03f_v4_independent_audit_result_check.py"
)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class IndependentAuditRunTests(unittest.TestCase):
    def test_archive_identity_is_strict_and_path_safe(self):
        key = "data/spot/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-2024-01.zip"
        self.assertEqual(parse_archive_identity(key), ("monthly", "BTCUSDT", "5m", "2024-01"))
        with self.assertRaises(ValueError):
            parse_archive_identity("data/spot/monthly/klines/../BTCUSDT.zip")

    def test_boundary_differential_discloses_integer_policy_risk(self):
        result = _boundary_differential()
        self.assertEqual(result["current_boundary_mismatches"], 0)
        self.assertTrue(result["fault_mismatch"])

    def test_source_orders_have_a_deterministic_total_identity(self):
        entries = [{"canonical_key": value} for value in ("b", "a", "c")]
        self.assertEqual(
            sorted(item["canonical_key"] for item in _source_order(entries, "shuffled")),
            ["a", "b", "c"],
        )

    def test_report_rendering_is_deterministic(self):
        summary = {
            "verdict": "failed_audit",
            "range": {"start": "2020-01", "end": "2026-06"},
            "source_freeze_hash": "a" * 64,
            "production_artifact_set_hash": "b" * 64,
            "independent_artifact_set_hash": "c" * 64,
            "counts": {
                "months": 78,
                "membership_rows": 1170,
                "source_archive_count": 27736,
                "gap_records": 241,
                "global_windows": 16,
                "symbol_month_quarantines": 2,
            },
            "critical_findings": [],
            "high_findings": ["integer policy"],
            "runs": [{
                "order": "normal", "artifact_set_hash": "c", "source_hash": "d",
                "membership_hash": "e", "grid_hash": "f", "lifecycle_hash": "g", "panel_hash": "h",
            }],
            "comparison": {"comparisons": {
                name: {
                    "production_content_hash": "p",
                    "independent_content_hash": "i",
                    "exact_content_match": True,
                    "row_count_match": True,
                    "field_type_match": True,
                    "mismatch_count": 0,
                    "first_mismatch": None,
                }
                for name in (
                    "row_conflict_resolution_manifest", "lifecycle_policy_manifest",
                    "lifecycle_resolution_registry", "symbol_availability_manifest",
                    "membership_manifest", "expected_grid_manifest",
                    "raw_row_quarantine_manifest", "lifecycle_event_quarantine_manifest",
                    "complete_day_mask", "active_universe_manifest", "qualified_panel_manifest",
                )
            }},
            "integer_time": {
                "full_data_integer_recomputation_executed": True,
                "current_data_artifact_difference": False,
                "policy_conformance": "fail",
                "boundary_differential": {},
                "static_findings": ["one"],
            },
            "qualification_report": {"exact_match": False, "committed_sha256": "x", "run_recorded_sha256": "y"},
            "v3_v4_diff_report": {"exact_match": True},
        }
        report = render_report(summary)
        self.assertEqual(report, render_report(summary))
        self.assertIn("## Minimal Counterexamples", report)
        self.assertIn("## Reconciliation Summary", report)


if __name__ == "__main__":
    unittest.main()
