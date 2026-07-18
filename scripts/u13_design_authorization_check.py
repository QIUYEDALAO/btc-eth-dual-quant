#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u13_design_authorization_v1.json"
U12_RESULT = ROOT / "reports/m1/evidence/u12_cross_sectional_paper_observation/run_manifest.json"
U11_RESULT = ROOT / "reports/m1/evidence/u11_cross_sectional_paper_observation/run_manifest.json"
U10_RESULT = ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation/run_manifest.json"
U09_CORRECTION = ROOT / "reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json"
PRIOR_RESULTS = [ROOT / f"reports/m1/evidence/u0{number}_cross_sectional_paper_observation/run_manifest.json" for number in (8, 7, 6, 5, 4)]
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_HASH = "8900ada4819a2d951fd26ab6a1d61e18e0e43de939207787c63e05f925866ce6"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], u12: Mapping[str, Any], u11: Mapping[str, Any], u10: Mapping[str, Any], u09: Mapping[str, Any], prior: list[Mapping[str, Any]], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-13 decision identity changed")
    bindings = document.get("bindings", {})
    if bindings.get("u12_run_content_hash") != u12.get("run_content_hash") or bindings.get("u12_three_order_identity_hash") != u12.get("orders", [{}])[0].get("content_identity_hash") or u12.get("status") != "failed_feasibility":
        failures.append("U-12 result binding changed")
    if u12.get("oos_opened") is not False or u12.get("second_run_executed") is not False or u12.get("formal_returns_computed") is not False:
        failures.append("U-12 isolation changed")
    if bindings.get("u11_attempt_content_hash") != u11.get("run_content_hash") or bindings.get("u10_run_content_hash") != u10.get("run_content_hash"):
        failures.append("U-10/U-11 binding changed")
    if bindings.get("u09_correction_content_hash") != u09.get("content_hash"):
        failures.append("U-09 correction binding changed")
    for number, result in zip((8, 7, 6, 5, 4), prior):
        if bindings.get(f"u0{number}_run_content_hash") != result.get("run_content_hash") or result.get("oos_opened") is not False:
            failures.append(f"U-0{number} result binding changed")
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash") or bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash") or bindings.get("source_freeze_hash") != "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c":
        failures.append("data authority binding changed")
    decision = document.get("decision", {})
    required = ("u13_design_authorized", "independent_economic_rationale_required", "u04_through_u12_outcome_direction_threshold_rule_or_censor_reuse_prohibited", "prior_failed_candidate_repair_retry_or_inversion_prohibited", "outcome_blind_preregistration_required", "separate_protocol_before_any_event_scan", "pre_result_implementation_and_data_scope_preflight_required")
    if any(decision.get(key) is not True for key in required) or decision.get("maximum_hypotheses") != 1:
        failures.append("decision invariant changed")
    expected = {"u13_hypothesis_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    stops = " ".join(map(str, document.get("stop_conditions", [])))
    if "may not select U-13" not in stops or "repaired, retried, inverted, relabeled or repackaged" not in stops:
        failures.append("prior-result reuse prohibition missing")
    return failures


def main() -> int:
    load = lambda path: json.loads(path.read_text())
    failures = validate(load(DECISION), load(U12_RESULT), load(U11_RESULT), load(U10_RESULT), load(U09_CORRECTION), [load(path) for path in PRIOR_RESULTS], load(AUDIT))
    if failures:
        print("u13_design_authorization_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u13_design_authorization_check PASS hash={EXPECTED_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
