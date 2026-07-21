#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from datetime import datetime,timedelta
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,identity_hash,load_json
from scripts.u05_cross_sectional_data_qualification import git_json,qualify as qualify_base
from scripts.u06_cross_sectional_data_qualification import verify_daily_authority
CONFIG=ROOT/"config/u10_cross_sectional_data_qualification_v1.json";BASE_CONFIG=ROOT/"config/u05_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u10_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u10_cross_sectional_paper_protocol_v1.json"
def canonical_hash(d:Mapping[str,Any])->str:return identity_hash({k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}})
def verify_ceiling(config:Mapping[str,Any])->dict[str,Any]:
 c=config["sample_ceiling_contract"];d=datetime.fromisoformat(c["is_start"].replace("Z","+00:00"));end=datetime.fromisoformat(c["is_end_exclusive"].replace("Z","+00:00"));eligible=[]
 while d+timedelta(days=c["reference_offset_days"])<=end:
  ref=d+timedelta(days=c["reference_offset_days"]);last=ref+timedelta(hours=c["primary_horizon_hours"])-timedelta(minutes=5)
  if (ref.year,ref.month)==(last.year,last.month):eligible.append(d)
  d+=timedelta(days=1)
 selected=[];previous=None;window=timedelta(hours=c["cluster_connected_window_hours"])
 for day in eligible:
  if previous is None or day-previous>window:selected.append(day);previous=day
 if len(eligible)!=c["eligible_constant_membership_decision_days"] or len(selected)!=c["maximum_independent_constant_membership_episodes"]:raise QualificationFailure("sample ceiling identity drift")
 if len(selected)<c["protocol_minimum_theoretical_episodes"] or len(selected)<c["paper_complete_is_episode_gate"]:raise QualificationFailure("sample ceiling Gate failed")
 return {"eligible_constant_membership_decision_days":len(eligible),"maximum_independent_constant_membership_episodes":len(selected),"maximum_independent_episodes_by_year":{str(y):sum(x.year==y for x in selected) for y in sorted({x.year for x in selected})}}
def qualify(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract hash drift")
 protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
 if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:raise QualificationFailure("protocol/review binding drift")
 base=load_json(BASE_CONFIG)
 if base.get("content_hash")!=config["base_v4_qualification_contract_hash"]:raise QualificationFailure("base contract drift")
 base_result=qualify_base(raw_root=raw_root,config=base);daily=verify_daily_authority(config);ceiling=verify_ceiling(config)
 if base_result["source_freeze_hash"]!=config["authority_bindings"]["source_freeze_hash"] or base_result["v4_artifact_set_hash"]!=config["authority_bindings"]["v4_artifact_set_hash"]:raise QualificationFailure("V4 authority drift")
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":base_result["source_freeze_hash"],"v4_artifact_set_hash":base_result["v4_artifact_set_hash"],"manifest_hashes":base_result["manifest_hashes"],"orders":base_result["orders"],"counts":{**base_result["counts"],**daily,**ceiling},"isolation":{"is_start":c["is_start"] if (c:=config["isolation_contract"]) else None,"is_end_exclusive":c["is_end_exclusive"],"oos_opened":False,"oos_ohlcv_values_decoded":0,"daily_signal_rows_generated":0,"candidate_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u10_cross_sectional_data_qualification_v1.json");a=ap.parse_args();r=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(f"U-10 qualification PASS archives={r['counts']['archive_count']} ceiling={r['counts']['maximum_independent_constant_membership_episodes']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
