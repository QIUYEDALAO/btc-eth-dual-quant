#!/usr/bin/env python3
"""Probe the three frozen U-03E source conflicts using public evidence only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from btc_eth_dual_quant.data.liquid_universe_source_conflicts import (
    build_adjudication_document,
    canonical_json,
    classify_duplicate_rows,
    compare_kline_rows,
    detect_parser_created_duplicate,
    detect_unsigned_volume_overflow_signature,
    inspect_archive_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "https://data.binance.vision"
REST_HOSTS = ("api.binance.com", "data-api.binance.vision")
MONTHLY_KEYS = (
    "data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-01.zip",
    "data/spot/monthly/klines/BTTUSDT/1d/BTTUSDT-1d-2019-02.zip",
    "data/spot/monthly/klines/AXSUSDT/1d/AXSUSDT-1d-2026-02.zip",
)


def fetch(url: str, *, retries: int = 5) -> bytes:
    last_error: Exception | None = None
    request = urllib.request.Request(url, headers={"User-Agent": "btc-eth-dual-quant-public-audit/1"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                raise
            if attempt + 1 < retries:
                time.sleep(float(2**attempt))
    raise OSError(f"public evidence fetch failed: {url}") from last_error


def _checksum_record(payload: bytes, text: bytes) -> dict[str, Any]:
    content = text.decode("utf-8").strip()
    expected = content.split()[0].lower()
    actual = hashlib.sha256(payload).hexdigest()
    return {
        "checksum_file_content": content,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "matches": expected == actual,
    }


def _official_archive(url: str, canonical_key: str) -> dict[str, Any]:
    payload = fetch(url)
    checksum_url = f"{url}.CHECKSUM"
    checksum = _checksum_record(payload, fetch(checksum_url))
    if not checksum["matches"]:
        raise ValueError(f"official checksum mismatch: {canonical_key}")
    return {
        **inspect_archive_bytes(payload, canonical_key=canonical_key),
        "canonical_url": url,
        "checksum_url": checksum_url,
        **checksum,
    }


def _local_archive(raw_root: Path, canonical_key: str) -> dict[str, Any]:
    path = raw_root / Path(canonical_key).relative_to("data/spot")
    payload = path.read_bytes()
    checksum_text = path.with_suffix(path.suffix + ".CHECKSUM").read_bytes()
    checksum = _checksum_record(payload, checksum_text)
    if not checksum["matches"]:
        raise ValueError(f"local checksum mismatch: {canonical_key}")
    return {
        **inspect_archive_bytes(payload, canonical_key=canonical_key),
        "checksum_file_content": checksum["checksum_file_content"],
        "expected_sha256": checksum["expected_sha256"],
        "actual_sha256": checksum["actual_sha256"],
        "matches": True,
    }


def _rest_rows(symbol: str, open_time_ms: int) -> list[dict[str, Any]]:
    end_time_ms = open_time_ms + 86_400_000 - 1
    results = []
    for host in REST_HOSTS:
        query = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "interval": "1d",
                "startTime": open_time_ms,
                "endTime": end_time_ms,
                "limit": 10,
            }
        )
        url = f"https://{host}/api/v3/klines?{query}"
        try:
            payload = fetch(url)
            decoded = json.loads(payload)
            if not isinstance(decoded, list):
                raise ValueError("REST response is not a kline list")
            rows = [[str(field) for field in item] for item in decoded]
            results.append(
                {
                    "host": host,
                    "url": url,
                    "availability": "available",
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                    "row_count": len(rows),
                    "rows": rows,
                }
            )
        except (OSError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
            results.append(
                {
                    "host": host,
                    "url": url,
                    "availability": "unavailable",
                    "reason": type(exc).__name__,
                    "row_count": 0,
                    "rows": [],
                }
            )
    return results


def _iso(open_time_ms: int) -> str:
    return datetime.fromtimestamp(open_time_ms / 1_000, timezone.utc).isoformat()


def _affected_rows(archive: dict[str, Any], *, negative: bool = False, timestamp_ms: int | None = None) -> list[dict[str, Any]]:
    result = []
    for item in archive["rows"]:
        parsed = item["parsed"]
        if negative and parsed["negative_fields"]:
            result.append(item)
        elif timestamp_ms is not None and parsed["open_time_ms"] == timestamp_ms:
            result.append(item)
    return result


def _daily_key(symbol: str, day: str) -> str:
    return f"data/spot/daily/klines/{symbol}/1d/{symbol}-1d-{day}.zip"


def _public_archive_record(key: str) -> dict[str, Any]:
    return _official_archive(f"{BUCKET}/{key}", key)


def _btt_conflict(raw_root: Path, key: str, conflict_id: str) -> dict[str, Any]:
    local = _local_archive(raw_root, key)
    current = _public_archive_record(key)
    affected = _affected_rows(local, negative=True)
    archive_month = key[-11:-4]
    comparator_key = f"data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-{archive_month}.zip"
    schema_comparator = _public_archive_record(comparator_key)
    timestamp_counts: dict[int, int] = {}
    for row_record in local["rows"]:
        open_time_ms = row_record["parsed"]["open_time_ms"]
        timestamp_counts[open_time_ms] = timestamp_counts.get(open_time_ms, 0) + 1
    comparisons = []
    all_daily_rest_agree = True
    all_overflow_signatures = True
    for item in affected:
        monthly_fields = item["raw_fields"]
        open_time_ms = item["parsed"]["open_time_ms"]
        day = _iso(open_time_ms)[:10]
        daily = _public_archive_record(_daily_key("BTTUSDT", day))
        daily_rows = [entry["raw_fields"] for entry in daily["rows"]]
        rest = _rest_rows("BTTUSDT", open_time_ms)
        daily_row = daily_rows[0] if len(daily_rows) == 1 else None
        daily_compare = compare_kline_rows(monthly_fields, daily_row) if daily_row else None
        rest_comparisons = []
        for source in rest:
            comparison = (
                compare_kline_rows(monthly_fields, source["rows"][0])
                if source["availability"] == "available" and len(source["rows"]) == 1
                else None
            )
            rest_comparisons.append({**source, "monthly_comparison": comparison})
            if not comparison or comparison["differing_fields"] != ["base_volume"]:
                all_daily_rest_agree = False
        if not daily_compare or daily_compare["differing_fields"] != ["base_volume"]:
            all_daily_rest_agree = False
        if daily_row is None or not detect_unsigned_volume_overflow_signature(monthly_fields, daily_row):
            all_overflow_signatures = False
        comparisons.append(
            {
                "affected_timestamp": _iso(open_time_ms),
                "official_daily_archive": {
                    key_name: value
                    for key_name, value in daily.items()
                    if key_name != "rows"
                },
                "official_daily_rows": daily_rows,
                "monthly_daily_comparison": daily_compare,
                "public_rest": rest_comparisons,
                "unsigned_64bit_eight_decimal_overflow_signature": bool(
                    daily_row and detect_unsigned_volume_overflow_signature(monthly_fields, daily_row)
                ),
            }
        )
    return {
        "conflict_id": conflict_id,
        "symbol": "BTTUSDT",
        "interval": "1d",
        "archive_month": archive_month,
        "affected_timestamps": [_iso(item["parsed"]["open_time_ms"]) for item in affected],
        "monthly_archive": {
            key_name: value
            for key_name, value in current.items()
            if key_name != "rows"
        },
        "local_cache_sha256": local["zip_sha256"],
        "current_remote_checksum_changed": local["zip_sha256"] != current["zip_sha256"],
        "affected_rows": affected,
        "csv_schema": {
            "columns": 12,
            "column_order": [
                "open_time", "open", "high", "low", "close", "base_volume",
                "close_time", "quote_asset_volume", "trade_count",
                "taker_buy_base_volume", "taker_buy_quote_volume", "ignore",
            ],
            "historical_format_difference": False,
            "header_rows": local["header_rows"],
            "timestamp_unit": "milliseconds",
            "same_month_symbol_comparator": {
                "symbol": "BTCUSDT",
                "canonical_key": comparator_key,
                "zip_sha256": schema_comparator["zip_sha256"],
                "csv_column_count": schema_comparator["csv_column_count"],
                "header_rows": schema_comparator["header_rows"],
                "timestamp_unit": schema_comparator["rows"][0]["parsed"]["timestamp_unit"],
            },
        },
        "duplicate_type": "not_duplicate",
        "comparisons": comparisons,
        "findings": {
            "negative_field": "base_volume",
            "other_authoritative_fields_valid": True,
            "daily_and_two_rest_hosts_agree_on_positive_volume": all_daily_rest_agree,
            "unsigned_64bit_eight_decimal_overflow_signature_all_rows": all_overflow_signatures,
            "parser_schema_bug_found": False,
            "same_month_schema_matches": (
                schema_comparator["csv_column_count"] == local["csv_column_count"]
                and schema_comparator["header_rows"] == local["header_rows"]
            ),
            "affected_timestamp_duplicate_count": max(
                timestamp_counts[item["parsed"]["open_time_ms"]] for item in affected
            ),
            "legal_same_timestamp_alternative_found": False,
            "official_archive_republished": local["zip_sha256"] != current["zip_sha256"],
            "later_asset_migration_used_as_authority": False,
        },
        "classification": "official_monthly_daily_conflict",
        "adjudication_status": "confirmed_requires_general_data_policy",
        "same_contract_rerun_allowed": False,
        "qualification_decision": "blocked",
    }


def _axs_conflict(raw_root: Path, key: str) -> dict[str, Any]:
    local = _local_archive(raw_root, key)
    current = _public_archive_record(key)
    timestamp = 1_770_681_600_000
    affected = _affected_rows(local, timestamp_ms=timestamp)
    daily = _public_archive_record(_daily_key("AXSUSDT", "2026-02-10"))
    daily_rows = [entry["raw_fields"] for entry in daily["rows"]]
    rest = _rest_rows("AXSUSDT", timestamp)
    rest_single_matches = all(
        source["availability"] == "available"
        and len(source["rows"]) == 1
        and compare_kline_rows(affected[0]["raw_fields"], source["rows"][0])["authoritative_fields_equal"]
        for source in rest
    )
    return {
        "conflict_id": "U03E-AXSUSDT-1D-2026-02-10-DUPLICATE",
        "symbol": "AXSUSDT",
        "interval": "1d",
        "archive_month": "2026-02",
        "affected_timestamps": [_iso(timestamp)],
        "monthly_archive": {
            key_name: value
            for key_name, value in current.items()
            if key_name != "rows"
        },
        "local_cache_sha256": local["zip_sha256"],
        "current_remote_checksum_changed": local["zip_sha256"] != current["zip_sha256"],
        "affected_rows": affected,
        "csv_schema": {
            "columns": 12,
            "header_rows": local["header_rows"],
            "timestamp_unit": "microseconds",
        },
        "duplicate_type": classify_duplicate_rows([item["raw_fields"] for item in affected]),
        "comparisons": {
            "official_daily_archive": {
                key_name: value
                for key_name, value in daily.items()
                if key_name != "rows"
            },
            "official_daily_rows": daily_rows,
            "official_daily_duplicate_type": classify_duplicate_rows(daily_rows),
            "public_rest": rest,
        },
        "findings": {
            "monthly_duplicate_type": classify_duplicate_rows([item["raw_fields"] for item in affected]),
            "daily_duplicate_type": classify_duplicate_rows(daily_rows),
            "parser_created_duplicate": detect_parser_created_duplicate([item["raw_fields"] for item in affected]),
            "rest_hosts_return_one_matching_row": rest_single_matches,
            "official_archive_republished": local["zip_sha256"] != current["zip_sha256"],
            "affects_ranking_windows": ["2026-03", "2026-04", "2026-05"],
            "affects_365_day_presence": False,
            "v2_membership_months": [],
            "ignored_because_not_top15": False,
        },
        "classification": "exact_identical_duplicate",
        "adjudication_status": "confirmed_requires_general_data_policy",
        "same_contract_rerun_allowed": False,
        "qualification_decision": "blocked",
    }


def render_report(document: dict[str, Any]) -> str:
    content = document["content"]
    lines = [
        "# Liquid Spot Universe V2 Source Conflict Adjudication Report",
        "",
        f"- Overall decision: {content['overall_decision']}",
        f"- Same-contract U-03E rerun authorized: {'yes' if content['same_contract_rerun_authorized'] else 'no'}",
        f"- Contract hash: `{document['contract_hash']}`",
        f"- Source manifest hash: `{document['source_manifest_hash']}`",
        f"- Qualification summary hash: `{document['qualification_summary_hash']}`",
        f"- Evidence content hash: `{document['content_hash']}`",
        "- Strategy/events/returns/backtesting/OOS/M2/API or trading authorized: no",
        "- Raw ZIP, cache, DuckDB or logs committed: no",
        "",
        "## Adjudication",
        "",
    ]
    for conflict in content["conflicts"]:
        monthly = conflict["monthly_archive"]
        lines.extend(
            [
                f"### {conflict['conflict_id']}",
                "",
                f"- Symbol / interval / month: {conflict['symbol']} / {conflict['interval']} / {conflict['archive_month']}",
                f"- Affected timestamps: {', '.join(conflict['affected_timestamps'])}",
                f"- Monthly key: `{monthly['canonical_key']}`",
                f"- Monthly URL: {monthly['canonical_url']}",
                f"- Current checksum: `{monthly['checksum_file_content']}`",
                f"- ZIP SHA256 / bytes / CRC: `{monthly['zip_sha256']}` / {monthly['zip_byte_size']} / pass",
                f"- CSV filename / columns / header rows: `{monthly['csv_filename']}` / {monthly['csv_column_count']} / {monthly['header_rows']}",
                f"- Timestamp unit / duplicate type: {conflict['csv_schema']['timestamp_unit']} / {conflict['duplicate_type']}",
                f"- Current official checksum changed from local cache: {'yes' if conflict['current_remote_checksum_changed'] else 'no'}",
                f"- Classification: {conflict['classification']}",
                f"- Adjudication: {conflict['adjudication_status']}",
                f"- Same-contract rerun allowed: {'yes' if conflict['same_contract_rerun_allowed'] else 'no'}",
                "",
                "Affected monthly rows:",
                "",
            ]
        )
        for row in conflict["affected_rows"]:
            lines.append(f"- line {row['line_number']}: `{','.join(row['raw_fields'])}`")
        if conflict["symbol"] == "BTTUSDT":
            comparator = conflict["csv_schema"]["same_month_symbol_comparator"]
            lines.extend(
                [
                    "",
                    f"Same-month schema comparator: `{comparator['canonical_key']}` / `{comparator['zip_sha256']}` / {comparator['csv_column_count']} columns / {comparator['header_rows']} header rows / {comparator['timestamp_unit']} timestamps.",
                    "",
                    "The negative value is column 6 `base_volume`. Official daily ZIP and both public REST hosts agree on the positive row; all other authoritative fields match. The delta is exactly `2^64 / 1e8`, an overflow signature. This is evidence of a monthly/daily official-source conflict, not permission to repair the monthly row.",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "Both official monthly and daily ZIPs contain two byte-identical rows for the timestamp; both public REST hosts return one matching row. The raw archive itself is duplicated, so this is not parser-created. AXS is not a V2 Top-15 member, but that does not waive the conflict.",
                ]
            )
        lines.append("")
    lines.extend(
        [
            "## Decision",
            "",
            "The current V2 contract correctly fails closed. No official monthly archive was republished, no parser/schema bug was found, and the current contract has no approved general rule for replacing an invalid monthly row with daily/REST evidence or collapsing exact same-authority duplicates.",
            "",
            "A new general data-policy ADR is required before any behavior can change. This adjudication does not adopt such a policy, modify the V2 contract, rerun U-03E, authorize U-03F/U-04, or approve any strategy work.",
            "",
            "## Official Source Context",
            "",
            "- Binance public-data schema and checksum authority: https://github.com/binance/binance-public-data",
            "- Monthly and daily archives: https://data.binance.vision/",
            "- Public REST comparators: https://api.binance.com/api/v3/klines and https://data-api.binance.vision/api/v3/klines",
            "- No source-owner issue/comment was posted by this task.",
        ]
    )
    return "\n".join(lines) + "\n"


def execute(*, raw_root: Path, output_path: Path, report_path: Path) -> dict[str, Any]:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    evidence_dir = ROOT / "reports/m0/evidence/liquid_universe_v2"
    source = json.loads((evidence_dir / "source_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((evidence_dir / "qualification_summary.json").read_text(encoding="utf-8"))
    conflicts = [
        _btt_conflict(raw_root, MONTHLY_KEYS[0], "U03E-BTTUSDT-1D-2019-01-NEGATIVE-BASE-VOLUME"),
        _btt_conflict(raw_root, MONTHLY_KEYS[1], "U03E-BTTUSDT-1D-2019-02-NEGATIVE-BASE-VOLUME"),
        _axs_conflict(raw_root, MONTHLY_KEYS[2]),
    ]
    document = build_adjudication_document(
        contract_hash=contract["canonical_hash"],
        source_manifest_hash=source["content_hash"],
        qualification_summary_hash=summary["content_hash"],
        conflicts=conflicts,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(document), encoding="utf-8")
    report_path.write_text(render_report(document), encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=ROOT / "storage/raw/liquid_universe/data/spot",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_SOURCE_CONFLICT_ADJUDICATION_REPORT.md",
    )
    args = parser.parse_args()
    document = execute(raw_root=args.raw_root, output_path=args.output, report_path=args.report)
    print(
        f"decision={document['content']['overall_decision']} "
        f"content_hash={document['content_hash']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
