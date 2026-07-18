#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];DECISION=ROOT/"config/u23_design_authorization_v1.json";FAILURE=ROOT/"reports/m1/evidence/u22_cross_sectional_paper_observation/run_manifest.json";PRIOR=ROOT/"config/u22_design_authorization_v1.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json";EXPECTED="70c60434bb7c78344eb733eb8a8d4393538f60bbc97bff60e840c68f10998d5a"
def identity_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],f:Mapping[str,Any],p:Mapping[str,Any],a:Mapping[str,Any])->list[str]:
 out=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}};b=d.get("bindings",{})
 if d.get("content_hash")!=EXPECTED or identity_hash(identity)!=EXPECTED:out.append("identity")
 if b.get("u22_run_content_hash")!=f.get("run_content_hash") or f.get("status")!="failed_feasibility":out.append("U-22 result")
 if f.get("oos_opened") is not False or f.get("formal_returns_computed") is not False or f.get("second_run_executed") is not False:out.append("U-22 isolation")
 if b.get("u22_protocol_content_hash")!=f.get("protocol_content_hash") or b.get("u22_design_authorization_hash")!=p.get("content_hash") or b.get("adr0015_audit_summary_hash")!=a.get("audit_summary_hash") or b.get("v4_artifact_set_hash")!=a.get("independent_artifact_set_hash") or b.get("source_freeze_hash")!=a.get("diagnostics",{}).get("source_freeze_content_hash"):out.append("authority")
 req=("u23_design_authorized","independent_economic_rationale_required","u04_through_u22_outcome_direction_threshold_rule_censor_or_failure_reuse_prohibited","u22_negative_result_inversion_repair_relabeling_or_repackaging_prohibited","prior_failed_candidate_repair_retry_inversion_or_relabeling_prohibited","outcome_blind_preregistration_required","synthetic_only_exact_core_complexity_feasibility_required_before_protocol_freeze","separate_protocol_before_any_public_data_or_event_scan","pre_result_data_authority_sample_ceiling_and_complexity_preflight_required");rules=d.get("decision",{})
 if rules.get("maximum_hypotheses")!=1 or any(rules.get(k) is not True for k in req):out.append("decision")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["u23_hypothesis_design"]:out.append("authorization")
 return out
def main()->int:
 load=lambda p:json.loads(p.read_text());f=validate(load(DECISION),load(FAILURE),load(PRIOR),load(AUDIT));print("u23_design_authorization_check "+("PASS" if not f else "FAIL")+f" hash={EXPECTED}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
