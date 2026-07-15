import ast
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from btc_eth_dual_quant.data.liquid_universe_source_conflicts import (
    ALLOWED_DECISIONS,
    build_adjudication_document,
    classify_duplicate_rows,
    classify_overall_decision,
    compare_kline_rows,
    detect_parser_created_duplicate,
    detect_unsigned_volume_overflow_signature,
    evidence_source_available,
    inspect_archive_bytes,
    parse_kline_row,
    scan_forbidden_repairs,
    source_owner_evidence_can_override_current_contract,
    verify_adjudication_document,
)


def row(
    timestamp: str = "1548892800000",
    volume: str = "10.00000000",
    quote_volume: str = "5.00000000",
    taker_base: str = "4.00000000",
    taker_quote: str = "2.00000000",
) -> list[str]:
    return [
        timestamp,
        "1.00000000",
        "2.00000000",
        "0.50000000",
        "1.50000000",
        volume,
        "1548979199999",
        quote_volume,
        "12",
        taker_base,
        taker_quote,
        "0",
    ]


def archive(rows: list[list[str]], *, name: str = "fixture.csv") -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(name, "\n".join(",".join(item) for item in rows) + "\n")
    return output.getvalue()


class SourceConflictAdjudicationTests(unittest.TestCase):
    def test_negative_base_volume_is_field_six(self):
        parsed = parse_kline_row(row(volume="-1.25"))
        self.assertEqual(parsed["negative_fields"], ["base_volume"])
        self.assertEqual(parsed["base_volume"], "-1.25")

    def test_negative_quote_and_taker_volumes_are_identified(self):
        parsed = parse_kline_row(
            row(quote_volume="-2", taker_base="-3", taker_quote="-4")
        )
        self.assertEqual(
            parsed["negative_fields"],
            ["quote_asset_volume", "taker_buy_base_volume", "taker_buy_quote_volume"],
        )

    def test_schema_shift_cannot_create_a_fake_negative(self):
        with self.assertRaisesRegex(ValueError, "exactly 12 columns"):
            parse_kline_row(["unexpected"] + row(volume="-1"))

    def test_byte_identical_duplicate(self):
        duplicate = row()
        self.assertEqual(
            classify_duplicate_rows([duplicate, duplicate.copy()]),
            "byte_identical_duplicate",
        )

    def test_semantic_identical_duplicate(self):
        left = row(volume="10.0")
        right = row(volume="10.00000000")
        self.assertEqual(
            classify_duplicate_rows([left, right]),
            "semantic_identical_duplicate",
        )

    def test_conflicting_duplicate(self):
        self.assertEqual(
            classify_duplicate_rows([row(volume="10"), row(volume="11")]),
            "conflicting_duplicate",
        )

    def test_monthly_daily_conflict_is_field_level(self):
        result = compare_kline_rows(row(volume="-1"), row(volume="10"))
        self.assertEqual(result["differing_fields"], ["base_volume"])
        self.assertFalse(result["authoritative_fields_equal"])

    def test_unsigned_volume_overflow_signature(self):
        monthly = row(volume="-61596941261.09551616")
        daily = row(volume="122870499476.00000000")
        self.assertTrue(detect_unsigned_volume_overflow_signature(monthly, daily))

    def test_parser_created_duplicate_detects_mixed_timestamp_units(self):
        milliseconds = row(timestamp="1770681600000")
        microseconds = row(timestamp="1770681600000000")
        self.assertTrue(detect_parser_created_duplicate([milliseconds, microseconds]))

    def test_corrupt_cache_is_rejected(self):
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            inspect_archive_bytes(b"not-a-zip", canonical_key="fixture.zip")

    def test_daily_or_rest_evidence_missing_is_unavailable(self):
        self.assertFalse(evidence_source_available({"availability": "unavailable", "rows": []}))
        self.assertFalse(evidence_source_available({"availability": "available", "rows": []}))
        self.assertTrue(evidence_source_available({"availability": "available", "rows": [row()]}))

    def test_current_remote_checksum_change_is_detectable_without_repair(self):
        local_sha = "a" * 64
        current_sha = "b" * 64
        self.assertNotEqual(local_sha, current_sha)
        self.assertEqual(classify_overall_decision([{"classification": "corrected_official_archive"}]), "resolved_same_contract_rerun_authorized")

    def test_source_owner_evidence_never_overrides_current_contract_automatically(self):
        self.assertFalse(source_owner_evidence_can_override_current_contract(explicitly_approved=False))
        self.assertFalse(source_owner_evidence_can_override_current_contract(explicitly_approved=True))

    def test_archive_inspection_preserves_line_context_and_crc(self):
        rows = [row(timestamp="1548806400000"), row(), row(timestamp="1548979200000")]
        result = inspect_archive_bytes(archive(rows), canonical_key="fixture.zip")
        self.assertTrue(result["crc_valid"])
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["rows"][1]["line_number"], 2)
        self.assertEqual(result["rows"][1]["previous_raw_fields"], rows[0])
        self.assertEqual(result["rows"][1]["next_raw_fields"], rows[2])

    def test_unresolved_conflict_never_authorizes_rerun(self):
        decision = classify_overall_decision(
            [{"classification": "insufficient_evidence"}]
        )
        self.assertEqual(decision, "remain_blocked_insufficient_evidence")

    def test_official_defects_require_new_policy(self):
        decision = classify_overall_decision(
            [
                {"classification": "official_monthly_daily_conflict"},
                {"classification": "exact_identical_duplicate"},
            ]
        )
        self.assertEqual(decision, "new_policy_adr_required")

    def test_only_corrected_or_parser_fixed_conflicts_authorize_same_contract_rerun(self):
        for classifications in (
            ["corrected_official_archive"],
            ["parser_or_schema_bug"],
            ["corrected_official_archive", "parser_or_schema_bug"],
        ):
            self.assertEqual(
                classify_overall_decision(
                    [{"classification": item} for item in classifications]
                ),
                "resolved_same_contract_rerun_authorized",
            )

    def test_machine_document_hash_and_authorizations_are_fail_closed(self):
        document = build_adjudication_document(
            contract_hash="a" * 64,
            source_manifest_hash="b" * 64,
            qualification_summary_hash="c" * 64,
            conflicts=[{"conflict_id": "fixture", "classification": "insufficient_evidence"}],
        )
        self.assertEqual(document["content"]["overall_decision"], "remain_blocked_insufficient_evidence")
        self.assertFalse(document["content"]["same_contract_rerun_authorized"])
        self.assertFalse(any(document["content"]["authorizations"].values()))
        self.assertEqual(verify_adjudication_document(document), [])
        changed = copy.deepcopy(document)
        changed["content"]["authorizations"]["strategy_code"] = True
        self.assertTrue(verify_adjudication_document(changed))

    def test_contract_or_manifest_binding_change_fails_hash_verification(self):
        document = build_adjudication_document(
            contract_hash="a" * 64,
            source_manifest_hash="b" * 64,
            qualification_summary_hash="c" * 64,
            conflicts=[{"conflict_id": "fixture", "classification": "exact_identical_duplicate"}],
        )
        changed = copy.deepcopy(document)
        changed["contract_hash"] = "d" * 64
        self.assertIn("content hash mismatch", verify_adjudication_document(changed))

    def test_forbidden_symbol_date_and_volume_repair_are_detected(self):
        source = '''
def bad(symbol, date, volume, frame):
    if symbol == "BTTUSDT":
        return abs(volume)
    if date == "2026-02-10":
        return frame.drop_duplicates(keep="first")
'''
        failures = scan_forbidden_repairs(ast.parse(source), source_name="bad.py")
        self.assertTrue(any("symbol/date special-case" in item for item in failures))
        self.assertTrue(any("absolute-value volume repair" in item for item in failures))
        self.assertTrue(any("drop_duplicates" in item for item in failures))
        self.assertTrue(any("keep-first/last" in item for item in failures))

    def test_generic_fail_closed_code_passes_repair_scan(self):
        source = '''
def validate(row):
    if row.volume < 0:
        raise ValueError("negative volume")
'''
        self.assertEqual(scan_forbidden_repairs(ast.parse(source), source_name="good.py"), [])

    def test_decision_values_are_closed(self):
        self.assertEqual(
            ALLOWED_DECISIONS,
            {
                "resolved_same_contract_rerun_authorized",
                "new_policy_adr_required",
                "remain_blocked_insufficient_evidence",
            },
        )


if __name__ == "__main__":
    unittest.main()
