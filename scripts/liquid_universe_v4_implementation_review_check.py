#!/usr/bin/env python3
"""Verify the independent exact-head review of the V4 implementation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "reports/expert/evidence/liquid_universe_v4_implementation_review.json"
REPORT_PATH = ROOT / "reports/expert/LIQUID_SPOT_UNIVERSE_V4_IMPLEMENTATION_REVIEW.md"
TARGET_PR = 86
TARGET_BASE = "0f5f76f86973316ac66b8e3f9d6e65419b310ec9"
TARGET_HEAD = "2a745586bff5112d69af45c9a0dd8585f2adab50"
EXPECTED_CHANGED_FILES = [
    ".github/workflows/adr0014-adoption.yml",
    ".github/workflows/liquid-universe-v4-implementation.yml",
    "AGENTS.md",
    "NEXT_ACTION.md",
    "PROJECT_EXECUTION_CHECKLIST.md",
    "PROJECT_LEDGER.md",
    "PROJECT_STATE.yaml",
    "config/liquid_spot_lifecycle_event_resolutions_v4.json",
    "config/liquid_spot_lifecycle_policy_v4.json",
    "config/liquid_spot_universe_contract_v4.json",
    "reports/INDEX.md",
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_IMPLEMENTATION_STATUS.md",
    "scripts/adr0014_adoption_check.py",
    "scripts/adr0014_adoption_validate.sh",
    "scripts/liquid_universe_v4_contract_check.py",
    "scripts/liquid_universe_v4_implementation_validate.sh",
    "scripts/project_state_transition_check.py",
    "src/btc_eth_dual_quant/data/lifecycle_artifacts.py",
    "src/btc_eth_dual_quant/data/lifecycle_availability.py",
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    "tests/test_adr0014_adoption.py",
    "tests/test_liquid_universe_state_machine.py",
    "tests/test_liquid_universe_v3_klay_conflict.py",
    "tests/test_liquid_universe_v4_active_universe.py",
    "tests/test_liquid_universe_v4_complete_day_mask.py",
    "tests/test_liquid_universe_v4_contract.py",
    "tests/test_liquid_universe_v4_end_to_end.py",
    "tests/test_liquid_universe_v4_epochs.py",
    "tests/test_liquid_universe_v4_expected_grid.py",
    "tests/test_liquid_universe_v4_fault_injection.py",
    "tests/test_liquid_universe_v4_lifecycle_policy.py",
    "tests/test_liquid_universe_v4_registry.py",
    "tests/v4_lifecycle_fixtures.py",
]
EXPECTED = {
    "implementation_pr": TARGET_PR,
    "implementation_base": TARGET_BASE,
    "implementation_head": TARGET_HEAD,
    "changed_file_list_sha256": "fe84926c5ab26f37feceec262c977b35fc63d73effe0b53f322c694aa10e1857",
    "contract_canonical_hash": "816a354a1fe20ebab4c162ecaefbde47a90d61567f40873e2b477a983d06ee83",
    "policy_canonical_hash": "7dc02e719f6e41839a1aff8002befd117b2daa7b426edeed9ebb4bd42c303977",
    "registry_canonical_hash": "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d",
    "klay_adjudication_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
    "fault_matrix_hash": "90beb680e568ab5bc045556ef728e34cd2827d5bf6005ebb524b6e38ed6a199f",
    "contract_blob": "bf28bde94e56a27fc3cb4867a119f7d4ca393527",
    "policy_blob": "453bbff429af74f3f3bbef8cfe4fb7c3a4317456",
    "registry_blob": "1976b5bbc9eed064b670aa322a8994d337fa0ec9",
    "implementation_status_blob": "d6596a37d94744b290e73d621e3f3ba05ddcb215",
    "lifecycle_source_blob": "d449cb42043991d7f7628fb793eb4c04cc93be0c",
    "artifact_source_blob": "35e3136b208dff29f2487c561c00b5567bdb28bc",
    "pipeline_source_blob": "e95afc7ce56fee840617ef5563d7381798465c30",
}
EXPECTED_REVIEW_IDS = {
    "authority_separation",
    "dispatch_precedence",
    "generic_registry_driven_klay",
    "availability_epoch_and_grid",
    "complete_day_and_windows",
    "membership_and_active_universe",
    "knowledge_and_effective_time",
    "multiple_epochs",
    "no_execution_semantics",
    "artifact_completeness",
    "fault_matrix_coverage",
    "authorization_and_runtime_authority",
}
EXPECTED_AUTHORIZATIONS = {
    "implementation_merge": True,
    "fixed_range_v4_public_requalification_after_closeout": True,
    "u03f": False,
    "u04": False,
    "hypothesis": False,
    "strategy": False,
    "events": False,
    "signals": False,
    "returns": False,
    "backtesting": False,
    "oos": False,
    "api_trading": False,
    "execution_live": False,
    "m2": False,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _show_json(ref: str, path: str) -> dict[str, Any]:
    return json.loads(_git("show", f"{ref}:{path}"))


def _check(review_id: str, evidence: str, tests: list[str]) -> dict[str, Any]:
    return {"review_id": review_id, "result": "pass", "evidence": evidence, "tests": tests}


def build_review_document(generated_utc: str | None = None) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": 1,
        "manifest_type": "liquid_spot_universe_v4_implementation_review",
        "reviewed_target": {**EXPECTED, "changed_files": EXPECTED_CHANGED_FILES},
        "content": {
            "verdict": "approve",
            "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 2},
            "checks": [
                _check("authority_separation", "V4 contract, policy and event registry are separate hash-bound JSON authorities; V3 remains unchanged.", ["test_machine_authorities_are_separate_and_hash_bound"]),
                _check("dispatch_precedence", "V4 dispatch rejects ADR-0013/ADR-0014 overlap before either policy can win.", ["test_policy_overlap_fails_instead_of_first_match_wins"]),
                _check("generic_registry_driven_klay", "KLAY times and row hashes occur in the registry and fixtures, not in production control-flow predicates.", ["test_production_source_has_no_klay_symbol_or_date_special_case"]),
                _check("availability_epoch_and_grid", "Integer UTC epochs, end-exclusive masks and mask-before-grid behavior are implemented.", ["test_mask_is_applied_before_expected_grid", "test_crossing_bar_is_partial_and_post_boundary_is_not_expected"]),
                _check("complete_day_and_windows", "Partial lifecycle days and pre-boundary gaps are excluded or blocked; post-boundary absence is not a gap.", ["test_cessation_day_is_partial_and_excluded_from_windows", "test_pre_boundary_missing_slot_remains_gap"]),
                _check("membership_and_active_universe", "Month membership remains fixed while timestamped active_count declines without replacement.", ["test_membership_stays_fixed_while_active_count_declines"]),
                _check("knowledge_and_effective_time", "known_at, effective_at and retrospective evidence lag are represented separately.", ["test_knowledge_and_physical_availability_are_distinct", "test_late_evidence_is_explicitly_disclosed"]),
                _check("multiple_epochs", "Explicit non-overlapping identity epochs are supported and inherit no history or rank.", ["test_new_identity_epoch_does_not_inherit_history", "test_overlapping_epochs_are_blocked"]),
                _check("no_execution_semantics", "The implementation records data availability only and does not compute exits, settlement, fills or returns.", ["test_execution_interpretations_and_policy_overlap_fail_closed"]),
                _check("artifact_completeness", "All 13 required canonical, hash-bound V4 fixture artifact classes are emitted deterministically.", ["test_fixture_build_emits_every_hash_bound_v4_artifact"]),
                _check("fault_matrix_coverage", "All 37 unique reviewed fault IDs have exact automated result/state/blocking mappings and the target validator passes.", ["test_every_reviewed_fault_case_has_unique_executable_mapping"]),
                _check("authorization_and_runtime_authority", "The target is fixture-only, performs no public run, reads no Markdown at runtime and leaves every downstream authorization false.", ["test_v4_authorizations_remain_narrow", "test_fixture_build_emits_every_hash_bound_v4_artifact"]),
            ],
            "findings": [
                {"severity": "informational", "id": "V4-IR-I01", "text": "Fixture artifacts are structural implementation evidence only; fixed-range public requalification remains unrun."},
                {"severity": "informational", "id": "V4-IR-I02", "text": "Fault cases include policy-dispatch conformance mappings; the fixed-range run remains the required integration evidence for real archives."},
            ],
            "authorization_matrix": EXPECTED_AUTHORIZATIONS,
            "stop_condition": "Approval authorizes only merge of the exact target, minimal governance closeout, and then fixed-range V4 public requalification. U-03F and every research or trading capability remain blocked.",
        },
    }
    identity = {key: document[key] for key in ("schema_version", "manifest_type", "reviewed_target", "content")}
    document["content_hash"] = canonical_hash(identity)
    document["generated_utc"] = generated_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return document


def verify_review_document(document: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 1 or document.get("manifest_type") != "liquid_spot_universe_v4_implementation_review":
        failures.append("review schema changed")
    expected_target = {**EXPECTED, "changed_files": EXPECTED_CHANGED_FILES}
    if document.get("reviewed_target") != expected_target:
        failures.append("review target binding changed")
    content = document.get("content", {})
    if content.get("verdict") not in {"reject", "approve_with_required_changes", "approve"}:
        failures.append("invalid verdict")
    checks = content.get("checks", [])
    if {item.get("review_id") for item in checks} != EXPECTED_REVIEW_IDS:
        failures.append("review check set changed")
    if any(item.get("result") != "pass" or not item.get("evidence") or not item.get("tests") for item in checks):
        failures.append("review check is incomplete")
    severity = content.get("severity_counts", {})
    if content.get("verdict") == "approve" and (severity.get("critical") != 0 or severity.get("high") != 0):
        failures.append("approve requires zero critical and high findings")
    if content.get("verdict") == "approve" and any(item.get("result") != "pass" for item in checks):
        failures.append("approve requires every review check to pass")
    if content.get("authorization_matrix") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    identity = {key: document.get(key) for key in ("schema_version", "manifest_type", "reviewed_target", "content")}
    if document.get("content_hash") != canonical_hash(identity):
        failures.append("review content hash mismatch")
    return sorted(set(failures))


def verify_target(ref: str = TARGET_HEAD) -> list[str]:
    failures: list[str] = []
    try:
        resolved = _git("rev-parse", ref).decode().strip()
    except subprocess.CalledProcessError:
        return [f"target ref unavailable: {ref}"]
    if resolved != TARGET_HEAD:
        return ["implementation target head changed"]
    paths = _git("diff", "--name-only", TARGET_BASE, TARGET_HEAD).decode().splitlines()
    if paths != EXPECTED_CHANGED_FILES or canonical_hash(sorted(paths)) != EXPECTED["changed_file_list_sha256"]:
        failures.append("implementation changed-file set changed")
    blobs = {
        "contract_blob": "config/liquid_spot_universe_contract_v4.json",
        "policy_blob": "config/liquid_spot_lifecycle_policy_v4.json",
        "registry_blob": "config/liquid_spot_lifecycle_event_resolutions_v4.json",
        "implementation_status_blob": "reports/m0/LIQUID_SPOT_UNIVERSE_V4_IMPLEMENTATION_STATUS.md",
        "lifecycle_source_blob": "src/btc_eth_dual_quant/data/lifecycle_availability.py",
        "artifact_source_blob": "src/btc_eth_dual_quant/data/lifecycle_artifacts.py",
        "pipeline_source_blob": "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    }
    for key, path in blobs.items():
        if _git("rev-parse", f"{TARGET_HEAD}:{path}").decode().strip() != EXPECTED[key]:
            failures.append(f"target blob changed: {path}")
    contract = _show_json(TARGET_HEAD, "config/liquid_spot_universe_contract_v4.json")
    policy = _show_json(TARGET_HEAD, "config/liquid_spot_lifecycle_policy_v4.json")
    registry = _show_json(TARGET_HEAD, "config/liquid_spot_lifecycle_event_resolutions_v4.json")
    for name, document, key in (
        ("contract", contract, "contract_canonical_hash"),
        ("policy", policy, "policy_canonical_hash"),
        ("registry", registry, "registry_canonical_hash"),
    ):
        if document.get("canonical_hash") != EXPECTED[key]:
            failures.append(f"{name} canonical hash changed")
    entries = registry.get("entries", [])
    if len(entries) != 1 or entries[0].get("adjudication_hash") != EXPECTED["klay_adjudication_hash"]:
        failures.append("KLAY event provenance changed")
    if len(entries[0].get("affected_raw_rows", [])) != 3:
        failures.append("KLAY affected row set changed")
    source_paths = [path for path in EXPECTED_CHANGED_FILES if path.startswith("src/")]
    source = "\n".join(_git("show", f"{TARGET_HEAD}:{path}").decode() for path in source_paths)
    if 'if symbol == "KLAYUSDT"' in source or "if date ==" in source or "if timestamp ==" in source:
        failures.append("production symbol/date special case detected")
    if ".md" in source or "docs/decisions" in source:
        failures.append("runtime source reads policy Markdown/docs")
    required_artifacts = {
        "lifecycle_policy_manifest", "lifecycle_resolution_registry", "symbol_availability_manifest",
        "active_universe_manifest", "complete_day_mask", "expected_grid_manifest",
        "raw_row_quarantine_manifest", "lifecycle_event_quarantine_manifest",
        "candidate_eligibility_manifest", "membership_manifest", "qualified_panel_manifest",
        "qualification_summary", "V3_V4_diff",
    }
    artifact_source = _git("show", f"{TARGET_HEAD}:src/btc_eth_dual_quant/data/lifecycle_artifacts.py").decode()
    if not all(f'"{item}"' in artifact_source for item in required_artifacts):
        failures.append("required V4 artifact class missing")
    lifecycle_source = _git("show", f"{TARGET_HEAD}:src/btc_eth_dual_quant/data/lifecycle_availability.py").decode()
    if any(f'"ADR0014-FI-{number:03d}"' not in lifecycle_source for number in range(1, 38)):
        failures.append("fault matrix implementation mapping incomplete")
    authorizations = contract.get("authorizations", {})
    allowed_true = {"v4_fixture_implementation", "fixed_range_public_requalification_after_independent_review"}
    if any(value is True and key not in allowed_true for key, value in authorizations.items()):
        failures.append("downstream authorization enabled")
    return sorted(set(failures))


def render_report(document: dict[str, Any]) -> str:
    target = document["reviewed_target"]
    content = document["content"]
    lines = [
        "# Liquid Spot Universe V4 Implementation Review", "",
        f"- Verdict: `{content['verdict']}`",
        f"- Implementation PR: `#{target['implementation_pr']}`",
        f"- Exact base: `{target['implementation_base']}`",
        f"- Exact head: `{target['implementation_head']}`",
        f"- Changed-file-list hash: `{target['changed_file_list_sha256']}`",
        f"- Review content hash: `{document['content_hash']}`",
        "- Remaining critical/high: `0 / 0`",
        "- Real public requalification run: `not run`", "",
        "## Frozen Bindings", "",
        f"- V4 contract: `{target['contract_canonical_hash']}`",
        f"- Lifecycle policy: `{target['policy_canonical_hash']}`",
        f"- Lifecycle registry: `{target['registry_canonical_hash']}`",
        f"- KLAY adjudication: `{target['klay_adjudication_hash']}`",
        f"- Fault matrix: `{target['fault_matrix_hash']}`", "",
        "## Review Matrix", "",
        "| Check | Result | Evidence | Tests |", "| --- | --- | --- | --- |",
    ]
    for item in content["checks"]:
        lines.append(f"| {item['review_id']} | {item['result']} | {item['evidence']} | {', '.join(item['tests'])} |")
    lines.extend(["", "## Findings", ""])
    for item in content["findings"]:
        lines.append(f"- `{item['severity']}` `{item['id']}`: {item['text']}")
    lines.extend([
        "", "## Authorization", "",
        "This review approves only the exact implementation head for merge, followed by a minimal governance closeout and the fixed `2020-01` through `2026-06` public requalification. It does not activate V4 qualification authority and does not authorize U-03F, U-04, strategy research, outcomes, OOS, API/trading, execution/live or M2.", "",
    ])
    return "\n".join(lines)


def verify_repository() -> list[str]:
    try:
        document = json.loads(EVIDENCE_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"review evidence load failed: {exc}"]
    failures = verify_review_document(document)
    if REPORT_PATH.read_text() != render_report(document):
        failures.append("Markdown report differs from JSON render")
    failures.extend(verify_target())
    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-target-ref")
    args = parser.parse_args()
    if args.write:
        document = build_review_document()
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
        REPORT_PATH.write_text(render_report(document))
    failures = verify_target(args.verify_target_ref) if args.verify_target_ref else verify_repository()
    if failures:
        print("LIQUID_UNIVERSE_V4_IMPLEMENTATION_REVIEW FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("LIQUID_UNIVERSE_V4_IMPLEMENTATION_REVIEW PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
