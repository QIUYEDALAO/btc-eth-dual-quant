#!/usr/bin/env python3
"""Build and verify the exact-head ADR-0014 required-changes conformance review."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "reports/expert/evidence/adr0014_required_changes_review.json"
REPORT_PATH = ROOT / "reports/expert/ADR_0014_REQUIRED_CHANGES_REVIEW.md"
TARGET_HEAD = "31c967c785128671769eb713baed265da8ae0f2a"
TARGET_BASE = "ab45ba4f12badab8a00faa0181b48c948643e223"
EXPECTED_CHANGED_FILES = [
    ".github/workflows/adr0014-draft-policy-validate.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md",
    "docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json",
    "docs/decisions/proposals/adr0014_lifecycle_policy_model.json",
    "docs/decisions/proposals/adr0014_mc_conformance.json",
    "reports/INDEX.md",
    "scripts/adr0014_draft_policy_check.py",
    "scripts/adr0014_draft_policy_validate.sh",
    "scripts/project_state_transition_check.py",
    "tests/test_adr0014_draft_policy.py",
    "tests/test_liquid_universe_state_machine.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
]
EXPECTED_TARGET = {
    "reviewed_pr_number": 81,
    "reviewed_pr_state": "OPEN_DRAFT_MERGEABLE",
    "reviewed_pr_head": TARGET_HEAD,
    "reviewed_base_branch": "main",
    "reviewed_base_sha": TARGET_BASE,
    "adr_path": "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md",
    "adr_blob_sha": "0e9cedc8a1cfa50d5c4d6457da78c9154a75390f",
    "adr_content_sha256": "a8c57bec6ee31342d0a9dd8e14deb4fd0ed28202aa838705d699522fa58d6790",
    "policy_model_path": "docs/decisions/proposals/adr0014_lifecycle_policy_model.json",
    "policy_model_blob_sha": "e920a2e3d915422860e37e79590b5576549777ed",
    "policy_model_hash": "bce56a1070ef0690b13cba492bf9619a456af2618be94eb2ecbe03ea7e709d97",
    "fault_matrix_path": "docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json",
    "fault_matrix_blob_sha": "ffaf2e791aef5694d132217db4d55df7fe96bc52",
    "fault_matrix_hash": "90beb680e568ab5bc045556ef728e34cd2827d5bf6005ebb524b6e38ed6a199f",
    "mc_conformance_path": "docs/decisions/proposals/adr0014_mc_conformance.json",
    "mc_conformance_blob_sha": "62b77c6964fe7a3c3541d67e5532dafe7e0ae354",
    "mc_conformance_hash": "303e4d28ea27575ed7fa46e9d9da459e5c237a0390f36f9c9de9cfcd7c9821d2",
    "changed_file_list_hash_algorithm": "sha256(canonical_json(sorted_utf8_paths)))",
    "changed_file_list_sha256": "1f9999545d237072eea41daec96579ab02ab265cedf4a9dfc71de5c5cd88f841",
    "changed_files": EXPECTED_CHANGED_FILES,
    "prior_review_content_hash": "3d7e089e3322970a8602dda8a4c4c82d01f5604276688567754d77319c932a15",
    "klay_adjudication_evidence_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
}
EXPECTED_MANDATORY_CHANGE_IDS = {f"MC-{number:02d}" for number in range(1, 12)}
EXPECTED_AUTHORIZATIONS = {
    "adr0014_adopted": False,
    "pr81_ready": False,
    "pr81_merge": False,
    "contract_mutation": False,
    "registry_mutation": False,
    "v4_implementation": False,
    "v3_or_v4_requalification": False,
    "cold_warm_or_worker_build": False,
    "u03f": False,
    "u04": False,
    "strategy_design_or_code": False,
    "event_scan": False,
    "returns_or_backtesting": False,
    "oos_access": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def content_identity(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": document["schema_version"],
        "manifest_type": document["manifest_type"],
        "reviewed_artifacts": document["reviewed_artifacts"],
        "content": document["content"],
    }


def _review(mc: str, evidence: list[str], tests: list[str]) -> dict[str, Any]:
    return {
        "review_id": f"ADR0014-RC-{mc[-2:]}",
        "mandatory_change_id": mc,
        "evidence": evidence,
        "acceptance_result": "pass",
        "test_mapping": tests,
        "severity": "resolved",
        "remaining_gap": "none",
        "pass": True,
    }


def _mandatory_change_reviews() -> list[dict[str, Any]]:
    return [
        _review("MC-01", ["Versioned lifecycle event binds all six row classes and KLAY 2024-10-28/29/30 raw hashes."], ["ADR0014-FI-005", "ADR0014-FI-006", "ADR0014-FI-007", "ADR0014-FI-009"]),
        _review("MC-02", ["Availability epochs and mask-before-grid order uniquely define 5m, 1h and 1d completeness."], ["ADR0014-FI-001", "ADR0014-FI-002", "ADR0014-FI-003", "ADR0014-FI-004", "ADR0014-FI-031", "ADR0014-FI-032", "ADR0014-FI-033"]),
        _review("MC-03", ["Seven knowledge/effective/archive/adjudication times are separate; retrospective lag is explicit."], ["ADR0014-FI-020", "ADR0014-FI-021"]),
        _review("MC-04", ["Monthly membership and timestamped active universe expose separate counts and closed state vocabulary."], ["ADR0014-FI-027", "ADR0014-FI-028", "ADR0014-FI-029", "ADR0014-FI-030"]),
        _review("MC-05", ["Data policy denies execution, settlement and return semantics and requires independent held-position review."], ["ADR0014-FI-034", "ADR0014-FI-035", "ADR0014-FI-036"]),
        _review("MC-06", ["announced_successor_symbol is provenance-only and inherits no history, rank, membership or continuity."], ["ADR0014-FI-017"]),
        _review("MC-07", ["Generic policy and evidence-bound registry are separate; drift, conflicts and special cases fail closed."], ["ADR0014-FI-009", "ADR0014-FI-010", "ADR0014-FI-022", "ADR0014-FI-023", "ADR0014-FI-024", "ADR0014-FI-025", "ADR0014-FI-037"]),
        _review("MC-08", ["Multiple identity-versioned non-overlapping epochs cover relisting, reactivation, migration and ticker reuse."], ["ADR0014-FI-018", "ADR0014-FI-019", "ADR0014-FI-026"]),
        _review("MC-09", ["Permanent lifecycle evidence requires joint official, archive, intraday, event-time and scope evidence."], ["ADR0014-FI-011", "ADR0014-FI-012", "ADR0014-FI-013", "ADR0014-FI-014", "ADR0014-FI-015", "ADR0014-FI-016"]),
        _review("MC-10", ["Future V4 machine artifacts, hash bindings, activation order, counters and zero-Gates are complete."], ["ADR0014-FI-021", "ADR0014-FI-022", "ADR0014-FI-023", "ADR0014-FI-024"]),
        _review("MC-11", ["The docs-only fault matrix contains unique ADR0014-FI-001 through ADR0014-FI-037 cases."], [f"ADR0014-FI-{number:03d}" for number in range(1, 38)]),
    ]


def build_review_document(generated_utc: str | None = None) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "manifest_type": "adr0014_required_changes_conformance_review",
        "reviewed_artifacts": EXPECTED_TARGET,
        "content": {
            "verdict": "approve",
            "mandatory_change_reviews": _mandatory_change_reviews(),
            "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 1},
            "checker_assessment": {
                "deep_structured_validation": True,
                "marker_only_validation": False,
                "adr_model_consistent": True,
                "fault_matrix_complete": True,
                "runtime_authority": False,
                "pr81_remains_draft": True,
            },
            "authorization_matrix": EXPECTED_AUTHORIZATIONS,
            "stop_condition": "Review approval is conformance evidence only. PR #81 remains Draft and unadopted; no downstream task is authorized.",
        },
    }
    document["content_hash"] = canonical_hash(content_identity(document))
    document["generated_utc"] = generated_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return document


def verify_review_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "adr0014_required_changes_conformance_review":
        failures.append("review schema or manifest type changed")
    reviewed = document.get("reviewed_artifacts", {})
    for key, value in EXPECTED_TARGET.items():
        if reviewed.get(key) != value:
            failures.append(f"reviewed artifact binding changed: {key}")
    content = document.get("content", {})
    reviews = content.get("mandatory_change_reviews", [])
    if {item.get("mandatory_change_id") for item in reviews} != EXPECTED_MANDATORY_CHANGE_IDS:
        failures.append("mandatory change review set mismatch")
    required_fields = {"review_id", "mandatory_change_id", "evidence", "acceptance_result", "test_mapping", "severity", "remaining_gap", "pass"}
    for item in reviews:
        if set(item) != required_fields or not item.get("evidence") or not item.get("test_mapping"):
            failures.append(f"mandatory change review malformed: {item.get('mandatory_change_id')}")
    if content.get("verdict") not in {"reject", "approve_with_required_changes", "approve"}:
        failures.append("invalid review verdict")
    if content.get("verdict") == "approve" and not all(
        item.get("pass") is True
        and item.get("acceptance_result") == "pass"
        and item.get("remaining_gap") == "none"
        for item in reviews
    ):
        failures.append("approve verdict requires every mandatory change to pass")
    severity = content.get("severity_counts", {})
    if content.get("verdict") == "approve" and (severity.get("critical") != 0 or severity.get("high") != 0):
        failures.append("approve verdict requires zero critical and high findings")
    if content.get("authorization_matrix") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    assessment = content.get("checker_assessment", {})
    expected_assessment = {
        "deep_structured_validation": True,
        "marker_only_validation": False,
        "adr_model_consistent": True,
        "fault_matrix_complete": True,
        "runtime_authority": False,
        "pr81_remains_draft": True,
    }
    if assessment != expected_assessment:
        failures.append("checker assessment changed")
    try:
        expected_hash = canonical_hash(content_identity(document))
    except KeyError:
        failures.append("content identity is incomplete")
    else:
        if document.get("content_hash") != expected_hash:
            failures.append("review content hash mismatch")
    return sorted(set(failures))


def render_report(document: dict[str, Any]) -> str:
    target = document["reviewed_artifacts"]
    content = document["content"]
    lines = [
        "# ADR-0014 Required Changes Conformance Review",
        "",
        f"- Verdict: `{content['verdict']}`",
        f"- Reviewed PR: #{target['reviewed_pr_number']}",
        f"- Exact revised head: `{target['reviewed_pr_head']}`",
        f"- Exact base: `{target['reviewed_base_sha']}`",
        f"- Review content hash: `{document['content_hash']}`",
        "- Remaining critical/high: `0 / 0`",
        "- PR #81 remains Draft: yes",
        "- Policy adoption authorized: no",
        "- Runtime authority created: no",
        "",
        "## Frozen Artifact Bindings",
        "",
        f"- ADR blob / content: `{target['adr_blob_sha']}` / `{target['adr_content_sha256']}`",
        f"- Policy model: `{target['policy_model_hash']}`",
        f"- Fault matrix: `{target['fault_matrix_hash']}`",
        f"- MC conformance: `{target['mc_conformance_hash']}`",
        f"- Changed-file list: `{target['changed_file_list_sha256']}`",
        f"- Prior review: `{target['prior_review_content_hash']}`",
        f"- KLAY evidence: `{target['klay_adjudication_evidence_hash']}`",
        "",
        "## Mandatory Change Matrix",
        "",
        "| ID | Result | Severity | Remaining Gap | Evidence | Tests |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in content["mandatory_change_reviews"]:
        lines.append(
            f"| {item['mandatory_change_id']} | {item['acceptance_result']} | {item['severity']} | {item['remaining_gap']} | "
            f"{' '.join(item['evidence'])} | {', '.join(item['test_mapping'])} |"
        )
    lines.extend([
        "",
        "## Review Conclusion",
        "",
        "MC-01 through MC-11 conform to the prior mandatory changes at the exact frozen head. The checker parses the structured Draft models, verifies ADR/model consistency, requires the complete fault matrix, rejects runtime imports and keeps every authorization false.",
        "",
        "This `approve` verdict is review evidence only. It does not adopt ADR-0014, mark PR #81 Ready, merge PR #81, create V4 authority, mutate a registry, run requalification, or authorize U-03F, U-04, strategy, OOS, API/trading or M2.",
        "",
    ])
    return "\n".join(lines)


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def verify_target_ref(ref: str) -> list[str]:
    failures: list[str] = []
    try:
        resolved = _git("rev-parse", ref).decode().strip()
    except subprocess.CalledProcessError:
        return [f"target ref unavailable: {ref}"]
    if resolved != TARGET_HEAD:
        failures.append("target ref does not resolve to frozen revised head")
        return failures
    paths = _git("diff", "--name-only", TARGET_BASE, TARGET_HEAD).decode().splitlines()
    if paths != EXPECTED_CHANGED_FILES:
        failures.append("target changed-file list changed")
    if canonical_hash(sorted(paths)) != EXPECTED_TARGET["changed_file_list_sha256"]:
        failures.append("target changed-file-list hash changed")
    for path_key, blob_key, hash_key, canonical in (
        ("adr_path", "adr_blob_sha", "adr_content_sha256", False),
        ("policy_model_path", "policy_model_blob_sha", "policy_model_hash", True),
        ("fault_matrix_path", "fault_matrix_blob_sha", "fault_matrix_hash", True),
        ("mc_conformance_path", "mc_conformance_blob_sha", "mc_conformance_hash", True),
    ):
        path = EXPECTED_TARGET[path_key]
        blob = _git("rev-parse", f"{TARGET_HEAD}:{path}").decode().strip()
        if blob != EXPECTED_TARGET[blob_key]:
            failures.append(f"target blob changed: {path}")
        raw = _git("show", f"{TARGET_HEAD}:{path}")
        digest = canonical_hash(json.loads(raw)) if canonical else hashlib.sha256(raw).hexdigest()
        if digest != EXPECTED_TARGET[hash_key]:
            failures.append(f"target content changed: {path}")
    forbidden = [path for path in paths if path.startswith(("src/", "config/", "reports/m0/evidence/liquid_universe_v3/"))]
    if forbidden:
        failures.append(f"target contains forbidden runtime/evidence changes: {forbidden}")
    return failures


def verify_repository() -> list[str]:
    try:
        document = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"review evidence load failed: {exc}"]
    failures = verify_review_document(document)
    if REPORT_PATH.read_text(encoding="utf-8") != render_report(document):
        failures.append("Markdown report is not the exact JSON render")
    failures.extend(verify_target_ref(TARGET_HEAD))
    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-target-ref")
    args = parser.parse_args()
    if args.write:
        document = build_review_document()
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        REPORT_PATH.write_text(render_report(document), encoding="utf-8")
    failures = verify_target_ref(args.verify_target_ref) if args.verify_target_ref else verify_repository()
    if failures:
        print("ADR0014_REQUIRED_CHANGES_REVIEW_CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    document = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8")) if EVIDENCE_PATH.exists() else build_review_document()
    print("ADR0014_REQUIRED_CHANGES_REVIEW_CHECK PASS")
    print(f"reviewed_head={TARGET_HEAD}")
    print(f"verdict={document['content']['verdict']}")
    print(f"content_hash={document['content_hash']}")
    print("remaining_critical=0")
    print("remaining_high=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
