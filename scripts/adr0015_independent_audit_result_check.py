#!/usr/bin/env python3
"""Validate the completed ADR-0015 three-order independent audit evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit"
REPORT = ROOT / "reports/m0/ADR_0015_INVALID_INTERVAL_INDEPENDENT_AUDIT_REPORT.md"
ARTIFACT_SET = "8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3"
SUMMARY_HASH = "e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4"
ORDERS = ("normal", "reverse", "deterministic_shuffled")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(name: str) -> Any:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def validate_documents(
    summary: Mapping[str, Any], comparison: Mapping[str, Any],
    manifest_hashes: Mapping[str, str], traversal: list[Mapping[str, Any]],
) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in summary.items() if key != "audit_summary_hash"}
    if summary.get("audit_summary_hash") != SUMMARY_HASH or canonical_hash(identity) != SUMMARY_HASH:
        failures.append("audit summary identity changed")
    expected_summary = {
        "verdict": "pass", "manifests_exact": 19, "manifests_total": 19,
        "critical_findings": [], "high_findings": [],
        "independent_artifact_set_hash": ARTIFACT_SET,
        "production_artifact_set_hash": ARTIFACT_SET,
        "production_evidence_mutated": False, "network_accessed": False,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            failures.append(f"summary Gate changed: {key}")
    if summary.get("count_checks") != {
        "events": True, "invalid_physical_rows": True,
        "total_active_slots_masked": True, "valid_minority_rows": True,
    }:
        failures.append("accounting Gate changed")
    diagnostics = summary.get("diagnostics", {})
    for key, value in {
        "source_archive_count": 27736, "invalid_interval_events": 8,
        "invalid_physical_rows": 119, "valid_minority_rows": 1,
        "total_active_slots_masked": 120,
    }.items():
        if diagnostics.get(key) != value:
            failures.append(f"diagnostic count changed: {key}")
    if any(summary.get("authorization", {}).values()):
        failures.append("downstream authorization enabled")
    if comparison.get("exact") is not True or comparison.get("artifact_set_match") is not True:
        failures.append("production comparison is not exact")
    comparisons = comparison.get("comparisons", {})
    if len(comparisons) != 19 or any(not item.get("exact_content_match") for item in comparisons.values()):
        failures.append("19/19 manifest comparison changed")
    if manifest_hashes != {name: item["production_content_hash"] for name, item in comparisons.items()}:
        failures.append("independent manifest hash ledger changed")
    if [item.get("order") for item in traversal] != list(ORDERS):
        failures.append("traversal order ledger changed")
    if any(item.get("content_identity_hash") != ARTIFACT_SET or item.get("artifact_set_hash") != ARTIFACT_SET for item in traversal):
        failures.append("traversal identity changed")
    if traversal != summary.get("orders"):
        failures.append("summary traversal binding changed")
    return failures


def main() -> int:
    failures = validate_documents(
        load("audit_summary.json"), load("production_comparison.json"),
        load("independent_manifest_hashes.json"), load("traversal_identity.json"),
    )
    report = REPORT.read_text(encoding="utf-8")
    for marker in ("- Verdict: `pass`", "- Exact manifests: 19/19", "- Critical findings: 0", "- High findings: 0"):
        if marker not in report:
            failures.append(f"report marker missing: {marker}")
    if failures:
        print("adr0015_independent_audit_result_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("adr0015_independent_audit_result_check PASS")
    print(f"audit_summary_hash={SUMMARY_HASH}")
    print(f"artifact_set_hash={ARTIFACT_SET}")
    print("manifests=19/19 critical=0 high=0 u04=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
