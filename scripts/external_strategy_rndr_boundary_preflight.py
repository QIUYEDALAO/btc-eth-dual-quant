#!/usr/bin/env python3
"""Result-blind, RNDR-only official archive and exact-row preflight.

This stage intentionally acquires one archive only.  It does not construct the
completed 92-boundary authority and it never exposes the row to strategy OHLCV.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "config/adr0018_scheduled_market_cessation_forced_exit_v1.json"
PR117_REVIEW = ROOT / "reports/expert/evidence/pr117_exact_head_review_v1.json"
MEMBERSHIP = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/membership_manifest.json"
LIFECYCLE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/lifecycle_resolution_registry.json"
INVALID_POLICY = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_policy_manifest.json"
INVALID_EVENTS = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_event_manifest.json"
INVALID_MASK = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_slot_mask_manifest.json"
OOS_GUARD = ROOT / "config/external_strategy_oos_guard_v1.json"
TRIAL_STATE = ROOT / "config/external_strategy_candidate_freeze_v1.json"

EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/rndr_original_symbol_preflight.json"
COMMAND_EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/rndr_original_symbol_preflight_command.json"
LOCAL_ARCHIVE = ROOT / "storage/raw/external_strategy_boundary_authority/data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-07-22.zip"

ARCHIVE_URL = "https://data.binance.vision/data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-07-22.zip"
CHECKSUM_URL = ARCHIVE_URL + ".CHECKSUM"
MEMBER_NAME = "RNDRUSDT-5m-2024-07-22.csv"
TARGET_OPEN_MS = 1721616900000
TARGET_CLOSE_MS = 1721617199999
TARGET_OPEN_UTC = "2024-07-22T02:55:00Z"
TARGET_CLOSE_UTC = "2024-07-22T02:59:59.999Z"
OOS_START_MS = 1726012800000

ADR_HASH = "8761fabac1f32d518d6c75c08dcf0a37288262059fe3192b87fb44de836b46e9"
PR117_HEAD = "bb22a08cc7bcd31c458ca7d362e536d88c0ca1e2"
PR117_REVIEW_HASH = "41f4360976a3b2dff2408bf3262fff548b23b3bf1460314d3c8882c1e9ad780f"
PR117_GATE_RUN = 29871317869
PR117_MERGE = "336563c67a6b23cc9ebbf91c7abd007db0df048b"
MEMBERSHIP_HASH = "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5"
LIFECYCLE_HASH = "adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef"
INVALID_POLICY_HASH = "8c2efd2f2598d851523cfc54ad361d7ab3639558b821fcec2e04fbb4a83fabc7"
INVALID_EVENTS_HASH = "8a4e022a9c837b1fb9d4fe7539b7e9c45605660d605e2dcdf71fff0ac34103a6"
INVALID_MASK_HASH = "23e78e15a4484af9167b03e29bf9d499a39ff1e1c8195a056fae72b984285487"

# Frozen after the single authorized acquisition.  CI validates these values
# without reacquiring the archive or reading any additional market row.
EXPECTED_EVIDENCE_HASH: str | None = "eceafea174381268c22df88b3262a3702a828a3aac079b8e060000686c9b38be"
EXPECTED_COMMAND_HASH: str | None = "cf3d7f83730ca93b5df679806cf87f47ee3b3b485f38073779854632d4e72d1f"
EXPECTED_ARCHIVE_SHA256: str | None = "e2da006ea431071e7eb1796dddaa72da8646f57ba1ecf75e0127c6e769491587"
EXPECTED_ARCHIVE_SIZE: int | None = 1720
EXPECTED_MEMBER_SHA256: str | None = "b321e6a21cc704ca8535e35f964f693c7b380482115448692dbffc0386e5f72c"
EXPECTED_ROW_SHA256: str | None = "89be4f1712abbe2ffe08277e6ac6cafbe28666513734be5595afc0a10dfe4f50"

COMMAND = "python3 scripts/external_strategy_rndr_boundary_preflight.py --acquire --write"
USER_AGENT = "btc-eth-dual-quant-rndr-boundary-preflight/1"


@dataclass(frozen=True)
class FetchResult:
    url: str
    effective_url: str
    status: int
    body: bytes
    headers: dict[str, str]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return sha256_bytes(encoded)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def official_fetch(url: str) -> FetchResult:
    if url not in {ARCHIVE_URL, CHECKSUM_URL}:
        raise ValueError(f"URL outside RNDR-only allowlist: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return FetchResult(
            url=url,
            effective_url=response.geturl(),
            status=int(response.status),
            body=response.read(),
            headers={key.casefold(): value for key, value in response.headers.items()},
        )


def parse_checksum(body: bytes) -> str:
    parts = body.decode("utf-8").strip().split()
    if len(parts) < 1 or len(parts[0]) != 64 or any(char not in "0123456789abcdefABCDEF" for char in parts[0]):
        raise ValueError("official checksum payload invalid")
    return parts[0].casefold()


def _ordered(lines: list[tuple[int, bytes]], mode: str) -> list[tuple[int, bytes]]:
    if mode == "normal":
        return list(lines)
    if mode == "reverse":
        return list(reversed(lines))
    if mode == "deterministic_shuffled":
        return sorted(lines, key=lambda item: hashlib.sha256(b"RNDR-PREFLIGHT-V1\0" + item[1]).digest())
    raise ValueError(f"unknown construction order: {mode}")


def _decimal(value: str, label: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{label} is not finite")
    return result


def parse_target_row(raw_line: bytes, line_number: int) -> dict[str, Any]:
    try:
        fields = next(csv.reader([raw_line.decode("utf-8")]))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("target row is not valid UTF-8 CSV") from exc
    if len(fields) != 12:
        raise ValueError("target row must have exactly 12 fields")
    try:
        open_ms = int(fields[0])
        close_ms = int(fields[6])
        trades = int(fields[8])
    except ValueError as exc:
        raise ValueError("target timestamp or trade count invalid") from exc
    if open_ms != TARGET_OPEN_MS or close_ms != TARGET_CLOSE_MS:
        raise ValueError("target row time mismatch")
    if close_ms - open_ms != 299999:
        raise ValueError("target row close delta mismatch")
    if open_ms >= OOS_START_MS:
        raise ValueError("target row crosses sealed OOS")
    open_price = _decimal(fields[1], "open")
    high = _decimal(fields[2], "high")
    low = _decimal(fields[3], "low")
    close = _decimal(fields[4], "close")
    volume = _decimal(fields[5], "volume")
    quote_volume = _decimal(fields[7], "quote volume")
    taker_base = _decimal(fields[9], "taker base volume")
    taker_quote = _decimal(fields[10], "taker quote volume")
    if min(open_price, high, low, close) <= 0:
        raise ValueError("OHLC must be positive")
    if high < max(open_price, close) or low > min(open_price, close) or high < low:
        raise ValueError("OHLC ordering invalid")
    if min(volume, quote_volume, taker_base, taker_quote) < 0 or trades < 0:
        raise ValueError("volume or trade count negative")
    return {
        "symbol": "RNDRUSDT",
        "interval": "5m",
        "line_number": line_number,
        "open_time_ms": open_ms,
        "open_time_utc": TARGET_OPEN_UTC,
        "close_time_ms": close_ms,
        "close_time_utc": TARGET_CLOSE_UTC,
        "raw_fields": fields,
        "raw_line_sha256": sha256_bytes(raw_line),
    }


def extract_target(member_bytes: bytes, mode: str) -> tuple[dict[str, Any], str]:
    lines = [(index, line) for index, line in enumerate(member_bytes.splitlines(), start=1) if line]
    ordered = _ordered(lines, mode)
    prefix = str(TARGET_OPEN_MS).encode() + b","
    matches = [(index, line) for index, line in ordered if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"expected one exact target row, found {len(matches)}")
    trace = sha256_bytes(json.dumps([index for index, _ in ordered], separators=(",", ":")).encode())
    return parse_target_row(matches[0][1], matches[0][0]), trace


def inspect_archive(archive_bytes: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC validation failed")
        names = archive.namelist()
        if names != [MEMBER_NAME]:
            raise ValueError(f"unexpected ZIP members: {names}")
        member_bytes = archive.read(MEMBER_NAME)
    results: dict[str, dict[str, Any]] = {}
    traces: dict[str, str] = {}
    for mode in ("normal", "reverse", "deterministic_shuffled"):
        row, trace = extract_target(member_bytes, mode)
        results[mode] = row
        traces[mode] = trace
    result_hashes = {mode: canonical_hash(row) for mode, row in results.items()}
    if len(set(result_hashes.values())) != 1:
        raise ValueError("RNDR target row order inconsistency")
    if len(set(traces.values())) != 3:
        raise ValueError("RNDR target row traversals were not independently ordered")
    return {
        "member_name": MEMBER_NAME,
        "member_size": len(member_bytes),
        "member_sha256": sha256_bytes(member_bytes),
        "row": results["normal"],
        "construction_result_hashes": result_hashes,
        "construction_trace_hashes": traces,
    }


def authority_bindings(root: Path = ROOT) -> dict[str, Any]:
    adr = load_json(root / ADR.relative_to(ROOT))
    review = load_json(root / PR117_REVIEW.relative_to(ROOT))
    membership = load_json(root / MEMBERSHIP.relative_to(ROOT))
    lifecycle = load_json(root / LIFECYCLE.relative_to(ROOT))
    invalid_policy = load_json(root / INVALID_POLICY.relative_to(ROOT))
    invalid_events = load_json(root / INVALID_EVENTS.relative_to(ROOT))
    invalid_mask = load_json(root / INVALID_MASK.relative_to(ROOT))
    if adr.get("content_hash") != ADR_HASH:
        raise ValueError("ADR-0018 identity drift")
    if review.get("content_hash") != PR117_REVIEW_HASH or review.get("reviewed_head") != PR117_HEAD:
        raise ValueError("PR #117 exact-head review drift")
    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0:
        raise ValueError("PR #117 review no longer approves 0/0")
    exact_hashes = (
        (membership, MEMBERSHIP_HASH, "membership"),
        (lifecycle, LIFECYCLE_HASH, "lifecycle"),
        (invalid_policy, INVALID_POLICY_HASH, "invalid policy"),
        (invalid_events, INVALID_EVENTS_HASH, "invalid events"),
        (invalid_mask, INVALID_MASK_HASH, "invalid mask"),
    )
    for document, expected, label in exact_hashes:
        if document.get("content_hash") != expected:
            raise ValueError(f"{label} identity drift")
    member_rows = [
        row for row in membership.get("content", [])
        if row.get("symbol") == "RNDRUSDT" and row.get("effective_month") == "2024-07-01"
    ]
    if len(member_rows) != 1 or member_rows[0].get("eligibility_status") != "qualified" or member_rows[0].get("rank") != 15:
        raise ValueError("RNDR July 2024 membership authority invalid")
    conflicts = [row for row in lifecycle.get("content", {}).get("entries", []) if row.get("symbol") == "RNDRUSDT"]
    if conflicts:
        raise ValueError("prior lifecycle registry conflicts with ADR-0018")
    masked = [
        row for row in invalid_mask.get("content", [])
        if row.get("symbol") == "RNDRUSDT" and row.get("open_time_ms") == TARGET_OPEN_MS
    ]
    events = [row for row in invalid_events.get("content", []) if row.get("open_time_ms") == TARGET_OPEN_MS]
    if masked or events:
        raise ValueError("RNDR forced-exit row is covered by invalid-interval authority")
    return {
        "adr0018_hash": ADR_HASH,
        "pr117_reviewed_head": PR117_HEAD,
        "pr117_review_hash": PR117_REVIEW_HASH,
        "pr117_gate_run": PR117_GATE_RUN,
        "pr117_merge_commit": PR117_MERGE,
        "membership_hash": MEMBERSHIP_HASH,
        "membership_row": member_rows[0],
        "lifecycle_registry_hash": LIFECYCLE_HASH,
        "lifecycle_authority": "ADR-0018-SCHEDULED-MARKET-CESSATION-FORCED-EXIT",
        "invalid_interval_policy_hash": INVALID_POLICY_HASH,
        "invalid_interval_event_hash": INVALID_EVENTS_HASH,
        "invalid_interval_mask_hash": INVALID_MASK_HASH,
        "target_masked": False,
    }


def build_evidence(
    archive: FetchResult,
    checksum: FetchResult,
    *,
    root: Path = ROOT,
    generated_utc: str | None = None,
    acquired_at_utc: str | None = None,
) -> dict[str, Any]:
    if archive.url != ARCHIVE_URL or checksum.url != CHECKSUM_URL:
        raise ValueError("source URL outside fixed RNDR pair")
    if archive.status != 200 or checksum.status != 200:
        raise ValueError("official RNDR archive or checksum is unavailable")
    if archive.effective_url != ARCHIVE_URL or checksum.effective_url != CHECKSUM_URL:
        raise ValueError("official source redirected outside exact URL")
    archive_sha = sha256_bytes(archive.body)
    official_sha = parse_checksum(checksum.body)
    if archive_sha != official_sha:
        raise ValueError("archive hash differs from official checksum")
    declared_length = archive.headers.get("content-length")
    if declared_length is not None and int(declared_length) != len(archive.body):
        raise ValueError("archive Content-Length mismatch")
    inspection = inspect_archive(archive.body)
    generation_time = generated_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    acquisition_time = acquired_at_utc or generation_time
    evidence: dict[str, Any] = {
        "schema_version": "external-strategy-rndr-boundary-preflight-v1",
        "generated_utc": generation_time,
        "status": "pass_rndr_original_symbol_archive_and_exact_row",
        "scope": "single_result_blind_rndr_original_symbol_preflight_only",
        "authority_bindings": authority_bindings(root),
        "source": {
            "archive_url": ARCHIVE_URL,
            "checksum_url": CHECKSUM_URL,
            "effective_archive_url": archive.effective_url,
            "effective_checksum_url": checksum.effective_url,
            "archive_http_status": archive.status,
            "checksum_http_status": checksum.status,
            "archive_byte_size": len(archive.body),
            "archive_sha256": archive_sha,
            "official_checksum_sha256": official_sha,
            "checksum_payload_sha256": sha256_bytes(checksum.body),
            "content_type": archive.headers.get("content-type"),
            "etag": archive.headers.get("etag"),
            "last_modified": archive.headers.get("last-modified"),
            "local_archive_path": str(LOCAL_ARCHIVE.relative_to(ROOT)),
            "acquired_at_utc": acquisition_time,
            "acquisition_tool_runtime": {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "user_agent": USER_AGENT,
            },
        },
        "archive": {
            "member_count": 1,
            "member_name": inspection["member_name"],
            "member_size": inspection["member_size"],
            "member_sha256": inspection["member_sha256"],
        },
        "exact_row": inspection["row"],
        "construction_result_hashes": inspection["construction_result_hashes"],
        "construction_trace_hashes": inspection["construction_trace_hashes"],
        "construction_passes_executed": 3,
        "completed_authority_nb01_satisfied": False,
        "completed_authority_nb01_status": "deferred_until_all_92_sources_are_separately_constructed",
        "isolation": {
            "forced_exit_lookup_only": True,
            "appended_to_candidate_ohlcv": False,
            "appended_to_indicator_history": False,
            "other_91_archives_requested": 0,
            "other_91_archives_downloaded": 0,
            "archive_requests": 1,
            "checksum_requests": 1,
            "market_rows_decoded": 1,
            "market_rows_outside_fixed_boundary": 0,
            "strategy_result_rows_read": 0,
            "is_trials_materialized": 0,
            "selection_trial_count": 0,
            "oos_rows_decoded": 0,
        },
        "next_stage": {
            "later_full_authority_acquisition_eligible": True,
            "later_full_authority_acquisition_executed": False,
            "boundary_authority_frozen": False,
            "original_is_authorized": False,
            "separate_completed_authority_exact_head_review_required": True,
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
    stdout = (
        "RNDR original-symbol boundary preflight PASS: "
        f"{evidence['content_hash']} archive={evidence['source']['archive_sha256']} "
        f"row={evidence['exact_row']['raw_line_sha256']} oos=0\n"
    )
    document = {
        "schema_version": "external-strategy-rndr-boundary-preflight-command-v1",
        "command": COMMAND,
        "exit_code": 0,
        "stdout_sha256": sha256_bytes(stdout.encode()),
        "stderr_sha256": sha256_bytes(b""),
        "evidence_content_hash": evidence["content_hash"],
        "archive_requests": 1,
        "checksum_requests": 1,
        "other_91_archives_requested": 0,
        "market_rows_decoded": 1,
        "oos_rows_decoded": 0,
    }
    document["content_hash"] = canonical_hash(document)
    return document


def validate(root: Path = ROOT, evidence: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    try:
        current = evidence or load_json(root / EVIDENCE.relative_to(ROOT))
        command = load_json(root / COMMAND_EVIDENCE.relative_to(ROOT))
        expected_bindings = authority_bindings(root)
        oos = load_json(root / OOS_GUARD.relative_to(ROOT))
        trial = load_json(root / TRIAL_STATE.relative_to(ROOT))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return [f"bound evidence unavailable: {exc}"]
    if current.get("content_hash") != canonical_hash(current):
        failures.append("RNDR preflight canonical hash mismatch")
    if EXPECTED_EVIDENCE_HASH is not None and current.get("content_hash") != EXPECTED_EVIDENCE_HASH:
        failures.append("RNDR preflight frozen identity mismatch")
    if current.get("authority_bindings") != expected_bindings:
        failures.append("RNDR preflight authority binding drift")
    source = current.get("source", {})
    exact_expected = {
        "archive_url": ARCHIVE_URL,
        "checksum_url": CHECKSUM_URL,
        "archive_http_status": 200,
        "checksum_http_status": 200,
    }
    for key, expected in exact_expected.items():
        if source.get(key) != expected:
            failures.append(f"RNDR source drift: {key}")
    if EXPECTED_ARCHIVE_SHA256 is not None and source.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256:
        failures.append("RNDR archive hash drift")
    if EXPECTED_ARCHIVE_SIZE is not None and source.get("archive_byte_size") != EXPECTED_ARCHIVE_SIZE:
        failures.append("RNDR archive size drift")
    archive = current.get("archive", {})
    if archive.get("member_name") != MEMBER_NAME or archive.get("member_count") != 1:
        failures.append("RNDR ZIP member identity drift")
    if EXPECTED_MEMBER_SHA256 is not None and archive.get("member_sha256") != EXPECTED_MEMBER_SHA256:
        failures.append("RNDR member hash drift")
    row = current.get("exact_row", {})
    if row.get("open_time_ms") != TARGET_OPEN_MS or row.get("close_time_ms") != TARGET_CLOSE_MS:
        failures.append("RNDR exact row timestamp drift")
    if row.get("open_time_utc") != TARGET_OPEN_UTC or row.get("close_time_utc") != TARGET_CLOSE_UTC:
        failures.append("RNDR exact row UTC drift")
    if EXPECTED_ROW_SHA256 is not None and row.get("raw_line_sha256") != EXPECTED_ROW_SHA256:
        failures.append("RNDR exact row hash drift")
    try:
        reparsed = parse_target_row(",".join(row.get("raw_fields", [])).encode(), int(row.get("line_number", 0)))
    except (TypeError, ValueError) as exc:
        failures.append(f"RNDR exact row invalid: {exc}")
    else:
        if reparsed != row:
            failures.append("RNDR exact row normalized identity drift")
    result_hashes = current.get("construction_result_hashes", {})
    trace_hashes = current.get("construction_trace_hashes", {})
    if set(result_hashes) != {"normal", "reverse", "deterministic_shuffled"} or len(set(result_hashes.values())) != 1:
        failures.append("RNDR traversal result inconsistency")
    if set(trace_hashes) != {"normal", "reverse", "deterministic_shuffled"} or len(set(trace_hashes.values())) != 3:
        failures.append("RNDR traversal traces are not distinct")
    isolation = current.get("isolation", {})
    exact_isolation = {
        "forced_exit_lookup_only": True,
        "appended_to_candidate_ohlcv": False,
        "appended_to_indicator_history": False,
        "other_91_archives_requested": 0,
        "other_91_archives_downloaded": 0,
        "archive_requests": 1,
        "checksum_requests": 1,
        "market_rows_decoded": 1,
        "market_rows_outside_fixed_boundary": 0,
        "strategy_result_rows_read": 0,
        "is_trials_materialized": 0,
        "selection_trial_count": 0,
        "oos_rows_decoded": 0,
    }
    if isolation != exact_isolation:
        failures.append("RNDR preflight isolation accounting drift")
    if current.get("completed_authority_nb01_satisfied") is not False:
        failures.append("single-row preflight falsely claims completed-authority NB-01")
    next_stage = current.get("next_stage", {})
    if next_stage.get("boundary_authority_frozen") is not False or next_stage.get("original_is_authorized") is not False:
        failures.append("RNDR preflight escalated authority")
    if any(current.get("permissions", {}).values()):
        failures.append("RNDR preflight enabled forbidden permission")
    if trial.get("selection_trial_count") != 0:
        failures.append("selection trial materialized during RNDR preflight")
    if (oos.get("oos_authorized"), oos.get("oos_opened"), oos.get("oos_runs"), oos.get("oos_rows_decoded")) != (False, False, 0, 0):
        failures.append("OOS guard opened during RNDR preflight")
    if command.get("content_hash") != canonical_hash(command):
        failures.append("RNDR command evidence canonical hash mismatch")
    if EXPECTED_COMMAND_HASH is not None and command.get("content_hash") != EXPECTED_COMMAND_HASH:
        failures.append("RNDR command evidence frozen identity mismatch")
    expected_command = command_document(current)
    if command != expected_command:
        failures.append("RNDR command evidence drift")
    return failures


def acquire(fetch: Callable[[str], FetchResult] = official_fetch) -> tuple[FetchResult, FetchResult]:
    requested: list[str] = []

    def guarded(url: str) -> FetchResult:
        if url not in {ARCHIVE_URL, CHECKSUM_URL}:
            raise ValueError("request outside fixed RNDR-only source pair")
        requested.append(url)
        return fetch(url)

    archive = guarded(ARCHIVE_URL)
    checksum = guarded(CHECKSUM_URL)
    if requested != [ARCHIVE_URL, CHECKSUM_URL]:
        raise ValueError("RNDR acquisition request sequence drift")
    return archive, checksum


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and not args.acquire:
        parser.error("--write requires --acquire")
    if args.acquire:
        archive, checksum = acquire()
        evidence = build_evidence(archive, checksum)
        command = command_document(evidence)
        if args.write:
            LOCAL_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
            LOCAL_ARCHIVE.write_bytes(archive.body)
            EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
            EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            COMMAND_EVIDENCE.write_text(json.dumps(command, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        evidence = load_json(EVIDENCE)
    failures = validate(ROOT, evidence)
    if failures:
        print("RNDR original-symbol boundary preflight FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "RNDR original-symbol boundary preflight PASS: "
        f"{evidence['content_hash']} archive={evidence['source']['archive_sha256']} "
        f"row={evidence['exact_row']['raw_line_sha256']} oos=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
