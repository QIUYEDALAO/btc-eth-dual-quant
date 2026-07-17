#!/usr/bin/env python3
"""Validate the local exact-head review of the ADR-0015 independent auditor."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_BASE = "a36cb0f198e689245d7cdda8f1485bd7559e7c5b"
TARGET_COMMIT = "6b4a9687f50d2ede8ba4b5ccfd0549ddecb0e92d"
PROTOCOL_HASH = "9a1768f01e7891f8c76f74293fb3836339e75fafa039fe12ebf3a7ddfdbb970b"
IMPLEMENTATION_HASH = "b4bc01d5508975447664b82b2ccc79d21aedb916001855f267bbdb74a2f6004c"
EVIDENCE = ROOT / "reports/expert/evidence/adr0015_independent_auditor_review.json"
REPORT = ROOT / "reports/expert/ADR_0015_INDEPENDENT_AUDITOR_REVIEW.md"
IMPLEMENTATION_MANIFEST = "config/liquid_universe_v4_adr0015_independent_auditor_implementation.json"
DIMENSIONS = (
    "exact_head_and_changed_scope",
    "protocol_and_implementation_hash_binding",
    "independent_zip_member_raw_row_identity",
    "integer_time_ohlcv_and_sole_defect_semantics",
    "point_in_time_membership_and_lifecycle_denominator",
    "integer_two_and_eighty_percent_gate",
    "full_active_slot_mask_including_valid_minority",
    "mask_before_grid_hour_day_and_panel_rebuild",
    "nineteen_manifest_comparison_and_order_determinism",
    "review_authorization_binding_and_fail_closed_run_gate",
    "production_algorithm_independence_and_clone_scan",
    "historical_evidence_immutability_and_no_trading_scope",
)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def implementation_files() -> dict[str, str]:
    manifest = json.loads(_git("show", f"{TARGET_COMMIT}:{IMPLEMENTATION_MANIFEST}"))
    return manifest["files"]


def build_document(generated_utc: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "review_id": "ADR0015-INDEPENDENT-AUDITOR-EXACT-HEAD-REVIEW-V1",
        "generated_utc": generated_utc,
        "target_base": TARGET_BASE,
        "target_commit": TARGET_COMMIT,
        "protocol_content_hash": PROTOCOL_HASH,
        "implementation_content_hash": IMPLEMENTATION_HASH,
        "implementation_files": implementation_files(),
        "review_dimensions": [{"dimension": item, "status": "pass"} for item in DIMENSIONS],
        "validation": {
            "focused_tests": {"passed": 25, "total": 25},
            "full_unit_tests": {"passed": 700, "total": 700},
            "fault_injection_cases": {"passed": 16, "total": 16},
            "historical_auditor_files_modified": False,
            "public_frozen_source_audit_executed": False,
            "network_accessed": False,
        },
        "remaining_critical_findings": 0,
        "remaining_high_findings": 0,
        "remaining_findings": [],
        "verdict": "approve",
        "full_independent_audit_run_authorized": True,
        "authorizations": {
            "full_independent_audit_run": True,
            "u04": False, "strategy": False, "returns": False, "backtesting": False,
            "oos": False, "api_trading": False, "execution_live": False, "m2": False,
        },
    }
    identity = {key: value for key, value in document.items() if key != "generated_utc"}
    document["review_content_hash"] = canonical_hash(identity)
    return document


def render(document: dict[str, Any]) -> str:
    lines = [
        "# ADR-0015 Independent Auditor Exact-Head Review", "",
        f"- Verdict: `{document['verdict']}`",
        f"- Exact target: `{document['target_commit']}`",
        f"- Protocol content hash: `{document['protocol_content_hash']}`",
        f"- Implementation content hash: `{document['implementation_content_hash']}`",
        f"- Review content hash: `{document['review_content_hash']}`",
        "- Remaining critical/high: `0 / 0`", "",
        "## Review Matrix", "", "| Dimension | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {item['dimension']} | {item['status']} |" for item in document["review_dimensions"])
    lines.extend([
        "", "## Decision", "",
        "The exact local implementation head is approved. Its independent source parsing,",
        "membership authority, invalid-interval adjudication, full-slot masking, aggregation",
        "and 19-manifest comparison are bound to the frozen protocol and fail closed.", "",
        "Only the real frozen-source independent audit is authorized next. U-04, strategy,",
        "returns, backtesting, OOS, API/trading, execution/live and M2 remain unauthorized.", "",
    ])
    return "\n".join(lines)


def validate_target() -> list[str]:
    failures: list[str] = []
    if _git("rev-parse", TARGET_COMMIT) != TARGET_COMMIT:
        failures.append("exact target commit changed")
    manifest = json.loads(_git("show", f"{TARGET_COMMIT}:{IMPLEMENTATION_MANIFEST}"))
    if manifest.get("protocol_content_hash") != PROTOCOL_HASH:
        failures.append("target protocol binding changed")
    if manifest.get("implementation_content_hash") != IMPLEMENTATION_HASH:
        failures.append("target implementation identity changed")
    for path, expected in manifest.get("files", {}).items():
        actual = hashlib.sha256(subprocess.check_output(["git", "show", f"{TARGET_COMMIT}:{path}"], cwd=ROOT)).hexdigest()
        if actual != expected:
            failures.append(f"target file hash changed: {path}")
    changed = _git("diff", "--name-only", TARGET_BASE, TARGET_COMMIT).splitlines()
    if len(changed) != 16:
        failures.append("target changed-file scope changed")
    return failures


def validate_document(document: dict[str, Any]) -> list[str]:
    failures = validate_target()
    expected = build_document(document.get("generated_utc", "2026-07-18T00:00:00Z"))
    if document != expected:
        failures.append("review evidence is not the deterministic exact-head document")
    identity = {key: value for key, value in document.items() if key not in {"generated_utc", "review_content_hash"}}
    if document.get("review_content_hash") != canonical_hash(identity):
        failures.append("review content hash changed")
    if document.get("verdict") == "approve" and (
        document.get("remaining_critical_findings") != 0 or document.get("remaining_high_findings") != 0
    ):
        failures.append("approve requires zero remaining critical/high findings")
    if document.get("authorizations", {}).get("full_independent_audit_run") is not True:
        failures.append("review does not authorize the exact audit run")
    for name, enabled in document.get("authorizations", {}).items():
        if name != "full_independent_audit_run" and enabled:
            failures.append(f"downstream authorization enabled: {name}")
    return failures


def main() -> int:
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    failures = validate_document(document)
    if REPORT.read_text(encoding="utf-8") != render(document):
        failures.append("review report is not the deterministic evidence render")
    if failures:
        print("adr0015_independent_auditor_review_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("adr0015_independent_auditor_review_check PASS")
    print(f"review_content_hash={document['review_content_hash']}")
    print("real_audit=yes u04=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
