#!/usr/bin/env python3
"""Deep fail-closed validation for the docs-only ADR-0014 Draft models."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml

from scripts.liquid_universe_v3_klay_conflict_check import validate as validate_klay_evidence


ADR = ROOT / "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md"
POLICY_MODEL = ROOT / "docs/decisions/proposals/adr0014_lifecycle_policy_model.json"
FAULT_MATRIX_MODEL = ROOT / "docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json"
CONFORMANCE_MODEL = ROOT / "docs/decisions/proposals/adr0014_mc_conformance.json"
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json"

EXPECTED_KLAY_EVIDENCE_HASH = "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a"
EXPECTED_PRIOR_REVIEW_HASH = "3d7e089e3322970a8602dda8a4c4c82d01f5604276688567754d77319c932a15"
EXPECTED_STATUS = "proposed_draft_non_authoritative"
EXPECTED_MCS = {f"MC-{number:02d}" for number in range(1, 12)}
EXPECTED_FAULT_IDS = {f"ADR0014-FI-{number:03d}" for number in range(1, 38)}
EXPECTED_AUTH_KEYS = {
    "adr0014_adoption",
    "contract_mutation",
    "registry_mutation",
    "v4_implementation",
    "v3_or_v4_requalification",
    "cold_warm_or_worker_build",
    "u03f",
    "u04",
    "hypothesis_preregistration",
    "strategy_design_or_code",
    "event_scan",
    "returns_or_backtesting",
    "oos_access",
    "api_or_trading",
    "execution_live",
    "m2",
}
EXPECTED_PIPELINE = [
    "validate_raw_data",
    "load_and_validate_lifecycle_policy",
    "load_and_validate_event_registry",
    "build_availability_epochs",
    "apply_availability_mask",
    "build_expected_grid",
    "detect_gaps",
    "build_complete_timeframes",
    "build_complete_day_mask",
    "rank_and_evaluate_eligibility",
]
EXPECTED_ROW_CLASSES = {
    "cessation_day_partial_row",
    "post_cessation_normal_duration_placeholder",
    "post_cessation_malformed_placeholder",
    "legitimate_zero_volume_row",
    "pre_cessation_valid_row",
    "unresolved_row",
}
EXPECTED_KLAY_ROWS = [
    ("2024-10-28", "cessation_day_partial_row", "692aa865b2c8924b0b2e64a9128346ac77b1db3d0f1b82fdf7cd79fe0cb96319"),
    ("2024-10-29", "post_cessation_normal_duration_placeholder", "fde7b4044554dff07cc39570082938a67e4c6763d2106e2b94809dd7d85695b7"),
    ("2024-10-30", "post_cessation_malformed_placeholder", "8c916992e12bcf4318a93c2ecaf4f00571e1ac7251748cef6676cdead535bfa1"),
]
EXPECTED_TIMES = {
    "known_at",
    "publication_time",
    "effective_at",
    "archive_first_available_at",
    "archive_revision_at",
    "adjudication_at",
    "resolution_approved_at",
}
EXPECTED_STATES = {
    "active_complete",
    "active_partial",
    "lifecycle_terminated",
    "data_quarantined",
    "unresolved_blocked",
    "not_yet_available",
}
EXPECTED_NON_TARGETS = {
    "exit_price",
    "liquidation",
    "settlement",
    "token_conversion",
    "swap_ratio",
    "stale_fill",
    "stale_price_forward_fill",
    "cross_cessation_return",
    "minus_100_percent_return",
    "zero_return",
    "cash_treatment",
    "position_migration",
    "forced_exit",
}
EXPECTED_V4_ARTIFACTS = {
    "lifecycle_policy_manifest",
    "lifecycle_resolution_registry",
    "symbol_availability_manifest",
    "active_universe_manifest",
    "complete_day_mask",
    "expected_grid_manifest",
    "raw_row_quarantine_manifest",
    "lifecycle_event_quarantine_manifest",
    "qualification_summary",
    "V3_V4_diff",
}
EXPECTED_ZERO_COUNTERS = {
    "synthetic_fills",
    "replacement_members",
    "overlapping_epochs",
    "unresolved_lifecycle_rows",
}


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _draft_envelope(document: dict, name: str, failures: list[str]) -> None:
    if document.get("schema_version") != 1:
        failures.append(f"{name} schema_version must be 1")
    if document.get("status") != EXPECTED_STATUS:
        failures.append(f"{name} is not a proposed non-authoritative Draft")
    for key in ("runtime_authority", "policy_adopted", "implementation_authorized"):
        if document.get(key) is not False:
            failures.append(f"{name} {key} must be false")


def verify_models(policy: dict, faults: dict, conformance: dict, adr_text: str) -> list[str]:
    failures: list[str] = []
    for document, name in (
        (policy, "policy model"),
        (faults, "fault matrix"),
        (conformance, "MC conformance"),
    ):
        _draft_envelope(document, name, failures)

    if policy.get("klay_evidence_hash") != EXPECTED_KLAY_EVIDENCE_HASH:
        failures.append("KLAY adjudication evidence hash changed")
    auth = policy.get("authorization_matrix", {})
    if set(auth) != EXPECTED_AUTH_KEYS or any(auth.values()):
        failures.append("Draft authorization matrix must contain exact all-false keys")

    event = policy.get("lifecycle_event_model", {})
    if event.get("object_type") != "versioned_lifecycle_availability_event":
        failures.append("MC-01 lifecycle object is not a versioned event")
    if set(event.get("row_classifications", [])) != EXPECTED_ROW_CLASSES:
        failures.append("MC-01 row classification vocabulary changed")
    for flag in (
        "post_cessation_rows_complete_history_eligible",
        "post_cessation_rows_ranking_window_eligible",
        "post_cessation_rows_eligibility_window_eligible",
    ):
        if event.get(flag) is not False:
            failures.append(f"MC-01 {flag} must be false")
    rows = event.get("frozen_klay_example", {}).get("affected_raw_rows", [])
    actual_rows = [(r.get("date"), r.get("classification"), r.get("raw_row_sha256")) for r in rows]
    if actual_rows != EXPECTED_KLAY_ROWS:
        failures.append("MC-01 frozen KLAY affected-row set changed")
    if event.get("new_post_cessation_row_result") != "fail_closed_re_adjudication_required":
        failures.append("MC-01 new post-cessation row does not fail closed")
    if event.get("affected_row_hash_change_result") != "fail_closed_re_adjudication_required":
        failures.append("MC-01 affected-row hash drift does not fail closed")

    if policy.get("qualification_pipeline_order") != EXPECTED_PIPELINE:
        failures.append("MC-02 qualification pipeline order changed")
    epochs = policy.get("availability_epoch_model", {})
    required_epoch_fields = {
        "epoch_id", "identity_version", "availability_start_inclusive",
        "availability_end_exclusive", "known_at", "effective_at",
        "event_resolution_reference", "source_evidence_hashes",
    }
    if not required_epoch_fields.issubset(set(epochs.get("required_fields", []))):
        failures.append("MC-02 availability epoch schema incomplete")
    if epochs.get("overlap_result") != "blocked":
        failures.append("MC-08 overlapping epochs must block")
    forbidden_inheritance = {
        "365_day_history", "90_day_ranking_window", "volume_history", "rank",
        "price_continuity", "membership",
    }
    if set(epochs.get("new_epoch_must_not_inherit", [])) != forbidden_inheritance:
        failures.append("MC-08 new-epoch non-inheritance changed")
    if epochs.get("new_epoch_inherits") != []:
        failures.append("MC-08 new epoch gained inherited state")

    timeframes = policy.get("timeframe_semantics", {})
    if timeframes.get("1h", {}).get("required_child_bars") != 12:
        failures.append("MC-02 1h must require 12 complete 5m bars")
    if timeframes.get("1h", {}).get("cross_epoch_aggregation") is not False:
        failures.append("MC-02 cross-epoch 1h aggregation must be false")
    if timeframes.get("1d", {}).get("partial_day_complete_window_eligible") is not False:
        failures.append("MC-02 partial day entered complete-day windows")
    if set(policy.get("quarantine_layers", [])) != {
        "raw_row_quarantine", "lifecycle_event_quarantine",
        "research_panel_availability_mask", "unresolved_data_quarantine",
    }:
        failures.append("MC-02 quarantine layers changed")

    knowledge = policy.get("point_in_time_knowledge", {})
    if set(knowledge.get("required_times", [])) != EXPECTED_TIMES:
        failures.append("MC-03 point-in-time vocabulary changed")
    expected_knowledge = {
        "physical_market_availability_uses": "effective_at",
        "research_knowledge_not_before": "known_at",
        "month_start_membership_rewritten_by_later_evidence": False,
        "successor_performance_can_rewrite_old_membership": False,
        "known_after_effective_label": "retrospective_evidence_lag",
        "lifecycle_label_feature_before_known_at": False,
    }
    for key, value in expected_knowledge.items():
        if knowledge.get(key) != value:
            failures.append(f"MC-03 {key} changed")

    universe = policy.get("universe_views", {})
    if universe.get("separate_counts") is not True:
        failures.append("MC-04 membership and active counts are not separate")
    if set(universe.get("required_counts", [])) != {"membership_count", "active_count"}:
        failures.append("MC-04 required count vocabulary changed")
    if set(universe.get("status_vocabulary", [])) != EXPECTED_STATES:
        failures.append("MC-04 status vocabulary changed")
    if universe.get("termination_means") != ["physical_unavailability"]:
        failures.append("MC-04 lifecycle termination gained non-data semantics")
    if set(universe.get("termination_does_not_mean", [])) != {
        "missing_data", "zero_return", "cash", "stale_price", "automatic_replacement",
    }:
        failures.append("MC-04 lifecycle termination exclusions changed")
    if universe.get("sixteenth_ranked_replacement") is not False:
        failures.append("MC-04 replacement member became allowed")

    if set(policy.get("non_targets", [])) != EXPECTED_NON_TARGETS:
        failures.append("MC-05 data-policy non-targets changed")
    held_gate = policy.get("held_position_downstream_gate", {})
    if any(held_gate.get(key) is not False for key in (
        "fixed_rule_contract_before_execution_policy_review",
        "freqtrade_backtest_before_execution_policy_review",
        "returns_validation_before_execution_policy_review",
    )):
        failures.append("MC-05 held-position downstream Gate opened")
    if held_gate.get("required_review") != "independent_delisting_execution_policy_review":
        failures.append("MC-05 independent execution-policy review missing")

    successor = policy.get("successor_metadata", {})
    if successor.get("field") != "announced_successor_symbol" or successor.get("authority") != "provenance_only":
        failures.append("MC-06 successor field or authority changed")
    if successor.get("inherits_history") is not False or successor.get("inherits") != []:
        failures.append("MC-06 successor inherited history")
    if any(successor.get(key) is not False for key in (
        "economic_equivalence", "price_continuity", "conversion_relationship",
        "automatic_conversion", "fills_old_symbol_gap",
    )):
        failures.append("MC-06 successor gained economic authority")

    separation = policy.get("authority_separation", {})
    if separation.get("separate_authorities") is not True:
        failures.append("MC-07 policy and event registry are not separate")
    if separation.get("production_symbol_date_special_cases") is not False:
        failures.append("MC-07 production special cases became allowed")
    registry = policy.get("event_registry", {})
    required_registry_fields = {
        "resolution_id", "exchange", "market", "pair", "symbol",
        "base_asset_identity", "event_type", "epoch_id", "availability_start",
        "availability_end_exclusive", "known_at", "effective_at",
        "last_valid_market_time", "expected_grid_end",
        "announcement_evidence_hashes", "archive_hashes", "raw_row_hashes",
        "intraday_evidence_hashes", "similar_scope_scan_hash", "policy_version",
        "adjudication_evidence_hash", "announced_successor_symbol", "authorization_status",
    }
    if not required_registry_fields.issubset(set(registry.get("required_fields", []))):
        failures.append("MC-07 event registry schema incomplete")
    if len(registry.get("fail_closed_on", [])) != 9:
        failures.append("MC-07 event registry failure modes incomplete")

    evidence = policy.get("evidence_sufficiency", {})
    if set(evidence.get("permanent_policy_event_types", [])) != {
        "permanent_cessation", "delisting", "migration_cessation",
    }:
        failures.append("MC-09 permanent lifecycle vocabulary changed")
    if set(evidence.get("non_permanent_or_unresolved_types", [])) != {
        "temporary_suspension", "maintenance", "unknown_event",
    }:
        failures.append("MC-09 temporary/unknown vocabulary changed")
    if evidence.get("archive_absence_is_proof") is not False or evidence.get("intraday_archive_absence_is_proof") is not False:
        failures.append("MC-09 archive absence became lifecycle proof")
    if evidence.get("announcement_is_canonical_override") is not False:
        failures.append("MC-09 announcement became canonical override")
    if evidence.get("trading_after_announced_cessation_result") != "blocked":
        failures.append("MC-09 trading-after-cessation no longer blocks")

    v4 = policy.get("future_v4_authority", {})
    if set(v4.get("required_artifacts", [])) != EXPECTED_V4_ARTIFACTS:
        failures.append("MC-10 future V4 artifact set changed")
    if set(v4.get("pass_requires_zero", [])) != EXPECTED_ZERO_COUNTERS:
        failures.append("MC-10 V4 zero-counter Gate changed")
    for key in ("canonical_serialization", "all_artifacts_hash_bound", "v3_remains_active_until_v4_pass", "cold_warm_worker_exact_match_required", "u03f_independent_recompute_required"):
        if v4.get(key) is not True:
            failures.append(f"MC-10 {key} must be true")
    if v4.get("markdown_is_input") is not False or v4.get("blocked_v4_becomes_authority") is not False:
        failures.append("MC-10 non-machine or blocked V4 authority enabled")

    cases = faults.get("fault_cases", [])
    ids = [case.get("test_id") for case in cases]
    if len(ids) != len(set(ids)):
        failures.append("MC-11 fault test IDs are not unique")
    if set(ids) != EXPECTED_FAULT_IDS:
        failures.append("MC-11 fault matrix is incomplete")
    required_case_fields = {
        "test_id", "precondition", "mutation_or_fault", "expected_result",
        "expected_state", "blocking_status",
    }
    for case in cases:
        if set(case) != required_case_fields or case.get("expected_state") not in EXPECTED_STATES:
            failures.append(f"MC-11 invalid fault case: {case.get('test_id')}")

    prior = conformance.get("prior_review", {})
    if prior != {"pr": 82, "merge_sha": "d507684564fc31812c8e7d4adb06d7ab61c7dab7", "content_hash": EXPECTED_PRIOR_REVIEW_HASH}:
        failures.append("MC conformance prior-review binding changed")
    changes = conformance.get("mandatory_changes", {})
    if set(changes) != EXPECTED_MCS:
        failures.append("MC-01..MC-11 conformance set incomplete")
    for mc, entry in changes.items():
        if entry.get("addressed") is not True or entry.get("blocking_until_independent_review") is not True:
            failures.append(f"{mc} is not addressed and independently blocked")
        if not entry.get("acceptance_criteria"):
            failures.append(f"{mc} acceptance criteria missing")
        tests = set(entry.get("required_tests", []))
        if not tests or not tests.issubset(EXPECTED_FAULT_IDS):
            failures.append(f"{mc} required test mapping invalid")

    required_adr_markers = [
        "Status: Proposed draft; not adopted",
        "## MC-01:", "## MC-02:", "## MC-03:", "## MC-04:", "## MC-05:",
        "## MC-06:", "## MC-07:", "## MC-08:", "## MC-09:", "## MC-10:", "## MC-11:",
        EXPECTED_KLAY_EVIDENCE_HASH, EXPECTED_PRIOR_REVIEW_HASH,
        "versioned_lifecycle_availability_event", "announced_successor_symbol",
        "Proposed draft; not adopted", "Policy adopted: false", "M2: false",
    ]
    for marker in required_adr_markers:
        if marker not in adr_text:
            failures.append(f"ADR/model consistency marker missing: {marker}")
    return sorted(set(failures))


def _runtime_import_failures() -> list[str]:
    failures: list[str] = []
    model_names = {POLICY_MODEL.name, FAULT_MATRIX_MODEL.name, CONFORMANCE_MODEL.name}
    for directory in (ROOT / "src", ROOT / "config"):
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name in model_names:
                if name in text:
                    failures.append(f"runtime path imports docs-only Draft model: {path.relative_to(ROOT)} -> {name}")
    return failures


def verify_repository() -> list[str]:
    try:
        policy = json.loads(POLICY_MODEL.read_text(encoding="utf-8"))
        faults = json.loads(FAULT_MATRIX_MODEL.read_text(encoding="utf-8"))
        conformance = json.loads(CONFORMANCE_MODEL.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Draft model load failed: {exc}"]
    failures = verify_models(policy, faults, conformance, ADR.read_text(encoding="utf-8"))
    frozen = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if frozen.get("content_hash") != EXPECTED_KLAY_EVIDENCE_HASH:
        failures.append("frozen KLAY evidence content hash changed")
    failures.extend(validate_klay_evidence())
    failures.extend(_runtime_import_failures())

    state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8"))
    expected_pair = (
        "ADR-0014 required-changes Draft completed pending independent conformance review",
        "adr0014_required_changes_draft_pending_conformance_review_not_adopted_no_requalification_no_strategy_no_m2",
    )
    if (state.get("current_phase"), state.get("current_status")) != expected_pair:
        failures.append("PROJECT_STATE does not identify revised Draft pending conformance review")
    work = next((item for item in state.get("open_work", []) if item.get("id") == "ADR-0014-DRAFT"), None)
    if not work or work.get("status") != "required_changes_completed_pending_conformance_review":
        failures.append("ADR-0014-DRAFT state is not pending independent conformance review")
    elif any(work.get(key) for key in ("adopted", "implemented", "registry_change", "requalification")):
        failures.append("ADR-0014-DRAFT gained downstream authority")
    if any(state.get("research_authorizations", {}).values()):
        failures.append("research authorization matrix must remain all false")
    if list((ROOT / "config").glob("*adr0014*")):
        failures.append("ADR-0014 Draft created a config/runtime artifact")
    return sorted(set(failures))


def main() -> int:
    failures = verify_repository()
    if failures:
        print("ADR0014_DRAFT_POLICY_CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    policy = json.loads(POLICY_MODEL.read_text(encoding="utf-8"))
    faults = json.loads(FAULT_MATRIX_MODEL.read_text(encoding="utf-8"))
    conformance = json.loads(CONFORMANCE_MODEL.read_text(encoding="utf-8"))
    print("ADR0014_DRAFT_POLICY_CHECK PASS")
    print(f"adr_content_hash={hashlib.sha256(ADR.read_bytes()).hexdigest()}")
    print(f"policy_model_hash={canonical_hash(policy)}")
    print(f"fault_matrix_hash={canonical_hash(faults)}")
    print(f"mc_conformance_hash={canonical_hash(conformance)}")
    print("policy_adopted=false")
    print("requalification_run=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
