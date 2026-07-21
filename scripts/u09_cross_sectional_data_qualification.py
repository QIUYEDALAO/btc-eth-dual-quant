#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import EVIDENCE,QualificationFailure,_verify_authority_content,_verify_manifest_hashes,content_hash,identity_hash,load_json,ordered,verify_archive
from scripts.u05_cross_sectional_data_qualification import _verify_named_bindings,git_json
from scripts.u08_cross_sectional_data_qualification import verify_ranks
CONFIG=ROOT/"config/u09_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u09_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u09_cross_sectional_paper_protocol_v1.json"
def verify_schedule(config:Mapping[str,Any])->dict[str,int]:
 g=config["schedule_gates"];start=datetime.fromisoformat(g["first_anchor"].replace("Z","+00:00"));end=datetime.fromisoformat(config["isolation_contract"]["is_end_exclusive"].replace("Z","+00:00"));step=timedelta(hours=g["anchor_interval_hours"]);horizon=step;anchors=[];x=start
 while x<end:anchors.append(x);x+=step
 complete=[x for x in anchors if x+horizon<=end]
 if len(anchors)!=g["is_anchors_before_boundary"] or len(complete)!=g["is_primary_complete_anchors"] or g["estimation_hours"]!=168 or g["half_window_hours"]*2!=g["estimation_hours"]:raise QualificationFailure("schedule Gate drift")
 return {"is_anchors_before_boundary":len(anchors),"is_primary_complete_anchors":len(complete)}
def qualify(*,raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if content_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract hash drift")
 protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
 if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:raise QualificationFailure("protocol/review binding drift")
 manifests=_verify_manifest_hashes(config);_verify_named_bindings(config,manifests);counts=_verify_authority_content(config);ranks=verify_ranks(config);schedule=verify_schedule(config)
 freeze=load_json(EVIDENCE/"source_freeze_manifest.json")
 if identity_hash(freeze["content"])!=config["authority_bindings"]["source_freeze_hash"]:raise QualificationFailure("source freeze drift")
 archives=freeze["content"]["archives"];seed=config["source_verification"]["deterministic_shuffle_seed"]
 verified=[verify_archive(raw_root,x) for x in ordered(archives,"normal",seed)];orders=[]
 for order in config["source_verification"]["traversal_orders"]:
  canonical=sorted(ordered(verified,order,seed),key=lambda x:(x["canonical_key"],x["sha256"],x["byte_size"]));orders.append({"order":order,"content_identity_hash":identity_hash(canonical),"archive_count":len(canonical)})
 if len({x["content_identity_hash"] for x in orders})!=1:raise QualificationFailure("order mismatch")
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":config["authority_bindings"]["source_freeze_hash"],"v4_artifact_set_hash":config["authority_bindings"]["v4_artifact_set_hash"],"manifest_hashes":manifests,"orders":orders,"counts":{**counts,**ranks,**schedule,"archive_count":len(verified),"manifests_exact":len(manifests)},"isolation":{"is_start":config["isolation_contract"]["is_start"],"is_end_exclusive":config["isolation_contract"]["is_end_exclusive"],"oos_opened":False,"oos_ohlc_values_decoded":0,"cohort_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u09_cross_sectional_data_qualification_v1.json");a=ap.parse_args();r=qualify(raw_root=a.raw_root,config=load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(f"U-09 data qualification PASS archives={r['counts']['archive_count']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
