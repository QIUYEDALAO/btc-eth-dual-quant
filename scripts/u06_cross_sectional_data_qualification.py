#!/usr/bin/env python3
"""Qualify U-06 frozen V4 daily price/quote-volume authority without outcomes."""
from __future__ import annotations
import argparse, json, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import EVIDENCE, QualificationFailure, identity_hash, load_json
from scripts.u05_cross_sectional_data_qualification import git_json, qualify as qualify_base

CONFIG=ROOT/"config/u06_cross_sectional_data_qualification_v1.json"; BASE_CONFIG=ROOT/"config/u05_cross_sectional_data_qualification_v1.json"
REVIEW=ROOT/"reports/expert/evidence/u06_cross_sectional_paper_protocol_review_v1.json"; PROTOCOL_PATH="config/u06_cross_sectional_paper_protocol_v1.json"

def canonical_hash(doc:Mapping[str,Any])->str:
 return identity_hash({k:v for k,v in doc.items() if k not in {"content_hash","generated_utc"}})

def verify_daily_authority(config:Mapping[str,Any])->dict[str,int]:
 contract=config["daily_signal_contract"]
 if contract.get("bars_per_complete_utc_day")!=288 or contract.get("quote_volume_column_index")!=7 or contract.get("masked_or_missing_5m_action")!="entire_member_day_ineligible" or contract.get("later_day_or_member_substitution_allowed") is not False: raise QualificationFailure("daily signal contract drift")
 membership=load_json(EVIDENCE/"membership_manifest.json")["content"]
 positive=0
 for row in membership:
  try:value=Decimal(str(row["median_daily_quote_volume_90d"]))
  except (KeyError,InvalidOperation):raise QualificationFailure("daily quote-volume authority unavailable")
  if not value.is_finite() or value<=0:raise QualificationFailure("nonpositive/nonfinite daily quote-volume authority")
  positive+=1
 grid=load_json(EVIDENCE/"expected_grid_manifest.json")["content"]
 expected_rows=sum(int(row["expected_count"]) for row in grid)
 complete_grid_rows=sum(1 for row in grid if row.get("complete") is True)
 mask=load_json(EVIDENCE/"complete_day_mask.json")["content"]
 invalid_slots=sum(len(row["active_members"]) for row in mask["invalid_interval_quarantined_days"])
 return {"quote_volume_authority_rows":positive,"expected_five_minute_rows":expected_rows,"complete_symbol_month_grids":complete_grid_rows,"invalid_interval_member_days":invalid_slots,"bars_per_complete_day":288}

def qualify(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("U-06 qualification contract hash drift")
 protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
 if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"]:raise QualificationFailure("protocol/review binding drift")
 if review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:raise QualificationFailure("review is not approve 0/0")
 base=load_json(BASE_CONFIG)
 if base.get("content_hash")!=config["base_v4_qualification_contract_hash"]:raise QualificationFailure("base qualification contract drift")
 base_result=qualify_base(raw_root=raw_root,config=base)
 daily=verify_daily_authority(config)
 if base_result["source_freeze_hash"]!=config["authority_bindings"]["source_freeze_hash"] or base_result["v4_artifact_set_hash"]!=config["authority_bindings"]["v4_artifact_set_hash"]:raise QualificationFailure("V4 authority drift")
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":base_result["source_freeze_hash"],"v4_artifact_set_hash":base_result["v4_artifact_set_hash"],"manifest_hashes":base_result["manifest_hashes"],"orders":base_result["orders"],"counts":{**base_result["counts"],**daily},"isolation":{"is_start":"2020-01-01T00:00:00Z","is_end_exclusive":"2024-09-11T00:00:00Z","oos_opened":False,"oos_archive_access":"opaque_identity_and_crc_only","oos_ohlcv_values_decoded":0,"daily_signal_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"event_scan_beyond_one_frozen_is_observation":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False}
 result["qualification_content_hash"]=identity_hash(result);return result

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u06_cross_sectional_data_qualification_v1.json");a=ap.parse_args();r=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(f"U-06 qualification PASS archives={r['counts']['archive_count']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
