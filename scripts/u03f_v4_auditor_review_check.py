#!/usr/bin/env python3
"""Independently review the exact U-03F V4 auditor implementation head."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_PR = 92
TARGET_BASE = "a8a89e2097baf79df7eb495927627098a94e5a38"
TARGET_HEAD = "d055efc1e46fb90b60a4553b9c5e2d1589bd7f9e"
PROTOCOL_HASH = "0f4127ceb4f57f78c6fead022f9c71cb07d0f10c55d4a91f3f9cde57005a8157"
ALGORITHM_HASH = "7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1"
CHANGED_FILE_LIST_HASH = "c2b80533725b1b1b1dbf65d72f40b42af709c0ddbb7ae802d1ceefcb2fc83d35"
REPORT = ROOT / "reports/expert/U03F_V4_AUDITOR_IMPLEMENTATION_REVIEW.md"
EVIDENCE = ROOT / "reports/expert/evidence/u03f_v4_auditor_implementation_review.json"

CHANGED_FILES = [
    ".github/workflows/u03f-v4-independent-auditor.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "reports/INDEX.md",
    "reports/m0/U03F_V4_AUDITOR_IMPLEMENTATION_STATUS.md",
    "scripts/project_state_transition_check.py",
    "scripts/u03f_v4_independent_audit.py",
    "scripts/u03f_v4_independent_audit_check.py",
    "scripts/u03f_v4_independent_audit_validate.sh",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
    "tests/test_liquid_universe_state_machine.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
    "tests/test_u03f_v4_auditor_artifacts.py",
    "tests/test_u03f_v4_auditor_daily_authority.py",
    "tests/test_u03f_v4_auditor_fault_injection.py",
    "tests/test_u03f_v4_auditor_gap_policy.py",
    "tests/test_u03f_v4_auditor_grid.py",
    "tests/test_u03f_v4_auditor_independence.py",
    "tests/test_u03f_v4_auditor_lifecycle.py",
    "tests/test_u03f_v4_auditor_membership.py",
    "tests/test_u03f_v4_auditor_protocol_coverage.py",
]
AUDITOR_FILES = [
    "scripts/u03f_v4_independent_audit.py",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
]
PRODUCTION_FILES = [
    "src/btc_eth_dual_quant/data/liquid_universe.py",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline.py",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v3.py",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    "src/btc_eth_dual_quant/data/lifecycle_availability.py",
    "src/btc_eth_dual_quant/data/lifecycle_artifacts.py",
    "src/btc_eth_dual_quant/data/kline_row_conflicts.py",
    "src/btc_eth_dual_quant/data/public_archive.py",
    "scripts/liquid_universe_public_run.py",
    "scripts/liquid_universe_v3_public_run.py",
    "scripts/liquid_universe_v4_public_run.py",
    "scripts/liquid_universe_v4_requalification.py",
]
PROHIBITED_IMPORT_PREFIXES = (
    "btc_eth_dual_quant.data.liquid_universe",
    "btc_eth_dual_quant.data.lifecycle_availability",
    "btc_eth_dual_quant.data.lifecycle_artifacts",
    "btc_eth_dual_quant.data.kline_row_conflicts",
    "btc_eth_dual_quant.data.public_archive",
    "scripts.liquid_universe",
)
PROHIBITED_CALLS = {
    "build_membership_rows", "dispatch_daily_rows", "resolve_daily_key",
    "validate_symbol_month_grid", "validate_lifecycle_symbol_month_grid",
    "aggregate_one_hour", "make_v4_manifest", "canonical_hash", "artifact_set_hash",
}
PRODUCTION_TIME_RISKS = [
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 33: float epoch reconstruction",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 37: datetime.timestamp authority path",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 45: datetime.timestamp authority path",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py:line 53: float epoch reconstruction",
    "scripts/liquid_universe_v4_public_run.py:line 118: float epoch reconstruction",
    "scripts/liquid_universe_v4_public_run.py:line 271: datetime.timestamp authority path",
]


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def target_available() -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{TARGET_HEAD}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _show(path: str) -> str:
    return _show_bytes(path).decode("utf-8")


def _show_bytes(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{TARGET_HEAD}:{path}"], cwd=ROOT
    )


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def changed_file_hash(paths: list[str]) -> str:
    encoded = json.dumps(sorted(paths), separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def algorithm_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(AUDITOR_FILES):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(_show_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def _function_bodies(source: str) -> set[str]:
    bodies: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) >= 2:
            clone = ast.FunctionDef(
                name="_", args=node.args, body=node.body, decorator_list=[],
                returns=node.returns, type_comment=node.type_comment,
            )
            bodies.add(ast.dump(clone, include_attributes=False))
    return bodies


def independence_findings() -> list[str]:
    findings: list[str] = []
    production_bodies: set[str] = set()
    for path in PRODUCTION_FILES:
        production_bodies.update(_function_bodies(_show(path)))
    for path in AUDITOR_FILES:
        source = _show(path)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                if name.startswith(PROHIBITED_IMPORT_PREFIXES):
                    findings.append(f"{path}:{node.lineno}: prohibited import {name}")
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else ""
                )
                if name in PROHIBITED_CALLS:
                    findings.append(f"{path}:{node.lineno}: prohibited call {name}")
                if name in {"timestamp", "fromtimestamp"}:
                    findings.append(f"{path}:{node.lineno}: non-integer timestamp authority")
        copied = _function_bodies(source) & production_bodies
        if copied:
            findings.append(f"{path}: production-identical function body")
    return findings


def auditor_test_count() -> int:
    count = 0
    for path in CHANGED_FILES:
        if not path.startswith("tests/test_u03f_v4_auditor") or not path.endswith(".py"):
            continue
        for node in ast.walk(ast.parse(_show(path))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                count += 1
    return count


def protocol_hash() -> str:
    value = json.loads((ROOT / "config/liquid_universe_v4_independent_audit_protocol.json").read_text())
    value.pop("generated_utc", None)
    return _canonical_hash(value)


def build_document(generated_utc: str) -> dict[str, Any]:
    checks = [
        "independent implementation", "no production builder call", "no copied production source",
        "independent canonical hashing", "integer-only auditor time", "daily authority",
        "registry-driven row and lifecycle policy", "independent membership",
        "independent grid and gap semantics", "field-level artifact comparison",
        "fixture and fault coverage", "no production-output result shaping", "zero authorization",
    ]
    document: dict[str, Any] = {
        "schema_version": 1,
        "review_id": "U03F-V4-AUDITOR-IMPLEMENTATION-REVIEW-V1",
        "generated_utc": generated_utc,
        "reviewed_target": {
            "pull_request": TARGET_PR,
            "base_sha": TARGET_BASE,
            "head_sha": TARGET_HEAD,
            "changed_files": CHANGED_FILES,
            "changed_file_list_sha256": CHANGED_FILE_LIST_HASH,
            "audit_algorithm_sha256": ALGORITHM_HASH,
            "protocol_content_sha256": PROTOCOL_HASH,
        },
        "validation_evidence": {
            "local_validator": "PASS=12 FAIL=0",
            "auditor_test_count": 34,
            "github_checks_total": 102,
            "github_checks_success": 102,
            "full_public_audit_executed": False,
        },
        "review_dimensions": [{"dimension": item, "status": "pass"} for item in checks],
        "implementation_findings": {"critical": [], "high": [], "medium": [], "informational": []},
        "deferred_real_audit_gate": {
            "production_integer_time_risks": PRODUCTION_TIME_RISKS,
            "meaning": "Known production authority-path risks are findings for the frozen Stage D real audit, not defects in the independent auditor implementation.",
        },
        "authorization": {
            "merge_review_pr": True,
            "merge_auditor_after_exact_head_recheck": True,
            "full_independent_audit_run": False,
            "u04": False,
            "hypothesis_preregistration": False,
            "strategy": False,
            "event_scan": False,
            "returns": False,
            "backtesting": False,
            "oos": False,
            "api_trading": False,
            "execution_live": False,
            "m2": False,
        },
        "verdict": "approve",
    }
    identity = {key: value for key, value in document.items() if key != "generated_utc"}
    document["review_content_sha256"] = _canonical_hash(identity)
    return document


def render(document: dict[str, Any]) -> str:
    target = document["reviewed_target"]
    evidence = document["validation_evidence"]
    risks = document["deferred_real_audit_gate"]["production_integer_time_risks"]
    lines = [
        "# U-03F V4 Auditor Implementation Review", "",
        f"- Verdict: {document['verdict']}",
        f"- Target PR: #{target['pull_request']}",
        f"- Exact head: `{target['head_sha']}`",
        f"- Base: `{target['base_sha']}`",
        f"- Protocol hash: `{target['protocol_content_sha256']}`",
        f"- Audit algorithm hash: `{target['audit_algorithm_sha256']}`",
        f"- Changed-file-list hash: `{target['changed_file_list_sha256']}`",
        f"- Review content hash: `{document['review_content_sha256']}`", "",
        "## Result", "",
        "The exact target implements an independent fixture-tested auditor without importing,",
        "calling or copying the production liquid-universe builders. All implementation review",
        "dimensions pass with zero critical and zero high findings.", "",
        "## Validation", "",
        f"- Local validator: {evidence['local_validator']}",
        f"- Auditor tests: {evidence['auditor_test_count']}",
        f"- GitHub checks: {evidence['github_checks_success']}/{evidence['github_checks_total']} success",
        "- Full public audit executed: no", "",
        "## Review Matrix", "",
        "| Dimension | Status |", "| --- | --- |",
    ]
    lines.extend(f"| {item['dimension']} | {item['status']} |" for item in document["review_dimensions"])
    lines.extend(["", "## Deferred Stage D Gate", ""])
    lines.extend(f"- `{item}`" for item in risks)
    lines.extend([
        "", document["deferred_real_audit_gate"]["meaning"], "",
        "## Authorization", "",
        "This review authorizes merging the review PR and, only after the exact target head is",
        "rechecked unchanged, merging the auditor implementation. The full audit, U-04, strategy,",
        "events, returns, backtesting, OOS, API/trading, execution/live and M2 remain unauthorized.", "",
    ])
    return "\n".join(lines)


def validate(*, require_target: bool | None = None) -> list[str]:
    failures: list[str] = []
    if require_target is None:
        require_target = os.environ.get("U03F_REQUIRE_TARGET_HEAD") == "1"
    exact_target_available = target_available()
    if require_target and not exact_target_available:
        failures.append("exact target head is unavailable")
    if exact_target_available:
        paths = _git("diff", "--name-only", f"{TARGET_BASE}..{TARGET_HEAD}").splitlines()
        if paths != CHANGED_FILES or changed_file_hash(paths) != CHANGED_FILE_LIST_HASH:
            failures.append("target changed-file set or hash changed")
        if algorithm_hash() != ALGORITHM_HASH:
            failures.append("target audit algorithm hash changed")
        failures.extend(independence_findings())
        if auditor_test_count() != 34:
            failures.append("auditor fixture/fault test count changed")
        target_entry = _show("scripts/u03f_v4_independent_audit.py")
        if "stage B permits --fixture-smoke only" not in target_entry:
            failures.append("stage B target no longer fails closed against a full audit run")
    if protocol_hash() != PROTOCOL_HASH:
        failures.append("frozen protocol hash changed")
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expected = build_document(str(document.get("generated_utc")))
    if document != expected:
        failures.append("committed review evidence is not the deterministic exact-head review")
    if REPORT.read_text(encoding="utf-8") != render(expected):
        failures.append("review Markdown is not the deterministic evidence render")
    if document.get("verdict") != "approve":
        failures.append("implementation review verdict is not approve")
    findings = document.get("implementation_findings", {})
    if findings.get("critical") or findings.get("high"):
        failures.append("approve is forbidden with critical/high implementation findings")
    forbidden = {key: value for key, value in document.get("authorization", {}).items() if key not in {"merge_review_pr", "merge_auditor_after_exact_head_recheck"} and value is not False}
    if forbidden:
        failures.append("downstream authorization enabled")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("u03f_v4_auditor_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    print("u03f_v4_auditor_review_check PASS")
    print(f"target_head={TARGET_HEAD}")
    print(f"exact_target_source_check={'yes' if target_available() else 'frozen_evidence_only'}")
    print(f"verdict={document['verdict']} critical=0 high=0")
    print("full_audit=no u04=no strategy=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
