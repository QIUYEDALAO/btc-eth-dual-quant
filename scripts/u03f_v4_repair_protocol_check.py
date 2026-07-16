#!/usr/bin/env python3
"""Validate the frozen U-03F V4 repair and requalification protocol."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/liquid_universe_v4_repair_requalification_protocol.json"
REPORT_PATH = ROOT / "reports/m0/U03F_V4_REPAIR_REQUALIFICATION_PROTOCOL.md"
DESIGN_PATH = ROOT / "docs/superpowers/specs/2026-07-16-u03f-v4-repair-requalification-design.md"

IMMUTABLE_FILES = {
    "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md": "dab79b1224e1c1f8be4c6f6e018b9ce6f40e751af58d380fd4d872d3f442045c",
    "reports/expert/evidence/liquid_universe_v4_independent_audit/audit_summary.json": "d11af8c2fdc54cac699909b0b418dd90a5f1c87e6a5e91e892770924c2184003",
}
ORIGINAL_PRODUCTION_FILES = {
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py": "6a9a3c11c749f3db5059119de70012eec0b5339a0b0b46f69022c71272f2a9f0",
    "scripts/liquid_universe_v4_public_run.py": "5622df8000c3cdd8f70a345536ed1530d954848781a6f6d7228d675c7d176623",
}

FINDING_IDS = {
    "F-CRITICAL-INTEGER-RECOMPUTATION",
    "F-HIGH-INTEGER-TIME-PATHS",
    "F-HIGH-REPORT-BINDING",
}

FAULT_IDS = {
    "FT-INT-PRECISION",
    "FT-STATIC-FLOAT-PATH",
    "FT-ADA-INVALID-INTERVAL",
    "FT-INVALID-CLOSE-BOUNDARY",
    "FT-REPORT-BYTE-DRIFT",
    "FT-RUN-MANIFEST-BINDING",
}

FALSE_AUTHORIZATIONS = {
    "u04", "hypothesis", "strategy", "event_scan", "returns", "backtesting",
    "oos", "api_trading", "execution_live", "m2",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _historical_sha256(revision: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"historical repair binding unavailable: {revision}:{relative}")
    return hashlib.sha256(result.stdout).hexdigest()


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol must be an object")
    return value


def protocol_content_hash(protocol: dict[str, Any]) -> str:
    value = copy.deepcopy(protocol)
    value.pop("generated_utc", None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if protocol.get("schema_version") != 1:
        failures.append("schema version changed")
    if protocol.get("protocol_id") != "U03F-V4-REPAIR-REQUALIFICATION-V1":
        failures.append("protocol id changed")
    if protocol.get("status") != "frozen_before_repair_implementation":
        failures.append("protocol is not frozen before implementation")
    if protocol.get("repository_binding") != {
        "repository": "QIUYEDALAO/btc-eth-dual-quant",
        "starting_main_sha": "513d321b69750d6c8bb47bddbf006d4caac04828",
        "failed_audit_pr": 95,
        "failed_audit_merge_sha": "36b81649fbdaf4f54aea7027f3e9325b0ea80de0",
        "failed_audit_result_head_sha": "fed6aa929d952a9d4744728d398dfa51fe399df1",
    }:
        failures.append("repository binding changed")

    scope = protocol.get("repair_scope", {})
    required_true = {"integer_time_only", "strict_5m_row_validation", "report_binding_atomic_with_run_manifest"}
    required_false = {
        "historical_evidence_mutation_allowed", "source_download_or_replacement_allowed",
        "validation_gate_reduction_allowed", "public_requalification_in_implementation_pr_allowed",
    }
    for key in required_true:
        if scope.get(key) is not True:
            failures.append(f"repair scope must require {key}")
    for key in required_false:
        if scope.get(key) is not False:
            failures.append(f"repair scope must forbid {key}")

    findings = protocol.get("finding_requirements", [])
    if {item.get("finding_id") for item in findings if isinstance(item, dict)} != FINDING_IDS:
        failures.append("finding mapping is incomplete or changed")
    referenced_faults = {
        fault
        for item in findings if isinstance(item, dict)
        for fault in item.get("required_fault_tests", [])
    }
    if set(protocol.get("required_fault_tests", {})) != FAULT_IDS or referenced_faults != FAULT_IDS:
        failures.append("fault-test mapping is incomplete or changed")

    review = protocol.get("exact_head_review_gate", {})
    if review != {
        "required": True,
        "reviewed_head_must_be_unchanged": True,
        "allowed_verdict": "approve",
        "critical_findings_required": 0,
        "high_findings_required": 0,
        "implementation_merge_before_review_allowed": False,
    }:
        failures.append("exact-head review Gate changed")

    requalification = protocol.get("public_requalification_gate", {})
    if requalification.get("range_start") != "2020-01" or requalification.get("range_end") != "2026-06":
        failures.append("fixed public range changed")
    if requalification.get("source_archive_count_expected") != 27736:
        failures.append("source archive count changed")
    if requalification.get("source_freeze_content_hash_required") != "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c":
        failures.append("source freeze changed")
    if requalification.get("orders") != ["cold", "warm", "worker"]:
        failures.append("requalification orders changed")
    for key in (
        "artifact_set_hashes_must_match", "all_blocking_counters_must_be_zero",
        "qualification_report_binding_must_match", "stop_before_later_orders_on_first_failure",
    ):
        if requalification.get(key) is not True:
            failures.append(f"requalification Gate must require {key}")

    audit = protocol.get("new_independent_audit_gate", {})
    if audit.get("orders") != ["normal", "reverse", "shuffled"]:
        failures.append("audit traversal orders changed")
    if audit.get("production_manifests_expected") != 15 or audit.get("exact_production_manifests_required") != 15:
        failures.append("audit must require 15/15 exact manifests")
    if audit.get("critical_findings_required") != 0 or audit.get("high_findings_required") != 0:
        failures.append("audit finding Gate changed")
    if audit.get("any_mismatch_must_fail_closed") is not True or audit.get("auditor_algorithm_hash_drift_allowed") is not False:
        failures.append("audit fail-closed/hash Gate changed")

    authorization = protocol.get("authorization", {})
    for key in FALSE_AUTHORIZATIONS:
        if authorization.get(key) is not False:
            failures.append(f"unauthorized scope enabled: {key}")
    return failures


def validate_immutable_inputs(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for relative, expected in IMMUTABLE_FILES.items():
        actual = _sha256(ROOT / relative)
        if actual != expected:
            failures.append(f"immutable input changed: {relative}: {actual}")
    starting_main = protocol.get("repository_binding", {}).get("starting_main_sha", "")
    for relative, expected in ORIGINAL_PRODUCTION_FILES.items():
        try:
            actual = _historical_sha256(starting_main, relative)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if actual != expected:
            failures.append(f"original production binding changed: {relative}: {actual}")
    audit = json.loads(
        (ROOT / "reports/expert/evidence/liquid_universe_v4_independent_audit/audit_summary.json").read_text()
    )
    bindings = protocol["immutable_historical_bindings"]
    if audit.get("audit_summary_hash") != bindings.get("failed_audit_summary_content_hash"):
        failures.append("failed-audit summary content binding changed")
    if audit.get("independent_artifact_set_hash") != bindings.get("failed_audit_independent_artifact_set_hash"):
        failures.append("failed-audit artifact-set binding changed")
    if audit.get("production_artifact_set_hash") != bindings.get("original_artifact_set_hash"):
        failures.append("historical production artifact-set binding changed")
    return failures


def validate_docs() -> list[str]:
    failures: list[str] = []
    report = REPORT_PATH.read_text(encoding="utf-8")
    design = DESIGN_PATH.read_text(encoding="utf-8")
    for item in (
        "- Status: frozen_before_repair_implementation",
        "- U-04 authorized: no",
        "Any mismatch, critical/high finding, exact-head drift, source/hash drift or",
        "15/15",
    ):
        if item not in report:
            failures.append(f"protocol report missing: {item}")
    for item in ("Design status: approved_by_explicit_delegation", "six-PR dependency chain", "Even a passing audit does not authorize U-04"):
        if item not in design:
            failures.append(f"design missing: {item}")
    return failures


def main() -> int:
    protocol = load_protocol()
    failures = validate_protocol(protocol) + validate_immutable_inputs(protocol) + validate_docs()
    if failures:
        print("u03f_v4_repair_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u03f_v4_repair_protocol_check PASS")
    print(f"protocol_content_hash={protocol_content_hash(protocol)}")
    print("repair_run=no requalification=no audit=no u04=no strategy=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
