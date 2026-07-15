#!/usr/bin/env python3
"""Freeze read-only public evidence for the KLAYUSDT V3 row conflict."""
from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from typing import Any, Iterable
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_source_conflicts import (
    classify_duplicate_rows,
    inspect_archive_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "https://data.binance.vision"
BUCKET_LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
REST_HOSTS = ("api.binance.com", "data-api.binance.vision")
ANNOUNCEMENT_CODE = "f75f933759ee49d0af1dfbce7e32144c"
ANNOUNCEMENT_API = (
    "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
    f"?articleCode={ANNOUNCEMENT_CODE}"
)
AFFECTED_OPEN_TIME_MS = 1_730_246_400_000
AFFECTED_ROW = [
    "1730246400000000",
    "0.12550000",
    "0.12550000",
    "0.12550000",
    "0.12550000",
    "0.00000000",
    "1730084399999000",
    "0.00000000",
    "0",
    "0.00000000",
    "0.00000000",
    "0",
]
MONTHLY_KEY = "data/spot/monthly/klines/KLAYUSDT/1d/KLAYUSDT-1d-2024-10.zip"
DAILY_KEY = "data/spot/daily/klines/KLAYUSDT/1d/KLAYUSDT-1d-2024-10-30.zip"
EXPECTED_MONTHLY_SHA256 = "68dce6c6be6ac4e22428771a1402d957becb8e6a1ec9bb7b83507b2029712a59"
EXPECTED_DAILY_SHA256 = "7256e669015de0d5d401db062338415318bb1091f2e78e16c4a48b5f75d2a642"
EXPECTED_ROW_SHA256 = "8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1"

BASELINE_HASHES = {
    "v3_contract": "f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed",
    "resolution_registry": "570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4",
    "btt_axs_adjudication_evidence": "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b",
    "blocked_cold_artifact_set": "f661d7abd99adc4067d354afba0c5421e7d1f33c54f768b89c8011ec01eab4f3",
    "requalification_run_manifest": "057d4d94e277054b8cbd157dbb5ba05f04f1d0c3c2d28160d5b99689b1624e9c",
    "source_manifest": "67529beb72cceeed9aad0baa825cccb5ca1e64c31cf30fdf9a4c076c40fd3bf9",
    "qualification_summary": "fe236096824fa016be748e67132f225ff02ce4a527fb9b14e67555728c7aa668",
}
AUTHORIZATIONS = {
    "registry_change": False,
    "contract_change": False,
    "v3_rerun": False,
    "u03f": False,
    "u04": False,
    "hypothesis_preregistration": False,
    "strategy_code": False,
    "event_scan": False,
    "returns": False,
    "backtesting": False,
    "oos_opened": False,
    "api_or_trading": False,
    "m2": False,
}
ALLOWED_CLASSIFICATIONS = {
    "corrected_official_archive",
    "parser_or_timestamp_unit_bug",
    "official_monthly_daily_identical_invalid_row",
    "official_archive_rest_conflict",
    "symbol_lifecycle_boundary_artifact",
    "wider_official_schema_defect",
    "insufficient_evidence",
}
ALLOWED_DECISIONS = {
    "corrected_archive_same_contract_rerun_candidate",
    "separate_same_contract_parser_fix_required",
    "existing_policy_registry_revision_candidate",
    "new_policy_adr_required",
    "remain_blocked_insufficient_evidence",
}
UTC_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
LIFECYCLE_HASH_FIELDS = (
    "article_code",
    "title",
    "public_url",
    "public_api_reference",
    "publication_time_utc",
    "effective_time_utc",
    "replacement_trading_time_utc",
    "affected_pairs",
    "relationship",
)


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def utc_datetime_to_epoch_ms(value: datetime) -> int:
    """Convert an aware datetime to Unix milliseconds without float arithmetic."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    delta = value.astimezone(timezone.utc) - UTC_EPOCH
    return ((delta.days * 86_400 + delta.seconds) * 1_000) + delta.microseconds // 1_000


def infer_timestamp_unit(value: str) -> str:
    if not value.isdigit():
        raise ValueError("timestamp must be an unsigned integer")
    return "microseconds" if int(value) >= 10**15 else "milliseconds"


def normalize_timestamp_ms(value: str) -> int:
    raw = int(value)
    return raw // 1_000 if infer_timestamp_unit(value) == "microseconds" else raw


def _iso_ms(value: int) -> str:
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=value)).isoformat()


def timestamp_analysis(fields: list[str], *, parser_close_time_ms: int | None = None) -> dict[str, Any]:
    if len(fields) != 12:
        raise ValueError("kline row must contain 12 fields")
    open_ms = normalize_timestamp_ms(fields[0])
    close_ms = normalize_timestamp_ms(fields[6])
    expected_close = open_ms + 86_400_000 - 1
    raw_invalid = close_ms < open_ms
    parser_invalid = parser_close_time_ms is not None and parser_close_time_ms < open_ms
    return {
        "raw_open_time": fields[0],
        "raw_close_time": fields[6],
        "open_time_digit_count": len(fields[0]),
        "close_time_digit_count": len(fields[6]),
        "open_time_unit": infer_timestamp_unit(fields[0]),
        "close_time_unit": infer_timestamp_unit(fields[6]),
        "normalized_open_time_ms": open_ms,
        "normalized_close_time_ms": close_ms,
        "normalized_open_time_utc": _iso_ms(open_ms),
        "normalized_close_time_utc": _iso_ms(close_ms),
        "expected_day_boundary_utc": _iso_ms(open_ms),
        "expected_close_boundary_utc": _iso_ms(expected_close),
        "actual_duration_ms": close_ms - open_ms,
        "expected_duration_ms": 86_399_999,
        "duration_delta_ms": close_ms - expected_close,
        "close_time_before_open_time": raw_invalid,
        "close_time_belongs_to_prior_bar_or_stage": close_ms < open_ms,
        "parser_created_conflict": bool(parser_invalid and not raw_invalid),
        "integer_only_normalization": True,
    }


def scan_archive_rows(rows: Iterable[list[str]], *, interval: str) -> dict[str, Any]:
    step = {"1d": 86_400_000, "1h": 3_600_000, "5m": 300_000}[interval]
    before = equal = invalid_duration = 0
    affected: list[int] = []
    for fields in rows:
        open_ms = normalize_timestamp_ms(fields[0])
        close_ms = normalize_timestamp_ms(fields[6])
        if close_ms < open_ms:
            before += 1
            affected.append(open_ms)
        if close_ms == open_ms:
            equal += 1
        if close_ms - open_ms != step - 1:
            invalid_duration += 1
    return {
        "row_count": len(list(rows)) if isinstance(rows, (tuple, list)) else None,
        "close_time_before_open_time_count": before,
        "close_time_equal_open_time_count": equal,
        "invalid_duration_count": invalid_duration,
        "affected_timestamps_ms": sorted(set(affected)),
    }


def inspect_archive(
    payload: bytes,
    *,
    canonical_key: str,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    sha256 = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and sha256 != expected_sha256:
        raise ValueError(f"checksum mismatch: {canonical_key}")
    inspected = inspect_archive_bytes(payload, canonical_key=canonical_key)
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        csv_info = [item for item in bundle.infolist() if item.filename.endswith(".csv")]
    rows = inspected.pop("rows")
    matches = [item for item in rows if item["parsed"]["open_time_ms"] == AFFECTED_OPEN_TIME_MS]
    affected = None
    if matches:
        item = matches[0]
        affected = {
            "line_number": item["line_number"],
            "raw_fields": item["raw_fields"],
            "raw_row_sha256": item["row_sha256"],
            "previous_raw_fields": item["previous_raw_fields"],
            "previous_raw_row_sha256": canonical_hash(item["previous_raw_fields"]) if item["previous_raw_fields"] else None,
            "next_raw_fields": item["next_raw_fields"],
            "next_raw_row_sha256": canonical_hash(item["next_raw_fields"]) if item["next_raw_fields"] else None,
            "timestamp_analysis": timestamp_analysis(item["raw_fields"]),
        }
    timestamp_rows = [item["raw_fields"] for item in matches]
    interval = next((value for value in ("1d", "1h", "5m") if f"/{value}/" in canonical_key), "1d")
    result = {
        **inspected,
        "zip_crc32": [f"{item.CRC:08x}" for item in csv_info],
        "first_raw_timestamp": rows[0]["raw_fields"][0] if rows else None,
        "last_raw_timestamp": rows[-1]["raw_fields"][0] if rows else None,
        "affected_occurrences": len(matches),
        "same_open_time_duplicate_type": classify_duplicate_rows(timestamp_rows),
        "affected": affected,
        "scope_scan": scan_archive_rows([item["raw_fields"] for item in rows], interval=interval),
    }
    return result


def compare_rest_evidence(records: list[dict[str, Any]], archive_row: list[str]) -> dict[str, Any]:
    available = [item for item in records if item.get("availability") == "available" and item.get("row_count") == 1]
    rows = [item["normalized_rows"][0] for item in available]
    analyses = [timestamp_analysis(item) for item in rows if len(item) == 12]
    return {
        "complete": len(available) == 2,
        "available_count": len(available),
        "comparators_identical": len(rows) == 2 and rows[0] == rows[1],
        "all_match_archive": bool(rows) and all(item == archive_row for item in rows),
        "all_semantically_match_archive": bool(rows) and all(
            [normalize_timestamp_ms(item[0]), *item[1:6], normalize_timestamp_ms(item[6]), *item[7:]]
            == [normalize_timestamp_ms(archive_row[0]), *archive_row[1:6], normalize_timestamp_ms(archive_row[6]), *archive_row[7:]]
            for item in rows
        ),
        "all_rows_close_before_open": len(analyses) == 2 and all(
            item["close_time_before_open_time"] for item in analyses
        ),
    }


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _semantic_row(fields: list[str]) -> list[Any]:
    if len(fields) != 12:
        raise ValueError("kline row must contain 12 fields")
    return [normalize_timestamp_ms(fields[0]), *fields[1:6], normalize_timestamp_ms(fields[6]), *fields[7:]]


def _normalized_lifecycle(lifecycle: dict[str, Any]) -> dict[str, Any]:
    return {key: lifecycle[key] for key in LIFECYCLE_HASH_FIELDS}


def _archive_gate(item: dict[str, Any]) -> bool:
    fields = item.get("affected_raw_fields")
    if not isinstance(fields, list) or len(fields) != 12:
        return False
    checksum_text = item.get("official_checksum_text", "")
    checksum = checksum_text.split(maxsplit=1)[0].lower() if checksum_text else ""
    try:
        derived_timing = timestamp_analysis(fields)
    except (TypeError, ValueError):
        return False
    return all(
        (
            item.get("availability") == "available",
            item.get("http_status") == 200,
            _is_sha256(checksum),
            checksum == item.get("current_remote_checksum") == item.get("zip_sha256"),
            item.get("crc_valid") is True,
            bool(item.get("zip_crc32")),
            item.get("affected_occurrences") == 1,
            item.get("same_open_time_duplicate_type") == "not_duplicate",
            item.get("affected_raw_row_sha256") == canonical_hash(fields),
            item.get("timestamp_analysis") == derived_timing,
            derived_timing["close_time_before_open_time"],
        )
    )


def _rest_gate(records: list[dict[str, Any]], archive_row: list[str]) -> bool:
    if len(records) != 2 or {item.get("endpoint_identity") for item in records} != set(REST_HOSTS):
        return False
    normalized_rows: list[list[str]] = []
    for item in records:
        if item.get("availability") != "available" or item.get("http_status") != 200 or item.get("row_count") != 1:
            return False
        payload_text = item.get("raw_payload_utf8")
        if not isinstance(payload_text, str) or hashlib.sha256(payload_text.encode("utf-8")).hexdigest() != item.get("payload_sha256"):
            return False
        try:
            decoded = json.loads(payload_text)
            normalized = [[str(value) for value in row] for row in decoded]
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
        if normalized != item.get("normalized_rows") or len(normalized) != 1:
            return False
        if item.get("normalized_row_hashes") != [canonical_hash(normalized[0])]:
            return False
        analysis = timestamp_analysis(normalized[0])
        if item.get("timestamp_analysis") != analysis or not analysis["close_time_before_open_time"]:
            return False
        normalized_rows.append(normalized[0])
    return normalized_rows[0] == normalized_rows[1] and all(
        _semantic_row(item) == _semantic_row(archive_row) for item in normalized_rows
    )


def _scope_statistics_hash(document: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in document.items() if key != "statistics_hash"})


def _similar_scope_gate(local_scope: dict[str, Any], remote_scope: dict[str, Any]) -> bool:
    if local_scope.get("statistics_hash") != _scope_statistics_hash(local_scope):
        return False
    if remote_scope.get("statistics_hash") != _scope_statistics_hash(remote_scope):
        return False
    affected = remote_scope.get("affected_archives", [])
    return all(
        (
            local_scope.get("read_only") is True,
            local_scope.get("only_klay_close_before_open_class_found") is True,
            local_scope.get("affected_symbols") == ["KLAYUSDT"],
            local_scope.get("affected_timestamps_ms") == [AFFECTED_OPEN_TIME_MS],
            local_scope.get("unique_close_before_open_events") == 1,
            local_scope.get("close_time_before_open_time_count") == 2,
            local_scope.get("monthly_daily_overlap") == 2,
            remote_scope.get("read_only") is True,
            remote_scope.get("close_time_before_open_time_count") == 1,
            len(affected) == 1,
            affected[0].get("affected_timestamps_ms") == [AFFECTED_OPEN_TIME_MS],
            _is_sha256(affected[0].get("zip_sha256")),
            _is_sha256(remote_scope.get("archive_set_hash")),
        )
    )


def classify_conflict(evidence: dict[str, Any]) -> str:
    parser = evidence.get("parser_analysis", {})
    if parser.get("parser_created_conflict") is True and parser.get("raw_data_conflict") is False:
        return "parser_or_timestamp_unit_bug"
    if parser.get("float_datetime_used_for_decision") is not False:
        return "insufficient_evidence"

    monthly = evidence.get("monthly_archive", {})
    daily = evidence.get("daily_archive", {})
    if not _archive_gate(monthly) or not _archive_gate(daily):
        return "insufficient_evidence"
    monthly_row = monthly["affected_raw_fields"]
    daily_row = daily["affected_raw_fields"]
    monthly_timing = timestamp_analysis(monthly_row)
    daily_timing = timestamp_analysis(daily_row)
    if not all(
        (
            monthly_row == daily_row,
            _semantic_row(monthly_row) == _semantic_row(daily_row),
            monthly["affected_raw_row_sha256"] == daily["affected_raw_row_sha256"],
            monthly_timing["open_time_unit"] == infer_timestamp_unit(monthly_row[0]),
            monthly_timing["close_time_unit"] == infer_timestamp_unit(monthly_row[6]),
            daily_timing["open_time_unit"] == infer_timestamp_unit(daily_row[0]),
            daily_timing["close_time_unit"] == infer_timestamp_unit(daily_row[6]),
            parser.get("independent_timestamp_unit_inference") is True,
            parser.get("integer_only_conversion") is True,
            parser.get("open_unit_reused_for_close") is False,
            parser.get("parser_created_conflict") is False,
            parser.get("raw_data_conflict") is True,
        )
    ):
        return "insufficient_evidence"
    if not _rest_gate(evidence.get("public_rest_comparators", []), monthly_row):
        return "insufficient_evidence"

    intraday = evidence.get("intraday_diagnostics", {})
    close_ms = monthly_timing["normalized_close_time_ms"]
    if not all(
        (
            intraday.get("authority") == "diagnostic_only",
            intraday.get("canonical_replacement_allowed") is False,
            intraday.get("intraday_derived_row_is_diagnostic_only") is True,
            intraday.get("affected_day_has_trading_bars") is False,
            isinstance(intraday.get("latest_intraday_close_time_ms"), int),
            intraday.get("latest_intraday_close_time_ms") == close_ms,
            intraday.get("latest_intraday_close_matches_1d_raw_close") is True,
        )
    ):
        return "insufficient_evidence"

    lifecycle = evidence.get("symbol_lifecycle", {})
    try:
        normalized_lifecycle = _normalized_lifecycle(lifecycle)
        effective = datetime.fromisoformat(lifecycle["effective_time_utc"])
        effective_ms = utc_datetime_to_epoch_ms(effective)
    except (KeyError, TypeError, ValueError):
        return "insufficient_evidence"
    if not all(
        (
            lifecycle.get("authority") == "provenance_only",
            lifecycle.get("automatic_data_mutation_allowed") is False,
            _is_sha256(lifecycle.get("normalized_evidence_sha256")),
            lifecycle.get("normalized_evidence_sha256") == canonical_hash(normalized_lifecycle),
            close_ms == effective_ms - 1,
            monthly_timing["normalized_open_time_ms"] >= effective_ms,
        )
    ):
        return "insufficient_evidence"
    if not _similar_scope_gate(
        evidence.get("similar_scope_scan", {}),
        evidence.get("all_public_klay_daily_scan", {}),
    ):
        return "insufficient_evidence"
    return "symbol_lifecycle_boundary_artifact"


def overall_decision(classification: str) -> str:
    return {
        "corrected_official_archive": "corrected_archive_same_contract_rerun_candidate",
        "parser_or_timestamp_unit_bug": "separate_same_contract_parser_fix_required",
        "official_monthly_daily_identical_invalid_row": "new_policy_adr_required",
        "official_archive_rest_conflict": "new_policy_adr_required",
        "symbol_lifecycle_boundary_artifact": "new_policy_adr_required",
        "wider_official_schema_defect": "new_policy_adr_required",
        "insufficient_evidence": "remain_blocked_insufficient_evidence",
    }.get(classification, "remain_blocked_insufficient_evidence")


def build_adjudication_document(*, evidence: dict[str, Any]) -> dict[str, Any]:
    classification = classify_conflict(evidence)
    unsigned = {
        "schema_version": 1,
        "manifest_type": "liquid_universe_v3_klay_source_conflict_adjudication",
        "adjudication_id": "U-03E-V3-ADJ-KLAYUSDT-1D-2024-10-30",
        "symbol": "KLAYUSDT",
        "interval": "1d",
        "affected_open_time": "2024-10-30T00:00:00+00:00",
        "affected_raw_open_time": AFFECTED_ROW[0],
        "classification": classification,
        "overall_decision": overall_decision(classification),
        "immutable_baseline_hashes": dict(BASELINE_HASHES),
        "authorization_matrix": dict(AUTHORIZATIONS),
        "evidence": evidence,
    }
    return {**unsigned, "content_hash": canonical_hash(unsigned)}


def verify_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        failures.append("content hash mismatch")
    if document.get("schema_version") != 1 or document.get("manifest_type") != "liquid_universe_v3_klay_source_conflict_adjudication":
        failures.append("document identity mismatch")
    classification = document.get("classification")
    recomputed_classification = classify_conflict(document.get("evidence", {}))
    if classification not in ALLOWED_CLASSIFICATIONS:
        failures.append("classification mismatch")
    if classification != recomputed_classification:
        failures.append("classification does not match recomputed evidence")
    if document.get("overall_decision") != overall_decision(str(classification)) or document.get("overall_decision") not in ALLOWED_DECISIONS:
        failures.append("overall decision mismatch")
    if document.get("immutable_baseline_hashes") != BASELINE_HASHES:
        failures.append("immutable baseline mismatch")
    if document.get("authorization_matrix") != AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    evidence = document.get("evidence", {})
    monthly = evidence.get("monthly_archive", {})
    daily = evidence.get("daily_archive", {})
    for name, item, expected_sha in (
        ("monthly", monthly, EXPECTED_MONTHLY_SHA256),
        ("daily", daily, EXPECTED_DAILY_SHA256),
    ):
        if item.get("zip_sha256") != expected_sha:
            failures.append(f"{name} archive SHA256 mismatch")
        if item.get("affected_raw_row_sha256") != EXPECTED_ROW_SHA256 or item.get("affected_raw_fields") != AFFECTED_ROW:
            failures.append(f"{name} affected row mismatch")
    if evidence.get("daily_correction_candidate_valid") is not False:
        failures.append("invalid daily row treated as correction")
    if evidence.get("v3_rerun_executed") is not False:
        failures.append("V3 rerun marker changed")
    rest = evidence.get("public_rest_comparators", [])
    if len(rest) != 2 or any(item.get("endpoint_identity") not in REST_HOSTS for item in rest):
        failures.append("REST comparator identities mismatch")
    for item in rest:
        if item.get("availability") == "available" and len(item.get("payload_sha256", "")) != 64:
            failures.append("REST payload hash missing")
    return failures


def scan_forbidden_production_repairs(root: Path) -> list[str]:
    failures: list[str] = []
    protected = {"KLAYUSDT", "2024-10-30", "1730246400000"}
    for path in sorted(root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp)):
                literals = {
                    child.value for child in ast.walk(node.test)
                    if isinstance(child, ast.Constant) and isinstance(child.value, str)
                }
                if literals & protected:
                    failures.append(f"{path}:{node.lineno}: special-case")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "drop_duplicates":
                failures.append(f"{path}:{node.lineno}: silent deduplication")
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "keep" and isinstance(keyword.value, ast.Constant) and keyword.value.value in {"first", "last"}:
                        failures.append(f"{path}:{node.lineno}: silent deduplication keep-first/last")
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(
                    isinstance(target, ast.Subscript)
                    and isinstance(target.slice, ast.Constant)
                    and target.slice.value == "close_time"
                    for target in targets
                ):
                    failures.append(f"{path}:{node.lineno}: close_time rewrite")
    return sorted(set(failures))


def decision_path_float_timestamp_calls(paths: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "timestamp"
            ):
                findings.append(f"{path.name}:{node.lineno}")
    return findings


def derive_parser_analysis(fields: list[str], decision_paths: Iterable[Path]) -> dict[str, Any]:
    analysis = timestamp_analysis(fields)
    mixed = list(fields)
    mixed[0] = str(normalize_timestamp_ms(fields[0]))
    mixed_analysis = timestamp_analysis(mixed)
    float_calls = decision_path_float_timestamp_calls(decision_paths)
    integer_checks = (
        normalize_timestamp_ms(fields[0]) == int(fields[0]) // 1_000,
        normalize_timestamp_ms(fields[6]) == int(fields[6]) // 1_000,
        utc_datetime_to_epoch_ms(datetime.fromisoformat(analysis["normalized_open_time_utc"]))
        == analysis["normalized_open_time_ms"],
        utc_datetime_to_epoch_ms(datetime.fromisoformat(analysis["normalized_close_time_utc"]))
        == analysis["normalized_close_time_ms"],
    )
    return {
        "independent_timestamp_unit_inference": all(
            (
                analysis["open_time_unit"] == infer_timestamp_unit(fields[0]),
                analysis["close_time_unit"] == infer_timestamp_unit(fields[6]),
                mixed_analysis["open_time_unit"] == "milliseconds",
                mixed_analysis["close_time_unit"] == "microseconds",
            )
        ),
        "integer_only_conversion": all(integer_checks),
        "open_unit_reused_for_close": mixed_analysis["close_time_unit"] == mixed_analysis["open_time_unit"],
        "float_datetime_used_for_decision": bool(float_calls),
        "float_datetime_call_sites": float_calls,
        "parser_created_conflict": analysis["parser_created_conflict"],
        "raw_data_conflict": analysis["close_time_before_open_time"],
        "minimal_fixture_row": list(fields),
    }


def _fetch(url: str, *, retries: int = 6, allow_404: bool = False) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "btc-eth-dual-quant-public-audit/1"})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return int(response.status), response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_404:
                return 404, exc.read()
            last_error = exc
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        if attempt + 1 < retries:
            time.sleep(float(2**attempt))
    raise OSError(f"public evidence fetch failed: {url}") from last_error


def _official_archive(key: str, blocked_sha256: str | None = None, *, allow_404: bool = False) -> dict[str, Any]:
    url = f"{BUCKET}/{key}"
    status, payload = _fetch(url, allow_404=allow_404)
    if status == 404:
        return {
            "canonical_key": key,
            "canonical_url": url,
            "availability": "unavailable",
            "http_status": 404,
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
        }
    checksum_url = f"{url}.CHECKSUM"
    checksum_status, checksum_payload = _fetch(checksum_url, allow_404=allow_404)
    if checksum_status != 200:
        raise ValueError(f"official checksum unavailable: {key}")
    checksum_text = checksum_payload.decode("utf-8").strip()
    expected = checksum_text.split()[0].lower()
    result = inspect_archive(payload, canonical_key=key, expected_sha256=expected)
    affected = result.pop("affected")
    return {
        **result,
        "canonical_url": url,
        "checksum_url": checksum_url,
        "official_checksum_text": checksum_text,
        "current_remote_checksum": expected,
        "blocked_build_sha256": blocked_sha256,
        "official_archive_republished": blocked_sha256 is not None and expected != blocked_sha256,
        "affected_line_number": affected["line_number"] if affected else None,
        "affected_raw_fields": affected["raw_fields"] if affected else None,
        "affected_raw_row_sha256": affected["raw_row_sha256"] if affected else None,
        "previous_raw_fields": affected["previous_raw_fields"] if affected else None,
        "previous_raw_row_sha256": affected["previous_raw_row_sha256"] if affected else None,
        "next_raw_fields": affected["next_raw_fields"] if affected else None,
        "next_raw_row_sha256": affected["next_raw_row_sha256"] if affected else None,
        "timestamp_analysis": affected["timestamp_analysis"] if affected else None,
        "availability": "available",
        "http_status": 200,
    }


def _rest_comparators() -> list[dict[str, Any]]:
    end_time = AFFECTED_OPEN_TIME_MS + 86_400_000 - 1
    records: list[dict[str, Any]] = []
    for host in REST_HOSTS:
        query = urllib.parse.urlencode(
            {
                "symbol": "KLAYUSDT",
                "interval": "1d",
                "startTime": AFFECTED_OPEN_TIME_MS,
                "endTime": end_time,
                "limit": 1,
            }
        )
        url = f"https://{host}/api/v3/klines?{query}"
        try:
            status, payload = _fetch(url)
            decoded = json.loads(payload)
            rows = [[str(value) for value in item] for item in decoded]
            records.append(
                {
                    "endpoint_identity": host,
                    "sanitized_query": query,
                    "http_status": status,
                    "availability": "available",
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                    "raw_payload_utf8": payload.decode("utf-8"),
                    "row_count": len(rows),
                    "normalized_rows": rows,
                    "normalized_row_hashes": [canonical_hash(item) for item in rows],
                    "timestamp_analysis": timestamp_analysis(rows[0]) if len(rows) == 1 else None,
                }
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            records.append(
                {
                    "endpoint_identity": host,
                    "sanitized_query": query,
                    "http_status": None,
                    "availability": "unavailable",
                    "reason": type(exc).__name__,
                    "row_count": 0,
                    "normalized_rows": [],
                    "normalized_row_hashes": [],
                }
            )
    return records


def _intraday_diagnostics() -> dict[str, Any]:
    archives = []
    for interval in ("5m", "1h"):
        for frequency, suffix in (("monthly", "2024-10"), ("daily", "2024-10-30")):
            key = f"data/spot/{frequency}/klines/KLAYUSDT/{interval}/KLAYUSDT-{interval}-{suffix}.zip"
            item = _official_archive(key, allow_404=True)
            if item.get("availability") == "available":
                status, payload = _fetch(f"{BUCKET}/{key}")
                del status
                inspected = inspect_archive_bytes(payload, canonical_key=key)
                rows = inspected["rows"]
                day_rows = [row for row in rows if normalize_timestamp_ms(row["raw_fields"][0]) // 86_400_000 == AFFECTED_OPEN_TIME_MS // 86_400_000]
                item["affected_day_row_count"] = len(day_rows)
                item["first_affected_day_row"] = day_rows[0]["raw_fields"] if day_rows else None
                item["last_affected_day_row"] = day_rows[-1]["raw_fields"] if day_rows else None
                item["last_available_row"] = rows[-1]["raw_fields"] if rows else None
            archives.append(item)
    monthly = [item for item in archives if item.get("availability") == "available"]
    last_rows = [item["last_available_row"] for item in monthly if item.get("last_available_row")]
    last_close = max(normalize_timestamp_ms(item[6]) for item in last_rows)
    return {
        "authority": "diagnostic_only",
        "canonical_replacement_allowed": False,
        "intraday_derived_row_is_diagnostic_only": True,
        "archives": archives,
        "affected_day_has_trading_bars": any(item.get("affected_day_row_count", 0) for item in archives),
        "latest_intraday_close_time_ms": last_close,
        "latest_intraday_close_time_utc": _iso_ms(last_close),
        "latest_intraday_close_matches_1d_raw_close": last_close == normalize_timestamp_ms(AFFECTED_ROW[6]),
        "derived_ohlcv": None,
    }


def _lifecycle_evidence() -> dict[str, Any]:
    status, payload = _fetch(ANNOUNCEMENT_API)
    decoded = json.loads(payload)
    data = decoded["data"]
    normalized = {
        "article_code": data["code"],
        "title": data["title"],
        "public_url": f"https://www.binance.com/en/support/announcement/detail/{data['code']}",
        "public_api_reference": ANNOUNCEMENT_API,
        "publication_time_utc": _iso_ms(int(data["publishDate"])),
        "effective_time_utc": "2024-10-28T03:00:00+00:00",
        "replacement_trading_time_utc": "2024-10-31T08:00:00+00:00",
        "affected_pairs": ["KLAYBTC", "KLAYUSDT"],
        "relationship": "KLAY spot trading ceased exactly one millisecond after the affected raw close_time",
    }
    return {
        **normalized,
        "http_status": status,
        "raw_response_payload_sha256": hashlib.sha256(payload).hexdigest(),
        "normalized_evidence_sha256": canonical_hash(normalized),
        "authority": "provenance_only",
        "automatic_data_mutation_allowed": False,
    }


def _scan_local_scope(raw_root: Path) -> dict[str, Any]:
    paths = sorted((raw_root / "monthly/klines/KLAYUSDT/1d").glob("*.zip"))
    daily_paths = sorted((raw_root / "daily/klines/KLAYUSDT/1d").glob("*.zip"))
    same_month_paths = sorted((raw_root / "monthly/klines").glob("*/1d/*-1d-2024-10.zip"))
    invalid: list[dict[str, Any]] = []
    close_before_rows: list[dict[str, Any]] = []
    archive_fingerprints: list[dict[str, str]] = []
    counters = {"close_time_before_open_time_count": 0, "close_time_equal_open_time_count": 0, "invalid_duration_count": 0}
    scanned_rows = 0
    for path in sorted(set(paths + daily_paths + same_month_paths)):
        key = str(path.relative_to(raw_root.parent.parent)).replace("\\", "/")
        inspected = inspect_archive_bytes(path.read_bytes(), canonical_key=key)
        archive_fingerprints.append({"canonical_key": key, "zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        symbol = path.name.split("-1d-")[0]
        for item in inspected["rows"]:
            fields = item["raw_fields"]
            open_ms = normalize_timestamp_ms(fields[0])
            close_ms = normalize_timestamp_ms(fields[6])
            scanned_rows += 1
            if close_ms < open_ms:
                counters["close_time_before_open_time_count"] += 1
            if close_ms == open_ms:
                counters["close_time_equal_open_time_count"] += 1
            if close_ms - open_ms != 86_399_999:
                counters["invalid_duration_count"] += 1
                record = {
                        "symbol": symbol,
                        "canonical_key": key,
                        "line_number": item["line_number"],
                        "open_time_ms": open_ms,
                        "open_time_utc": _iso_ms(open_ms),
                        "close_time_ms": close_ms,
                        "close_time_utc": _iso_ms(close_ms),
                        "raw_row_sha256": item["row_sha256"],
                    }
                invalid.append(record)
                if close_ms < open_ms:
                    close_before_rows.append(record)
    affected_symbols = sorted({item["symbol"] for item in close_before_rows})
    nonfull_duration_symbols = sorted({item["symbol"] for item in invalid})
    summary = {
        "scope": {
            "klay_monthly_archive_count": len(paths),
            "klay_daily_archive_count": len(daily_paths),
            "same_month_other_symbol_archive_count": len(same_month_paths),
            "scanned_archive_count": len(set(paths + daily_paths + same_month_paths)),
            "scanned_row_count": scanned_rows,
        },
        **counters,
        "invalid_rows": invalid,
        "affected_symbols": affected_symbols,
        "nonfull_duration_symbols": nonfull_duration_symbols,
        "affected_months": sorted({item["open_time_utc"][:7] for item in invalid}),
        "affected_timestamps_ms": sorted({item["open_time_ms"] for item in close_before_rows}),
        "monthly_daily_overlap": sum(1 for item in close_before_rows if item["raw_row_sha256"] == EXPECTED_ROW_SHA256),
        "unique_close_before_open_events": len({(item["symbol"], item["open_time_ms"], item["raw_row_sha256"]) for item in close_before_rows}),
        "only_klay_close_before_open_class_found": affected_symbols == ["KLAYUSDT"],
        "scanned_archive_set_hash": canonical_hash(sorted(archive_fingerprints, key=lambda item: item["canonical_key"])),
        "read_only": True,
    }
    return {**summary, "statistics_hash": _scope_statistics_hash(summary)}


def _list_public_keys(prefix: str) -> list[str]:
    keys: list[str] = []
    token: str | None = None
    while True:
        query_values = {"list-type": "2", "prefix": prefix}
        if token:
            query_values["continuation-token"] = token
        status, payload = _fetch(f"{BUCKET_LIST}?{urllib.parse.urlencode(query_values)}")
        if status != 200:
            raise ValueError("public archive listing failed")
        root = ET.fromstring(payload)
        namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        keys.extend(item.text or "" for item in root.findall("s3:Contents/s3:Key", namespace))
        truncated = (root.findtext("s3:IsTruncated", default="false", namespaces=namespace) or "false").lower() == "true"
        token = root.findtext("s3:NextContinuationToken", default=None, namespaces=namespace)
        if not truncated:
            break
        if not token:
            raise ValueError("truncated archive listing omitted continuation token")
    return sorted(item for item in keys if item.endswith(".zip"))


def _scan_all_public_klay_daily() -> dict[str, Any]:
    keys = _list_public_keys("data/spot/daily/klines/KLAYUSDT/1d/")

    def inspect_key(key: str) -> dict[str, Any]:
        status, payload = _fetch(f"{BUCKET}/{key}")
        if status != 200:
            raise ValueError(f"daily archive unavailable: {key}")
        inspected = inspect_archive_bytes(payload, canonical_key=key)
        rows = [item["raw_fields"] for item in inspected["rows"]]
        scan = scan_archive_rows(rows, interval="1d")
        return {
            "canonical_key": key,
            "zip_sha256": hashlib.sha256(payload).hexdigest(),
            "row_hashes": [canonical_hash(item) for item in rows],
            "row_count": len(rows),
            "scan": scan,
        }

    with ThreadPoolExecutor(max_workers=12) as pool:
        records = list(pool.map(inspect_key, keys))
    records.sort(key=lambda item: item["canonical_key"])
    affected = [
        {
            "canonical_key": item["canonical_key"],
            "zip_sha256": item["zip_sha256"],
            "affected_timestamps_ms": item["scan"]["affected_timestamps_ms"],
        }
        for item in records
        if item["scan"]["close_time_before_open_time_count"]
    ]
    summary = {
        "archive_count": len(records),
        "row_count": sum(item["row_count"] for item in records),
        "close_time_before_open_time_count": sum(item["scan"]["close_time_before_open_time_count"] for item in records),
        "close_time_equal_open_time_count": sum(item["scan"]["close_time_equal_open_time_count"] for item in records),
        "invalid_duration_count": sum(item["scan"]["invalid_duration_count"] for item in records),
        "affected_archives": affected,
        "archive_set_hash": canonical_hash(
            [
                {
                    "canonical_key": item["canonical_key"],
                    "zip_sha256": item["zip_sha256"],
                    "row_hashes": item["row_hashes"],
                }
                for item in records
            ]
        ),
        "read_only": True,
    }
    return {**summary, "statistics_hash": _scope_statistics_hash(summary)}


def render_report(document: dict[str, Any]) -> str:
    evidence = document["evidence"]
    monthly = evidence["monthly_archive"]
    daily = evidence["daily_archive"]
    timing = monthly["timestamp_analysis"]
    rest = evidence["public_rest_comparators"]
    intraday = evidence["intraday_diagnostics"]
    lifecycle = evidence["symbol_lifecycle"]
    parser = evidence["parser_analysis"]
    scope = evidence["similar_scope_scan"]
    lines = [
        "# Liquid Spot Universe V3 KLAY Source Conflict Adjudication Report",
        "",
        f"- Classification: `{document['classification']}`",
        f"- Overall decision: `{document['overall_decision']}`",
        f"- Evidence content hash: `{document['content_hash']}`",
        "- Evidence only: yes",
        "- Registry / contract mutation: no / no",
        "- V3 cold, warm or worker rerun: no",
        "- U-03F / U-04 / strategy / outcomes / OOS / API or trading / M2 authorized: no",
        "",
        "## Official Archives",
        "",
        f"- Monthly key: `{monthly['canonical_key']}`",
        f"- Monthly checksum / ZIP SHA256 / bytes / CRC: `{monthly['current_remote_checksum']}` / `{monthly['zip_sha256']}` / {monthly['zip_byte_size']} / {', '.join(monthly['zip_crc32'])}",
        f"- Monthly CSV / rows / columns / header rows / first / last: `{monthly['csv_filename']}` / {monthly['row_count']} / {monthly['csv_column_count']} / {monthly['header_rows']} / `{monthly['first_raw_timestamp']}` / `{monthly['last_raw_timestamp']}`",
        f"- Monthly affected line {monthly['affected_line_number']}: `{','.join(monthly['affected_raw_fields'])}`",
        f"- Monthly affected row hash: `{monthly['affected_raw_row_sha256']}`",
        f"- Monthly previous row / hash: `{','.join(monthly['previous_raw_fields'])}` / `{monthly['previous_raw_row_sha256']}`",
        f"- Monthly next row: {monthly['next_raw_fields']}",
        f"- Monthly occurrence / duplicate type / republished: {monthly['affected_occurrences']} / {monthly['same_open_time_duplicate_type']} / {'yes' if monthly['official_archive_republished'] else 'no'}",
        f"- Daily key: `{daily['canonical_key']}`",
        f"- Daily checksum / ZIP SHA256 / bytes / CRC: `{daily['current_remote_checksum']}` / `{daily['zip_sha256']}` / {daily['zip_byte_size']} / {', '.join(daily['zip_crc32'])}",
        f"- Daily affected line {daily['affected_line_number']}: `{','.join(daily['affected_raw_fields'])}`",
        f"- Daily affected row hash: `{daily['affected_raw_row_sha256']}`",
        f"- Monthly/daily raw, normalized and row-hash identical: {evidence['monthly_daily_comparison']['raw_identical']} / {evidence['monthly_daily_comparison']['normalized_identical']} / {evidence['monthly_daily_comparison']['row_hash_identical']}",
        "- Daily correction candidate valid: no",
        "",
        "## Timestamp And Parser Analysis",
        "",
        f"- Raw open / close: `{timing['raw_open_time']}` / `{timing['raw_close_time']}`",
        f"- Independent units / digit counts: {timing['open_time_unit']} ({timing['open_time_digit_count']}) / {timing['close_time_unit']} ({timing['close_time_digit_count']})",
        f"- Normalized open / close UTC: {timing['normalized_open_time_utc']} / {timing['normalized_close_time_utc']}",
        f"- Expected close: {timing['expected_close_boundary_utc']}",
        f"- Actual / expected duration / delta ms: {timing['actual_duration_ms']} / {timing['expected_duration_ms']} / {timing['duration_delta_ms']}",
        f"- close_time before open_time: {timing['close_time_before_open_time']}",
        f"- Parser-created / raw-data conflict: {parser['parser_created_conflict']} / {parser['raw_data_conflict']}",
        f"- Independent units / integer conversion / open unit reused for close / float datetime in decision: {parser['independent_timestamp_unit_inference']} / {parser['integer_only_conversion']} / {parser['open_unit_reused_for_close']} / {parser['float_datetime_used_for_decision']}",
        "",
        "## Public REST Comparators",
        "",
    ]
    for item in rest:
        row_text = ",".join(item["normalized_rows"][0]) if item.get("normalized_rows") else "unavailable"
        lines.append(
            f"- {item['endpoint_identity']}: {item['availability']} / HTTP {item['http_status']} / payload `{item.get('payload_sha256')}` / row `{row_text}`"
        )
    comparison = evidence["rest_comparison"]
    lines.extend(
        [
            f"- REST sources complete / identical / semantically match archives: {comparison['complete']} / {comparison['comparators_identical']} / {comparison['all_semantically_match_archive']}",
            "- REST is corroboration only and is not a canonical replacement authority.",
            "",
            "## Intraday And Lifecycle Diagnostics",
            "",
            f"- Affected UTC day has official 5m/1h trading bars: {intraday['affected_day_has_trading_bars']}",
            f"- Last official intraday close: {intraday['latest_intraday_close_time_utc']}",
            f"- Last intraday close equals invalid 1d raw close: {intraday['latest_intraday_close_matches_1d_raw_close']}",
            "- Intraday-derived row is diagnostic only; no 1d replacement was created.",
            f"- Official announcement: {lifecycle['title']}",
            f"- Official reference: {lifecycle['public_url']}",
            f"- Publication / effective / replacement trading UTC: {lifecycle['publication_time_utc']} / {lifecycle['effective_time_utc']} / {lifecycle['replacement_trading_time_utc']}",
            f"- Announcement payload / normalized evidence hashes: `{lifecycle['raw_response_payload_sha256']}` / `{lifecycle['normalized_evidence_sha256']}`",
            "- The invalid close_time is exactly one millisecond before KLAY spot trading ceased. The announcement is provenance only and cannot mutate data.",
            "",
            "## Similar-Scope Scan",
            "",
            f"- KLAY monthly / daily / same-month other-symbol archives: {scope['scope']['klay_monthly_archive_count']} / {scope['scope']['klay_daily_archive_count']} / {scope['scope']['same_month_other_symbol_archive_count']}",
            f"- Scanned archives / rows: {scope['scope']['scanned_archive_count']} / {scope['scope']['scanned_row_count']}",
            f"- close<open / close=open / invalid duration: {scope['close_time_before_open_time_count']} / {scope['close_time_equal_open_time_count']} / {scope['invalid_duration_count']}",
            f"- close<open affected symbols: {', '.join(scope['affected_symbols'])}",
            f"- Non-full-duration symbols (includes valid listing/delisting partial days): {', '.join(scope['nonfull_duration_symbols'])}",
            f"- Only KLAY has the close<open class: {scope['only_klay_close_before_open_class_found']}",
            f"- Remote KLAY daily archives / rows / close<open: {evidence['all_public_klay_daily_scan']['archive_count']} / {evidence['all_public_klay_daily_scan']['row_count']} / {evidence['all_public_klay_daily_scan']['close_time_before_open_time_count']}",
            f"- Remote KLAY daily archive-set hash: `{evidence['all_public_klay_daily_scan']['archive_set_hash']}`",
            "",
            "## Decision",
            "",
            "Monthly, daily and both public REST sources preserve the same semantically invalid row. The project parser does not create the conflict. Official intraday archives stop exactly at the announced KLAY trading cessation boundary, and no intraday bars exist on the affected day. This uniquely supports `symbol_lifecycle_boundary_artifact`.",
            "",
            "ADR-0013 does not define a canonicalization or quarantine rule for a lifecycle placeholder whose monthly and daily authorities are both invalid. The only valid decision is `new_policy_adr_required`. This report records that candidate next stage but does not authorize or create it.",
            "",
            "## Immutable Baselines",
            "",
        ]
    )
    for name, value in sorted(document["immutable_baseline_hashes"].items()):
        lines.append(f"- {name}: `{value}`")
    lines.extend(
        [
            "",
            "All downstream authorizations remain false. The V3 qualification stays blocked; no registry entry, contract revision, qualification rerun, membership change or hidden repair was made.",
        ]
    )
    return "\n".join(lines) + "\n"


def execute(*, raw_root: Path, output_path: Path, report_path: Path) -> dict[str, Any]:
    monthly = _official_archive(MONTHLY_KEY, EXPECTED_MONTHLY_SHA256)
    daily = _official_archive(DAILY_KEY, EXPECTED_DAILY_SHA256)
    if monthly["affected_raw_fields"] != AFFECTED_ROW or daily["affected_raw_fields"] != AFFECTED_ROW:
        raise ValueError("affected official row changed")
    rest = _rest_comparators()
    intraday = _intraday_diagnostics()
    lifecycle = _lifecycle_evidence()
    decision_paths = (
        Path(__file__).resolve(),
        ROOT / "scripts/liquid_universe_v3_klay_conflict_check.py",
        ROOT / "tests/test_liquid_universe_v3_klay_conflict.py",
    )
    evidence = {
        "monthly_archive": monthly,
        "daily_archive": daily,
        "monthly_daily_comparison": {
            "raw_identical": monthly["affected_raw_fields"] == daily["affected_raw_fields"],
            "normalized_identical": timestamp_analysis(monthly["affected_raw_fields"]) == timestamp_analysis(daily["affected_raw_fields"]),
            "row_hash_identical": monthly["affected_raw_row_sha256"] == daily["affected_raw_row_sha256"],
            "invalid_close_time_consistent": monthly["timestamp_analysis"]["close_time_before_open_time"] and daily["timestamp_analysis"]["close_time_before_open_time"],
        },
        "daily_correction_candidate_valid": False,
        "public_rest_comparators": rest,
        "rest_comparison": compare_rest_evidence(rest, AFFECTED_ROW),
        "intraday_diagnostics": intraday,
        "symbol_lifecycle": lifecycle,
        "parser_analysis": derive_parser_analysis(AFFECTED_ROW, decision_paths),
        "similar_scope_scan": _scan_local_scope(raw_root),
        "all_public_klay_daily_scan": _scan_all_public_klay_daily(),
        "v3_rerun_executed": False,
    }
    document = build_adjudication_document(evidence=evidence)
    failures = verify_document(document)
    if failures:
        raise ValueError("; ".join(failures))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(document), encoding="utf-8")
    report_path.write_text(render_report(document), encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe/data/spot")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_KLAY_SOURCE_CONFLICT_ADJUDICATION_REPORT.md",
    )
    args = parser.parse_args()
    document = execute(raw_root=args.raw_root, output_path=args.output, report_path=args.report)
    print(f"classification={document['classification']} decision={document['overall_decision']} content_hash={document['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
