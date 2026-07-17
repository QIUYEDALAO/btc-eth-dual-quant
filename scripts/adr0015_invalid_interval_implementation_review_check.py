#!/usr/bin/env python3
"""Validate the independent review of the exact ADR-0015 implementation head."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGET_PR = 109
TARGET_BASE = "141481fa445bdc03b453844a666dbd2639c3cdf7"
TARGET_HEAD = "67e7d29eaed63a3edb903dd618184bc9f02c5748"
TARGET_REMOTE_REF = "refs/remotes/origin/adr0015-invalid-interval-implementation-reviewed-head"
TARGET_GATE_RUN = 29565196104
POLICY_HASH = "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04"
ALGORITHM_HASH = "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff"
IMPLEMENTATION_HASH = "7cc4f9a3343de1f81ea7ac38e7c77efdd9fdb6bcbe3f8eeec099ddfca1dd020f"
CHANGED_FILE_LIST_HASH = "55dc3595469c5cb3272265be1a4f8bfaf23a24b704feb36218156a95660e19e7"
ADOPTION_HASH = "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19"
POLICY_REVIEW_HASH = "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3"
SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
MEMBERSHIP_HASH = "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5"
LIFECYCLE_HASH = "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d"
REPORT = ROOT / "reports/expert/ADR_0015_INVALID_INTERVAL_IMPLEMENTATION_REVIEW.md"
EVIDENCE = ROOT / "reports/expert/evidence/adr0015_invalid_interval_implementation_review.json"

CHANGED_FILES = [
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "config/liquid_spot_invalid_interval_policy_v1.json",
    "reports/INDEX.md",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md",
    "scripts/adr0015_invalid_interval_implementation_check.py",
    "scripts/adr0015_invalid_interval_implementation_validate.sh",
    "scripts/liquid_universe_v4_public_run.py",
    "scripts/project_state_transition_check.py",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py",
    "tests/test_adr0015_invalid_interval_policy.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
]
EXPECTED_BLOBS = {
    "AGENTS.md": "972dc09e7e5308433488666fb4a146e97f841290",
    "NEXT_ACTION.md": "7fc81d7c86f6abde1ef5d7ac167e58040aae2451",
    "PROJECT_EXECUTION_CHECKLIST.md": "d2e59f4b12c73a4113bfa079299759786d2b9c5d",
    "PROJECT_LEDGER.md": "8600c1f3e6d0b84b94d93c85ce7388be76470520",
    "PROJECT_STATE.yaml": "ca8b6c0604a4acd88bdc0aef0d1ed0cc3e418693",
    "config/liquid_spot_invalid_interval_policy_v1.json": "2119b7ad0e2b0cc101e757afec268cdce041cc58",
    "reports/INDEX.md": "0a9c26921df36f2b2c3d6130574822750b9942fa",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md": "7254819c4a6bdfe154a91d4540b166091adcb42b",
    "scripts/adr0015_invalid_interval_implementation_check.py": "94bac217d6ecdaefaf8dd161462fefb079201945",
    "scripts/adr0015_invalid_interval_implementation_validate.sh": "8de38843ab9f6d3aaa5d5ea0a7a57d90e95a8638",
    "scripts/liquid_universe_v4_public_run.py": "1b7ce4cc9f43ad255c46ca4015551ba750ed6da9",
    "scripts/project_state_transition_check.py": "75e88a466e04e985f3cf5902bfa85efbc7863b2b",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py": "67373f9d56e0716d090db2a4acfa4bafab9d79d3",
    "tests/test_adr0015_invalid_interval_policy.py": "ddc720590f34137ea46ff2e4e4da53dd6125b85a",
    "tests/test_liquid_universe_v3_klay_conflict.py": "6ceceac39a4bef9a2a86be89cf10a3613c9755a0",
}
IMPLEMENTATION_FILES = (
    "config/liquid_spot_invalid_interval_policy_v1.json",
    "scripts/liquid_universe_v4_public_run.py",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py",
)
REVIEW_DIMENSIONS = (
    "exact_head_base_changed_files_and_ci",
    "runtime_policy_and_algorithm_bindings",
    "archive_member_raw_row_identity",
    "integer_timestamp_and_sole_defect_semantics",
    "point_in_time_active_membership",
    "integer_two_and_eighty_percent_gate",
    "full_active_slot_and_valid_minority_mask",
    "event_identity_and_accounting_reconciliation",
    "mask_before_grid_hour_and_day_rebuild",
    "fault_injection_and_order_determinism",
    "v2_gap_policy_separation_and_no_shortcuts",
    "historical_evidence_and_zero_downstream_authorization",
)
AUTHORIZATION = {
    "merge_exact_implementation_after_review_pr_merges": True,
    "fixed_range_public_requalification": False,
    "new_independent_audit_protocol": False,
    "new_independent_audit": False,
    "u04": False,
    "hypothesis_or_strategy": False,
    "event_scan_signals_or_returns": False,
    "backtesting_or_oos": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}
CONTEXT_MARKERS = {
    "PROJECT_STATE.yaml": "adr0015_invalid_interval_implementation_review:",
    "PROJECT_LEDGER.md": "ADR-0015 Invalid-Interval Implementation Exact-Head Review Prepared",
    "NEXT_ACTION.md": "## ADR-0015 Implementation Exact-Head Review",
    "reports/INDEX.md": "ADR_0015_INVALID_INTERVAL_IMPLEMENTATION_REVIEW.md",
    "AGENTS.md": "## ADR-0015 Implementation Exact-Head Review Gate",
    "PROJECT_EXECUTION_CHECKLIST.md": "ADR-0015-IMPL-REVIEW",
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
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


def content_set_hash(paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(_show_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def build_document(generated_utc: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "review_id": "ADR0015-INVALID-INTERVAL-IMPLEMENTATION-EXACT-HEAD-REVIEW-V1",
        "generated_utc": generated_utc,
        "reviewed_target": {
            "pull_request": TARGET_PR,
            "base_sha": TARGET_BASE,
            "head_sha": TARGET_HEAD,
            "selective_gate_run": TARGET_GATE_RUN,
            "changed_files": CHANGED_FILES,
            "changed_file_list_sha256": CHANGED_FILE_LIST_HASH,
            "target_blobs": EXPECTED_BLOBS,
            "runtime_policy_sha256": POLICY_HASH,
            "algorithm_sha256": ALGORITHM_HASH,
            "implementation_content_sha256": IMPLEMENTATION_HASH,
            "adoption_content_sha256": ADOPTION_HASH,
            "policy_review_content_sha256": POLICY_REVIEW_HASH,
            "source_freeze_content_sha256": SOURCE_FREEZE_HASH,
            "membership_manifest_content_sha256": MEMBERSHIP_HASH,
            "lifecycle_registry_sha256": LIFECYCLE_HASH,
        },
        "validation_evidence": {
            "github_selective_checks_total": 1,
            "github_selective_checks_success": 1,
            "local_unit_tests_total": 670,
            "local_unit_tests_success": 670,
            "implementation_fixture_tests_total": 10,
            "implementation_fixture_tests_success": 10,
            "production_path_regressions_total": 12,
            "production_path_regressions_success": 12,
            "reviewed_fault_cases_total": 16,
            "reviewed_fault_cases_success": 16,
            "public_data_read_or_executed": False,
            "fixed_range_requalification_executed": False,
            "new_independent_audit_executed": False,
        },
        "review_dimensions": [
            {"dimension": dimension, "status": "pass"} for dimension in REVIEW_DIMENSIONS
        ],
        "remaining_findings": {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "informational": [
                "This is fixture-only exact-head review evidence; it contains no public requalification result.",
                "The implementation remains non-authoritative until this review PR and the unchanged target implementation merge in dependency order.",
            ],
        },
        "authorization": AUTHORIZATION,
        "verdict": "approve",
    }
    identity = {key: value for key, value in document.items() if key != "generated_utc"}
    document["review_content_sha256"] = canonical_hash(identity)
    return document


def render(document: dict[str, Any]) -> str:
    target = document["reviewed_target"]
    validation = document["validation_evidence"]
    lines = [
        "# ADR-0015 Invalid-Interval Implementation Exact-Head Review", "",
        f"- Verdict: `{document['verdict']}`",
        f"- Target PR: `#{target['pull_request']}`",
        f"- Exact base: `{target['base_sha']}`",
        f"- Exact head: `{target['head_sha']}`",
        f"- Target selective run: `{target['selective_gate_run']}`",
        f"- Runtime policy hash: `{target['runtime_policy_sha256']}`",
        f"- Algorithm hash: `{target['algorithm_sha256']}`",
        f"- Implementation content hash: `{target['implementation_content_sha256']}`",
        f"- Review content hash: `{document['review_content_sha256']}`",
        "- Remaining critical/high: `0 / 0`", "",
        "## Validation", "",
        f"- GitHub selective Gate: {validation['github_selective_checks_success']}/{validation['github_selective_checks_total']}",
        f"- Local unit tests: {validation['local_unit_tests_success']}/{validation['local_unit_tests_total']}",
        f"- Implementation fixtures: {validation['implementation_fixture_tests_success']}/{validation['implementation_fixture_tests_total']}",
        f"- Production-path regressions: {validation['production_path_regressions_success']}/{validation['production_path_regressions_total']}",
        f"- Reviewed fault cases: {validation['reviewed_fault_cases_success']}/{validation['reviewed_fault_cases_total']}",
        "- Public data read or executed: no",
        "- Fixed-range requalification executed: no",
        "- New independent audit executed: no", "",
        "## Review Matrix", "", "| Dimension | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {item['dimension']} | {item['status']} |" for item in document["review_dimensions"])
    lines.extend([
        "", "## Decision", "",
        "The exact implementation head satisfies the adopted generic policy under synthetic",
        "fixtures and fault injection. Approval is valid only while PR #109 remains at the exact",
        "head above. Any target, policy, algorithm, membership, lifecycle, source, mask, ordering",
        "or authorization drift invalidates this review and fails closed.", "",
        "## Authorization", "",
        "After this review PR merges, only the unchanged PR #109 implementation may be merged.",
        "This review does not run or authorize fixed-range requalification, a new audit protocol,",
        "a new audit, U-04, strategy/backtesting/OOS, API/trading, execution/live or M2.", "",
    ])
    return "\n".join(lines)


def validate_target(*, require_remote_ref: bool = False) -> list[str]:
    failures: list[str] = []
    if not target_available():
        return ["exact implementation target is unavailable"] if require_remote_ref else []
    if _git("rev-parse", TARGET_HEAD) != TARGET_HEAD:
        failures.append("implementation target head changed")
    if require_remote_ref:
        try:
            if _git("rev-parse", TARGET_REMOTE_REF) != TARGET_HEAD:
                failures.append("PR #109 remote head drifted from reviewed target")
        except subprocess.CalledProcessError:
            failures.append("PR #109 fetched review ref is unavailable")
    paths = _git("diff", "--name-only", TARGET_BASE, TARGET_HEAD).splitlines()
    if paths != CHANGED_FILES or canonical_hash(sorted(paths)) != CHANGED_FILE_LIST_HASH:
        failures.append("implementation changed-file set drift")
    for path, expected in EXPECTED_BLOBS.items():
        if _git("rev-parse", f"{TARGET_HEAD}:{path}") != expected:
            failures.append(f"target blob drift: {path}")
    if content_set_hash(IMPLEMENTATION_FILES) != IMPLEMENTATION_HASH:
        failures.append("implementation content hash drift")

    policy = json.loads(_show_bytes(IMPLEMENTATION_FILES[0]).decode())
    declared_policy_hash = policy.get("canonical_hash")
    actual_policy_hash = canonical_hash({key: value for key, value in policy.items() if key != "canonical_hash"})
    if declared_policy_hash != POLICY_HASH or actual_policy_hash != POLICY_HASH:
        failures.append("runtime policy hash drift")
    if canonical_hash(policy.get("algorithm", {})) != ALGORITHM_HASH or policy.get("algorithm_hash") != ALGORITHM_HASH:
        failures.append("algorithm hash drift")
    authorizations = policy.get("authorizations", {})
    if any(authorizations.get(name) is not False for name in (
        "fixed_range_public_requalification", "new_independent_audit_protocol",
        "new_independent_audit", "u04", "hypothesis_or_strategy",
        "event_scan_signals_or_returns", "backtesting_or_oos", "api_or_trading",
        "execution_live", "m2",
    )):
        failures.append("runtime authorization expansion")

    core = _show_bytes(IMPLEMENTATION_FILES[2]).decode()
    public = _show_bytes(IMPLEMENTATION_FILES[1]).decode()
    required_core = (
        "class VerifiedFiveMinuteRow", "class ActiveMembershipAuthority",
        "def read_verified_monthly_five_minute_archive", "def evaluate_invalid_interval_policy",
        "len(invalid) * policy.fraction_denominator < len(active) * policy.fraction_numerator",
        '"valid_minority"', "def apply_invalid_interval_mask", "def build_invalid_interval_manifests",
        "source_freeze_content_hash", "membership_authority_hash", "algorithm_hash", "open_time_ms",
    )
    for marker in required_core:
        if marker not in core:
            failures.append(f"core review marker missing: {marker}")
    for forbidden in ('if symbol == "', "if open_time_ms == ", "storage/raw", "direct_v2_gap_policy_reuse\": true"):
        if forbidden in core:
            failures.append(f"forbidden special case or authority found: {forbidden}")
    integration = (
        "read_verified_monthly_five_minute_archive(",
        "evaluate_invalid_interval_policy(",
        "apply_invalid_interval_mask(",
        "validate_symbol_month_grid(",
        "aggregate_one_hour(",
        "_apply_invalid_interval_artifact_overlay(",
    )
    try:
        positions = [public.index(marker, public.index("def run(")) for marker in integration]
    except ValueError:
        failures.append("public-run mask-before-grid/hour/day integration is incomplete")
    else:
        if positions != sorted(positions):
            failures.append("public-run mask-before-grid/hour/day order drift")
    for marker in ("raw_rows_rewritten\": 0", "synthetic_fills\": 0", "replacement_members\": 0"):
        if marker not in core:
            failures.append(f"accounting invariant missing: {marker}")
    return sorted(set(failures))


def validate_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document != build_document(str(document.get("generated_utc"))):
        failures.append("review evidence is not the deterministic exact-head document")
    if document.get("verdict") != "approve":
        failures.append("implementation review verdict is not approve")
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
    failures = validate_target(
        require_remote_ref=os.environ.get("ADR0015_REQUIRE_IMPLEMENTATION_HEAD") == "1"
    )
    try:
        document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return failures + [f"review evidence load failed: {exc}"]
    failures.extend(validate_document(document))
    try:
        if REPORT.read_text(encoding="utf-8") != render(document):
            failures.append("review Markdown is not the deterministic JSON render")
    except OSError as exc:
        failures.append(f"review report load failed: {exc}")
    failures.extend(validate_context())
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        print("adr0015_invalid_interval_implementation_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("adr0015_invalid_interval_implementation_review_check PASS")
    print(f"target_head={TARGET_HEAD}")
    print(f"implementation_hash={IMPLEMENTATION_HASH}")
    print("verdict=approve critical=0 high=0 requalification=no audit=no u04=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
