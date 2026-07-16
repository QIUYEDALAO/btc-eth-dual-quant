#!/usr/bin/env python3
"""Validate committed fixed-range V4 public requalification evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from btc_eth_dual_quant.data.liquid_universe import canonical_hash


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4"
REQUIRED_SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"


def _load_v4(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        raise ValueError(f"content hash mismatch: {path}")
    return document


def check() -> dict:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v4.json").read_text())
    lifecycle = json.loads((ROOT / "config/liquid_spot_lifecycle_event_resolutions_v4.json").read_text())
    artifacts = {name: _load_v4(EVIDENCE / f"{name}.json") for name in V4_MANIFEST_TYPES}
    for name, document in artifacts.items():
        if document.get("schema_version") != 4 or document.get("manifest_type") != name:
            raise ValueError(f"V4 manifest identity mismatch: {name}")
        if document.get("contract_hash") != contract["canonical_hash"]:
            raise ValueError(f"V4 contract binding mismatch: {name}")
        if document.get("lifecycle_registry_hash") != lifecycle["canonical_hash"]:
            raise ValueError(f"V4 lifecycle binding mismatch: {name}")

    run = _load_v4(EVIDENCE / "requalification_run_manifest.json")
    freeze = json.loads((EVIDENCE / "source_freeze_manifest.json").read_text())
    if freeze.get("content_hash") != canonical_hash(freeze.get("content")):
        raise ValueError("source freeze hash mismatch")
    if freeze.get("content_hash") != REQUIRED_SOURCE_FREEZE_HASH:
        raise ValueError("source freeze content hash drift")
    if freeze.get("content", {}).get("archive_count") != 27_736:
        raise ValueError("source freeze archive count drift")
    content = run["content"]
    summary = artifacts["qualification_summary"]["content"]
    if content["range"] != {"start": "2020-01", "end": "2026-06"}:
        raise ValueError("V4 frozen range mismatch")
    if content.get("source_mode") != "frozen_local_only":
        raise ValueError("V4 requalification must use only frozen local sources")
    if content["source_freeze_hash"] != freeze["content_hash"]:
        raise ValueError("run/source freeze mismatch")
    if content["status"] != summary["status"]:
        raise ValueError("run/summary status mismatch")
    if summary["expected_months"] != 78 or summary["membership_rows"] != 1170:
        raise ValueError("V4 month or membership coverage mismatch")
    required_zero = (
        "processing_errors", "unresolved_row_conflicts", "unresolved_lifecycle_rows",
        "epoch_overlaps", "unresolved_gaps", "excluded_category_members",
        "synthetic_fills", "replacement_members", "stale_prices",
        "membership_replacements_after_lifecycle",
    )
    if summary["status"] == "pass":
        if any(summary[field] != 0 for field in required_zero):
            raise ValueError("V4 pass evidence contains blocker")
        if set(content["builds_completed"]) != {"cold", "warm", "worker"}:
            raise ValueError("V4 pass requires cold/warm/worker")
        if content["determinism_status"] != "pass" or content["deterministic_mismatches"] != 0:
            raise ValueError("V4 pass requires deterministic equality")
        artifact_sets = {record["artifact_set_hash"] for record in content["builds"].values()}
        if len(artifact_sets) != 1:
            raise ValueError("V4 build artifact sets differ")
        for name in V4_MANIFEST_TYPES:
            hashes = {record["manifest_hashes"][name] for record in content["builds"].values()}
            if hashes != {artifacts[name]["content_hash"]}:
                raise ValueError(f"V4 build manifest mismatch: {name}")
    else:
        if content["builds_completed"] != ["cold"] or not content["stop_reasons"]:
            raise ValueError("blocked V4 evidence must stop truthfully after cold")
    if any(summary["authorizations"].values()) or any(content["authorizations"].values()):
        raise ValueError("V4 requalification cannot authorize downstream work")
    if summary["lifecycle_event_count"] != 1 or summary["partial_lifecycle_days"] != 1:
        raise ValueError("KLAY lifecycle evidence count mismatch")
    if summary["post_cessation_rows_quarantined"] != 3:
        raise ValueError("KLAY post-cessation quarantine mismatch")
    if len(artifacts["raw_row_quarantine_manifest"]["content"]) != 4:
        raise ValueError("all four physical KLAY raw rows must remain quarantined")
    diff = artifacts["V3_V4_diff"]["content"]
    if diff["v3_mutated"] or diff["v3_status"] != "blocked" or diff["v4_status"] != summary["status"]:
        raise ValueError("V3/V4 authority diff mismatch")
    report = (ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md").read_text()
    for marker in (f"- Status: {summary['status']}", "- Determinism: pass", "- M2 authorized: no"):
        if marker not in report:
            raise ValueError(f"V4 report marker missing: {marker}")
    report_sha256 = hashlib.sha256(
        (ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md").read_bytes()
    ).hexdigest()
    bindings = {record.get("qualification_report_sha256") for record in content["builds"].values()}
    if bindings != {report_sha256}:
        raise ValueError("V4 qualification report/run-manifest binding mismatch")
    return {"status": summary["status"], "content_hash": run["content_hash"]}


def main() -> int:
    result = check()
    print(f"V4 requalification check PASS status={result['status']} hash={result['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
