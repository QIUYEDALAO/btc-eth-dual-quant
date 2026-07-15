#!/usr/bin/env python3
"""Validate committed V3 public requalification evidence and authorization state."""
from __future__ import annotations

import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe import canonical_hash


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3"
MANIFESTS = (
    "source_manifest", "conflict_resolution_manifest", "candidate_eligibility_manifest",
    "membership_manifest", "quarantine_manifest", "qualified_panel_manifest",
    "qualification_summary",
)


def load_verified(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    expected = canonical_hash({key: value for key, value in document.items() if key != "content_hash"})
    if document.get("content_hash") != expected:
        raise ValueError(f"content hash mismatch: {path}")
    return document


def check() -> dict:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v3.json").read_text())
    registry = json.loads((ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json").read_text())
    artifacts = {name: load_verified(EVIDENCE / f"{name}.json") for name in MANIFESTS}
    run = load_verified(EVIDENCE / "requalification_run_manifest.json")
    for name, document in artifacts.items():
        if document.get("schema_version") != 3 or document.get("manifest_type") != name:
            raise ValueError(f"V3 manifest identity mismatch: {name}")
        if document.get("contract_hash") != contract["canonical_hash"]:
            raise ValueError(f"contract hash mismatch: {name}")
        if document.get("resolution_registry_hash") != registry["canonical_hash"]:
            raise ValueError(f"resolution registry hash mismatch: {name}")
        if document.get("adjudication_evidence_hash") != registry["adjudication_evidence_hash"]:
            raise ValueError(f"adjudication evidence hash mismatch: {name}")

    summary = artifacts["qualification_summary"]["content"]
    run_content = run["content"]
    if run_content["status"] != summary["status"]:
        raise ValueError("run/summary status mismatch")
    if run_content["range"] != {"start": "2020-01", "end": "2026-06"}:
        raise ValueError("frozen range mismatch")
    if summary["expected_months"] != 78 or summary["monthly_memberships"] != 78:
        raise ValueError("expected month coverage mismatch")
    for field in ("processing_errors", "unresolved_row_conflicts", "unresolved_gaps", "synthetic_fills", "replacement_members"):
        if run_content[field] != summary[field]:
            raise ValueError(f"run/summary counter mismatch: {field}")
    if any(run_content["authorizations"].values()):
        raise ValueError("downstream authorization must remain false")

    if summary["status"] == "pass":
        required_zero = (
            "processing_errors", "unresolved_row_conflicts", "unresolved_gaps",
            "excluded_category_members", "synthetic_fills", "replacement_members",
        )
        if any(summary[field] != 0 for field in required_zero):
            raise ValueError("pass evidence contains a non-zero blocker")
        if run_content["determinism_status"] != "pass" or set(run_content["builds_completed"]) != {"cold", "warm", "worker"}:
            raise ValueError("pass evidence requires exact three-way builds")
    else:
        if not run_content.get("stop_reasons"):
            raise ValueError("blocked evidence requires explicit stop reasons")
        if run_content["determinism_status"] != "not_run_due_fail_closed_cold_block":
            raise ValueError("blocked cold stop must not claim determinism")
        if run_content["builds_completed"] != ["cold"]:
            raise ValueError("warm/worker must not run after cold blocker")
        if summary["unresolved_row_conflicts"] < 1 and summary["processing_errors"] < 1:
            raise ValueError("blocked evidence has no machine blocker")

    report = (ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_QUALIFICATION_REPORT.md").read_text()
    if f"- Status: {summary['status']}" not in report:
        raise ValueError("Markdown status mismatch")
    return {"status": summary["status"], "content_hash": run["content_hash"]}


def main() -> int:
    result = check()
    print(f"V3 requalification check PASS status={result['status']} hash={result['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
