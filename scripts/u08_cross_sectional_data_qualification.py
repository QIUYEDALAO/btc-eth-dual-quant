#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import EVIDENCE,QualificationFailure,_verify_authority_content,_verify_manifest_hashes,content_hash,identity_hash,load_json,ordered,verify_archive
from scripts.u05_cross_sectional_data_qualification import _verify_named_bindings,git_json
CONFIG=ROOT/"config/u08_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u08_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u08_cross_sectional_paper_protocol_v1.json"
def verify_ranks(config:Mapping[str,Any])->dict[str,int]:
 rows=load_json(EVIDENCE/"membership_manifest.json")["content"];by_month=defaultdict(list)
 for row in rows:
  if row.get("eligibility_status")=="qualified":by_month[str(row["effective_month"])[:7]].append(row)
 gates=config["membership_rank_gates"]
 if len(rows)!=gates["membership_rows"] or len(by_month)!=gates["expected_months"]:raise QualificationFailure("membership row/month count drift")
 required=gates["required_ranks"]
 for month,items in by_month.items():
  if len(items)!=gates["members_per_month"] or sorted(int(x["rank"]) for x in items)!=required or len({x["symbol"] for x in items})!=len(items):raise QualificationFailure(f"membership rank identity drift: {month}")
  effective=f"{month}-01"
  for row in items:
   volume=Decimal(str(row["median_daily_quote_volume_90d"]))
   if row["ranking_window_end_exclusive"]!=effective or row["history_window_end_exclusive"]!=effective or not volume.is_finite() or volume<=0:raise QualificationFailure(f"prior-only rank authority drift: {month}")
 return {"membership_rows":len(rows),"membership_months":len(by_month),"rank_rows_verified":sum(map(len,by_month.values()))}
def qualify(*,raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if content_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract hash drift")
 protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
 if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:raise QualificationFailure("protocol/review binding drift")
 manifests=_verify_manifest_hashes(config);_verify_named_bindings(config,manifests);counts=_verify_authority_content(config);ranks=verify_ranks(config)
 freeze=load_json(EVIDENCE/"source_freeze_manifest.json")
 if identity_hash(freeze["content"])!=config["authority_bindings"]["source_freeze_hash"]:raise QualificationFailure("source freeze drift")
 archives=freeze["content"]["archives"];seed=config["source_verification"]["deterministic_shuffle_seed"]
 verified=[verify_archive(raw_root,x) for x in ordered(archives,"normal",seed)];orders=[]
 for order in config["source_verification"]["traversal_orders"]:
  canonical=sorted(ordered(verified,order,seed),key=lambda x:(x["canonical_key"],x["sha256"],x["byte_size"]));orders.append({"order":order,"content_identity_hash":identity_hash(canonical),"archive_count":len(canonical)})
 if len({x["content_identity_hash"] for x in orders})!=1:raise QualificationFailure("order mismatch")
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":config["authority_bindings"]["source_freeze_hash"],"v4_artifact_set_hash":config["authority_bindings"]["v4_artifact_set_hash"],"manifest_hashes":manifests,"orders":orders,"counts":{**counts,**ranks,"archive_count":len(verified),"manifests_exact":len(manifests)},"isolation":{"is_start":config["isolation_contract"]["is_start"],"is_end_exclusive":config["isolation_contract"]["is_end_exclusive"],"oos_opened":False,"oos_ohlc_values_decoded":0,"membership_entry_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u08_cross_sectional_data_qualification_v1.json");a=ap.parse_args();r=qualify(raw_root=a.raw_root,config=load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(f"U-08 data qualification PASS archives={r['counts']['archive_count']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
