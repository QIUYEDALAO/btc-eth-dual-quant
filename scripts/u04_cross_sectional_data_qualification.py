#!/usr/bin/env python3
"""Qualify frozen V4 authority without decoding research outcomes or OOS OHLC."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit"
MANIFEST_NAMES = (
    "V3_V4_diff", "active_universe_manifest", "candidate_eligibility_manifest",
    "complete_day_mask", "expected_grid_manifest", "invalid_interval_accounting_manifest",
    "invalid_interval_event_manifest", "invalid_interval_policy_manifest",
    "invalid_interval_slot_mask_manifest", "lifecycle_event_quarantine_manifest",
    "lifecycle_policy_manifest", "lifecycle_resolution_registry", "membership_manifest",
    "qualification_summary", "qualified_panel_manifest", "raw_row_quarantine_manifest",
    "row_conflict_resolution_manifest", "source_manifest", "symbol_availability_manifest",
)


class QualificationFailure(ValueError):
    """Fail-closed data qualification error."""


class SealedOOSAccess(QualificationFailure):
    """Raised before an OOS value can be decoded."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def identity_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def content_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise QualificationFailure(f"JSON root is not an object: {path}")
    return value


def utc_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise QualificationFailure("timestamp must be timezone-aware")
    return int(parsed.timestamp() * 1000)


def require_is_open_time(open_time_ms: int, contract: Mapping[str, Any]) -> None:
    start = utc_ms(str(contract["is_start"]))
    end = utc_ms(str(contract["is_end_exclusive"]))
    if not isinstance(open_time_ms, int) or isinstance(open_time_ms, bool):
        raise QualificationFailure("open time must be an integer millisecond timestamp")
    if open_time_ms < start:
        raise QualificationFailure("timestamp precedes frozen IS")
    if open_time_ms >= end:
        raise SealedOOSAccess("sealed OOS boundary reached before OHLC decode")


def _safe_archive_path(raw_root: Path, canonical_key: str) -> Path:
    key = PurePosixPath(canonical_key)
    if key.is_absolute() or ".." in key.parts or not canonical_key.endswith(".zip"):
        raise QualificationFailure(f"unsafe archive key: {canonical_key}")
    path = raw_root.joinpath(*key.parts)
    if not path.is_file():
        raise QualificationFailure(f"frozen archive missing: {canonical_key}")
    return path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_archive(raw_root: Path, binding: Mapping[str, Any]) -> dict[str, Any]:
    key = str(binding["canonical_key"])
    path = _safe_archive_path(raw_root, key)
    size = path.stat().st_size
    if size != binding["byte_size"]:
        raise QualificationFailure(f"archive size drift: {key}")
    if _file_sha256(path) != binding["sha256"]:
        raise QualificationFailure(f"archive SHA-256 drift: {key}")
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise QualificationFailure(f"archive CRC failure: {key}")
    except zipfile.BadZipFile as exc:
        raise QualificationFailure(f"invalid ZIP: {key}") from exc
    return {"canonical_key": key, "byte_size": size, "sha256": binding["sha256"]}


def ordered(values: Iterable[Mapping[str, Any]], order: str, seed: int) -> list[Mapping[str, Any]]:
    output = sorted(values, key=lambda item: str(item["canonical_key"]))
    if order == "reverse":
        output.reverse()
    elif order == "deterministic_shuffled":
        random.Random(seed).shuffle(output)
    elif order != "normal":
        raise QualificationFailure(f"unknown traversal order: {order}")
    return output


def _verify_manifest_hashes(config: Mapping[str, Any]) -> dict[str, str]:
    run = load_json(EVIDENCE / "requalification_run_manifest.json")
    expected = run["content"]["builds"]["cold"]["manifest_hashes"]
    hashes: dict[str, str] = {}
    for name in MANIFEST_NAMES:
        document = load_json(EVIDENCE / f"{name}.json")
        declared = document.get("content_hash")
        if name == "source_freeze_manifest":
            actual = identity_hash(document["content"])
        else:
            actual = content_hash(document)
        if declared != actual or expected.get(name) != actual:
            raise QualificationFailure(f"manifest hash drift: {name}")
        hashes[name] = actual
    audit = load_json(AUDIT / "audit_summary.json")
    if audit.get("verdict") != "pass" or audit.get("manifests_exact") != 19 or audit.get("manifests_total") != 19:
        raise QualificationFailure("ADR-0015 audit authority is not an exact pass")
    if audit.get("audit_summary_hash") != config["authority_bindings"]["adr0015_audit_summary_hash"]:
        raise QualificationFailure("audit summary authority drift")
    return hashes


def _verify_authority_content(config: Mapping[str, Any]) -> dict[str, int]:
    membership = load_json(EVIDENCE / "membership_manifest.json")["content"]
    grid = load_json(EVIDENCE / "expected_grid_manifest.json")["content"]
    panel = load_json(EVIDENCE / "qualified_panel_manifest.json")["content"]
    accounting = load_json(EVIDENCE / "invalid_interval_accounting_manifest.json")["content"]
    summary = load_json(EVIDENCE / "qualification_summary.json")["content"]
    gates = config["data_authority_gates"]
    if len(membership) != gates["membership_rows"]:
        raise QualificationFailure("membership row count drift")
    months: dict[str, set[str]] = {}
    for row in membership:
        month = str(row["effective_month"])[:7]
        if row.get("eligibility_status") != "qualified":
            continue
        symbols = months.setdefault(month, set())
        if row["symbol"] in symbols:
            raise QualificationFailure(f"duplicate membership: {month}:{row['symbol']}")
        symbols.add(str(row["symbol"]))
    if len(months) != gates["expected_months"] or any(len(values) != gates["monthly_members"] for values in months.values()):
        raise QualificationFailure("point-in-time membership cardinality drift")
    if any(
        row.get("errors")
        or int(row["actual_count"]) + int(row["missing_count"]) + int(row["invalid_interval_policy_masked_count"]) != int(row["expected_count"])
        for row in grid
    ):
        raise QualificationFailure("5m expected-grid accounting drift")
    if any(int(row["valid_1h_count"]) + int(row["quarantined_1h_count"]) != int(row["expected_1h_count"]) for row in panel):
        raise QualificationFailure("1h panel accounting drift")
    allowed_panel_status = {
        "clean", "global_window_quarantined", "symbol_month_quarantined",
        "synchronized_invalid_interval_quarantined",
    }
    if any(row.get("status") not in allowed_panel_status for row in panel):
        raise QualificationFailure("unknown qualified-panel status")
    expected_accounting = {
        "event_count": gates["invalid_interval_events"],
        "invalid_rows_quarantined": gates["invalid_physical_rows"],
        "valid_minority_rows_quarantined": gates["valid_minority_rows"],
        "total_rows_quarantined": gates["total_active_slots_masked"],
        "replacement_members": gates["replacement_members"],
        "synthetic_fills": gates["synthetic_fills"],
    }
    if any(accounting.get(key) != value for key, value in expected_accounting.items()):
        raise QualificationFailure("invalid-interval accounting drift")
    if summary.get("blockers") or summary.get("invalid_interval_policy_blockers") != 0:
        raise QualificationFailure("qualification blockers are non-zero")
    return {"membership_rows": len(membership), "months": len(months), "grid_rows": len(grid), "panel_rows": len(panel)}


def qualify(*, repository: Path, raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if content_hash(config) != config.get("content_hash"):
        raise QualificationFailure("qualification contract hash drift")
    protocol = load_json(repository / "config/u04_cross_sectional_paper_protocol_v1.json")
    review = load_json(repository / "reports/expert/evidence/u04_cross_sectional_paper_protocol_review_v1.json")
    if protocol.get("content_hash") != config["protocol_content_hash"] or review.get("review_content_hash") != config["protocol_review_content_hash"]:
        raise QualificationFailure("protocol or review binding drift")
    manifest_hashes = _verify_manifest_hashes(config)
    counts = _verify_authority_content(config)
    freeze = load_json(EVIDENCE / "source_freeze_manifest.json")
    if identity_hash(freeze["content"]) != config["authority_bindings"]["source_freeze_hash"]:
        raise QualificationFailure("source-freeze content drift")
    archives = freeze["content"]["archives"]
    if len(archives) != config["authority_bindings"]["source_archive_count"]:
        raise QualificationFailure("source archive count drift")
    source = config["source_verification"]
    verified = [verify_archive(raw_root, binding) for binding in ordered(archives, "normal", source["deterministic_shuffle_seed"])]
    order_rows = []
    for order in source["traversal_orders"]:
        traversal = ordered(verified, order, source["deterministic_shuffle_seed"])
        canonical = sorted(traversal, key=lambda item: (item["canonical_key"], item["sha256"], item["byte_size"]))
        order_rows.append({"order": order, "content_identity_hash": identity_hash(canonical), "archive_count": len(canonical)})
    if len({row["content_identity_hash"] for row in order_rows}) != 1:
        raise QualificationFailure("source traversal identity mismatch")
    result = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "pass",
        "contract_content_hash": config["content_hash"],
        "protocol_content_hash": config["protocol_content_hash"],
        "protocol_review_content_hash": config["protocol_review_content_hash"],
        "source_freeze_hash": config["authority_bindings"]["source_freeze_hash"],
        "v4_artifact_set_hash": config["authority_bindings"]["v4_artifact_set_hash"],
        "manifest_hashes": manifest_hashes,
        "orders": order_rows,
        "counts": {**counts, "archive_count": len(verified), "manifests_exact": len(manifest_hashes)},
        "isolation": {
            "is_start": config["isolation_contract"]["is_start"],
            "is_end_exclusive": config["isolation_contract"]["is_end_exclusive"],
            "oos_opened": False,
            "oos_archive_access": "opaque_identity_and_crc_only",
            "oos_ohlc_values_decoded": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "return_rows_generated": 0,
        },
        "authorizations": {
            "one_sealed_is_paper_observation": True,
            "event_scan_beyond_one_frozen_is_observation": False,
            "strategy": False, "backtesting": False, "oos": False,
            "api_trading": False, "execution_live": False, "m2": False,
        },
        "network_accessed": False,
        "production_evidence_mutated": False,
    }
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/u04_cross_sectional_data_qualification_v1.json")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u04_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(repository=ROOT, raw_root=args.raw_root, config=load_json(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"U-04 data qualification PASS archives={result['counts']['archive_count']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
