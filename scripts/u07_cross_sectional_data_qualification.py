#!/usr/bin/env python3
"""Qualify U-07 frozen V4 4h/1h/5m authority without events or outcomes."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any, Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import EVIDENCE, QualificationFailure, _verify_authority_content, _verify_manifest_hashes, content_hash, identity_hash, load_json, ordered, verify_archive
from scripts.u05_cross_sectional_data_qualification import _verify_named_bindings, git_json, verify_four_hour_authority

CONFIG=ROOT/"config/u07_cross_sectional_data_qualification_v1.json"
REVIEW=ROOT/"reports/expert/evidence/u07_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH="config/u07_cross_sectional_paper_protocol_v1.json"

def qualify(*,raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if content_hash(config)!=config.get("content_hash"):raise QualificationFailure("U-07 qualification contract hash drift")
 protocol=git_json(str(config["protocol_target_commit"]),PROTOCOL_PATH);review=load_json(REVIEW)
 if protocol.get("content_hash")!=config["protocol_content_hash"]:raise QualificationFailure("target protocol binding drift")
 for key in ("membership_authority_hash","lifecycle_registry_hash"):
  if protocol.get("authority_bindings",{}).get(key)!=config["authority_bindings"].get(key):raise QualificationFailure(f"protocol authority binding drift: {key}")
 if review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:raise QualificationFailure("protocol review is not exact approve 0/0")
 manifest_hashes=_verify_manifest_hashes(config);_verify_named_bindings(config,manifest_hashes);counts=_verify_authority_content(config);four_hour=verify_four_hour_authority(config)
 freeze=load_json(EVIDENCE/"source_freeze_manifest.json")
 if identity_hash(freeze["content"])!=config["authority_bindings"]["source_freeze_hash"]:raise QualificationFailure("source-freeze content drift")
 archives=freeze["content"]["archives"]
 if len(archives)!=config["authority_bindings"]["source_archive_count"]:raise QualificationFailure("source archive count drift")
 source=config["source_verification"]
 verified=[verify_archive(raw_root,binding) for binding in ordered(archives,"normal",source["deterministic_shuffle_seed"])]
 order_rows=[]
 for order in source["traversal_orders"]:
  traversal=ordered(verified,order,source["deterministic_shuffle_seed"]);canonical=sorted(traversal,key=lambda item:(item["canonical_key"],item["sha256"],item["byte_size"]))
  order_rows.append({"order":order,"content_identity_hash":identity_hash(canonical),"archive_count":len(canonical)})
 if len({row["content_identity_hash"] for row in order_rows})!=1:raise QualificationFailure("source traversal identity mismatch")
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":config["authority_bindings"]["source_freeze_hash"],"v4_artifact_set_hash":config["authority_bindings"]["v4_artifact_set_hash"],"manifest_hashes":manifest_hashes,"orders":order_rows,"counts":{**counts,**four_hour,"archive_count":len(verified),"manifests_exact":len(manifest_hashes)},"isolation":{"is_start":config["isolation_contract"]["is_start"],"is_end_exclusive":config["isolation_contract"]["is_end_exclusive"],"oos_opened":False,"oos_archive_access":"opaque_identity_and_crc_only","oos_ohlc_values_decoded":0,"market_stress_rows_generated":0,"relative_resilience_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"event_scan_beyond_one_frozen_is_observation":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False}
 result["qualification_content_hash"]=identity_hash(result);return result

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u07_cross_sectional_data_qualification_v1.json");a=ap.parse_args();r=qualify(raw_root=a.raw_root,config=load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n",encoding="utf-8");print(f"U-07 data qualification PASS archives={r['counts']['archive_count']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
