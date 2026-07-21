#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECISION = ROOT / "config/u11_design_authorization_v1.json"
U10_RESULT = ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation/run_manifest.json"
CORRECTION = ROOT / "reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json"
PRIOR_RESULTS = [ROOT / f"reports/m1/evidence/u0{number}_cross_sectional_paper_observation/run_manifest.json" for number in (8, 7, 6, 5, 4)]
AUDIT = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_SOURCE_FREEZE = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
EXPECTED_HASH = "c5db3dc0c01bc4e1ffe381150c132742446ce4b05b3fb8c381dc03612cff274a"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(decision_document: Mapping[str, Any], u10: Mapping[str, Any], correction: Mapping[str, Any], prior_results: list[Mapping[str, Any]], audit: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in decision_document.items() if key not in {"content_hash", "generated_utc"}}
    if decision_document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("U-11 decision identity changed")
    bindings = decision_document.get("bindings", {})
    if bindings.get("u10_run_content_hash") != u10.get("run_content_hash") or bindings.get("u10_three_order_identity_hash") != u10.get("orders", [{}])[0].get("content_identity_hash"):
        failures.append("U-10 result binding changed")
    if u10.get("status") != "failed_feasibility" or u10.get("oos_opened") is not False or u10.get("second_run_executed") is not False:
        failures.append("U-10 must remain failed, single-run and OOS-sealed")
    if bindings.get("u09_correction_content_hash") != correction.get("content_hash") or correction.get("status") != "failed_pre_observation_sample_ceiling":
        failures.append("U-09 correction binding changed")
    for number, prior in zip((8, 7, 6, 5, 4), prior_results):
        if bindings.get(f"u0{number}_run_content_hash") != prior.get("run_content_hash") or prior.get("status") != "failed_feasibility" or prior.get("oos_opened") is not False:
            failures.append(f"U-0{number} result binding changed")
    if bindings.get("adr0015_audit_summary_hash") != audit.get("audit_summary_hash") or bindings.get("v4_artifact_set_hash") != audit.get("independent_artifact_set_hash") or bindings.get("source_freeze_hash") != EXPECTED_SOURCE_FREEZE:
        failures.append("data authority binding changed")
    decision = decision_document.get("decision", {})
    required = ("u11_design_authorized", "independent_economic_rationale_required", "u04_through_u10_outcome_derived_direction_threshold_or_rule_prohibited", "u09_sample_defect_reuse_prohibited", "u10_sparse_sample_or_path_result_repair_prohibited", "outcome_blind_preregistration_required", "separate_protocol_before_any_event_scan")
    for key in required:
        if decision.get(key) is not True:
            failures.append(f"invariant changed: {key}")
    if decision.get("maximum_hypotheses") != 1:
        failures.append("maximum hypothesis count changed")
    expected = {"u11_hypothesis_design": True, "event_scan": False, "signals": False, "returns": False, "strategy_rule_selection": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if decision_document.get("authorizations") != expected:
        failures.append("authorization matrix changed")
    if not any("may not be repaired" in str(item) for item in decision_document.get("stop_conditions", [])):
        failures.append("prior defect/result reuse prohibition missing")
    return failures


def main() -> int:
    load = lambda path: json.loads(path.read_text())
    failures = validate(load(DECISION), load(U10_RESULT), load(CORRECTION), [load(path) for path in PRIOR_RESULTS], load(AUDIT))
    if failures:
        print("u11_design_authorization_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u11_design_authorization_check PASS hash={EXPECTED_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
