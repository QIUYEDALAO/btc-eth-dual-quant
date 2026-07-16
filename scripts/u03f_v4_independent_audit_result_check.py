#!/usr/bin/env python3
"""Validate committed U-03F evidence without re-reading ignored raw data."""

from __future__ import annotations

import json
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_run import (
    PRODUCTION_NAMES,
    ZERO_AUTHORIZATIONS,
    render_report,
)
from btc_eth_dual_quant.audit.liquid_universe_v4_independent import audit_identity_hash


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/expert/evidence/liquid_universe_v4_independent_audit"
REPORT = ROOT / "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md"
FILES = {
    "audit_source_manifest.json",
    "audit_row_conflict_manifest.json",
    "audit_lifecycle_manifest.json",
    "audit_membership_manifest.json",
    "audit_expected_grid_manifest.json",
    "audit_quarantine_manifest.json",
    "audit_complete_day_manifest.json",
    "audit_active_universe_manifest.json",
    "audit_qualified_panel_manifest.json",
    "production_comparison_manifest.json",
    "audit_run_manifest.json",
    "audit_summary.json",
}


def validate() -> list[str]:
    failures: list[str] = []
    observed = {path.name for path in EVIDENCE.glob("*.json")} if EVIDENCE.is_dir() else set()
    if observed != FILES:
        failures.append(f"evidence file set mismatch: missing={sorted(FILES-observed)} extra={sorted(observed-FILES)}")
        return failures
    summary = json.loads((EVIDENCE / "audit_summary.json").read_text(encoding="utf-8"))
    comparison = json.loads((EVIDENCE / "production_comparison_manifest.json").read_text(encoding="utf-8"))
    if summary.get("verdict") not in {"pass", "failed_audit"}:
        failures.append("audit verdict is invalid")
    if summary.get("authorization") != ZERO_AUTHORIZATIONS:
        failures.append("audit authorization changed")
    if summary.get("comparison") != comparison:
        failures.append("comparison evidence differs from summary")
    identity = dict(summary)
    recorded_summary_hash = identity.pop("audit_summary_hash", None)
    if recorded_summary_hash != audit_identity_hash(identity):
        failures.append("audit summary identity hash is invalid")
    comparisons = comparison.get("comparisons", {})
    if set(comparisons) != set(PRODUCTION_NAMES):
        failures.append("production comparison does not cover all 15 manifests")
    if summary.get("counts", {}).get("months") != 78:
        failures.append("month count is not 78")
    if summary.get("counts", {}).get("membership_rows") != 1170:
        failures.append("membership row count is not 1170")
    if not all(summary.get("determinism", {}).values()):
        failures.append("independent audit runs are not deterministic")
    runs = summary.get("runs", [])
    for field in ("source_hash", "membership_hash", "grid_hash", "lifecycle_hash", "panel_hash", "artifact_set_hash"):
        if len({run.get(field) for run in runs}) != 1:
            failures.append(f"run identity differs for {field}")
    run_manifest = json.loads((EVIDENCE / "audit_run_manifest.json").read_text(encoding="utf-8"))
    expected_run_manifest = {
        "schema_version": 1,
        "audit_id": summary.get("audit_id"),
        "runs": runs,
        "determinism": summary.get("determinism"),
        "authorization": ZERO_AUTHORIZATIONS,
    }
    if run_manifest != expected_run_manifest:
        failures.append("audit run manifest differs from summary")
    if summary.get("verdict") == "pass" and (summary.get("critical_findings") or summary.get("high_findings")):
        failures.append("pass verdict contains critical/high findings")
    if summary.get("verdict") == "failed_audit" and not (summary.get("critical_findings") or summary.get("high_findings")):
        failures.append("failed audit lacks a critical/high finding")
    if summary.get("production_evidence_mutated") is not False or summary.get("network_accessed") is not False:
        failures.append("offline/no-mutation attestations changed")
    if summary.get("verdict") == "failed_audit" and comparison.get("exact") is not False:
        failures.append("failed audit must disclose a production comparison mismatch")
    if summary.get("counts", {}).get("source_archive_count") != 27736:
        failures.append("frozen source archive count is not 27736")
    if REPORT.read_text(encoding="utf-8") != render_report(summary):
        failures.append("Markdown report is not a deterministic summary rendering")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1
    print("U-03F V4 independent audit result: PASS (evidence self-consistent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
