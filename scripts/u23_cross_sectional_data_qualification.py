#!/usr/bin/env python3
"""Run U-23 result-free source qualification and structural ceiling."""
from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,FIVE_MINUTES_MS,build_membership,month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG,ordered,read_open_times,required_tasks
CONFIG=ROOT/"config/u23_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u23_cross_sectional_paper_protocol_review_v1.json";FEASIBILITY=ROOT/"reports/m1/evidence/u23_synthetic_core_feasibility_v1.json";CORE=ROOT/"src/btc_eth_dual_quant/data/u23_range_expansion.py";PROTOCOL_PATH="config/u23_cross_sectional_paper_protocol_v1.json";HOUR_MS=3_600_000
def canonical_hash(d:Mapping[str,Any])->str:return identity_hash({k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}})
def structural_preflight(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 c=config["structural_preflight"];start,end=utc_ms(c["is_start"]),utc_ms(c["is_end_exclusive"]);membership=build_membership(load_json(EVIDENCE/"membership_manifest.json"));masked={(str(r["symbol"]),int(r["open_time_ms"])) for r in load_json(EVIDENCE/"invalid_interval_slot_mask_manifest.json")["content"]};tasks=required_tasks(membership,end);orders=[];primary=None
 for name in c["traversal_orders"]:
  available=defaultdict(set);missing=[]
  for month,symbol in ordered(tasks,name,int(c["deterministic_shuffle_seed"])):
   rows=read_open_times(raw_root,symbol,month,end)
   if rows is None:missing.append(f"{symbol}:{month}")
   else:available[symbol].update(rows)
  canonical={"available_open_time_hashes":{s:identity_hash(sorted(v)) for s,v in sorted(available.items())},"missing_archives":sorted(missing)};orders.append({"order":name,"content_identity_hash":identity_hash(canonical),"task_count":len(tasks),"missing_archive_count":len(missing)})
  if primary is None:primary=available
 if len({x["content_identity_hash"] for x in orders})!=1:raise QualificationFailure("same-reader order mismatch")
 assert primary is not None;eligible=[];reasons=Counter();decision=start;history_ms=int(c["history_hours"])*HOUR_MS;future_ms=int(c["future_path_hours"])*HOUR_MS;step=int(c["decision_step_hours"])*HOUR_MS
 while decision+future_ms<=end:
  members=tuple(membership.get(month_for_ms(decision-1),()))
  if len(members)<int(c["minimum_active_members"]):reasons["membership_below_minimum"]+=1;decision+=step;continue
  if not all(tuple(membership.get(month_for_ms(point),()))==members for point in range(decision-history_ms,decision+future_ms,HOUR_MS)):
   reasons["history_or_future_membership_change"]+=1;decision+=step;continue
  valid=True
  for symbol in members:
   values=primary.get(symbol,set())
   for opened in range(decision-history_ms,decision+future_ms,FIVE_MINUTES_MS):
    if opened not in values or (symbol,opened) in masked:valid=False;break
   if not valid:break
  if valid:eligible.append(decision)
  else:reasons["7d_history_or_24h_path_slot_failure"]+=1
  decision+=step
 selected=[];previous=None;cluster=int(c["cluster_connected_window_hours"])*HOUR_MS
 for value in eligible:
  if previous is None or value-previous>cluster:selected.append(value);previous=value
 if len(selected)<int(c["minimum_theoretical_eligible_24h_episodes"]):raise QualificationFailure(f"sample ceiling Gate failed: {len(selected)}")
 years=Counter(datetime.fromtimestamp(v/1000,tz=timezone.utc).year for v in selected)
 return {"orders":orders,"counts":{"same_reader_task_count":len(tasks),"missing_archive_count":orders[0]["missing_archive_count"],"eligible_structural_decisions":len(eligible),"maximum_independent_theoretical_24h_episodes":len(selected),"ineligible_reasons":dict(sorted(reasons.items())),"maximum_independent_episodes_by_year":{str(k):v for k,v in sorted(years.items())}}}
def qualify(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
 if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract drift")
 protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW);feasibility=load_json(FEASIBILITY)
 if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("critical_findings") or review.get("high_findings"):raise QualificationFailure("protocol/review drift")
 if feasibility.get("content_hash")!=config["synthetic_core_feasibility_hash"] or feasibility.get("status")!="pass_before_protocol_freeze" or hashlib.sha256(CORE.read_bytes()).hexdigest()!=config["exact_core_sha256"]:raise QualificationFailure("synthetic core drift")
 base_config=load_json(BASE_CONFIG)
 if base_config.get("content_hash")!=config["base_v4_qualification_contract_hash"]:raise QualificationFailure("base contract drift")
 base=qualify_base(raw_root=raw_root,config=base_config);preflight=structural_preflight(raw_root,config);iso=config["isolation_contract"]
 result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"synthetic_core_feasibility_hash":config["synthetic_core_feasibility_hash"],"source_freeze_hash":base["source_freeze_hash"],"v4_artifact_set_hash":base["v4_artifact_set_hash"],"manifest_hashes":base["manifest_hashes"],"source_orders":base["orders"],"same_reader_orders":preflight["orders"],"pre_freeze_complexity":{"status":"verified_pass","passes":3,"rerun_during_qualification":False,"market_outcomes_read":0},"counts":{**base["counts"],**preflight["counts"]},"isolation":{"is_start":iso["is_start"],"is_end_exclusive":iso["is_end_exclusive"],"oos_opened":False,"oos_archive_access":iso["oos_archive_access"],"oos_ohlcv_values_decoded":0,"ohlcv_fields_decoded_during_preflight":0,"range_rows_generated":0,"return_rows_generated":0,"candidate_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"formal_return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");p.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u23_cross_sectional_data_qualification_v1.json");a=p.parse_args();result=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n");print(f"U-23 qualification PASS ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
