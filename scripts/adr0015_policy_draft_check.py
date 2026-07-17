#!/usr/bin/env python3
"""Fail-closed validation for the docs-only ADR-0015 policy Draft."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = ROOT / "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md"
MODEL_PATH = ROOT / "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json"
REPORT_PATH = ROOT / "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_DRAFT.md"
RUN_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication/diagnostic_run_manifest.json"
ROWS_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication/invalid_interval_rows.json"
WINDOWS_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication/synchronized_window_summary.json"

EXPECTED_MODEL_CONTENT_HASH = "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c"
EXPECTED_EVIDENCE = {
    "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
    "source_freeze_content_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
    "diagnostic_run_content_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
    "diagnostic_run_file_sha256": "ef768648f8cd8c60d40b617fcad1773e77bc89d318489f09df1ba9e15215c38f",
    "invalid_rows_file_sha256": "7dcd57fc0c9ff5fcf6976e21e0374971d919162c620ba21be54f8b6a27e519b9",
    "synchronized_windows_file_sha256": "d0ec2a886135ae343507ee8a167d2037a0d10516ed48cb4dd5597952d9f27bdb",
    "v2_gap_policy_contract_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
}
EXPECTED_AUTH_KEYS = {
    "adr0015_adoption",
    "production_policy_implementation",
    "production_pipeline_modification",
    "fixed_range_public_requalification",
    "new_independent_audit",
    "u04",
    "hypothesis_or_strategy",
    "event_scan_signals_or_returns",
    "backtesting_or_oos",
    "api_or_trading",
    "execution_live",
    "m2",
}
EXPECTED_HARD_BLOCKS = {
    "open_time_off_grid",
    "non_time_field_invalid_or_nonfinite",
    "ohlcv_legality_failure",
    "missing_expected_row",
    "duplicate_row",
    "non_member_row",
    "membership_ambiguity",
    "archive_or_evidence_hash_drift",
    "source_revision",
    "affected_fraction_below_threshold",
    "affected_symbol_count_below_threshold",
    "policy_overlap",
    "order_content_hash_mismatch",
}
EXPECTED_INVARIANTS = {
    "one_event_per_accepted_open_time",
    "pre_mask_active_set_equals_bound_membership_set",
    "quarantine_set_equals_full_pre_mask_active_set",
    "invalid_plus_valid_minority_equals_total_quarantined",
    "raw_rows_are_byte_immutable",
    "zero_synthetic_fills",
    "zero_replacement_members",
    "masked_5m_grid_precedes_1h_and_day_completeness",
    "cold_warm_worker_content_identity",
}
EXPECTED_CHAIN = [
    "draft_merge",
    "exact_head_independent_policy_review",
    "separate_conditional_adoption",
    "separate_generic_implementation",
    "exact_head_independent_implementation_review",
    "fixed_range_public_requalification",
    "new_independent_audit",
    "governance_closeout",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: Path = MODEL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("ADR-0015 model must be an object")
    return value


def model_content_hash(model: dict[str, Any]) -> str:
    value = copy.deepcopy(model)
    value.pop("generated_utc", None)
    value.pop("content_hash", None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_model(model: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if model_content_hash(model) != EXPECTED_MODEL_CONTENT_HASH:
        failures.append("ADR-0015 model content hash changed")
    if model.get("content_hash") != EXPECTED_MODEL_CONTENT_HASH:
        failures.append("ADR-0015 embedded content hash changed")
    if model.get("schema_version") != 1:
        failures.append("schema version changed")
    if model.get("status") != "proposed_draft_non_authoritative":
        failures.append("Draft status changed")
    for key in ("runtime_authority", "policy_adopted", "implementation_authorized"):
        if model.get(key) is not False:
            failures.append(f"Draft authority enabled: {key}")

    binding = model.get("repository_binding", {})
    expected_binding = {
        "repository": "QIUYEDALAO/btc-eth-dual-quant",
        "draft_base_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
        "protocol_pr": 102,
        "protocol_exact_head_sha": "07e4fc13d4a6d027e4881863b9224906be776e9a",
        "protocol_merge_sha": "70c784b1573de8437e189672c89e9c00b6505978",
        "diagnostic_pr": 103,
        "diagnostic_exact_head_sha": "e4b6f6e70bf6df2b10dbd7acc71a734f107d5076",
        "diagnostic_merge_sha": "49e028712695cf2a946aae9abf14c5668a5343f2",
        "diagnostic_closeout_pr": 104,
        "diagnostic_closeout_merge_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
    }
    if binding != expected_binding:
        failures.append("repository/evidence PR binding changed")
    if model.get("immutable_evidence_bindings") != EXPECTED_EVIDENCE:
        failures.append("immutable evidence bindings changed")

    facts = model.get("diagnostic_facts_not_policy_exceptions", {})
    if facts.get("source_archive_count") != 27736 or facts.get("invalid_physical_rows") != 119:
        failures.append("diagnostic counts changed")
    if facts.get("synchronized_windows") != 8 or facts.get("decision") != "new_policy_adr_required":
        failures.append("diagnostic window/decision facts changed")
    if facts.get("traversal_orders") != ["normal", "reverse", "deterministic_shuffled"]:
        failures.append("diagnostic traversal facts changed")
    if facts.get("known_window_dates_are_runtime_inputs") is not False:
        failures.append("known dates became runtime inputs")

    predicate = model.get("candidate_predicate", {})
    expected_predicate = {
        "exchange": "binance",
        "market": "spot",
        "interval": "5m",
        "open_time_grid_ms": 300000,
        "valid_close_delta_ms": 299999,
        "open_time_must_be_grid_aligned": True,
        "sole_allowed_defect": "close_time_ms != open_time_ms + 299999",
        "all_non_time_fields_must_pass_existing_strict_checks": True,
        "archive_size_sha_zip_crc_and_single_member_required": True,
        "raw_row_hash_required": True,
        "active_membership_binding_required": True,
        "group_key": "open_time_ms",
        "minimum_invalid_active_members": 2,
        "minimum_invalid_active_fraction": 0.8,
        "fraction_denominator": "all_active_members_at_open_time",
        "event_identity_derivation": [
            "source_freeze_content_hash", "membership_authority_hash", "policy_version",
            "algorithm_hash", "open_time_ms",
        ],
        "date_or_symbol_registry_allowed": False,
    }
    if predicate != expected_predicate:
        failures.append("generic candidate predicate changed")

    semantics = model.get("accepted_event_semantics", {})
    required_true = {
        "valid_minority_rows_are_quarantined",
        "physical_rows_remain_immutable_evidence",
        "mask_is_separate_hash_bound_authority",
    }
    required_false = {
        "invalid_rows_only_partial_mask_allowed",
        "raw_row_rewrite_allowed",
        "timestamp_repair_allowed",
        "synthetic_fill_allowed",
        "source_replacement_allowed",
        "replacement_member_allowed",
    }
    if semantics.get("policy_family") != "synchronized_official_invalid_interval_quarantine":
        failures.append("policy family changed")
    if semantics.get("quarantine_scope") != "all_active_members_at_open_time":
        failures.append("full-slot quarantine scope changed")
    for key in required_true:
        if semantics.get(key) is not True:
            failures.append(f"required event semantic disabled: {key}")
    for key in required_false:
        if semantics.get(key) is not False:
            failures.append(f"forbidden event semantic enabled: {key}")
    if semantics.get("complete_timeframes_rebuilt_after_mask") != ["1h", "1d"]:
        failures.append("post-mask completeness order changed")

    if set(model.get("accounting_invariants", [])) != EXPECTED_INVARIANTS:
        failures.append("accounting invariants changed")
    if set(model.get("hard_block_conditions", [])) != EXPECTED_HARD_BLOCKS:
        failures.append("hard-block conditions changed")

    relationship = model.get("v2_gap_policy_relationship", {})
    if relationship != {
        "contract_is_immutable_reference_only": True,
        "direct_reuse_as_new_policy_authority": False,
        "implicit_adoption": False,
        "new_policy_family_required": True,
    }:
        failures.append("V2 gap-policy separation changed")

    review = model.get("independent_review_gate", {})
    if review.get("exact_draft_head_required") is not True:
        failures.append("exact-head independent review disabled")
    if review.get("maximum_critical_findings") != 0 or review.get("maximum_high_findings") != 0:
        failures.append("independent review severity Gate lowered")
    if review.get("mismatch_result") != "fail_closed" or review.get("approval_adopts_policy") is not False:
        failures.append("independent review fail-closed/adoption Gate changed")

    faults = model.get("fault_cases", [])
    expected_fault_ids = {f"ADR0015-FI-{index:03d}" for index in range(1, 17)}
    actual_fault_ids = {item.get("id") for item in faults}
    if len(faults) != 16 or actual_fault_ids != expected_fault_ids:
        failures.append("fault case IDs are incomplete or duplicated")
    if any(item.get("expected") != "hard_block" for item in faults):
        failures.append("a fault case no longer hard-blocks")
    if model.get("future_dependency_chain") != EXPECTED_CHAIN:
        failures.append("future dependency chain changed")
    auth = model.get("authorization_matrix", {})
    if set(auth) != EXPECTED_AUTH_KEYS or any(auth.values()):
        failures.append("Draft authorization matrix must be exact and all false")
    return failures


def validate_evidence() -> list[str]:
    failures: list[str] = []
    expected_files = {
        RUN_PATH: EXPECTED_EVIDENCE["diagnostic_run_file_sha256"],
        ROWS_PATH: EXPECTED_EVIDENCE["invalid_rows_file_sha256"],
        WINDOWS_PATH: EXPECTED_EVIDENCE["synchronized_windows_file_sha256"],
    }
    for path, expected in expected_files.items():
        if sha256(path) != expected:
            failures.append(f"immutable evidence file changed: {path.relative_to(ROOT)}")
    run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
    if run.get("content_hash") != EXPECTED_EVIDENCE["diagnostic_run_content_hash"]:
        failures.append("diagnostic run content hash changed")
    content = run.get("content", {})
    if content.get("status") != "completed_new_policy_adr_required":
        failures.append("diagnostic status changed")
    if content.get("invalid_physical_rows") != 119 or content.get("synchronized_windows") != 8:
        failures.append("diagnostic result counts changed")
    if content.get("diagnostic_content_hash") != EXPECTED_EVIDENCE["diagnostic_content_hash"]:
        failures.append("diagnostic canonical content hash changed")
    return failures


def validate_docs() -> list[str]:
    failures: list[str] = []
    adr = ADR_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in (
        "Proposed Draft; non-authoritative pending independent policy review",
        "valid minority row",
        "No date, symbol, row or known-window exception registry",
        "Any mismatch, critical finding or high finding stops the chain",
        "A future audit pass still does not automatically authorize U-04",
    ):
        if phrase not in adr:
            failures.append(f"ADR missing mandatory phrase: {phrase}")
    for phrase in (
        "- Policy adopted: no",
        "- Implementation authorized: no",
        "- Production pipeline modified: no",
        "- U-04 authorized: no",
        "- M2 authorized: no",
        "Review approval alone does not adopt the policy",
    ):
        if phrase not in report:
            failures.append(f"Draft report missing mandatory phrase: {phrase}")
    return failures


def validate_runtime_separation() -> list[str]:
    failures: list[str] = []
    needle = MODEL_PATH.name
    for root in (ROOT / "src", ROOT / "config"):
        for path in root.rglob("*"):
            if path.is_file() and needle in path.read_text(encoding="utf-8", errors="ignore"):
                failures.append(f"Draft model imported by runtime/config: {path.relative_to(ROOT)}")
    return failures


def verify_repository() -> list[str]:
    return validate_model(load_model()) + validate_evidence() + validate_docs() + validate_runtime_separation()


def main() -> int:
    failures = verify_repository()
    if failures:
        print("adr0015_policy_draft_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("adr0015_policy_draft_check PASS")
    print(f"model_content_hash={EXPECTED_MODEL_CONTENT_HASH}")
    print("adopted=no implementation=no requalification=no audit=no u04=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
