import ast
import copy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import yaml

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from scripts.liquid_universe_v3_klay_conflict_probe import (
    AFFECTED_OPEN_TIME_MS,
    AFFECTED_ROW,
    AUTHORIZATIONS,
    BASELINE_HASHES,
    build_adjudication_document,
    classify_conflict,
    compare_rest_evidence,
    decision_path_float_timestamp_calls,
    infer_timestamp_unit,
    inspect_archive,
    normalize_timestamp_ms,
    render_report,
    scan_archive_rows,
    scan_forbidden_production_repairs,
    timestamp_analysis,
    utc_datetime_to_epoch_ms,
    verify_document,
)
from scripts.liquid_universe_v3_klay_conflict_check import validate_document


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json"
REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_KLAY_SOURCE_CONFLICT_ADJUDICATION_REPORT.md"


def row(
    open_time: str = "1730246400000000",
    close_time: str = "1730084399999000",
) -> list[str]:
    return [
        open_time,
        "0.12550000",
        "0.12550000",
        "0.12550000",
        "0.12550000",
        "0.00000000",
        close_time,
        "0.00000000",
        "0",
        "0.00000000",
        "0.00000000",
        "0",
    ]


def archive(rows: list[list[str]], name: str = "fixture.csv") -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(name, "\n".join(",".join(item) for item in rows) + "\n")
    return output.getvalue()


def rest(host: str, rows: list[list[str]] | None) -> dict:
    if rows is None:
        return {
            "endpoint_identity": host,
            "availability": "unavailable",
            "http_status": 404,
            "row_count": 0,
            "normalized_rows": [],
        }
    return {
        "endpoint_identity": host,
        "availability": "available",
        "http_status": 200,
        "payload_sha256": canonical_hash(rows),
        "row_count": len(rows),
        "normalized_rows": rows,
    }


def frozen_evidence() -> dict:
    return copy.deepcopy(json.loads(EVIDENCE.read_text()))


def rehash(document: dict) -> dict:
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    document["content_hash"] = canonical_hash(unsigned)
    return document


class KlaySourceConflictTests(unittest.TestCase):
    def test_01_affected_monthly_row_is_exact(self):
        document = json.loads(EVIDENCE.read_text())
        item = document["evidence"]["monthly_archive"]
        self.assertEqual(item["affected_line_number"], 30)
        self.assertEqual(item["affected_raw_fields"], AFFECTED_ROW)

    def test_02_affected_daily_row_is_exact(self):
        document = json.loads(EVIDENCE.read_text())
        item = document["evidence"]["daily_archive"]
        self.assertEqual(item["affected_line_number"], 1)
        self.assertEqual(item["affected_raw_fields"], AFFECTED_ROW)

    def test_03_monthly_and_daily_rows_are_identical(self):
        document = json.loads(EVIDENCE.read_text())
        comparison = document["evidence"]["monthly_daily_comparison"]
        self.assertTrue(comparison["raw_identical"])
        self.assertTrue(comparison["normalized_identical"])
        self.assertTrue(comparison["row_hash_identical"])

    def test_04_timestamp_units_are_inferred_independently(self):
        analysis = timestamp_analysis(AFFECTED_ROW)
        self.assertEqual(analysis["open_time_unit"], "microseconds")
        self.assertEqual(analysis["close_time_unit"], "microseconds")
        self.assertEqual(analysis["open_time_digit_count"], 16)
        self.assertEqual(analysis["close_time_digit_count"], 16)

    def test_05_close_time_is_before_open_time(self):
        analysis = timestamp_analysis(AFFECTED_ROW)
        self.assertTrue(analysis["close_time_before_open_time"])
        self.assertLess(analysis["actual_duration_ms"], 0)

    def test_06_milliseconds_fixture(self):
        self.assertEqual(infer_timestamp_unit("1730246400000"), "milliseconds")
        self.assertEqual(normalize_timestamp_ms("1730246400000"), AFFECTED_OPEN_TIME_MS)

    def test_07_microseconds_fixture(self):
        self.assertEqual(infer_timestamp_unit("1730246400000000"), "microseconds")
        self.assertEqual(normalize_timestamp_ms("1730246400000000"), AFFECTED_OPEN_TIME_MS)

    def test_08_mixed_units_are_normalized_independently(self):
        mixed = row("1730246400000", "1730332799999000")
        analysis = timestamp_analysis(mixed)
        self.assertEqual(analysis["open_time_unit"], "milliseconds")
        self.assertEqual(analysis["close_time_unit"], "microseconds")
        self.assertEqual(analysis["actual_duration_ms"], 86_399_999)

    def test_09_integer_normalization_avoids_float_precision(self):
        raw = "99999999999999999"
        self.assertEqual(normalize_timestamp_ms(raw), 99_999_999_999_999)
        self.assertNotEqual(int(int(raw) / 1000), normalize_timestamp_ms(raw))

    def test_10_parser_created_conflict_is_distinct(self):
        document = frozen_evidence()
        document["evidence"]["parser_analysis"]["parser_created_conflict"] = True
        document["evidence"]["parser_analysis"]["raw_data_conflict"] = False
        self.assertEqual(classify_conflict(document["evidence"]), "parser_or_timestamp_unit_bug")

    def test_11_raw_archive_conflict_is_reproducible(self):
        inspected = inspect_archive(archive([AFFECTED_ROW]), canonical_key="fixture.zip")
        self.assertEqual(inspected["row_count"], 1)
        self.assertTrue(inspected["affected"]["timestamp_analysis"]["close_time_before_open_time"])

    def test_12_current_checksum_change_is_detected(self):
        inspected = inspect_archive(archive([AFFECTED_ROW]), canonical_key="fixture.zip")
        inspected["blocked_build_sha256"] = "0" * 64
        self.assertTrue(inspected["zip_sha256"] != inspected["blocked_build_sha256"])

    def test_13_monthly_checksum_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            inspect_archive(
                archive([AFFECTED_ROW]),
                canonical_key="fixture.zip",
                expected_sha256="0" * 64,
            )

    def test_14_daily_checksum_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            inspect_archive(
                archive([AFFECTED_ROW]),
                canonical_key="daily.zip",
                expected_sha256="f" * 64,
            )

    def test_15_rest_comparators_agree(self):
        evidence = [rest("api.binance.com", [AFFECTED_ROW]), rest("data-api.binance.vision", [AFFECTED_ROW])]
        result = compare_rest_evidence(evidence, AFFECTED_ROW)
        self.assertTrue(result["comparators_identical"])
        self.assertTrue(result["all_match_archive"])

    def test_16_rest_comparators_disagree(self):
        changed = row(close_time="1730332799999000")
        result = compare_rest_evidence(
            [rest("api.binance.com", [AFFECTED_ROW]), rest("data-api.binance.vision", [changed])],
            AFFECTED_ROW,
        )
        self.assertFalse(result["comparators_identical"])

    def test_17_one_rest_source_unavailable(self):
        result = compare_rest_evidence(
            [rest("api.binance.com", [AFFECTED_ROW]), rest("data-api.binance.vision", None)],
            AFFECTED_ROW,
        )
        self.assertEqual(result["available_count"], 1)
        self.assertFalse(result["complete"])

    def test_18_both_rest_sources_unavailable(self):
        result = compare_rest_evidence(
            [rest("api.binance.com", None), rest("data-api.binance.vision", None)],
            AFFECTED_ROW,
        )
        self.assertEqual(result["available_count"], 0)
        self.assertFalse(result["complete"])

    def test_19_intraday_evidence_is_diagnostic_only(self):
        document = json.loads(EVIDENCE.read_text())
        self.assertEqual(document["evidence"]["intraday_diagnostics"]["authority"], "diagnostic_only")
        self.assertFalse(document["evidence"]["intraday_diagnostics"]["canonical_replacement_allowed"])

    def test_20_lifecycle_announcement_is_diagnostic_only(self):
        document = json.loads(EVIDENCE.read_text())
        lifecycle = document["evidence"]["symbol_lifecycle"]
        self.assertEqual(lifecycle["authority"], "provenance_only")
        self.assertFalse(lifecycle["automatic_data_mutation_allowed"])

    def test_21_unknown_conflict_remains_blocked(self):
        evidence = frozen_evidence()["evidence"]
        evidence["symbol_lifecycle"]["effective_time_utc"] = "2024-10-29T03:00:00+00:00"
        classification = classify_conflict(evidence)
        self.assertEqual(classification, "insufficient_evidence")

    def test_22_registry_hash_is_unchanged(self):
        self.assertEqual(BASELINE_HASHES["resolution_registry"], "570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4")

    def test_23_contract_hash_is_unchanged(self):
        self.assertEqual(BASELINE_HASHES["v3_contract"], "f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed")

    def test_24_cold_artifact_hash_is_unchanged(self):
        self.assertEqual(BASELINE_HASHES["blocked_cold_artifact_set"], "f661d7abd99adc4067d354afba0c5421e7d1f33c54f768b89c8011ec01eab4f3")

    def test_25_run_manifest_hash_is_unchanged(self):
        self.assertEqual(BASELINE_HASHES["requalification_run_manifest"], "057d4d94e277054b8cbd157dbb5ba05f04f1d0c3c2d28160d5b99689b1624e9c")

    def test_26_production_source_has_no_special_case(self):
        failures = scan_forbidden_production_repairs(ROOT / "src")
        self.assertFalse(any("special-case" in item for item in failures), failures)

    def test_27_silent_deduplication_is_forbidden(self):
        tree = ast.parse("frame.drop_duplicates(keep='first')")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.py"
            path.write_text(ast.unparse(tree))
            failures = scan_forbidden_production_repairs(Path(tmp))
        self.assertTrue(any("silent deduplication" in item for item in failures))

    def test_28_close_time_rewrite_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.py"
            path.write_text("def bad(row):\n    row['close_time'] = row['open_time'] + 86400000 - 1\n")
            failures = scan_forbidden_production_repairs(Path(tmp))
        self.assertTrue(any("close_time rewrite" in item for item in failures))

    def test_29_v3_rerun_is_not_authorized(self):
        document = json.loads(EVIDENCE.read_text())
        self.assertFalse(document["evidence"]["v3_rerun_executed"])
        self.assertFalse(document["authorization_matrix"]["v3_rerun"])

    def test_30_all_downstream_authorizations_are_false(self):
        self.assertFalse(any(AUTHORIZATIONS.values()))
        document = json.loads(EVIDENCE.read_text())
        self.assertEqual(document["authorization_matrix"], AUTHORIZATIONS)

    def test_31_report_is_exactly_regenerated_from_json(self):
        document = json.loads(EVIDENCE.read_text())
        self.assertEqual(REPORT.read_text(), render_report(document))

    def test_32_canonical_hash_is_order_independent(self):
        document = json.loads(EVIDENCE.read_text())
        unsigned = {key: value for key, value in document.items() if key != "content_hash"}
        reordered = dict(reversed(list(unsigned.items())))
        self.assertEqual(canonical_hash(unsigned), canonical_hash(reordered))
        self.assertEqual(document["content_hash"], canonical_hash(unsigned))

    def test_repository_evidence_has_unique_classification_and_decision(self):
        document = json.loads(EVIDENCE.read_text())
        self.assertEqual(document["classification"], "symbol_lifecycle_boundary_artifact")
        self.assertEqual(document["overall_decision"], "new_policy_adr_required")
        self.assertEqual(verify_document(document), [])

    def test_similar_scope_scan_counts_raw_invalid_rows(self):
        rows = [row("1730160000000000", "1730246399999999"), AFFECTED_ROW]
        result = scan_archive_rows(rows, interval="1d")
        self.assertEqual(result["close_time_before_open_time_count"], 1)
        self.assertEqual(result["invalid_duration_count"], 1)

    def test_lifecycle_match_is_required_for_lifecycle_classification(self):
        evidence = frozen_evidence()["evidence"]
        self.assertEqual(classify_conflict(evidence), "symbol_lifecycle_boundary_artifact")
        evidence["symbol_lifecycle"]["effective_time_utc"] = "2024-10-29T03:00:00+00:00"
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_normalized_utc_values_are_exact(self):
        analysis = timestamp_analysis(AFFECTED_ROW)
        self.assertEqual(analysis["normalized_open_time_utc"], "2024-10-30T00:00:00+00:00")
        self.assertEqual(analysis["normalized_close_time_utc"], "2024-10-28T02:59:59.999000+00:00")
        expected = datetime(2024, 10, 28, 3, tzinfo=timezone.utc)
        self.assertEqual(analysis["normalized_close_time_ms"], utc_datetime_to_epoch_ms(expected) - 1)

    def test_utc_datetime_to_epoch_ms_is_integer_only_and_rejects_naive(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            utc_datetime_to_epoch_ms(datetime(2024, 1, 1))
        offset = timezone(timedelta(hours=8))
        self.assertEqual(
            utc_datetime_to_epoch_ms(datetime(2024, 10, 28, 11, 0, 0, 999999, tzinfo=offset)),
            1_730_084_400_999,
        )
        self.assertEqual(
            utc_datetime_to_epoch_ms(datetime(2500, 1, 1, 0, 0, 0, 999999, tzinfo=timezone.utc)),
            16_725_225_600_999,
        )

    def test_decision_path_contains_no_float_timestamp_calls(self):
        paths = [
            ROOT / "scripts/liquid_universe_v3_klay_conflict_probe.py",
            ROOT / "scripts/liquid_universe_v3_klay_conflict_check.py",
            ROOT / "tests/test_liquid_universe_v3_klay_conflict.py",
        ]
        self.assertEqual(decision_path_float_timestamp_calls(paths), [])
        with tempfile.TemporaryDirectory() as tmp:
            injected = Path(tmp) / "bad.py"
            injected.write_text("def bad(value):\n    return value." + "timestamp()\n")
            self.assertTrue(decision_path_float_timestamp_calls([injected]))

    def test_rest_source_unavailable_cannot_lifecycle_pass(self):
        evidence = frozen_evidence()["evidence"]
        evidence["public_rest_comparators"][1]["availability"] = "unavailable"
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_rest_sources_disagree_cannot_lifecycle_pass(self):
        evidence = frozen_evidence()["evidence"]
        evidence["public_rest_comparators"][1]["normalized_rows"][0][4] = "0.12600000"
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_rest_archive_mismatch_cannot_lifecycle_pass(self):
        evidence = frozen_evidence()["evidence"]
        for item in evidence["public_rest_comparators"]:
            item["normalized_rows"][0][4] = "0.12600000"
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_legal_rest_row_cannot_lifecycle_pass_invalid_archives(self):
        evidence = frozen_evidence()["evidence"]
        legal = row("1730246400000", "1730332799999")
        for item in evidence["public_rest_comparators"]:
            item["normalized_rows"] = [legal]
        self.assertNotEqual(classify_conflict(evidence), "symbol_lifecycle_boundary_artifact")

    def test_intraday_bars_or_boundary_mismatch_cannot_lifecycle_pass(self):
        evidence = frozen_evidence()["evidence"]
        evidence["intraday_diagnostics"]["affected_day_has_trading_bars"] = True
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")
        evidence = frozen_evidence()["evidence"]
        evidence["intraday_diagnostics"]["latest_intraday_close_time_ms"] += 1
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_monthly_or_daily_row_change_cannot_lifecycle_pass(self):
        evidence = frozen_evidence()["evidence"]
        evidence["daily_archive"]["affected_raw_fields"][4] = "0.12600000"
        self.assertEqual(classify_conflict(evidence), "insufficient_evidence")

    def test_checker_rejects_lifecycle_hash_classification_and_decision_tampering(self):
        for mutation in ("lifecycle_hash", "classification", "decision"):
            document = frozen_evidence()
            if mutation == "lifecycle_hash":
                document["evidence"]["symbol_lifecycle"]["normalized_evidence_sha256"] = "0" * 64
            elif mutation == "classification":
                document["classification"] = "insufficient_evidence"
            else:
                document["overall_decision"] = "remain_blocked_insufficient_evidence"
            self.assertTrue(validate_document(rehash(document)), mutation)

    def test_checker_rejects_rest_payload_normalized_row_and_hash_tampering(self):
        for field in ("raw_payload_utf8", "normalized_rows", "normalized_row_hashes"):
            document = frozen_evidence()
            item = document["evidence"]["public_rest_comparators"][0]
            if field == "raw_payload_utf8":
                item[field] += " "
            elif field == "normalized_rows":
                item[field][0][4] = "0.12600000"
            else:
                item[field][0] = "0" * 64
            self.assertTrue(validate_document(rehash(document)), field)

    def test_repository_governance_closes_adjudication_and_limits_adoption(self):
        state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text())
        self.assertEqual(
            state["current_phase"],
            "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        )
        self.assertEqual(
            state["current_status"],
            "u04_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
        )
        self.assertFalse(any(item["id"] == "U-03E-V3-ADJ" for item in state["open_work"]))
        milestone = next(
            item
            for item in state["completed_milestones"]
            if item["phase"] == "Liquid universe V3 KLAY official-source conflict adjudication"
        )
        self.assertEqual(milestone["merged_pr"], 79)
        adoption = next(
            item
            for item in state["completed_milestones"]
            if item["phase"] == "ADR-0014 conditional adoption"
        )
        self.assertEqual(adoption["merged_pr"], 85)
        self.assertEqual(
            adoption["merge_commit"],
            "0f5f76f86973316ac66b8e3f9d6e65419b310ec9",
        )
        self.assertFalse(any(item["id"] == "U-03E-V4-RUN" for item in state["open_work"]))
        self.assertFalse(any(item["id"] == "U-03F" for item in state["open_work"]))
        self.assertFalse(
            any(item["id"] == "U-03F-REPAIR-REQUALIFICATION" for item in state["open_work"])
        )
        policy_adoption = next(
            item for item in state["completed_milestones"]
            if item["phase"] == "ADR-0015 conditional adoption"
        )
        self.assertEqual(
            policy_adoption["status"],
            "accepted_for_generic_policy_implementation_and_exact_head_implementation_review_only_merged",
        )
        self.assertEqual(policy_adoption["merged_pr"], 108)
        self.assertEqual(
            policy_adoption["result_head_sha"],
            "01d98b60ce8a9a0b33082777c946cec70d380fc7",
        )
        self.assertEqual(
            policy_adoption["merge_commit"],
            "141481fa445bdc03b453844a666dbd2639c3cdf7",
        )
        implementation = state["adr0015_invalid_interval_policy_implementation"]
        self.assertEqual(
            implementation["status"],
            "implementation_integrated_requalification_pass",
        )
        self.assertEqual(
            implementation["policy_hash"],
            "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
        )
        self.assertEqual(
            implementation["algorithm_hash"],
            "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
        )
        self.assertFalse(implementation["exact_head_implementation_review_required"])
        self.assertTrue(implementation["exact_head_implementation_review_complete"])
        self.assertEqual(implementation["review_pr"], 110)
        self.assertTrue(implementation["fixed_range_public_requalification_authorized"])
        self.assertTrue(implementation["fixed_range_public_requalification_complete"])
        self.assertFalse(implementation["new_independent_audit_authorized"])
        self.assertFalse(implementation["u04_authorized"])
        self.assertFalse(implementation["m2_authorized"])
        self.assertTrue(implementation["public_data_run_executed"])
        protocol = next(
            item for item in state["open_work"]
            if item["id"] == "U-04-DATA-QUALIFICATION"
        )
        self.assertEqual(protocol["status"], "authorized_ready")
        self.assertEqual(protocol["candidate_id"], "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL")
        self.assertTrue(protocol["data_qualification_authorized"])
        self.assertFalse(protocol["event_scan_authorized"])
        audit_protocol = state["adr0015_invalid_interval_independent_audit_protocol"]
        self.assertEqual(
            audit_protocol["protocol_content_hash"],
            "9a1768f01e7891f8c76f74293fb3836339e75fafa039fe12ebf3a7ddfdbb970b",
        )
        self.assertEqual(audit_protocol["production_manifests_exact_required"], 19)
        self.assertFalse(audit_protocol["real_independent_audit_authorized"])
        requalification = next(
            item for item in state["completed_milestones"]
            if item["phase"] == "ADR-0015 fixed-range invalid-interval requalification"
        )
        self.assertEqual(requalification["status"], "pass_local_complete")
        self.assertEqual(requalification["invalid_physical_rows_quarantined"], 119)
        self.assertEqual(requalification["valid_minority_rows_quarantined"], 1)
        repair = next(
            item
            for item in state["completed_milestones"]
            if item["phase"] == "U-03F V4 repair public requalification"
        )
        self.assertEqual(repair["status"], "blocked_invalid_5m_interval_boundaries_merged_closed")
        self.assertEqual(repair["merged_pr"], 100)
        self.assertEqual(
            repair["merge_commit"],
            "927f121651d6e1e07f174410a39595f6d09e9a5d",
        )
        audit = next(
            item
            for item in state["completed_milestones"]
            if item["phase"] == "U-03F V4 independent audit"
        )
        self.assertEqual(audit["status"], "failed_audit")
        self.assertEqual(audit["merged_pr"], 95)
        self.assertEqual(
            audit["evidence"],
            "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md",
        )
        self.assertFalse(any(item["id"] == "ADR-0014-ADOPT" for item in state["open_work"]))
        self.assertFalse(any(item["id"] == "ADR-0014-REVIEW" for item in state["open_work"]))
        self.assertEqual(
            state["research_authorizations"],
            {
                "hypothesis_preregistration": False,
                "strategy_code": False,
                "event_scan": False,
                "returns": False,
                "backtesting": False,
                "oos_opened": False,
                "m2": False,
                "api_or_trading": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
