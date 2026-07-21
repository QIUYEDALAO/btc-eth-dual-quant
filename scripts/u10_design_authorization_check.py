#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];DECISION=ROOT/"config/u10_design_authorization_v1.json";CORRECTION=ROOT/"reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json";RESULTS=[ROOT/f"reports/m1/evidence/u0{i}_cross_sectional_paper_observation/run_manifest.json" for i in (8,7,6,5,4)];AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json";EXPECTED_SOURCE_FREEZE="c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c";EXPECTED_HASH="e196cc0fdd20e8b8fc84872b440baa09ae69e0752c75005bebefb51a4060c7a0"
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],correction:Mapping[str,Any],results:list[Mapping[str,Any]],audit:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=EXPECTED_HASH or canonical_hash(identity)!=EXPECTED_HASH:f.append("U-10 decision identity changed")
 b=d.get("bindings",{})
 if b.get("u09_correction_content_hash")!=correction.get("content_hash") or correction.get("status")!="failed_pre_observation_sample_ceiling" or correction.get("isolation",{}).get("oos_opened") is not False:f.append("U-09 correction binding changed")
 for number,prior in zip((8,7,6,5,4),results):
  if b.get(f"u0{number}_run_content_hash")!=prior.get("run_content_hash"):f.append(f"U-0{number} result binding changed")
  if prior.get("status")!="failed_feasibility" or prior.get("oos_opened") is not False or prior.get("second_run_executed") is not False:f.append(f"U-0{number} must remain failed, single-run and OOS-sealed")
 if b.get("adr0015_audit_summary_hash")!=audit.get("audit_summary_hash") or b.get("v4_artifact_set_hash")!=audit.get("independent_artifact_set_hash") or b.get("source_freeze_hash")!=EXPECTED_SOURCE_FREEZE:f.append("data authority binding changed")
 decision=d.get("decision",{})
 for k in ("u10_design_authorized","independent_economic_rationale_required","u04_through_u08_outcome_derived_direction_or_rule_prohibited","u09_protocol_feasibility_defect_reuse_prohibited","outcome_blind_preregistration_required","separate_protocol_before_any_event_scan"):
  if decision.get(k) is not True:f.append(f"invariant changed: {k}")
 if decision.get("maximum_hypotheses")!=1:f.append("maximum hypothesis count changed")
 expected={"u10_hypothesis_design":True,"event_scan":False,"signals":False,"returns":False,"strategy_rule_selection":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if d.get("authorizations")!=expected:f.append("authorization matrix changed")
 if not any("may not be repaired" in str(x) for x in d.get("stop_conditions",[])):f.append("U-09 defect reuse prohibition missing")
 return f
def main()->int:
 load=lambda p:json.loads(p.read_text());f=validate(load(DECISION),load(CORRECTION),[load(p) for p in RESULTS],load(AUDIT))
 if f:print("u10_design_authorization_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u10_design_authorization_check PASS hash={EXPECTED_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
