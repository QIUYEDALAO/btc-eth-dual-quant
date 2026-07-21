#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u12_design_authorization_v1.json"
U11_ATTEMPT = ROOT / "reports/m1/evidence/u11_cross_sectional_paper_observation/run_manifest.json"
U11_ADJUDICATION = ROOT / "reports/m1/U11_PAPER_OBSERVATION_ADJUDICATION.md"
U10_RESULT = ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation/run_manifest.json"
CORRECTION = ROOT / "reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json"
PRIOR_RESULTS = [ROOT / f"reports/m1/evidence/u0{number}_cross_sectional_paper_observation/run_manifest.json" for number in (8, 7, 6, 5, 4)]
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_SOURCE_FREEZE = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
EXPECTED_HASH = "ecb8fd7801eda5a42652091a27bad46368d4193240d58423827cdc8c8c8602e7"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], u11: Mapping[str, Any], adjudication: str, u10: Mapping[str, Any], correction: Mapping[str, Any], prior: list[Mapping[str, Any]], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-12 decision identity changed")
    bindings = document.get("bindings", {})
    if bindings.get("u11_attempt_content_hash") != u11.get("run_content_hash") or bindings.get("u11_three_order_identity_hash") != u11.get("orders", [{}])[0].get("content_identity_hash"):
        failures.append("U-11 attempt binding changed")
    if "failed_execution_invalid_observation" not in adjudication or "Retry authorized: `false`" not in adjudication:
        failures.append("U-11 adjudication changed")
    if any((u11.get("oos_opened") is not False, u11.get("second_run_executed") is not False, u11.get("formal_returns_computed") is not False)):
        failures.append("U-11 isolation changed")
    if bindings.get("u11_adjudicated_status") != "failed_execution_invalid_observation" or bindings.get("u11_economic_result_admissible") is not False or bindings.get("u11_retry_authorized") is not False:
        failures.append("U-11 invalid-result semantics changed")
    if bindings.get("u10_run_content_hash") != u10.get("run_content_hash") or u10.get("status") != "failed_feasibility" or u10.get("oos_opened") is not False:
        failures.append("U-10 result binding changed")
    if bindings.get("u09_correction_content_hash") != correction.get("content_hash") or correction.get("status") != "failed_pre_observation_sample_ceiling":
        failures.append("U-09 correction binding changed")
    for number, result in zip((8, 7, 6, 5, 4), prior):
        if bindings.get(f"u0{number}_run_content_hash") != result.get("run_content_hash") or result.get("status") != "failed_feasibility" or result.get("oos_opened") is not False:
            failures.append(f"U-0{number} result binding changed")
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash") or bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash") or bindings.get("source_freeze_hash") != EXPECTED_SOURCE_FREEZE:
        failures.append("data authority binding changed")
    decision = document.get("decision", {})
    required = ("u12_design_authorized", "independent_economic_rationale_required", "u04_through_u10_outcome_derived_direction_threshold_or_rule_prohibited", "u11_invalid_attempt_may_not_be_interpreted_as_economic_result", "u11_execution_defect_repair_or_reuse_prohibited", "outcome_blind_preregistration_required", "separate_protocol_before_any_event_scan", "pre_result_implementation_and_data_scope_preflight_required")
    for key in required:
        if decision.get(key) is not True:
            failures.append(f"invariant changed: {key}")
    if decision.get("maximum_hypotheses") != 1:
        failures.append("maximum hypothesis count changed")
    expected = {"u12_hypothesis_design": True, "public_data_read": False, "event_scan": False, "signals": False, "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    stops = " ".join(map(str, document.get("stop_conditions", [])))
    if "may not be repaired, retried or repackaged" not in stops or "may not be treated as evidence" not in stops:
        failures.append("invalid-attempt reuse prohibition missing")
    return failures


def main() -> int:
    load = lambda path: json.loads(path.read_text())
    failures = validate(load(DECISION), load(U11_ATTEMPT), U11_ADJUDICATION.read_text(), load(U10_RESULT), load(CORRECTION), [load(path) for path in PRIOR_RESULTS], load(AUDIT))
    if failures:
        print("u12_design_authorization_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_design_authorization_check PASS hash={EXPECTED_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
