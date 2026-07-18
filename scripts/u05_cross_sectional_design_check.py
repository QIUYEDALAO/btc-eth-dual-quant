#!/usr/bin/env python3
"""Validate the outcome-blind U-05 breadth-demand persistence design."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config/u05_cross_sectional_design_scope_v1.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
AUTH_PATH = ROOT / "config/u05_design_authorization_v1.json"
U04_PATH = ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation/run_manifest.json"
AUDIT_PATH = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
RQ_ROOT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
POLICY_PATH = ROOT / "config/liquid_spot_invalid_interval_policy_v1.json"

EXPECTED_CANDIDATE = "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE"
EXPECTED_HYPOTHESIS = (
    "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE: Binance spot USDT long/cash only; "
    "at a completed UTC observation time, broadly distributed positive participation across the exact "
    "point-in-time active liquid universe may identify diversified common demand rather than an isolated "
    "asset move, and that demand may persist after the next eligible open; no U-04 outcome inversion, "
    "current-membership hindsight, replacement members, shorting, leverage, loss adding, or "
    "lifecycle-crossing assumption."
)
EXPECTED_HYPOTHESIS_HASH = "ad164b1d9a94d9d61145bf7431a805cfa795a77a6c8aef2cdc488f6bd9e7349b"
EXPECTED_CONTENT_HASH = "ae12172aeea45c8447cb40d39dc7d83c4cd85852138a3ee994bf977112b8c2bb"
EXPECTED_BINDINGS = {
    "u05_design_authorization_hash": "48482a1d72b34d4925e3b0ed8ab218df202d560af7d8057c4fa8be403c46dc2c",
    "u04_closed_run_hash": "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2",
    "adr0015_audit_summary_hash": "e26c9a084767e0f3f29a479552d14d24ac27d0a0fff426f953c811bac3d606c4",
    "v4_artifact_set_hash": "8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3",
    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "membership_manifest_hash": "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5",
    "membership_authority_hash": "52aa8cc97b24d1f092fb5b222c44b22012406d6a74a5664d8feef176523093e2",
    "lifecycle_registry_hash": "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d",
    "invalid_interval_runtime_policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
    "invalid_interval_algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
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
    required_top = {
        "schema_version", "status", "candidate_id", "hypothesis_sha256", "bindings",
        "research_scope", "economic_hypothesis", "causal_and_membership_invariants",
        "non_duplication", "unresolved_until_separate_protocol", "authorizations",
        "content_hash", "generated_utc",
    }
    if set(scope) != required_top:
        failures.append("design schema changed or gained a premature rule")
    identity = {key: value for key, value in scope.items() if key not in {"content_hash", "generated_utc"}}
    if scope.get("content_hash") != EXPECTED_CONTENT_HASH or canonical_hash(identity) != EXPECTED_CONTENT_HASH:
        failures.append("design content identity changed")
    if scope.get("candidate_id") != EXPECTED_CANDIDATE or scope.get("hypothesis_sha256") != EXPECTED_HYPOTHESIS_HASH:
        failures.append("candidate identity changed")
    if scope.get("bindings") != EXPECTED_BINDINGS:
        failures.append("authorization, U-04 closure or data authority binding changed")
    research = scope.get("research_scope", {})
    if research != {
        "market": "binance_spot_usdt", "universe": "exact_point_in_time_active_liquid_spot_members",
        "maximum_monthly_members": 15, "direction": "spot_long_cash_only", "oos_opened": False,
        "public_data_read_in_design": False, "event_outcomes_read_in_design": False,
        "returns_computed_in_design": False,
    }:
        failures.append("outcome-blind long/cash scope changed")
    economic = scope.get("economic_hypothesis", {})
    if economic.get("family") != "cross_sectional_breadth_confirmed_common_demand_then_persistence":
        failures.append("economic family changed")
    if len(economic.get("failure_regimes", [])) != 8:
        failures.append("failure regime coverage changed")
    invariants = scope.get("causal_and_membership_invariants", {})
    if not invariants or any(value is not True for value in invariants.values()):
        failures.append("causal or membership invariant changed")
    nondup = scope.get("non_duplication", {})
    if not nondup or any(value is not True for value in nondup.values()):
        failures.append("non-duplication boundary changed")
    unresolved = scope.get("unresolved_until_separate_protocol", [])
    required_unresolved_terms = (
        ("threshold",), ("timeframe",), ("horizon", "window"),
        ("exit",), ("stop",), ("position",),
    )
    if len(unresolved) != 15 or not all(
        any(any(token in str(item) for token in alternatives) for item in unresolved)
        for alternatives in required_unresolved_terms
    ):
        failures.append("protocol or fixed-rule fields were resolved prematurely")
    expected_auth = {
        "u05_paper_protocol_design": True, "event_scan": False, "signals": False,
        "returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False,
        "backtesting": False, "oos": False, "api_trading": False,
        "execution_live": False, "m2": False,
    }
    if scope.get("authorizations") != expected_auth:
        failures.append("only U-05 paper protocol design may be authorized")
    return failures


def validate_ledger() -> list[str]:
    ledger = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if str(item.get("id", "")).startswith("U05-")]
    if len(matches) != 1 or matches[0].get("id") != EXPECTED_CANDIDATE:
        return ["exactly one U-05 candidate must be registered"]
    candidate = matches[0]
    failures: list[str] = []
    if candidate.get("hypothesis") != EXPECTED_HYPOTHESIS:
        failures.append("registered U-05 hypothesis text changed")
    if candidate.get("sha256") != EXPECTED_HYPOTHESIS_HASH or hashlib.sha256(str(candidate.get("hypothesis", "")).encode()).hexdigest() != EXPECTED_HYPOTHESIS_HASH:
        failures.append("registered U-05 hypothesis hash changed")
    if candidate.get("status") != "declared_unopened" or candidate.get("oos_opened") is not False:
        failures.append("U-05 must remain declared and OOS sealed")
    return failures


def validate_bound_evidence() -> list[str]:
    failures: list[str] = []
    auth, u04, audit = load_json(AUTH_PATH), load_json(U04_PATH), load_json(AUDIT_PATH)
    run = load_json(RQ_ROOT / "requalification_run_manifest.json")
    membership = load_json(RQ_ROOT / "membership_manifest.json")
    event = load_json(RQ_ROOT / "invalid_interval_event_manifest.json")
    policy = load_json(POLICY_PATH)
    if auth.get("content_hash") != EXPECTED_BINDINGS["u05_design_authorization_hash"]:
        failures.append("U-05 authorization drifted")
    if u04.get("run_content_hash") != EXPECTED_BINDINGS["u04_closed_run_hash"] or u04.get("status") != "failed_feasibility" or u04.get("oos_opened") is not False:
        failures.append("U-04 closed result drifted")
    if audit.get("audit_summary_hash") != EXPECTED_BINDINGS["adr0015_audit_summary_hash"] or audit.get("verdict") != "pass":
        failures.append("ADR-0015 audit drifted")
    artifacts = {item.get("artifact_set_hash") for item in run.get("content", {}).get("builds", {}).values() if isinstance(item, dict)}
    if artifacts != {EXPECTED_BINDINGS["v4_artifact_set_hash"]} or run.get("content", {}).get("source_freeze_hash") != EXPECTED_BINDINGS["source_freeze_hash"]:
        failures.append("V4 artifact or source authority drifted")
    if membership.get("content_hash") != EXPECTED_BINDINGS["membership_manifest_hash"] or membership.get("lifecycle_registry_hash") != EXPECTED_BINDINGS["lifecycle_registry_hash"]:
        failures.append("membership or lifecycle authority drifted")
    if event.get("membership_authority_hash") != EXPECTED_BINDINGS["membership_authority_hash"]:
        failures.append("point-in-time membership authority drifted")
    if policy.get("canonical_hash") != EXPECTED_BINDINGS["invalid_interval_runtime_policy_hash"] or policy.get("algorithm_hash") != EXPECTED_BINDINGS["invalid_interval_algorithm_hash"]:
        failures.append("invalid-interval authority drifted")
    return failures


def main() -> int:
    failures = validate_scope(load_json(SCOPE_PATH)) + validate_ledger() + validate_bound_evidence()
    if failures:
        print("u05_cross_sectional_design_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u05_cross_sectional_design_check PASS")
    print(f"candidate={EXPECTED_CANDIDATE} content_hash={EXPECTED_CONTENT_HASH}")
    print("authorized_next=paper_protocol_design events=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
