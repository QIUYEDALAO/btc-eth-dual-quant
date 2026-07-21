#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];DECISION=ROOT/"config/u16_design_authorization_v1.json";FAILURE=ROOT/"reports/m1/evidence/u15_taker_buy_field_qualification_failure_v1.json";PRIOR=ROOT/"config/u15_design_authorization_v1.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json";EXPECTED="05346312b0e47168a17a77cd19d1a73525b17eb9f64de29b2b157a5c673528fc"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],failure:Mapping[str,Any],prior:Mapping[str,Any],audit:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}};b=d.get("bindings",{})
    if d.get("content_hash")!=EXPECTED or h(identity)!=EXPECTED:f.append("identity")
    accounting=failure.get("execution_accounting",{});decision=failure.get("decision",{})
    if b.get("u15_failure_content_hash")!=failure.get("content_hash") or failure.get("status")!="failed_pre_result_field_qualification" or decision.get("candidate_closed") is not True:f.append("U-15 failure binding")
    if b.get("u15_event_rows_generated")!=accounting.get("event_rows_generated") or b.get("u15_return_rows_generated")!=accounting.get("return_rows_generated") or b.get("u15_second_run_executed")!=accounting.get("second_run_executed") or accounting.get("oos_values_decoded")!=0:f.append("U-15 isolation")
    if b.get("u15_design_authorization_hash")!=prior.get("content_hash") or b.get("adr0015_audit_summary_hash")!=audit.get("audit_summary_hash") or b.get("v4_artifact_set_hash")!=audit.get("independent_artifact_set_hash"):f.append("authority")
    required=("u16_design_authorized","independent_economic_rationale_required","u04_through_u15_outcome_direction_threshold_rule_censor_or_failure_reuse_prohibited","u15_field_contract_repair_relaxation_or_repackaging_prohibited","prior_failed_candidate_repair_retry_inversion_or_relabeling_prohibited","outcome_blind_preregistration_required","separate_protocol_before_any_data_or_event_scan")
    if d.get("decision",{}).get("maximum_hypotheses")!=1 or any(d.get("decision",{}).get(k) is not True for k in required):f.append("decision")
    if [k for k,v in d.get("authorizations",{}).items() if v] != ["u16_hypothesis_design"]:f.append("authorization")
    return f
def main()->int:
    load=lambda p:json.loads(p.read_text());f=validate(load(DECISION),load(FAILURE),load(PRIOR),load(AUDIT));print("u16_design_authorization_check "+("PASS" if not f else "FAIL")+f" hash={EXPECTED}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
