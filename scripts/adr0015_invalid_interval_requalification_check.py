#!/usr/bin/env python3
"""Validate ADR-0015 fixed-range requalification evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.data.invalid_interval_quarantine import ADR0015_MANIFEST_TYPES
from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from scripts.adr0015_invalid_interval_requalification import (
    EVIDENCE,
    REPORT,
    RUN_BINDINGS,
    RUNTIME_POLICY_HASH,
)
from scripts.liquid_universe_v4_requalification import REQUIRED_SOURCE_FREEZE_HASH


ALL_MANIFEST_TYPES = V4_MANIFEST_TYPES | set(ADR0015_MANIFEST_TYPES)


def _load_v4(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        raise ValueError(f"content hash mismatch: {path}")
    return document


def _load_policy_manifest(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    identity = {
        key: value for key, value in document.items()
        if key not in {"content_hash", "generated_utc"}
    }
    if document.get("content_hash") != canonical_hash(identity):
        raise ValueError(f"policy manifest content hash mismatch: {path}")
    return document


def check() -> dict:
    artifacts = {
        name: (_load_v4 if name in V4_MANIFEST_TYPES else _load_policy_manifest)(EVIDENCE / f"{name}.json")
        for name in ALL_MANIFEST_TYPES
    }
    run = _load_v4(EVIDENCE / "requalification_run_manifest.json")
    freeze = json.loads((EVIDENCE / "source_freeze_manifest.json").read_text(encoding="utf-8"))
    if freeze.get("content_hash") != canonical_hash(freeze.get("content")):
        raise ValueError("source freeze hash mismatch")
    if freeze.get("content_hash") != REQUIRED_SOURCE_FREEZE_HASH:
        raise ValueError("source freeze content hash drift")
    if freeze.get("content", {}).get("archive_count") != 27_736:
        raise ValueError("source freeze archive count drift")

    content = run["content"]
    summary = artifacts["qualification_summary"]["content"]
    if content.get("bindings") != RUN_BINDINGS:
        raise ValueError("requalification implementation binding drift")
    if content.get("range") != {"start": "2020-01", "end": "2026-06"}:
        raise ValueError("requalification range drift")
    if content.get("source_mode") != "frozen_local_only":
        raise ValueError("requalification source mode drift")
    if content.get("source_freeze_hash") != freeze["content_hash"]:
        raise ValueError("run/source freeze mismatch")
    if content.get("status") != summary.get("status"):
        raise ValueError("run/summary status mismatch")
    if summary.get("expected_months") != 78 or summary.get("membership_rows") != 1170:
        raise ValueError("month or membership coverage drift")

    required_zero = (
        "processing_errors", "unresolved_row_conflicts", "unresolved_lifecycle_rows",
        "epoch_overlaps", "unresolved_gaps", "excluded_category_members",
        "synthetic_fills", "replacement_members", "stale_prices",
        "membership_replacements_after_lifecycle", "invalid_interval_policy_blockers",
    )
    if summary["status"] == "pass":
        if any(summary.get(field) != 0 for field in required_zero):
            raise ValueError("pass evidence contains blocker")
        if content.get("builds_completed") != ["cold", "warm", "worker"]:
            raise ValueError("pass requires ordered cold/warm/worker builds")
        if content.get("determinism_status") != "pass" or content.get("deterministic_mismatches") != 0:
            raise ValueError("pass requires deterministic equality")
    elif summary["status"] == "blocked":
        if content.get("builds_completed") != ["cold"] or not content.get("stop_reasons"):
            raise ValueError("blocked evidence must stop truthfully after cold")
    else:
        raise ValueError("unsupported requalification status")

    for record in content["builds"].values():
        if set(record["manifest_hashes"]) != ALL_MANIFEST_TYPES:
            raise ValueError("build manifest inventory drift")
        for name in ALL_MANIFEST_TYPES:
            if record["manifest_hashes"][name] != artifacts[name]["content_hash"]:
                raise ValueError(f"build manifest mismatch: {name}")
    if len({record["artifact_set_hash"] for record in content["builds"].values()}) != 1:
        raise ValueError("build artifact sets differ")

    policy = artifacts["invalid_interval_policy_manifest"]
    accounting = artifacts["invalid_interval_accounting_manifest"]["content"]
    events = artifacts["invalid_interval_event_manifest"]["content"]
    masks = artifacts["invalid_interval_slot_mask_manifest"]["content"]
    if policy.get("policy_canonical_hash") != RUNTIME_POLICY_HASH:
        raise ValueError("runtime policy binding drift")
    if any(accounting.get("blockers", [])):
        raise ValueError("invalid-interval accounting contains blockers")
    if summary["status"] == "pass":
        if len(events) != 8 or accounting.get("event_count") != 8:
            raise ValueError("expected eight synchronized invalid-interval events")
        if accounting.get("invalid_rows_quarantined") != 119:
            raise ValueError("invalid physical-row accounting drift")
        if accounting.get("total_rows_quarantined") != len(masks):
            raise ValueError("slot-mask accounting mismatch")
        if accounting.get("invalid_rows_quarantined", 0) + accounting.get("valid_minority_rows_quarantined", 0) != len(masks):
            raise ValueError("invalid/minority accounting mismatch")
        if any(event["invalid_count"] < 2 or event["invalid_count"] * 5 < len(event["active_members"]) * 4 for event in events):
            raise ValueError("event threshold drift")
        if sum(len(event["active_members"]) for event in events) != len(masks):
            raise ValueError("full active-slot mask mismatch")

    if any(summary.get("authorizations", {}).values()) or any(content.get("authorizations", {}).values()):
        raise ValueError("requalification cannot authorize downstream work")
    report_hash = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    if {record.get("qualification_report_sha256") for record in content["builds"].values()} != {report_hash}:
        raise ValueError("report/run-manifest binding mismatch")
    return {"status": summary["status"], "content_hash": run["content_hash"]}


def main() -> int:
    result = check()
    print(f"ADR-0015 requalification check PASS status={result['status']} hash={result['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
