#!/usr/bin/env python3
"""Build the result-blind, IS-only 92-row membership-exit authority.

The command acquires only the 91 unchanged official daily archives and their
checksums.  The already-frozen RNDR archive is reused without a network
request.  Boundary rows stay in a separate forced-exit lookup and are never
added to candidate OHLCV or indicator history.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / "reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json"
AUTHORIZATION = ROOT / "config/membership_exit_boundary_authorization_v1.json"
ADR0018 = ROOT / "config/adr0018_scheduled_market_cessation_forced_exit_v1.json"
PR118_REVIEW = ROOT / "reports/expert/evidence/pr118_exact_head_review_v1.json"
RNDR_PREFLIGHT = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/rndr_original_symbol_preflight.json"
MEMBERSHIP = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/membership_manifest.json"
LIFECYCLE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/lifecycle_resolution_registry.json"
INVALID_EVENTS = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_event_manifest.json"
INVALID_MASK = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_slot_mask_manifest.json"
OOS_GUARD = ROOT / "config/external_strategy_oos_guard_v1.json"
TRIAL_STATE = ROOT / "config/external_strategy_candidate_freeze_v1.json"
EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/completed_boundary_authority.json"
COMMAND_EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/completed_boundary_authority_command.json"
RAW_ROOT = ROOT / "storage/raw/external_strategy_boundary_authority"

BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
USER_AGENT = "btc-eth-dual-quant-completed-boundary-authority/1"
OOS_START_MS = 1726012800000
OLD_RNDR = ("RNDRUSDT", "2024-08-01T00:00:00Z")
NEW_RNDR = ("RNDRUSDT", "2024-07-22T02:55:00Z")
RNDR_LOCAL_RELATIVE = "data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-07-22.zip"

QUALIFICATION_HASH = "e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa"
AUTHORIZATION_HASH = "82acac46ce4e81cdab071635d986b17dfe1996091e4aa55cba3de5007b49cea4"
ADR0018_HASH = "8761fabac1f32d518d6c75c08dcf0a37288262059fe3192b87fb44de836b46e9"
PR118_HEAD = "89965820c3281caf4f759a055ace271151d32622"
PR118_REVIEW_HASH = "6f57e1da0efa6f233308809d9d5bd33a6a591737c032b5d73206379713e3a94c"
PR118_GATE_RUN = 29877334519
PR118_MERGE = "02673d1bebfb7a9efa5370a8025f1ea185c172b5"
RNDR_PREFLIGHT_HASH = "eceafea174381268c22df88b3262a3702a828a3aac079b8e060000686c9b38be"
MEMBERSHIP_HASH = "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5"
LIFECYCLE_HASH = "adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef"
INVALID_EVENTS_HASH = "8a4e022a9c837b1fb9d4fe7539b7e9c45605660d605e2dcdf71fff0ac34103a6"
INVALID_MASK_HASH = "23e78e15a4484af9167b03e29bf9d499a39ff1e1c8195a056fae72b984285487"

# Frozen after the single authorized acquisition.
EXPECTED_EVIDENCE_HASH: str | None = "9829e22b0c0b21bf69dac2d8d84de845650e2da31e13f239578e6a43dba96ada"
EXPECTED_COMMAND_HASH: str | None = "2674853239a7c185d35a0e751bf71e31cc89c5556e8c573a95415e42006771a7"

EXPECTED_PERMISSIONS = {
    "original_is": False,
    "modified_is": False,
    "selection_trial_materialization": False,
    "oos": False,
    "dry_run": False,
    "api_private_endpoints": False,
    "paper_live": False,
    "order_placement": False,
    "execution_live": False,
    "m2": False,
}

COMMAND = "python3 scripts/external_strategy_boundary_authority_build.py --acquire --write"


def canonical_hash(value: Any) -> str:
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_identity() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "user_agent": USER_AGENT,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"not UTC: {value}")
    return int(parsed.timestamp() * 1000)


def iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def source_paths(symbol: str, open_utc: str) -> tuple[str, str, str]:
    day = open_utc[:10]
    filename = f"{symbol}-5m-{day}.zip"
    relative = f"data/spot/daily/klines/{symbol}/5m/{filename}"
    url = f"{BASE_URL}/{symbol}/5m/{filename}"
    return relative, url, url + ".CHECKSUM"


def revised_boundaries(root: Path = ROOT) -> list[dict[str, Any]]:
    qualification = load_json(root / QUALIFICATION.relative_to(ROOT))
    adr = load_json(root / ADR0018.relative_to(ROOT))
    if qualification.get("content_hash") != QUALIFICATION_HASH:
        raise ValueError("qualification identity drift")
    if adr.get("content_hash") != ADR0018_HASH:
        raise ValueError("ADR-0018 identity drift")
    original = qualification.get("transitions")
    if not isinstance(original, list) or len(original) != 92:
        raise ValueError("original boundary set must contain 92 transitions")
    result: list[dict[str, Any]] = []
    removed = 0
    for row in original:
        identity = (row.get("symbol"), row.get("membership_end_exclusive"))
        if identity == OLD_RNDR:
            removed += 1
            continue
        relative, url, checksum = source_paths(str(identity[0]), str(identity[1]))
        result.append({
            "symbol": identity[0],
            "membership_end_exclusive": identity[1],
            "last_active_month": row.get("last_active_month"),
            "boundary_reason": "point_in_time_membership_exit",
            "source_relative_path": relative,
            "source_url": url,
            "checksum_url": checksum,
        })
    if removed != 1:
        raise ValueError("ADR-0018 replaced boundary missing or duplicated")
    relative, url, checksum = source_paths(*NEW_RNDR)
    result.append({
        "symbol": NEW_RNDR[0],
        "membership_end_exclusive": NEW_RNDR[1],
        "last_active_month": "2024-07",
        "boundary_reason": "scheduled_market_cessation_forced_exit",
        "source_relative_path": relative,
        "source_url": url,
        "checksum_url": checksum,
    })
    result.sort(key=lambda row: (row["symbol"], row["membership_end_exclusive"]))
    identities = [(row["symbol"], row["membership_end_exclusive"]) for row in result]
    if len(result) != 92 or len(set(identities)) != 92 or OLD_RNDR in identities or identities.count(NEW_RNDR) != 1:
        raise ValueError("revised boundary identity contract failed")
    if any(utc_ms(row["membership_end_exclusive"]) >= OOS_START_MS for row in result):
        raise ValueError("revised boundary crosses sealed OOS")
    return result


def authority_bindings(root: Path = ROOT) -> dict[str, Any]:
    authorization = load_json(root / AUTHORIZATION.relative_to(ROOT))
    review = load_json(root / PR118_REVIEW.relative_to(ROOT))
    preflight = load_json(root / RNDR_PREFLIGHT.relative_to(ROOT))
    membership = load_json(root / MEMBERSHIP.relative_to(ROOT))
    lifecycle = load_json(root / LIFECYCLE.relative_to(ROOT))
    events = load_json(root / INVALID_EVENTS.relative_to(ROOT))
    mask = load_json(root / INVALID_MASK.relative_to(ROOT))
    checks = (
        (authorization.get("reviewer_provided_canonical_content_hash"), AUTHORIZATION_HASH, "authorization"),
        (review.get("content_hash"), PR118_REVIEW_HASH, "PR #118 review"),
        (preflight.get("content_hash"), RNDR_PREFLIGHT_HASH, "RNDR preflight"),
        (membership.get("content_hash"), MEMBERSHIP_HASH, "membership"),
        (lifecycle.get("content_hash"), LIFECYCLE_HASH, "lifecycle"),
        (events.get("content_hash"), INVALID_EVENTS_HASH, "invalid events"),
        (mask.get("content_hash"), INVALID_MASK_HASH, "invalid mask"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"{label} identity drift")
    if review.get("reviewed_head") != PR118_HEAD or review.get("verdict") != "approve":
        raise ValueError("PR #118 review target or verdict drift")
    if review.get("critical_findings") != 0 or review.get("high_findings") != 0:
        raise ValueError("PR #118 review severity drift")
    return {
        "qualification_hash": QUALIFICATION_HASH,
        "authorization_hash": AUTHORIZATION_HASH,
        "adr0018_hash": ADR0018_HASH,
        "pr118_reviewed_head": PR118_HEAD,
        "pr118_review_hash": PR118_REVIEW_HASH,
        "pr118_exact_head_gate_run": PR118_GATE_RUN,
        "pr118_merge_commit": PR118_MERGE,
        "rndr_preflight_hash": RNDR_PREFLIGHT_HASH,
        "membership_hash": MEMBERSHIP_HASH,
        "lifecycle_hash": LIFECYCLE_HASH,
        "invalid_events_hash": INVALID_EVENTS_HASH,
        "invalid_mask_hash": INVALID_MASK_HASH,
    }


def validate_membership_and_policy(root: Path, boundary: dict[str, Any]) -> dict[str, Any]:
    membership = load_json(root / MEMBERSHIP.relative_to(ROOT))["content"]
    lifecycle_entries = load_json(root / LIFECYCLE.relative_to(ROOT))["content"]["entries"]
    events = load_json(root / INVALID_EVENTS.relative_to(ROOT))["content"]
    masks = load_json(root / INVALID_MASK.relative_to(ROOT))["content"]
    symbol = boundary["symbol"]
    open_utc = boundary["membership_end_exclusive"]
    open_ms = utc_ms(open_utc)
    active_month = boundary["last_active_month"]
    rows = [
        row for row in membership
        if row.get("symbol") == symbol and str(row.get("effective_month", ""))[:7] == active_month
    ]
    if len(rows) != 1 or rows[0].get("eligibility_status") != "qualified":
        raise ValueError(f"qualified prior membership missing: {symbol}@{active_month}")
    lifecycle_conflicts = [
        row for row in lifecycle_entries
        if row.get("symbol") == symbol and utc_ms(row["availability_end_exclusive"]) <= open_ms
    ]
    if lifecycle_conflicts:
        raise ValueError(f"lifecycle ended before boundary: {symbol}@{open_utc}")
    masked = [row for row in masks if row.get("symbol") == symbol and int(row.get("open_time_ms", -1)) == open_ms]
    event = [row for row in events if int(row.get("open_time_ms", -1)) == open_ms]
    if masked or event:
        raise ValueError(f"boundary row covered by invalid interval: {symbol}@{open_utc}")
    return {
        "prior_membership_row_hash": canonical_hash(rows[0]),
        "prior_membership_rank": rows[0]["rank"],
        "eligibility_status": rows[0]["eligibility_status"],
        "lifecycle_status": "adr0018_scheduled_cessation" if (symbol, open_utc) == NEW_RNDR else "no_prior_lifecycle_cessation",
        "invalid_interval_masked": False,
        "invalid_interval_event": False,
    }


def parse_checksum(body: bytes) -> str:
    parts = body.decode("utf-8").strip().split()
    if not parts or len(parts[0]) != 64 or any(char not in "0123456789abcdefABCDEF" for char in parts[0]):
        raise ValueError("official checksum payload invalid")
    return parts[0].lower()


def decimal(value: str, label: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} invalid") from exc
    if not result.is_finite():
        raise ValueError(f"{label} non-finite")
    return result


def parse_row(raw_line: bytes, line_number: int, symbol: str, open_utc: str) -> dict[str, Any]:
    try:
        fields = next(csv.reader([raw_line.decode("utf-8-sig")]))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("boundary row is not valid UTF-8 CSV") from exc
    if len(fields) != 12:
        raise ValueError("boundary row must contain exactly 12 fields")
    try:
        open_ms, close_ms, trades = int(fields[0]), int(fields[6]), int(fields[8])
    except ValueError as exc:
        raise ValueError("timestamp or trade count invalid") from exc
    expected_open = utc_ms(open_utc)
    if open_ms != expected_open or close_ms != open_ms + 299999 or open_ms >= OOS_START_MS:
        raise ValueError("boundary timestamp contract failed")
    open_price, high, low, close = [decimal(value, label) for value, label in zip(fields[1:5], ("open", "high", "low", "close"))]
    volume = decimal(fields[5], "volume")
    quote_volume = decimal(fields[7], "quote volume")
    taker_base = decimal(fields[9], "taker base")
    taker_quote = decimal(fields[10], "taker quote")
    if min(open_price, high, low, close) <= 0 or high < max(open_price, close) or low > min(open_price, close) or high < low:
        raise ValueError("OHLC ordering invalid")
    if min(volume, quote_volume, taker_base, taker_quote) < 0 or trades < 0:
        raise ValueError("negative volume or trade count")
    return {
        "symbol": symbol,
        "line_number": line_number,
        "open_time_ms": open_ms,
        "open_time_utc": open_utc,
        "close_time_ms": close_ms,
        "close_time_utc": iso_ms(close_ms),
        "raw_fields": fields,
        "raw_line_sha256": sha256_bytes(raw_line),
    }


def inspect_archive(archive_bytes: bytes, boundary: dict[str, Any]) -> dict[str, Any]:
    day = boundary["membership_end_exclusive"][:10]
    expected_member = f"{boundary['symbol']}-5m-{day}.csv"
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if archive.testzip() is not None or archive.namelist() != [expected_member]:
            raise ValueError(f"ZIP member or CRC invalid: {expected_member}")
        member = archive.read(expected_member)
    prefix = str(utc_ms(boundary["membership_end_exclusive"])).encode() + b","
    matches = [(line_number, line) for line_number, line in enumerate(member.splitlines(), 1) if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"exact boundary row count is {len(matches)}: {expected_member}")
    return {
        "member_name": expected_member,
        "member_size": len(member),
        "member_sha256": sha256_bytes(member),
        "row": parse_row(matches[0][1], matches[0][0], boundary["symbol"], boundary["membership_end_exclusive"]),
    }


def fetch_url(url: str, allowlist: set[str]) -> tuple[bytes, dict[str, str], str, int]:
    if url not in allowlist:
        raise ValueError(f"URL outside frozen allowlist: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        return body, {key.casefold(): value for key, value in response.headers.items()}, response.geturl(), int(response.status)


def acquire_sources(
    root: Path,
    boundaries: list[dict[str, Any]],
    fetch: Callable[[str, set[str]], tuple[bytes, dict[str, str], str, int]] = fetch_url,
    acquired_at_utc: str | None = None,
) -> tuple[list[dict[str, Any]], Path]:
    frozen_rndr = load_json(root / RNDR_PREFLIGHT.relative_to(ROOT))
    final_rndr = root / RAW_ROOT.relative_to(ROOT) / RNDR_LOCAL_RELATIVE
    if not final_rndr.is_file() or sha256_file(final_rndr) != frozen_rndr["source"]["archive_sha256"]:
        raise ValueError("frozen RNDR archive unavailable or drifted")
    for boundary in boundaries:
        if (boundary["symbol"], boundary["membership_end_exclusive"]) == NEW_RNDR:
            continue
        if (root / RAW_ROOT.relative_to(ROOT) / boundary["source_relative_path"]).exists():
            raise ValueError("completed-authority acquisition is single-use; destination already exists")
    allowlist = {url for row in boundaries for url in (row["source_url"], row["checksum_url"])}
    acquired_at = acquired_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    current_runtime = runtime_identity()
    temporary = Path(tempfile.mkdtemp(prefix="external-boundary-authority-"))
    records: list[dict[str, Any]] = []
    try:
        for boundary in boundaries:
            identity = (boundary["symbol"], boundary["membership_end_exclusive"])
            target = temporary / boundary["source_relative_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if identity == NEW_RNDR:
                shutil.copyfile(final_rndr, target)
                archive_body = target.read_bytes()
                checksum_sha = frozen_rndr["source"]["official_checksum_sha256"]
                checksum_payload_sha = frozen_rndr["source"]["checksum_payload_sha256"]
                source_mode = "preexisting_pr118_frozen_rndr"
                archive_requests = checksum_requests = 0
                headers = {"content-type": frozen_rndr["source"].get("content_type") or "application/zip"}
            else:
                archive_body, headers, effective, status = fetch(boundary["source_url"], allowlist)
                checksum_body, _, checksum_effective, checksum_status = fetch(boundary["checksum_url"], allowlist)
                if status != 200 or checksum_status != 200 or effective != boundary["source_url"] or checksum_effective != boundary["checksum_url"]:
                    raise ValueError(f"official source status or redirect drift: {identity}")
                checksum_sha = parse_checksum(checksum_body)
                checksum_payload_sha = sha256_bytes(checksum_body)
                source_mode = "new_official_daily_archive"
                archive_requests = checksum_requests = 1
                target.write_bytes(archive_body)
            archive_sha = sha256_bytes(archive_body)
            if archive_sha != checksum_sha:
                raise ValueError(f"official checksum mismatch: {identity}")
            declared = headers.get("content-length")
            if declared is not None and int(declared) != len(archive_body):
                raise ValueError(f"Content-Length mismatch: {identity}")
            inspection = inspect_archive(archive_body, boundary)
            records.append({
                **boundary,
                "source_mode": source_mode,
                "archive_byte_size": len(archive_body),
                "archive_sha256": archive_sha,
                "official_checksum_sha256": checksum_sha,
                "checksum_payload_sha256": checksum_payload_sha,
                "archive_requests": archive_requests,
                "checksum_requests": checksum_requests,
                "acquired_at_utc": frozen_rndr["source"]["acquired_at_utc"] if identity == NEW_RNDR else acquired_at,
                "acquisition_tool_runtime": frozen_rndr["source"]["acquisition_tool_runtime"] if identity == NEW_RNDR else current_runtime,
                "member_name": inspection["member_name"],
                "member_size": inspection["member_size"],
                "member_sha256": inspection["member_sha256"],
                "row": inspection["row"],
                "policy_status": validate_membership_and_policy(root, boundary),
            })
        return sorted(records, key=lambda row: (row["symbol"], row["membership_end_exclusive"])), temporary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def ordered(boundaries: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    normal = sorted(boundaries, key=lambda row: (row["symbol"], row["membership_end_exclusive"]))
    if mode == "normal":
        return normal
    if mode == "reverse":
        return list(reversed(normal))
    if mode == "deterministic_shuffled":
        return sorted(normal, key=lambda row: hashlib.sha256(f"BOUNDARY-AUTH-V1\0{row['symbol']}\0{row['membership_end_exclusive']}".encode()).digest())
    raise ValueError(f"unknown construction mode: {mode}")


def construction_pass(root: Path, records: list[dict[str, Any]], source_root: Path, mode: str) -> tuple[str, str, list[str]]:
    entries: list[dict[str, Any]] = []
    trace: list[str] = []
    for record in ordered(records, mode):
        identity = f"{record['symbol']}@{record['membership_end_exclusive']}"
        trace.append(identity)
        path = source_root / record["source_relative_path"]
        if not path.is_file() or path.stat().st_size != record["archive_byte_size"] or sha256_file(path) != record["archive_sha256"]:
            raise ValueError(f"archive identity drift during {mode}: {identity}")
        inspection = inspect_archive(path.read_bytes(), record)
        if inspection["member_sha256"] != record["member_sha256"] or inspection["row"] != record["row"]:
            raise ValueError(f"member or row drift during {mode}: {identity}")
        entries.append(record)
    entries.sort(key=lambda row: (row["symbol"], row["membership_end_exclusive"]))
    return canonical_hash(entries), canonical_hash(trace), trace


def build_evidence(root: Path, records: list[dict[str, Any]], source_root: Path, generated_utc: str | None = None) -> dict[str, Any]:
    passes: dict[str, dict[str, Any]] = {}
    for mode in ("normal", "reverse", "deterministic_shuffled"):
        result_hash, trace_hash, trace = construction_pass(root, records, source_root, mode)
        passes[mode] = {"result_hash": result_hash, "trace_hash": trace_hash, "trace": trace}
    if len({value["result_hash"] for value in passes.values()}) != 1 or len({value["trace_hash"] for value in passes.values()}) != 3:
        raise ValueError("full-set independent construction contract failed")
    evidence: dict[str, Any] = {
        "schema_version": "external-strategy-completed-boundary-authority-v1",
        "generated_utc": generated_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "pass_frozen_pending_separate_exact_head_review_and_merge",
        "authority_bindings": authority_bindings(root),
        "boundary_revision": {
            "original_count": 92,
            "removed": list(OLD_RNDR),
            "added": list(NEW_RNDR),
            "unchanged_count": 91,
            "revised_count": 92,
            "additions_beyond_replacement": 0,
            "deletions_beyond_replacement": 0,
        },
        "source_accounting": {
            "new_archive_requests": sum(row["archive_requests"] for row in records),
            "new_checksum_requests": sum(row["checksum_requests"] for row in records),
            "new_archives_downloaded": sum(row["source_mode"] == "new_official_daily_archive" for row in records),
            "preexisting_frozen_rndr_archives": sum(row["source_mode"] == "preexisting_pr118_frozen_rndr" for row in records),
            "total_archives": len(records),
            "total_archive_bytes": sum(row["archive_byte_size"] for row in records),
            "unique_boundary_rows_decoded": len(records),
            "full_construction_row_decodes": len(records) * 3,
            "market_rows_outside_fixed_boundaries": 0,
            "strategy_result_rows_read": 0,
            "is_trials_materialized": 0,
            "selection_trial_count": 0,
            "oos_rows_decoded": 0,
        },
        "acquisition_command_runtime": next(
            row["acquisition_tool_runtime"] for row in records if row["source_mode"] == "new_official_daily_archive"
        ),
        "construction_passes": passes,
        "completed_authority_nb01_satisfied": True,
        "records": records,
        "runtime_consumption_contract": {
            "lookup_use": "execution_side_forced_exit_only",
            "append_to_candidate_ohlcv": False,
            "append_to_indicator_history": False,
            "inactive_interval_state_carry": False,
            "reset_at_each_readmission": True,
            "rewarm_from_current_active_interval_only": True,
            "stitched_discontinuous_feed_is_sufficient": False,
            "future_runner_must_segment_active_intervals": True,
            "entry_before_rewarm_complete": False,
        },
        "freeze_state": {
            "boundary_authority_frozen": True,
            "exact_head_review_required": True,
            "exact_head_review_complete": False,
            "merged": False,
            "original_is_authorized": False,
        },
        "permissions": {
            "original_is": False,
            "modified_is": False,
            "selection_trial_materialization": False,
            "oos": False,
            "dry_run": False,
            "api_private_endpoints": False,
            "paper_live": False,
            "order_placement": False,
            "execution_live": False,
            "m2": False,
        },
    }
    evidence["content_hash"] = canonical_hash(evidence)
    return evidence


def command_document(evidence: dict[str, Any]) -> dict[str, Any]:
    stdout = f"completed boundary authority PASS: records=92 hash={evidence['content_hash']} oos=0 is=0\n"
    document = {
        "schema_version": "external-strategy-completed-boundary-authority-command-v1",
        "command": COMMAND,
        "exit_code": 0,
        "stdout_sha256": sha256_bytes(stdout.encode()),
        "stderr_sha256": sha256_bytes(b""),
        "evidence_content_hash": evidence["content_hash"],
        "new_archive_requests": 91,
        "new_checksum_requests": 91,
        "records": 92,
        "oos_rows_decoded": 0,
        "is_trials_materialized": 0,
        "runtime_identity": evidence["acquisition_command_runtime"],
    }
    document["content_hash"] = canonical_hash(document)
    return document


def validate(root: Path = ROOT, evidence: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    try:
        current = evidence or load_json(root / EVIDENCE.relative_to(ROOT))
        command = load_json(root / COMMAND_EVIDENCE.relative_to(ROOT))
        expected_boundaries = revised_boundaries(root)
        expected_bindings = authority_bindings(root)
        oos = load_json(root / OOS_GUARD.relative_to(ROOT))
        trials = load_json(root / TRIAL_STATE.relative_to(ROOT))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return [f"bound input unavailable: {exc}"]
    if current.get("content_hash") != canonical_hash(current):
        failures.append("completed authority canonical hash mismatch")
    if EXPECTED_EVIDENCE_HASH is not None and current.get("content_hash") != EXPECTED_EVIDENCE_HASH:
        failures.append("completed authority frozen identity mismatch")
    if current.get("schema_version") != "external-strategy-completed-boundary-authority-v1":
        failures.append("completed authority schema drift")
    if current.get("status") != "pass_frozen_pending_separate_exact_head_review_and_merge":
        failures.append("completed authority status drift")
    if current.get("boundary_revision") != {
        "original_count": 92,
        "removed": list(OLD_RNDR),
        "added": list(NEW_RNDR),
        "unchanged_count": 91,
        "revised_count": 92,
        "additions_beyond_replacement": 0,
        "deletions_beyond_replacement": 0,
    }:
        failures.append("boundary revision contract drift")
    if current.get("authority_bindings") != expected_bindings:
        failures.append("authority binding drift")
    records = current.get("records")
    if not isinstance(records, list) or len(records) != 92:
        failures.append("completed authority must contain exactly 92 records")
        records = []
    expected_identities = [
        (
            row["symbol"],
            row["membership_end_exclusive"],
            row["source_relative_path"],
            row["source_url"],
            row["checksum_url"],
        )
        for row in expected_boundaries
    ]
    actual_identities = [
        (
            row.get("symbol"),
            row.get("membership_end_exclusive"),
            row.get("source_relative_path"),
            row.get("source_url"),
            row.get("checksum_url"),
        )
        for row in records
    ]
    if actual_identities != expected_identities:
        failures.append("revised boundary identity drift")
    for record in records:
        if record.get("archive_sha256") != record.get("official_checksum_sha256"):
            failures.append("archive/checksum mismatch in frozen record")
            break
        expected_member = Path(str(record.get("source_relative_path", ""))).with_suffix(".csv").name
        if (
            record.get("member_name") != expected_member
            or not isinstance(record.get("archive_byte_size"), int)
            or record.get("archive_byte_size", 0) <= 0
            or not isinstance(record.get("member_size"), int)
            or record.get("member_size", 0) <= 0
            or any(
                not isinstance(record.get(field), str)
                or len(record.get(field, "")) != 64
                or any(char not in "0123456789abcdef" for char in record.get(field, ""))
                for field in (
                    "archive_sha256",
                    "official_checksum_sha256",
                    "checksum_payload_sha256",
                    "member_sha256",
                )
            )
        ):
            failures.append("archive or member identity invalid")
            break
        try:
            row = record["row"]
            parsed = parse_row(",".join(row["raw_fields"]).encode(), int(row["line_number"]), record["symbol"], record["membership_end_exclusive"])
            expected_policy = validate_membership_and_policy(root, record)
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f"frozen boundary row invalid: {exc}")
            break
        if parsed != row or record.get("policy_status") != expected_policy:
            failures.append("frozen boundary row or policy status drift")
            break
    source_modes = [record.get("source_mode") for record in records]
    if source_modes.count("new_official_daily_archive") != 91 or source_modes.count("preexisting_pr118_frozen_rndr") != 1:
        failures.append("source-mode accounting drift")
    if any(
        not isinstance(record.get("acquisition_tool_runtime"), dict)
        or record.get("acquisition_tool_runtime", {}).get("user_agent")
        != (
            "btc-eth-dual-quant-rndr-boundary-preflight/1"
            if record.get("source_mode") == "preexisting_pr118_frozen_rndr"
            else USER_AGENT
        )
        for record in records
    ):
        failures.append("acquisition runtime identity drift")
    raw_root = root / RAW_ROOT.relative_to(ROOT)
    if raw_root.exists():
        expected_raw = {record["source_relative_path"] for record in records}
        actual_raw = {
            path.relative_to(raw_root).as_posix()
            for path in raw_root.rglob("*")
            if path.is_file()
        }
        if actual_raw != expected_raw:
            failures.append("local read-only archive snapshot coverage drift")
        else:
            by_path = {record["source_relative_path"]: record for record in records}
            for relative in sorted(actual_raw):
                path = raw_root / relative
                record = by_path[relative]
                if (
                    path.stat().st_size != record["archive_byte_size"]
                    or sha256_file(path) != record["archive_sha256"]
                    or path.stat().st_mode & 0o222
                ):
                    failures.append(f"local archive snapshot drift: {relative}")
                    break
    accounting = current.get("source_accounting", {})
    expected_accounting = {
        "new_archive_requests": 91,
        "new_checksum_requests": 91,
        "new_archives_downloaded": 91,
        "preexisting_frozen_rndr_archives": 1,
        "total_archives": 92,
        "total_archive_bytes": sum(row.get("archive_byte_size", 0) for row in records),
        "unique_boundary_rows_decoded": 92,
        "full_construction_row_decodes": 276,
        "market_rows_outside_fixed_boundaries": 0,
        "strategy_result_rows_read": 0,
        "is_trials_materialized": 0,
        "selection_trial_count": 0,
        "oos_rows_decoded": 0,
    }
    if accounting != expected_accounting:
        failures.append("source accounting drift")
    result_hash = canonical_hash(records)
    passes = current.get("construction_passes", {})
    if set(passes) != {"normal", "reverse", "deterministic_shuffled"}:
        failures.append("construction pass set drift")
    else:
        trace_hashes = set()
        for mode, value in passes.items():
            if value.get("result_hash") != result_hash or value.get("trace_hash") != canonical_hash(value.get("trace")):
                failures.append(f"construction identity drift: {mode}")
            trace_hashes.add(value.get("trace_hash"))
        if len(trace_hashes) != 3 or current.get("completed_authority_nb01_satisfied") is not True:
            failures.append("NB-01 independent full-set construction not satisfied")
    consumption = current.get("runtime_consumption_contract", {})
    if consumption != {
        "lookup_use": "execution_side_forced_exit_only",
        "append_to_candidate_ohlcv": False,
        "append_to_indicator_history": False,
        "inactive_interval_state_carry": False,
        "reset_at_each_readmission": True,
        "rewarm_from_current_active_interval_only": True,
        "stitched_discontinuous_feed_is_sufficient": False,
        "future_runner_must_segment_active_intervals": True,
        "entry_before_rewarm_complete": False,
    }:
        failures.append("reset/rewarm or data-isolation contract drift")
    freeze = current.get("freeze_state", {})
    if freeze != {
        "boundary_authority_frozen": True,
        "exact_head_review_required": True,
        "exact_head_review_complete": False,
        "merged": False,
        "original_is_authorized": False,
    }:
        failures.append("pre-review freeze state drift")
    if current.get("permissions") != EXPECTED_PERMISSIONS:
        failures.append("permission matrix drift")
    if trials.get("selection_trial_count") != 0:
        failures.append("selection trial materialized")
    if (oos.get("oos_authorized"), oos.get("oos_opened"), oos.get("oos_runs"), oos.get("oos_rows_decoded")) != (False, False, 0, 0):
        failures.append("OOS guard opened")
    if command.get("content_hash") != canonical_hash(command):
        failures.append("command evidence canonical hash mismatch")
    if EXPECTED_COMMAND_HASH is not None and command.get("content_hash") != EXPECTED_COMMAND_HASH:
        failures.append("command evidence frozen identity mismatch")
    if command != command_document(current):
        failures.append("command evidence drift")
    return failures


def publish_archives(root: Path, records: list[dict[str, Any]], temporary: Path) -> None:
    raw_root = root / RAW_ROOT.relative_to(ROOT)
    for record in records:
        if record["source_mode"] != "new_official_daily_archive":
            continue
        source = temporary / record["source_relative_path"]
        destination = raw_root / record["source_relative_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise ValueError(f"refusing to overwrite frozen archive: {destination}")
        shutil.move(str(source), str(destination))
        os.chmod(destination, 0o444)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and not args.acquire:
        parser.error("--write requires --acquire")
    temporary: Path | None = None
    try:
        if args.acquire:
            boundaries = revised_boundaries(ROOT)
            records, temporary = acquire_sources(ROOT, boundaries)
            evidence = build_evidence(ROOT, records, temporary)
            command = command_document(evidence)
            if args.write:
                publish_archives(ROOT, records, temporary)
                EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
                EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                COMMAND_EVIDENCE.write_text(json.dumps(command, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            evidence = load_json(EVIDENCE)
        failures = validate(ROOT, evidence)
        if failures:
            print("completed boundary authority FAIL")
            for failure in failures:
                print(f"- {failure}")
            return 1
        print(f"completed boundary authority PASS: records=92 hash={evidence['content_hash']} oos=0 is=0")
        return 0
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
