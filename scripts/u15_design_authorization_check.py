#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];DECISION=ROOT/"config/u15_design_authorization_v1.json";RUN=ROOT/"reports/m1/evidence/u14_cross_sectional_paper_observation/run_manifest.json";PRIOR=ROOT/"config/u14_design_authorization_v1.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json";EXPECTED="98d4ec9049d3b40ded8f98c045405eda8a010c783b5597653586853a825b7e68"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],run:Mapping[str,Any],prior:Mapping[str,Any],audit:Mapping[str,Any])->list[str]:
 f=[];i={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}};b=d.get("bindings",{})
 if d.get("content_hash")!=EXPECTED or h(i)!=EXPECTED:f.append("identity")
 if b.get("u14_run_content_hash")!=run.get("run_content_hash") or b.get("u14_three_order_identity_hash")!=run.get("orders",[{}])[0].get("content_identity_hash") or run.get("status")!="failed_feasibility":f.append("U-14 binding")
 if run.get("oos_opened") is not False or run.get("second_run_executed") is not False or run.get("formal_returns_computed") is not False:f.append("U-14 isolation")
 if b.get("u14_design_authorization_hash")!=prior.get("content_hash") or b.get("adr0015_audit_summary_hash")!=audit.get("audit_summary_hash") or b.get("v4_artifact_set_hash")!=audit.get("independent_artifact_set_hash"):f.append("authority")
 required=("u15_design_authorized","independent_economic_rationale_required","u04_through_u14_outcome_direction_threshold_rule_or_censor_reuse_prohibited","prior_failed_candidate_repair_retry_or_inversion_prohibited","outcome_blind_preregistration_required","separate_protocol_before_any_event_scan")
 if d.get("decision",{}).get("maximum_hypotheses")!=1 or any(d.get("decision",{}).get(k) is not True for k in required):f.append("decision")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["u15_hypothesis_design"]:f.append("authorization")
 return f
def main()->int:
 load=lambda p:json.loads(p.read_text());f=validate(load(DECISION),load(RUN),load(PRIOR),load(AUDIT));print("u15_design_authorization_check "+("PASS" if not f else "FAIL")+f" hash={EXPECTED}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
