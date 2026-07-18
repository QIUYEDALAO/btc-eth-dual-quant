#!/usr/bin/env python3
"""Validate the outcome-blind U-04 residual-reversal design."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config/u04_cross_sectional_design_scope_v1.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTH_PATH = ROOT / "config/u04_design_authorization_v1.json"
AUDIT_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
RQ_ROOT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
POLICY_PATH = ROOT / "config/liquid_spot_invalid_interval_policy_v1.json"

EXPECTED_CANDIDATE = "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL"
EXPECTED_HYPOTHESIS = (
    "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL: Binance spot USDT long/cash only; "
    "at a completed UTC observation time, the prior-only price move of each asset is compared "
    "with the contemporaneous move of the exact point-in-time active liquid universe; an "
    "asset-specific negative residual may reflect temporary local liquidity pressure and may "
    "partially reverse after the next eligible open; no shorting, leverage, loss adding, "
    "current-membership hindsight, replacement members, or lifecycle-crossing assumption."
)
EXPECTED_HYPOTHESIS_HASH = "85e9fc11e8f6b69597fecdb6a40485611eb24163a20cea4534e81d0f08e5ec7a"
EXPECTED_CONTENT_HASH = "b384e6484180a0ec358125fbb0338d7376b860372ab065fe7043667931f178b8"

EXPECTED_BINDINGS = {
    "u04_design_authorization_hash": "84d9b499329169719a880af80b1e2e7f0d5d5cbbc6c62a6aa762cd738aa04e89",
    "adr0015_audit_summary_hash": "e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4",
    "v4_artifact_set_hash": "8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3",
    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "membership_manifest_hash": "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5",
    "membership_authority_hash": "52aa8cc97b24d1f092fb5b222c44b22012406d6a74a5664d8feef176523093e2",
    "lifecycle_registry_hash": "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d",
    "invalid_interval_runtime_policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
    "invalid_interval_algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
}
EXPECTED_FAILURES = [
    "permanent_asset_specific_information_shock",
    "lifecycle_termination_or_unresolved_delisting_execution_treatment",
    "common_component_estimate_dominated_by_a_small_number_of_members",
    "cross_sectional_dependence_overstates_independent_sample_size",
    "relative_weakness_continues_instead_of_reversing",
    "partial_reversal_is_too_small_to_cover_stressed_costs",
    "membership_source_lifecycle_or_invalid_interval_authority_drift",
    "broad_market_decline_creates_material_absolute_long_exposure_despite_a_relative_signal",
]
EXPECTED_UNRESOLVED = [
    "is_oos_boundary", "completed_observation_timeframe", "common_market_component_estimator",
    "asset_specific_residual_definition", "negative_residual_event_threshold",
    "cross_sectional_cluster_and_episode_rule", "future_observation_windows",
    "sample_and_concentration_gates", "cost_coverage_gate", "future_entry_detail",
    "fixed_rule_exit_family", "risk_invalidation_stop", "position_cap",
    "lifecycle_intersection_treatment",
]
EXPECTED_AUTHORIZATIONS = {
    "u04_paper_protocol_design": True, "event_scan": False, "signals": False,
    "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False,
    "backtesting": False, "oos": False, "api_trading": False,
    "execution_live": False, "m2": False,
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_scope(scope: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if set(scope) != {
        "schema_version", "status", "candidate_id", "hypothesis_sha256", "bindings",
        "research_scope", "economic_hypothesis", "causal_and_membership_invariants",
        "non_duplication", "unresolved_until_separate_protocol", "authorizations",
        "content_hash", "generated_utc",
    }:
        failures.append("top-level design schema changed or a rule was selected prematurely")
    identity = {key: value for key, value in scope.items() if key not in {"content_hash", "generated_utc"}}
    if scope.get("content_hash") != EXPECTED_CONTENT_HASH or canonical_hash(identity) != EXPECTED_CONTENT_HASH:
        failures.append("design content identity changed")
    if scope.get("schema_version") != 1 or scope.get("status") != "economic_hypothesis_pass_protocol_design_only":
        failures.append("design version or status changed")
    if scope.get("candidate_id") != EXPECTED_CANDIDATE or scope.get("hypothesis_sha256") != EXPECTED_HYPOTHESIS_HASH:
        failures.append("candidate identity changed")
    if scope.get("bindings") != EXPECTED_BINDINGS:
        failures.append("audit or data-authority binding changed")

    research = scope.get("research_scope", {})
    if research != {
        "market": "binance_spot_usdt", "universe": "exact_point_in_time_active_liquid_spot_members",
        "maximum_monthly_members": 15, "direction": "spot_long_cash_only",
        "oos_opened": False, "public_data_read_in_design": False,
        "event_outcomes_read_in_design": False, "returns_computed_in_design": False,
    }:
        failures.append("outcome-blind long/cash research scope changed")

    economic = scope.get("economic_hypothesis", {})
    if set(economic) != {"family", "return_source", "mechanism", "failure_regimes"}:
        failures.append("economic hypothesis schema changed or gained parameters")
    if economic.get("family") != "cross_sectional_asset_specific_negative_residual_then_partial_reversal":
        failures.append("economic family changed")
    if economic.get("failure_regimes") != EXPECTED_FAILURES:
        failures.append("failure regimes changed")

    invariants = scope.get("causal_and_membership_invariants", {})
    required_invariants = {
        "completed_observations_only", "prior_only_inputs", "exact_active_member_set_required",
        "complete_active_member_rows_required", "current_membership_hindsight_prohibited",
        "replacement_members_prohibited", "survivorship_rewrite_prohibited",
        "absolute_drop_alone_is_not_candidate_identity",
        "post_outcome_winner_or_loser_selection_prohibited",
        "lifecycle_crossing_assumption_prohibited", "next_eligible_open_earliest_future_entry",
    }
    if set(invariants) != required_invariants or any(invariants.get(key) is not True for key in required_invariants):
        failures.append("causal or point-in-time membership invariant changed")

    nondup = scope.get("non_duplication", {})
    required_nondup = {
        "m1c_long_horizon_winner_momentum_reuse_prohibited",
        "m1g_absolute_single_asset_panic_trigger_reuse_prohibited",
        "m1e_compression_breakout_continuation_reuse_prohibited",
        "m1h_funding_crowding_input_reuse_prohibited",
        "m1a_sma_donchian_atr_bundle_reuse_prohibited",
        "failed_candidate_outcome_derived_rule_prohibited",
    }
    if set(nondup) != required_nondup or any(nondup.get(key) is not True for key in required_nondup):
        failures.append("non-duplication boundary changed")
    if scope.get("unresolved_until_separate_protocol") != EXPECTED_UNRESOLVED:
        failures.append("a protocol parameter was selected, removed, or changed prematurely")
    if scope.get("authorizations") != EXPECTED_AUTHORIZATIONS:
        failures.append("only U-04 paper-protocol design may be authorized")
    return failures


def validate_ledger(path: Path = LEDGER_PATH) -> list[str]:
    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if str(item.get("id", "")).startswith("U04-")]
    if len(matches) != 1 or matches[0].get("id") != EXPECTED_CANDIDATE:
        return ["exactly one U-04 candidate must be registered"]
    candidate = matches[0]
    failures: list[str] = []
    if candidate.get("hypothesis") != EXPECTED_HYPOTHESIS:
        failures.append("registered U-04 hypothesis text changed")
    digest = hashlib.sha256(str(candidate.get("hypothesis", "")).encode()).hexdigest()
    if digest != EXPECTED_HYPOTHESIS_HASH or candidate.get("sha256") != EXPECTED_HYPOTHESIS_HASH:
        failures.append("registered U-04 hypothesis hash changed")
    if candidate.get("oos_opened") is not False:
        failures.append("U-04 OOS must remain sealed")
    status = candidate.get("status")
    if status == "failed_feasibility":
        result_path = ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation/run_manifest.json"
        result = load_json(result_path) if result_path.is_file() else {}
        if (
            result.get("status") != "failed_feasibility"
            or result.get("run_content_hash") != "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2"
            or result.get("oos_opened") is not False
        ):
            failures.append("U-04 failed-feasibility ledger status lacks exact sealed result evidence")
    elif status != "declared_unopened":
        failures.append("U-04 ledger status is not an allowed sealed research state")
    return failures


def validate_bound_repository_evidence() -> list[str]:
    failures: list[str] = []
    auth, audit = load_json(AUTH_PATH), load_json(AUDIT_PATH)
    run = load_json(RQ_ROOT / "requalification_run_manifest.json")
    membership = load_json(RQ_ROOT / "membership_manifest.json")
    policy = load_json(POLICY_PATH)
    event_manifest = load_json(RQ_ROOT / "invalid_interval_event_manifest.json")
    if auth.get("content_hash") != EXPECTED_BINDINGS["u04_design_authorization_hash"]:
        failures.append("U-04 authorization evidence drifted")
    if audit.get("audit_summary_hash") != EXPECTED_BINDINGS["adr0015_audit_summary_hash"] or audit.get("verdict") != "pass":
        failures.append("passing ADR-0015 audit evidence drifted")
    run_content = run.get("content", {})
    artifact_hashes = {
        item.get("artifact_set_hash")
        for item in run_content.get("builds", {}).values()
        if isinstance(item, dict)
    }
    if artifact_hashes != {EXPECTED_BINDINGS["v4_artifact_set_hash"]}:
        failures.append("V4 requalification artifact set drifted")
    if run_content.get("source_freeze_hash") != EXPECTED_BINDINGS["source_freeze_hash"]:
        failures.append("source freeze evidence drifted")
    if membership.get("content_hash") != EXPECTED_BINDINGS["membership_manifest_hash"]:
        failures.append("membership manifest evidence drifted")
    if membership.get("lifecycle_registry_hash") != EXPECTED_BINDINGS["lifecycle_registry_hash"]:
        failures.append("lifecycle registry evidence drifted")
    if event_manifest.get("membership_authority_hash") != EXPECTED_BINDINGS["membership_authority_hash"]:
        failures.append("point-in-time membership authority drifted")
    if policy.get("canonical_hash") != EXPECTED_BINDINGS["invalid_interval_runtime_policy_hash"] or policy.get("algorithm_hash") != EXPECTED_BINDINGS["invalid_interval_algorithm_hash"]:
        failures.append("invalid-interval policy authority drifted")
    return failures


def main() -> int:
    failures = validate_scope(load_json(SCOPE_PATH)) + validate_ledger() + validate_bound_repository_evidence()
    if failures:
        print("u04_cross_sectional_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u04_cross_sectional_design_check PASS")
    print(f"candidate={EXPECTED_CANDIDATE} content_hash={EXPECTED_CONTENT_HASH}")
    print("authorized_next=paper_protocol_design events=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
