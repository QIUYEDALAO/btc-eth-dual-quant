"""Deterministic, outcome-free adjudication helpers for official archive conflicts."""
from __future__ import annotations

import ast
import csv
from decimal import Decimal
import hashlib
import io
import json
from typing import Any, Iterable
import zipfile

from btc_eth_dual_quant.data.liquid_universe import canonical_hash

KLINE_COLUMNS = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "base_volume",
    "close_time",
    "quote_asset_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
)
DECIMAL_FIELDS = {
    "open",
    "high",
    "low",
    "close",
    "base_volume",
    "quote_asset_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
}
VOLUME_FIELDS = (
    "base_volume",
    "quote_asset_volume",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)
ALLOWED_CLASSIFICATIONS = {
    "corrected_official_archive",
    "parser_or_schema_bug",
    "official_monthly_daily_conflict",
    "exact_identical_duplicate",
    "conflicting_duplicate",
    "confirmed_official_archive_defect",
    "insufficient_evidence",
}
ALLOWED_DECISIONS = {
    "resolved_same_contract_rerun_authorized",
    "new_policy_adr_required",
    "remain_blocked_insufficient_evidence",
}
ZERO_AUTHORIZATIONS = {
    "hypothesis_preregistration": False,
    "strategy_code": False,
    "event_scan": False,
    "returns": False,
    "backtesting": False,
    "oos_opened": False,
    "m2": False,
    "api_or_trading": False,
}
UINT64_DECIMAL_8_SCALE = Decimal(2**64) / Decimal(10**8)


def timestamp_unit(value: str) -> str:
    raw = int(value)
    return "microseconds" if raw >= 10**15 else "milliseconds"


def timestamp_ms(value: str) -> int:
    raw = int(value)
    return raw // 1_000 if timestamp_unit(value) == "microseconds" else raw


def parse_kline_row(fields: list[str]) -> dict[str, Any]:
    if len(fields) != len(KLINE_COLUMNS):
        raise ValueError("kline row must contain exactly 12 columns")
    if not fields[0].isdigit() or not fields[6].isdigit():
        raise ValueError("kline timestamps must be unsigned integers")
    values = dict(zip(KLINE_COLUMNS, fields, strict=True))
    for field in DECIMAL_FIELDS:
        value = Decimal(values[field])
        if not value.is_finite():
            raise ValueError(f"non-finite kline field: {field}")
    if not values["trade_count"].isdigit():
        raise ValueError("trade count must be a non-negative integer")
    negative = [field for field in VOLUME_FIELDS if Decimal(values[field]) < 0]
    return {
        **values,
        "open_time_ms": timestamp_ms(values["open_time"]),
        "close_time_ms": timestamp_ms(values["close_time"]),
        "timestamp_unit": timestamp_unit(values["open_time"]),
        "negative_fields": negative,
    }


def _semantic_authority(row: list[str]) -> tuple[Any, ...]:
    parsed = parse_kline_row(row)
    result: list[Any] = []
    for field in KLINE_COLUMNS:
        if field == "open_time":
            result.append(parsed["open_time_ms"])
        elif field == "close_time":
            result.append(parsed["close_time_ms"])
        elif field in DECIMAL_FIELDS:
            result.append(Decimal(parsed[field]))
        elif field == "trade_count":
            result.append(int(parsed[field]))
        else:
            result.append(parsed[field])
    return tuple(result)


def compare_kline_rows(left: list[str], right: list[str]) -> dict[str, Any]:
    left_parsed = parse_kline_row(left)
    right_parsed = parse_kline_row(right)
    differing = []
    for index, field in enumerate(KLINE_COLUMNS):
        if field == "open_time":
            equal = left_parsed["open_time_ms"] == right_parsed["open_time_ms"]
        elif field == "close_time":
            equal = left_parsed["close_time_ms"] == right_parsed["close_time_ms"]
        elif field in DECIMAL_FIELDS:
            equal = Decimal(left[index]) == Decimal(right[index])
        elif field == "trade_count":
            equal = int(left[index]) == int(right[index])
        else:
            equal = left[index] == right[index]
        if not equal:
            differing.append(field)
    return {
        "authoritative_fields_equal": not differing,
        "differing_fields": differing,
        "left_row_sha256": canonical_hash(left),
        "right_row_sha256": canonical_hash(right),
    }


def classify_duplicate_rows(rows: list[list[str]]) -> str:
    if len(rows) < 2:
        return "not_duplicate"
    if all(item == rows[0] for item in rows[1:]):
        return "byte_identical_duplicate"
    if all(_semantic_authority(item) == _semantic_authority(rows[0]) for item in rows[1:]):
        return "semantic_identical_duplicate"
    return "conflicting_duplicate"


def detect_parser_created_duplicate(rows: list[list[str]]) -> bool:
    raw_timestamps = [item[0] for item in rows]
    normalized = [timestamp_ms(item[0]) for item in rows]
    return len(raw_timestamps) == len(set(raw_timestamps)) and len(normalized) != len(set(normalized))


def detect_unsigned_volume_overflow_signature(monthly: list[str], comparison: list[str]) -> bool:
    left = parse_kline_row(monthly)
    right = parse_kline_row(comparison)
    if compare_kline_rows(monthly, comparison)["differing_fields"] != ["base_volume"]:
        return False
    return Decimal(right["base_volume"]) - Decimal(left["base_volume"]) == UINT64_DECIMAL_8_SCALE


def evidence_source_available(record: dict[str, Any]) -> bool:
    """Return whether a comparison source supplied exactly one usable row."""
    return record.get("availability") == "available" and len(record.get("rows", [])) == 1


def source_owner_evidence_can_override_current_contract(*, explicitly_approved: bool) -> bool:
    """External commentary is provenance only until a versioned policy is adopted."""
    del explicitly_approved
    return False


def inspect_archive_bytes(payload: bytes, *, canonical_key: str) -> dict[str, Any]:
    try:
        bundle = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile:
        raise
    with bundle:
        broken = bundle.testzip()
        if broken is not None:
            raise ValueError(f"ZIP CRC failure: {broken}")
        csv_names = [name for name in bundle.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("archive must contain exactly one CSV")
        name = csv_names[0]
        text = io.TextIOWrapper(bundle.open(name), encoding="utf-8")
        raw_rows = [item for item in csv.reader(text) if item]
    data_rows: list[list[str]] = []
    header_rows = 0
    for item in raw_rows:
        if item[0].isdigit():
            parse_kline_row(item)
            data_rows.append(item)
        else:
            header_rows += 1
    rows = []
    for index, item in enumerate(data_rows):
        rows.append(
            {
                "line_number": index + 1 + header_rows,
                "raw_fields": item,
                "previous_raw_fields": data_rows[index - 1] if index else None,
                "next_raw_fields": data_rows[index + 1] if index + 1 < len(data_rows) else None,
                "parsed": parse_kline_row(item),
                "row_sha256": canonical_hash(item),
            }
        )
    return {
        "canonical_key": canonical_key,
        "zip_sha256": hashlib.sha256(payload).hexdigest(),
        "zip_byte_size": len(payload),
        "crc_valid": True,
        "csv_filename": name,
        "csv_column_count": len(KLINE_COLUMNS),
        "header_rows": header_rows,
        "row_count": len(rows),
        "rows": rows,
    }


def classify_overall_decision(conflicts: Iterable[dict[str, Any]]) -> str:
    classifications = [item.get("classification") for item in conflicts]
    if not classifications or any(item not in ALLOWED_CLASSIFICATIONS for item in classifications):
        return "remain_blocked_insufficient_evidence"
    if "insufficient_evidence" in classifications:
        return "remain_blocked_insufficient_evidence"
    if all(item in {"corrected_official_archive", "parser_or_schema_bug"} for item in classifications):
        return "resolved_same_contract_rerun_authorized"
    return "new_policy_adr_required"


def build_adjudication_document(
    *,
    contract_hash: str,
    source_manifest_hash: str,
    qualification_summary_hash: str,
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    decision = classify_overall_decision(conflicts)
    document = {
        "schema_version": 1,
        "manifest_type": "liquid_universe_v2_source_conflict_adjudication",
        "contract_hash": contract_hash,
        "source_manifest_hash": source_manifest_hash,
        "qualification_summary_hash": qualification_summary_hash,
        "content": {
            "overall_decision": decision,
            "same_contract_rerun_authorized": decision == "resolved_same_contract_rerun_authorized",
            "conflicts": conflicts,
            "authorizations": dict(ZERO_AUTHORIZATIONS),
        },
    }
    return {**document, "content_hash": canonical_hash(document)}


def verify_adjudication_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "liquid_universe_v2_source_conflict_adjudication":
        failures.append("document identity mismatch")
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        failures.append("content hash mismatch")
    for binding in ("contract_hash", "source_manifest_hash", "qualification_summary_hash"):
        value = document.get(binding)
        if not isinstance(value, str) or len(value) != 64:
            failures.append(f"invalid binding: {binding}")
    content = document.get("content", {})
    conflicts = content.get("conflicts", [])
    decision = classify_overall_decision(conflicts)
    if content.get("overall_decision") != decision or decision not in ALLOWED_DECISIONS:
        failures.append("overall decision mismatch")
    if content.get("same_contract_rerun_authorized") != (decision == "resolved_same_contract_rerun_authorized"):
        failures.append("rerun authorization mismatch")
    if content.get("authorizations") != ZERO_AUTHORIZATIONS:
        failures.append("research authorization matrix changed")
    return failures


def scan_forbidden_repairs(tree: ast.AST, *, source_name: str) -> list[str]:
    failures: list[str] = []
    protected_literals = {"BTTUSDT", "AXSUSDT", "2026-02-10"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)):
            test = node.test
            literals = {
                child.value
                for child in ast.walk(test)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)
            }
            if literals & protected_literals:
                failures.append(f"{source_name}:{node.lineno}: symbol/date special-case")
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "abs" and node.args:
            if "volume" in ast.unparse(node.args[0]).lower():
                failures.append(f"{source_name}:{node.lineno}: absolute-value volume repair")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "drop_duplicates":
            failures.append(f"{source_name}:{node.lineno}: drop_duplicates is prohibited")
        for keyword in node.keywords:
            if keyword.arg == "keep" and isinstance(keyword.value, ast.Constant) and keyword.value.value in {"first", "last"}:
                failures.append(f"{source_name}:{node.lineno}: keep-first/last is prohibited")
    return sorted(set(failures))


def canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
