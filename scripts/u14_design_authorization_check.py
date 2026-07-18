#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1]
DECISION=ROOT/"config/u14_design_authorization_v1.json"
U13_RESULT=ROOT/"reports/m1/evidence/u13_cross_sectional_paper_observation/run_manifest.json"
U13_DECISION=ROOT/"config/u13_design_authorization_v1.json"
AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
EXPECTED_HASH="ebcf8b78a75911a2567bf84d58363d3c4bd554ec0495bb63457c4d593e34e640"
def canonical_hash(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(document:Mapping[str,Any],u13:Mapping[str,Any],prior:Mapping[str,Any],audit:Mapping[str,Any])->list[str]:
    failures=[];identity={k:v for k,v in document.items() if k not in {"content_hash","generated_utc"}}
    if document.get("content_hash")!=EXPECTED_HASH or canonical_hash(identity)!=EXPECTED_HASH:failures.append("U-14 decision identity changed")
    bindings=document.get("bindings",{})
    if bindings.get("u13_run_content_hash")!=u13.get("run_content_hash") or bindings.get("u13_three_order_identity_hash")!=u13.get("orders",[{}])[0].get("content_identity_hash") or u13.get("status")!="failed_feasibility":failures.append("U-13 result binding changed")
    if u13.get("oos_opened") is not False or u13.get("second_run_executed") is not False or u13.get("formal_returns_computed") is not False:failures.append("U-13 isolation changed")
    if bindings.get("u13_design_authorization_hash")!=prior.get("content_hash"):failures.append("prior chain binding changed")
    if bindings.get("adr0015_audit_summary_hash")!=audit.get("audit_summary_hash") or bindings.get("v4_artifact_set_hash")!=audit.get("independent_artifact_set_hash"):failures.append("data authority binding changed")
    decision=document.get("decision",{});required=("u14_design_authorized","independent_economic_rationale_required","u04_through_u13_outcome_direction_threshold_rule_or_censor_reuse_prohibited","prior_failed_candidate_repair_retry_or_inversion_prohibited","outcome_blind_preregistration_required","separate_protocol_before_any_event_scan","pre_result_complexity_benchmark_required","pre_result_implementation_and_data_scope_preflight_required")
    if any(decision.get(k) is not True for k in required) or decision.get("maximum_hypotheses")!=1:failures.append("decision invariant changed")
    expected={"u14_hypothesis_design":True,"public_data_read":False,"event_scan":False,"signals":False,"returns":False,"strategy_rule_selection":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if document.get("authorizations")!=expected:failures.append("authorization matrix changed")
    stops=" ".join(map(str,document.get("stop_conditions",[])))
    if "may not select U-14" not in stops or "repaired, retried, inverted, relabeled or repackaged" not in stops or "complexity benchmark" not in stops:failures.append("reuse or complexity prohibition missing")
    return failures
def main()->int:
    load=lambda p:json.loads(p.read_text());failures=validate(load(DECISION),load(U13_RESULT),load(U13_DECISION),load(AUDIT))
    if failures:
        print("u14_design_authorization_check FAIL");[print(f"- {x}") for x in failures];return 1
    print(f"u14_design_authorization_check PASS hash={EXPECTED_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
