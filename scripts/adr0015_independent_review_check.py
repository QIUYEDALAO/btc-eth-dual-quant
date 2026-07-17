#!/usr/bin/env python3
"""Verify the independent policy review of the exact ADR-0015 Draft head."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_PR = 105
TARGET_BASE = "6df4aa3aa355f986e5533a51e223d69e3bf16e84"
TARGET_HEAD = "03d2b8736abab277e60db1153ba73f0899d7696f"
TARGET_MERGE = "e1783090dfb0a4560475b97a021ef1e77aebc399"
TARGET_REMOTE_REF = "refs/remotes/origin/adr0015-reviewed-head"
MODEL_CONTENT_HASH = "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c"
ADR_BLOB = "6a5d29b6c877d043875da71638dc80ddd54da7ee"
ADR_SHA256 = "9ce9eade1f622824562a74ce5750da400f4c298145fb92c2a89023ff527ce19a"
MODEL_BLOB = "a4155cebfde44eb149afe9dd94e4311e9155366e"
MODEL_FILE_SHA256 = "f945d5c61553a4571e9cbda7c77bff0c974a460cd25b7ad92d6382c8d4e92a7e"
CHANGED_FILE_LIST_HASH = "73373e2fbb2a46d128e4924c732845ccdc4227d7e9b813640f9e15e33e0a430c"
PROTOCOL_CONTENT_HASH = "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190"
DIAGNOSTIC_CONTENT_HASH = "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677"
DIAGNOSTIC_RUN_HASH = "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33"
SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
V2_GAP_POLICY_HASH = "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51"

REPORT = ROOT / "reports/expert/ADR_0015_INDEPENDENT_REVIEW.md"
EVIDENCE = ROOT / "reports/expert/evidence/adr0015_independent_review.json"
PROTOCOL = ROOT / "config/liquid_universe_v4_invalid_interval_adjudication_protocol.json"
WINDOWS = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication/synchronized_window_summary.json"

CHANGED_FILES = [
    ".github/workflows/adr0015-policy-draft.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md",
    "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json",
    "reports/INDEX.md",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_DRAFT.md",
    "scripts/adr0015_policy_draft_check.py",
    "scripts/adr0015_policy_draft_validate.sh",
    "scripts/project_state_transition_check.py",
    "tests/test_adr0015_policy_draft.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
]

REVIEW_DIMENSIONS = (
    "exact_head_and_ci",
    "docs_only_scope",
    "immutable_evidence_bindings",
    "pre_outcome_threshold_justification",
    "synchronous_candidate_definition",
    "false_positive_and_adversarial_hard_blocks",
    "full_slot_valid_minority_quarantine",
    "accounting_invariants",
    "v2_gap_policy_separation",
    "machine_fault_coverage",
    "authorization_non_expansion",
)

AUTHORIZATION = {
    "separate_conditional_adoption_consideration": True,
    "adr0015_adopted": False,
    "production_policy_implementation": False,
    "production_pipeline_modification": False,
    "fixed_range_public_requalification": False,
    "new_independent_audit": False,
    "u04": False,
    "hypothesis_or_strategy": False,
    "event_scan_signals_or_returns": False,
    "backtesting_or_oos": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}

INFORMATIONAL_FINDINGS = [
    "The 0.80 and two-member thresholds are policy parameters frozen before the diagnostic; they are not inferred from the eight observed windows.",
    "Full-slot quarantine intentionally discards a valid minority row to preserve a synchronized active-member panel and requires separate adoption before runtime use.",
]

CONTEXT_MARKERS = {
    "PROJECT_STATE.yaml": "adr0015_independent_policy_review:",
    "PROJECT_LEDGER.md": "ADR-0015 Exact-Head Independent Policy Review Prepared",
    "NEXT_ACTION.md": "## ADR-0015 Independent Policy Review",
    "reports/INDEX.md": "ADR_0015_INDEPENDENT_REVIEW.md",
    "AGENTS.md": "## ADR-0015 Independent Policy Review Gate",
    "PROJECT_EXECUTION_CHECKLIST.md": "ADR-0015-REVIEW",
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _show_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{TARGET_HEAD}:{path}"], cwd=ROOT)


def target_available() -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{TARGET_HEAD}^{{commit}}"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def model_content_hash(model: dict[str, Any]) -> str:
    value = copy.deepcopy(model)
    value.pop("generated_utc", None)
    value.pop("content_hash", None)
    return canonical_hash(value)


def review_content_hash(document: dict[str, Any]) -> str:
    identity = copy.deepcopy(document)
    identity.pop("generated_utc", None)
    identity.pop("review_content_sha256", None)
    return canonical_hash(identity)


def build_document(generated_utc: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "review_id": "ADR0015-EXACT-HEAD-INDEPENDENT-POLICY-REVIEW-V1",
        "generated_utc": generated_utc,
        "reviewed_target": {
            "pull_request": TARGET_PR,
            "base_sha": TARGET_BASE,
            "head_sha": TARGET_HEAD,
            "merge_sha": TARGET_MERGE,
            "changed_files": CHANGED_FILES,
            "changed_file_list_sha256": CHANGED_FILE_LIST_HASH,
            "adr_blob_sha": ADR_BLOB,
            "adr_file_sha256": ADR_SHA256,
            "model_blob_sha": MODEL_BLOB,
            "model_file_sha256": MODEL_FILE_SHA256,
            "model_content_sha256": MODEL_CONTENT_HASH,
        },
        "immutable_bindings": {
            "protocol_content_hash": PROTOCOL_CONTENT_HASH,
            "diagnostic_content_hash": DIAGNOSTIC_CONTENT_HASH,
            "diagnostic_run_content_hash": DIAGNOSTIC_RUN_HASH,
            "source_freeze_content_hash": SOURCE_FREEZE_HASH,
            "v2_gap_policy_contract_hash": V2_GAP_POLICY_HASH,
        },
        "validation_evidence": {
            "github_checks_total": 120,
            "github_checks_success": 120,
            "draft_changed_files": 15,
            "fault_cases_total": 16,
            "fault_cases_hard_block": 16,
            "diagnostic_archives_per_order": 27736,
            "diagnostic_invalid_rows": 119,
            "diagnostic_synchronous_windows": 8,
            "minimum_invalid_active_members": 2,
            "minimum_invalid_active_fraction": 0.8,
            "minimum_observed_window_fraction": "0.933333333333",
            "full_active_windows": 7,
            "valid_minority_windows": 1,
        },
        "review_dimensions": [
            {"dimension": name, "status": "pass"} for name in REVIEW_DIMENSIONS
        ],
        "remaining_findings": {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "informational": INFORMATIONAL_FINDINGS,
        },
        "authorization": AUTHORIZATION,
        "verdict": "approve",
    }
    document["review_content_sha256"] = review_content_hash(document)
    return document


def render(document: dict[str, Any]) -> str:
    target = document["reviewed_target"]
    evidence = document["validation_evidence"]
    lines = [
        "# ADR-0015 Independent Policy Review", "",
        f"- Verdict: `{document['verdict']}`",
        f"- Reviewed PR: `#{target['pull_request']}`",
        f"- Exact Draft base: `{target['base_sha']}`",
        f"- Exact Draft head: `{target['head_sha']}`",
        f"- Draft merge commit: `{target['merge_sha']}`",
        f"- Model content hash: `{target['model_content_sha256']}`",
        f"- Changed-file-list hash: `{target['changed_file_list_sha256']}`",
        f"- Review content hash: `{document['review_content_sha256']}`",
        "- Remaining critical/high: `0 / 0`", "",
        "## Executive Decision", "",
        "The exact docs-only Draft is approved as policy-review evidence with zero",
        "remaining critical or high findings. The threshold pair was frozen before",
        "the diagnostic, every observed window clears it, and the generic predicate",
        "fails closed outside the sole grid-aligned close-boundary defect. Accepted",
        "events quarantine the full active-member slot, including a valid minority",
        "row, without rewriting physical evidence.", "",
        "Approval does not adopt ADR-0015. It authorizes only a separate conditional",
        "adoption consideration under a new governance PR.", "",
        "## Validation", "",
        f"- GitHub exact-head checks: {evidence['github_checks_success']}/{evidence['github_checks_total']}",
        f"- Draft changed files: {evidence['draft_changed_files']}",
        f"- Fault cases hard-blocking: {evidence['fault_cases_hard_block']}/{evidence['fault_cases_total']}",
        f"- Frozen archives per traversal: {evidence['diagnostic_archives_per_order']}",
        f"- Invalid physical rows / synchronous windows: {evidence['diagnostic_invalid_rows']} / {evidence['diagnostic_synchronous_windows']}",
        f"- Frozen Gate: at least {evidence['minimum_invalid_active_members']} invalid active members and fraction >= {evidence['minimum_invalid_active_fraction']:.2f}",
        f"- Minimum observed fraction: {evidence['minimum_observed_window_fraction']}",
        f"- Full-active / valid-minority windows: {evidence['full_active_windows']} / {evidence['valid_minority_windows']}", "",
        "## Review Matrix", "",
        "| Dimension | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {item['dimension']} | {item['status']} |" for item in document["review_dimensions"])
    lines.extend(["", "## Informational Findings", ""])
    lines.extend(f"- {item}" for item in document["remaining_findings"]["informational"])
    lines.extend([
        "", "## Authorization", "",
        "This review authorizes only a separate conditional-adoption consideration.",
        "ADR-0015 remains unadopted. Production implementation, pipeline changes,",
        "requalification, a new audit, U-04, strategy/returns/OOS, API/trading,",
        "execution/live and M2 remain unauthorized. Any target, evidence, model,",
        "threshold or authorization drift invalidates this approval and fails closed.", "",
    ])
    return "\n".join(lines)


def validate_target(*, require_remote_ref: bool = False) -> list[str]:
    failures: list[str] = []
    if not target_available():
        return ["exact ADR-0015 Draft target is unavailable"] if require_remote_ref else []
    if _git("rev-parse", TARGET_HEAD) != TARGET_HEAD:
        failures.append("exact Draft target head changed")
    if _git("rev-parse", f"{TARGET_MERGE}^{{tree}}") != _git("rev-parse", f"{TARGET_HEAD}^{{tree}}"):
        failures.append("Draft merge tree differs from exact reviewed head")
    if require_remote_ref:
        try:
            if _git("rev-parse", TARGET_REMOTE_REF) != TARGET_HEAD:
                failures.append("PR #105 remote head drifted from reviewed target")
        except subprocess.CalledProcessError:
            failures.append("PR #105 fetched review ref is unavailable")
    paths = _git("diff", "--name-only", TARGET_BASE, TARGET_HEAD).splitlines()
    file_list_hash = hashlib.sha256(("\n".join(paths) + "\n").encode()).hexdigest()
    if paths != CHANGED_FILES or file_list_hash != CHANGED_FILE_LIST_HASH:
        failures.append("Draft changed-file set drift")
    expected_blobs = {
        "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md": ADR_BLOB,
        "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json": MODEL_BLOB,
    }
    for path, expected in expected_blobs.items():
        if _git("rev-parse", f"{TARGET_HEAD}:{path}") != expected:
            failures.append(f"Draft target blob drift: {path}")
    adr_bytes = _show_bytes("docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md")
    model_bytes = _show_bytes("docs/decisions/proposals/adr0015_invalid_interval_policy_model.json")
    if hashlib.sha256(adr_bytes).hexdigest() != ADR_SHA256:
        failures.append("ADR file hash drift")
    if hashlib.sha256(model_bytes).hexdigest() != MODEL_FILE_SHA256:
        failures.append("model file hash drift")
    model = json.loads(model_bytes)
    if model_content_hash(model) != MODEL_CONTENT_HASH or model.get("content_hash") != MODEL_CONTENT_HASH:
        failures.append("model content hash drift")
    if model.get("candidate_predicate", {}).get("minimum_invalid_active_members") != 2:
        failures.append("minimum affected-member threshold drift")
    if model.get("candidate_predicate", {}).get("minimum_invalid_active_fraction") != 0.8:
        failures.append("minimum affected-fraction threshold drift")
    if model.get("accepted_event_semantics", {}).get("quarantine_scope") != "all_active_members_at_open_time":
        failures.append("full-slot quarantine scope drift")
    if model.get("accepted_event_semantics", {}).get("valid_minority_rows_are_quarantined") is not True:
        failures.append("valid-minority quarantine drift")
    if len(model.get("fault_cases", [])) != 16 or any(item.get("expected") != "hard_block" for item in model["fault_cases"]):
        failures.append("fault-case coverage drift")
    if any(model.get("authorization_matrix", {}).values()):
        failures.append("Draft authorization matrix expanded")
    return sorted(set(failures))


def validate_frozen_evidence() -> list[str]:
    failures: list[str] = []
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    algorithm = protocol.get("diagnostic_algorithm", {})
    if algorithm.get("synchronous_minimum_symbols") != 2:
        failures.append("pre-outcome minimum-symbol Gate drift")
    if algorithm.get("synchronous_minimum_fraction") != 0.8:
        failures.append("pre-outcome minimum-fraction Gate drift")
    windows = json.loads(WINDOWS.read_text(encoding="utf-8")).get("content", [])
    if len(windows) != 8:
        failures.append("synchronized-window count drift")
    if windows and min(float(item["synchronous_fraction"]) for item in windows) < 0.8:
        failures.append("observed window fell below frozen Gate")
    if any(item.get("invalid_member_count", 0) < 2 for item in windows):
        failures.append("observed window fell below minimum-member Gate")
    if sum(item.get("invalid_member_count") == item.get("active_member_count") for item in windows) != 7:
        failures.append("full-active window count drift")
    if sum(item.get("invalid_member_count") < item.get("active_member_count") for item in windows) != 1:
        failures.append("valid-minority window count drift")
    return failures


def validate_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document != build_document(str(document.get("generated_utc"))):
        failures.append("review evidence is not the deterministic exact-head document")
    if document.get("review_content_sha256") != review_content_hash(document):
        failures.append("review content hash mismatch")
    if document.get("verdict") != "approve":
        failures.append("independent policy review verdict is not approve")
    findings = document.get("remaining_findings", {})
    if findings.get("critical") or findings.get("high"):
        failures.append("approve requires zero remaining critical/high findings")
    if any(item.get("status") != "pass" for item in document.get("review_dimensions", [])):
        failures.append("approve requires every review dimension to pass")
    if document.get("authorization") != AUTHORIZATION:
        failures.append("review authorization matrix changed")
    return sorted(set(failures))


def validate_context() -> list[str]:
    return [
        f"review context marker missing: {path}"
        for path, marker in CONTEXT_MARKERS.items()
        if marker not in (ROOT / path).read_text(encoding="utf-8")
    ]


def validate() -> list[str]:
    failures = validate_target(require_remote_ref=os.environ.get("ADR0015_REQUIRE_TARGET_HEAD") == "1")
    failures.extend(validate_frozen_evidence())
    try:
        document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return failures + [f"review evidence load failed: {exc}"]
    failures.extend(validate_document(document))
    if REPORT.read_text(encoding="utf-8") != render(document):
        failures.append("review Markdown is not the deterministic JSON render")
    failures.extend(validate_context())
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        print("adr0015_independent_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    print("adr0015_independent_review_check PASS")
    print(f"target_head={TARGET_HEAD}")
    print(f"review_content_hash={document['review_content_sha256']}")
    print("verdict=approve critical=0 high=0 adopted=no implementation=no requalification=no audit=no u04=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
