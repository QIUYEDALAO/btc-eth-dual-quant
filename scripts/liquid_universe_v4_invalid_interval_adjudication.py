#!/usr/bin/env python3
"""Run the frozen U-03F V4 invalid-interval evidence diagnostic."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import random
import tempfile
from typing import Any, Iterable, Mapping, Sequence
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "storage/raw/liquid_universe/data/spot"
PROTOCOL_PATH = ROOT / "config/liquid_universe_v4_invalid_interval_adjudication_protocol.json"
SOURCE_FREEZE_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/source_freeze_manifest.json"
MEMBERSHIP_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/membership_manifest.json"
QUALIFICATION_SUMMARY_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/qualification_summary.json"
EVIDENCE_DIR = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication"
REPORT_PATH = ROOT / "reports/m0/U03F_V4_INVALID_INTERVAL_ADJUDICATION_REPORT.md"

PROTOCOL_CONTENT_HASH = "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190"
PROTOCOL_MERGE_COMMIT = "70c784b1573de8437e189672c89e9c00b6505978"
SOURCE_FREEZE_CONTENT_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
SOURCE_FREEZE_FILE_SHA256 = "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb"
MEMBERSHIP_FILE_SHA256 = "d3dbf7508b1cd8373834a70cf7ee307937de754643687bd9ad9928f082aea72f"
QUALIFICATION_SUMMARY_FILE_SHA256 = "b2afe36cd8a7c8e91cb628ecf3ce479b6860701bc073a114fdec443212b84b19"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

OUTPUT_NAMES = (
    "input_binding_summary",
    "invalid_interval_rows",
    "synchronized_window_summary",
    "order_determinism_summary",
    "policy_gap_assessment",
    "authorization_matrix",
)


class DiagnosticMismatch(ValueError):
    """Raised when the frozen evidence cannot be reproduced exactly."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in items:
            if key in output:
                raise DiagnosticMismatch(f"duplicate JSON key: {path}:{key}")
            output[key] = value
        return output

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda item: (_ for _ in ()).throw(DiagnosticMismatch(item)),
    )
    if not isinstance(value, dict):
        raise DiagnosticMismatch(f"JSON root is not an object: {path}")
    return value


def normalize_timestamp_ms(value: str) -> int:
    if not value or not value.isdigit():
        raise DiagnosticMismatch("timestamp is not an unsigned integer")
    raw = int(value)
    if raw >= 10**14:
        raw //= 1_000
    if raw >= 10**14 or raw < 10**11:
        raise DiagnosticMismatch("unsupported timestamp unit")
    return raw


def utc_iso(milliseconds: int) -> str:
    value = EPOCH + timedelta(milliseconds=milliseconds)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def month_for_timestamp(milliseconds: int) -> str:
    value = EPOCH + timedelta(milliseconds=milliseconds)
    return f"{value.year:04d}-{value.month:02d}"


def parse_identity(canonical_key: str) -> tuple[str, str, str, str]:
    parts = PurePosixPath(canonical_key).parts
    if len(parts) != 7 or parts[:2] != ("data", "spot") or parts[3] != "klines":
        raise DiagnosticMismatch(f"unsupported frozen archive key: {canonical_key}")
    frequency, symbol, interval, filename = parts[2], parts[4], parts[5], parts[6]
    if frequency not in {"monthly", "daily"} or interval not in {"1d", "5m"}:
        raise DiagnosticMismatch(f"unsupported frozen archive identity: {canonical_key}")
    prefix = f"{symbol}-{interval}-"
    if not filename.startswith(prefix) or not filename.endswith(".zip"):
        raise DiagnosticMismatch(f"archive filename identity mismatch: {canonical_key}")
    period = filename[len(prefix):-4]
    expected_length = 7 if frequency == "monthly" else 10
    if len(period) != expected_length:
        raise DiagnosticMismatch(f"archive period identity mismatch: {canonical_key}")
    return frequency, symbol, interval, period


def source_path(raw_root: Path, canonical_key: str) -> Path:
    path = PurePosixPath(canonical_key)
    return raw_root.joinpath(*path.parts[2:])


def source_order(
    entries: Sequence[Mapping[str, Any]], mode: str
) -> list[Mapping[str, Any]]:
    ordered = sorted(entries, key=lambda item: str(item["canonical_key"]))
    if mode == "reverse":
        ordered.reverse()
    elif mode == "deterministic_shuffled":
        seed = int(PROTOCOL_CONTENT_HASH[:16], 16)
        random.Random(seed).shuffle(ordered)
    elif mode != "normal":
        raise DiagnosticMismatch(f"unsupported diagnostic order: {mode}")
    return ordered


def _parse_csv_line(raw_line: bytes, line_number: int) -> tuple[str, ...] | None:
    try:
        text = raw_line.decode("utf-8-sig" if line_number == 1 else "utf-8")
    except UnicodeDecodeError as exc:
        raise DiagnosticMismatch(f"invalid CSV encoding at line {line_number}") from exc
    records = list(csv.reader(io.StringIO(text)))
    if len(records) != 1:
        raise DiagnosticMismatch(f"ambiguous CSV row at line {line_number}")
    fields = tuple(item.strip() for item in records[0])
    if line_number == 1 and fields and not fields[0].isdigit():
        return None
    if len(fields) != 12:
        raise DiagnosticMismatch(f"non-12-field kline at line {line_number}")
    return fields


def inspect_archive(
    *, raw_root: Path, entry: Mapping[str, Any]
) -> list[dict[str, Any]]:
    key = str(entry["canonical_key"])
    frequency, symbol, interval, period = parse_identity(key)
    path = source_path(raw_root, key)
    if not path.is_file():
        raise DiagnosticMismatch(f"missing frozen archive: {key}")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != entry.get("sha256") or len(payload) != entry.get("byte_size"):
        raise DiagnosticMismatch(f"source binding drift: {key}")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) != 1:
                raise DiagnosticMismatch(f"archive member count mismatch: {key}")
            member = members[0]
            expected_member = f"{symbol}-{interval}-{period}.csv"
            if PurePosixPath(member.filename).name != expected_member:
                raise DiagnosticMismatch(f"archive member identity mismatch: {key}")
            member_payload = archive.read(member)
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise DiagnosticMismatch(f"ZIP/CRC failure: {key}") from exc

    if frequency != "monthly" or interval != "5m":
        return []

    invalid: list[dict[str, Any]] = []
    seen_open_times: set[int] = set()
    previous_open_time: int | None = None
    for line_number, raw_line in enumerate(member_payload.splitlines(), start=1):
        fields = _parse_csv_line(raw_line, line_number)
        if fields is None:
            continue
        open_time_ms = normalize_timestamp_ms(fields[0])
        close_time_ms = normalize_timestamp_ms(fields[6])
        if month_for_timestamp(open_time_ms) != period:
            raise DiagnosticMismatch(f"out-of-period 5m row: {key}:{line_number}")
        if open_time_ms in seen_open_times:
            raise DiagnosticMismatch(f"duplicate 5m open time: {key}:{line_number}")
        if previous_open_time is not None and open_time_ms <= previous_open_time:
            raise DiagnosticMismatch(f"unordered 5m rows: {key}:{line_number}")
        seen_open_times.add(open_time_ms)
        previous_open_time = open_time_ms
        off_grid = open_time_ms % 300_000 != 0
        invalid_close = close_time_ms != open_time_ms + 299_999
        if off_grid or invalid_close:
            invalid.append({
                "archive_byte_size": len(payload),
                "archive_sha256": digest,
                "canonical_key": key,
                "close_delta_ms": close_time_ms - open_time_ms,
                "close_time_ms": close_time_ms,
                "close_time_utc": utc_iso(close_time_ms),
                "line_number": line_number,
                "member_name": member.filename,
                "month": period,
                "off_grid_open": off_grid,
                "open_time_ms": open_time_ms,
                "open_time_utc": utc_iso(open_time_ms),
                "raw_row_sha256": hashlib.sha256(raw_line).hexdigest(),
                "raw_close_time": fields[6],
                "raw_close_time_unit": (
                    "microseconds" if int(fields[6]) >= 10**14 else "milliseconds"
                ),
                "raw_open_time": fields[0],
                "raw_open_time_unit": (
                    "microseconds" if int(fields[0]) >= 10**14 else "milliseconds"
                ),
                "symbol": symbol,
            })
    return invalid


def membership_map(document: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    rows = document.get("content")
    if not isinstance(rows, list) or len(rows) != 1_170:
        raise DiagnosticMismatch("membership row count changed")
    grouped: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise DiagnosticMismatch("membership row is not an object")
        month = str(row.get("effective_month", ""))[:7]
        symbol = str(row.get("symbol", ""))
        grouped.setdefault(month, []).append(symbol)
    result = {month: tuple(sorted(symbols)) for month, symbols in grouped.items()}
    if len(result) != 78 or any(len(symbols) != 15 for symbols in result.values()):
        raise DiagnosticMismatch("monthly Top-15 membership changed")
    return result


def expected_blockers(document: Mapping[str, Any]) -> set[tuple[str, str]]:
    content = document.get("content", {})
    blockers = content.get("blockers", [])
    if content.get("processing_errors") != 119 or len(blockers) != 119:
        raise DiagnosticMismatch("known blocker count changed")
    output: set[tuple[str, str]] = set()
    for blocker in blockers:
        parts = str(blocker).split(":")
        if len(parts) != 3 or parts[2] != "5m interval boundary is invalid":
            raise DiagnosticMismatch(f"known blocker class changed: {blocker}")
        output.add((parts[0], parts[1]))
    if len(output) != 119:
        raise DiagnosticMismatch("known blocker identities are not unique")
    return output


def input_bindings(
    *, freeze: Mapping[str, Any], membership: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "diagnostic_base_main": PROTOCOL_MERGE_COMMIT,
        "protocol_content_hash": PROTOCOL_CONTENT_HASH,
        "protocol_merge_commit": PROTOCOL_MERGE_COMMIT,
        "protocol_pr": 102,
        "source_archive_count": freeze["content"]["archive_count"],
        "source_freeze_content_hash": freeze["content_hash"],
        "source_freeze_file_sha256": file_sha256(SOURCE_FREEZE_PATH),
        "membership_content_hash": membership["content_hash"],
        "membership_file_sha256": file_sha256(MEMBERSHIP_PATH),
        "qualification_summary_file_sha256": file_sha256(QUALIFICATION_SUMMARY_PATH),
        "source_mode": "frozen_local_only",
    }


def synchronized_windows(
    rows: Sequence[Mapping[str, Any]], members: Mapping[str, tuple[str, ...]]
) -> list[dict[str, Any]]:
    grouped: dict[int, list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["open_time_ms"]), []).append(row)
    output: list[dict[str, Any]] = []
    for open_time in sorted(grouped):
        records = sorted(grouped[open_time], key=lambda item: str(item["symbol"]))
        month = month_for_timestamp(open_time)
        active = members.get(month)
        if active is None:
            raise DiagnosticMismatch(f"invalid row month has no membership: {month}")
        symbols = tuple(str(item["symbol"]) for item in records)
        if len(symbols) != len(set(symbols)):
            raise DiagnosticMismatch(f"duplicate invalid symbol in window: {open_time}")
        if not set(symbols).issubset(set(active)):
            raise DiagnosticMismatch(f"non-member invalid row: {open_time}")
        numerator, denominator = len(symbols), len(active)
        synchronous = numerator >= 2 and numerator * 10 >= denominator * 8
        output.append({
            "active_member_count": denominator,
            "active_members": list(active),
            "invalid_member_count": numerator,
            "invalid_members": list(symbols),
            "missing_invalid_members": sorted(set(active) - set(symbols)),
            "month": month,
            "open_time_ms": open_time,
            "open_time_utc": utc_iso(open_time),
            "synchronous_candidate": synchronous,
            "synchronous_fraction": format(
                Decimal(numerator) / Decimal(denominator), ".12f"
            ),
            "threshold_fraction": "0.800000000000",
            "threshold_minimum_symbols": 2,
            "verified_archive_count": numerator,
        })
    return output


def policy_assessment(
    *, rows: Sequence[Mapping[str, Any]], windows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    exact = len(rows) == 119
    all_synchronous = bool(windows) and all(item["synchronous_candidate"] for item in windows)
    decision = (
        "new_policy_adr_required"
        if exact and all_synchronous
        else "official_source_followup_required"
    )
    return {
        "all_invalid_rows_exact": exact,
        "all_windows_synchronous": all_synchronous,
        "decision": decision,
        "direct_existing_gap_policy_adoption_allowed": False,
        "existing_v2_gap_policy_contract_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
        "invalid_physical_row_count": len(rows),
        "per_row_exception_registry_allowed": False,
        "production_pipeline_change_allowed": False,
        "synchronized_window_count": sum(bool(item["synchronous_candidate"]) for item in windows),
        "total_window_count": len(windows),
        "v4_policy_currently_authorizes_invalid_row_to_gap_conversion": False,
    }


def authorization_matrix() -> dict[str, bool]:
    return {
        "diagnostic_executed": True,
        "draft_policy_adr_after_diagnostic_merge": False,
        "policy_adoption": False,
        "repair_implementation": False,
        "public_requalification": False,
        "new_independent_audit": False,
        "u04": False,
        "hypothesis": False,
        "strategy": False,
        "event_scan": False,
        "returns": False,
        "backtesting": False,
        "oos": False,
        "api_trading": False,
        "execution_live": False,
        "m2": False,
    }


def scan_order(
    *, raw_root: Path, entries: Sequence[Mapping[str, Any]], mode: str,
    members: Mapping[str, tuple[str, ...]], known: set[tuple[str, str]],
    bindings: Mapping[str, Any],
) -> dict[str, Any]:
    invalid: list[dict[str, Any]] = []
    for index, entry in enumerate(source_order(entries, mode), start=1):
        invalid.extend(inspect_archive(raw_root=raw_root, entry=entry))
        if index % 2_000 == 0 or index == len(entries):
            print(f"order={mode} archives={index}/{len(entries)} invalid_rows={len(invalid)}", flush=True)
    invalid.sort(key=lambda item: (item["open_time_ms"], item["symbol"], item["canonical_key"], item["line_number"]))
    identities = [(str(row["symbol"]), str(row["month"])) for row in invalid]
    if len(invalid) != len(known) or set(identities) != known:
        raise DiagnosticMismatch(
            f"invalid-row identity mismatch: expected={len(known)} actual={len(invalid)}"
        )
    if len(identities) != len(set(identities)):
        raise DiagnosticMismatch("expected invalid row is missing or duplicated")
    windows = synchronized_windows(invalid, members)
    assessment = policy_assessment(rows=invalid, windows=windows)
    if assessment["decision"] != "new_policy_adr_required":
        raise DiagnosticMismatch(f"unexpected evidence decision: {assessment['decision']}")
    return {
        "input_binding_summary": dict(bindings),
        "invalid_interval_rows": invalid,
        "synchronized_window_summary": windows,
        "policy_gap_assessment": assessment,
        "authorization_matrix": authorization_matrix(),
    }


def wrapped(manifest_type: str, content: Any, generated_utc: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_type": manifest_type,
        "generated_utc": generated_utc,
        "content": content,
        "content_hash": content_hash(content),
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(path: Path, document: Mapping[str, Any]) -> None:
    atomic_write(
        path,
        (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8"),
    )


def render_report(documents: Mapping[str, Mapping[str, Any]], run: Mapping[str, Any]) -> str:
    rows = documents["invalid_interval_rows"]["content"]
    windows = documents["synchronized_window_summary"]["content"]
    policy = documents["policy_gap_assessment"]["content"]
    deterministic = documents["order_determinism_summary"]["content"]
    bindings = documents["input_binding_summary"]["content"]
    lines = [
        "# U-03F V4 Invalid-Interval Adjudication Diagnostic",
        "",
        "- Status: completed_new_policy_adr_required",
        f"- Decision: `{policy['decision']}`",
        f"- Diagnostic base main: `{bindings['diagnostic_base_main']}`",
        f"- Protocol content hash: `{bindings['protocol_content_hash']}`",
        f"- Source freeze: `{bindings['source_freeze_content_hash']}`",
        f"- Frozen archives verified per order: {bindings['source_archive_count']:,}",
        f"- Invalid physical rows: {len(rows)}",
        f"- Synchronized windows: {policy['synchronized_window_count']} / {policy['total_window_count']}",
        f"- Three-order canonical hash: `{deterministic['canonical_diagnostic_content_hash']}`",
        f"- Diagnostic run manifest: `{run['content_hash']}`",
        "- Production pipeline modified: no",
        "- Policy adopted: no",
        "- Requalification/new audit/U-04/OOS/M2 authorized: no",
        "",
        "## Evidence",
        "",
        "All 27,736 source-freeze entries passed exact byte-size, SHA256, ZIP CRC",
        "and single-member identity checks in normal, reverse and deterministic-",
        "shuffled traversal. The 1,170 frozen Top-15 member-month 5m archives were",
        "then scanned with integer-only timestamp normalization.",
        "",
        "The 119 known blocked symbol-months resolve to exactly 119 physical rows.",
        "They group into eight exact UTC open times; every group meets the frozen",
        "two-symbol and 80% synchronous evidence threshold.",
        "",
        "| Open time UTC | Invalid / active | Missing invalid member | Close deltas ms |",
        "| --- | ---: | --- | --- |",
    ]
    for window in windows:
        member_rows = [row for row in rows if row["open_time_ms"] == window["open_time_ms"]]
        deltas = ", ".join(str(item) for item in sorted({row["close_delta_ms"] for row in member_rows}))
        missing = ", ".join(window["missing_invalid_members"]) or "none"
        lines.append(
            f"| {window['open_time_utc']} | {window['invalid_member_count']} / {window['active_member_count']} | {missing} | {deltas} |"
        )
    lines.extend([
        "",
        "## Policy Boundary",
        "",
        "This is evidence, not policy adoption. The current V4 contract does not",
        "authorize converting invalid physical rows into accepted synchronized gaps.",
        "Direct reuse of the existing gap policy and per-row exception registration",
        "remain forbidden. After this evidence merges, only a separate Draft policy",
        "ADR may be created and independently reviewed.",
        "",
        "Historical PR #89, PR #95 and PR #100 evidence and every frozen source byte",
        "remain unchanged. Runtime implementation, public requalification, a new",
        "independent audit, U-04, strategy/backtesting, OOS, API/trading,",
        "`execution/live` and M2 remain unauthorized.",
        "",
    ])
    return "\n".join(lines)


def validate_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol = strict_json(PROTOCOL_PATH)
    if content_hash({key: value for key, value in protocol.items() if key != "generated_utc"}) != PROTOCOL_CONTENT_HASH:
        raise DiagnosticMismatch("protocol content hash drift")
    freeze = strict_json(SOURCE_FREEZE_PATH)
    membership = strict_json(MEMBERSHIP_PATH)
    summary = strict_json(QUALIFICATION_SUMMARY_PATH)
    if freeze.get("content_hash") != SOURCE_FREEZE_CONTENT_HASH:
        raise DiagnosticMismatch("source freeze content hash drift")
    if file_sha256(SOURCE_FREEZE_PATH) != SOURCE_FREEZE_FILE_SHA256:
        raise DiagnosticMismatch("source freeze file hash drift")
    if file_sha256(MEMBERSHIP_PATH) != MEMBERSHIP_FILE_SHA256:
        raise DiagnosticMismatch("membership file hash drift")
    if file_sha256(QUALIFICATION_SUMMARY_PATH) != QUALIFICATION_SUMMARY_FILE_SHA256:
        raise DiagnosticMismatch("qualification summary file hash drift")
    entries = freeze.get("content", {}).get("archives", [])
    if len(entries) != 27_736 or freeze["content"].get("archive_count") != 27_736:
        raise DiagnosticMismatch("source archive count drift")
    keys = [str(item.get("canonical_key")) for item in entries]
    if len(keys) != len(set(keys)):
        raise DiagnosticMismatch("source freeze has duplicate keys")
    return protocol, freeze, membership, summary


def execute(
    *, raw_root: Path = RAW_ROOT, evidence_dir: Path = EVIDENCE_DIR,
    report_path: Path = REPORT_PATH, generated_utc: str | None = None,
) -> dict[str, Any]:
    _, freeze, membership, summary = validate_inputs()
    members = membership_map(membership)
    known = expected_blockers(summary)
    entries = freeze["content"]["archives"]
    five_minute_keys = {
        (parse_identity(str(item["canonical_key"]))[1], parse_identity(str(item["canonical_key"]))[3])
        for item in entries if "/5m/" in str(item["canonical_key"])
    }
    expected_member_keys = {(symbol, month) for month, symbols in members.items() for symbol in symbols}
    if five_minute_keys != expected_member_keys:
        raise DiagnosticMismatch("frozen 5m archive set does not equal membership set")
    bindings = input_bindings(freeze=freeze, membership=membership)
    order_contents: dict[str, dict[str, Any]] = {}
    order_hashes: dict[str, str] = {}
    for mode in ("normal", "reverse", "deterministic_shuffled"):
        result = scan_order(
            raw_root=raw_root, entries=entries, mode=mode, members=members,
            known=known, bindings=bindings,
        )
        order_contents[mode] = result
        order_hashes[mode] = content_hash(result)
    if len(set(order_hashes.values())) != 1:
        raise DiagnosticMismatch(f"order content hash mismatch: {order_hashes}")

    timestamp = generated_utc or datetime.now(timezone.utc).isoformat()
    base = order_contents["normal"]
    order_summary = {
        "canonical_diagnostic_content_hash": order_hashes["normal"],
        "deterministic_mismatches": 0,
        "orders": [
            {"content_hash": order_hashes[name], "name": name, "status": "pass"}
            for name in ("normal", "reverse", "deterministic_shuffled")
        ],
        "shuffle_seed_source": f"protocol_content_hash_prefix:{PROTOCOL_CONTENT_HASH[:16]}",
        "status": "pass",
    }
    component_contents = {
        "input_binding_summary": base["input_binding_summary"],
        "invalid_interval_rows": base["invalid_interval_rows"],
        "synchronized_window_summary": base["synchronized_window_summary"],
        "order_determinism_summary": order_summary,
        "policy_gap_assessment": base["policy_gap_assessment"],
        "authorization_matrix": base["authorization_matrix"],
    }
    documents = {
        name: wrapped(f"u03f_v4_{name}", component_contents[name], timestamp)
        for name in OUTPUT_NAMES
    }
    run_content = {
        "authorizations": base["authorization_matrix"],
        "component_hashes": {name: documents[name]["content_hash"] for name in OUTPUT_NAMES},
        "decision": base["policy_gap_assessment"]["decision"],
        "diagnostic_content_hash": order_hashes["normal"],
        "invalid_physical_rows": len(base["invalid_interval_rows"]),
        "orders": order_summary["orders"],
        "protocol_content_hash": PROTOCOL_CONTENT_HASH,
        "source_archive_count": 27_736,
        "source_freeze_content_hash": SOURCE_FREEZE_CONTENT_HASH,
        "status": "completed_new_policy_adr_required",
        "synchronized_windows": len(base["synchronized_window_summary"]),
    }
    run = wrapped("u03f_v4_invalid_interval_adjudication_run", run_content, timestamp)
    for name, document in documents.items():
        write_json(evidence_dir / f"{name}.json", document)
    write_json(evidence_dir / "diagnostic_run_manifest.json", run)
    atomic_write(report_path, render_report(documents, run).encode("utf-8"))
    print(
        f"status={run_content['status']} decision={run_content['decision']} "
        f"rows={run_content['invalid_physical_rows']} windows={run_content['synchronized_windows']} "
        f"run_hash={run['content_hash']}",
        flush=True,
    )
    return run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--generated-utc")
    args = parser.parse_args()
    try:
        execute(
            raw_root=args.raw_root,
            evidence_dir=args.evidence_dir,
            report_path=args.report,
            generated_utc=args.generated_utc,
        )
    except DiagnosticMismatch as exc:
        print(f"blocked_evidence_mismatch: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
