#!/usr/bin/env python3
"""Run U-16 result-free source qualification, structural ceiling and synthetic complexity Gate."""
from __future__ import annotations
import argparse,json,resource,sys,time
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Iterator,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from btc_eth_dual_quant.data.u16_correlation_breakdown import CorrelationCandidatePath,evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,FIVE_MINUTES_MS,build_membership,month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG,ordered,read_open_times,required_tasks
CONFIG=ROOT/"config/u16_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u16_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u16_cross_sectional_paper_protocol_v1.json";HOUR_MS=3_600_000
def canonical_hash(d:Mapping[str,Any])->str:return identity_hash({k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}})
def rss_mib()->float:
    v=float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);return v/(1024*1024) if sys.platform=="darwin" else v/1024
BASE=tuple(.001 if i%2==0 else -.001 for i in range(36));PEER_RECENT=tuple(.001 if i%2==0 else -.001 for i in range(12));EVENT_RECENT=(.003,)*8+(0.0,)*4;NON_EVENT_RECENT=(0.0,)*12;PATH=(.003,.006,.010,.014,.019,.025)
def synthetic_rows(total:int)->Iterator[CorrelationCandidatePath]:
    for i in range(total):
        candidate=BASE+(EVENT_RECENT if i%100==0 else NON_EVENT_RECENT)
        yield CorrelationCandidatePath(i*14_400_000,f"S{i%15:02d}USDT",candidate,BASE+PEER_RECENT,PATH)
def complexity(config:Mapping[str,Any])->dict[str,Any]:
    c=config["complexity_benchmark"];passes=[];digest=None
    for i in range(int(c["benchmark_passes_required"])):
        started=time.perf_counter();result=evaluate_stream(synthetic_rows(int(c["synthetic_fixture_rows"])));elapsed=time.perf_counter()-started;got=identity_hash(result);peak=rss_mib()
        if elapsed>float(c["maximum_elapsed_seconds_per_pass"]) or peak>float(c["maximum_peak_rss_mib"]) or result["input_rows"]!=int(c["synthetic_fixture_rows"]):raise QualificationFailure("complexity Gate failed")
        if digest is not None and got!=digest:raise QualificationFailure("complexity output mismatch")
        digest=got;passes.append({"pass":i+1,"fixture_rows":result["input_rows"],"elapsed_seconds":f"{elapsed:.6f}","peak_rss_mib":f"{peak:.3f}","output_hash":got})
    return {"status":"pass","passes":passes,"same_code_path":c["same_event_and_path_code_path"],"market_outcomes_read":0,"synthetic_output_hash":digest}
def structural_preflight(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
    c=config["structural_preflight"];start,end=utc_ms(c["is_start"]),utc_ms(c["is_end_exclusive"]);membership=build_membership(load_json(EVIDENCE/"membership_manifest.json"));masked={(str(r["symbol"]),int(r["open_time_ms"])) for r in load_json(EVIDENCE/"invalid_interval_slot_mask_manifest.json")["content"]};tasks=required_tasks(membership,end);orders=[];primary=None
    for order in c["traversal_orders"]:
        available=defaultdict(set);missing=[]
        for month,symbol in ordered(tasks,order,int(c["deterministic_shuffle_seed"])):
            rows=read_open_times(raw_root,symbol,month,end)
            if rows is None:missing.append(f"{symbol}:{month}")
            else:available[symbol].update(rows)
        canonical={"available_open_time_hashes":{s:identity_hash(sorted(v)) for s,v in sorted(available.items())},"missing_archives":sorted(missing)};orders.append({"order":order,"content_identity_hash":identity_hash(canonical),"task_count":len(tasks),"missing_archive_count":len(missing)})
        if primary is None:primary=available
    if len({x["content_identity_hash"] for x in orders})!=1:raise QualificationFailure("same-reader order mismatch")
    assert primary is not None;eligible=[];reasons=Counter();decision=start
    history_ms=int(c["history_hours"])*HOUR_MS;future_ms=int(c["future_path_hours"])*HOUR_MS;step=int(c["decision_step_hours"])*HOUR_MS
    while decision+future_ms<=end:
        members=tuple(membership.get(month_for_ms(decision-1),()))
        if len(members)<int(c["minimum_active_members"]):reasons["membership_below_minimum"]+=1;decision+=step;continue
        future_membership_constant=all(tuple(membership.get(month_for_ms(t),()))==members for t in range(decision,decision+future_ms,HOUR_MS))
        if not future_membership_constant:reasons["future_membership_change_right_censor"]+=1;decision+=step;continue
        valid=True
        for symbol in members:
            values=primary.get(symbol,set())
            for opened in range(decision-history_ms,decision+future_ms,FIVE_MINUTES_MS):
                if opened not in values or (symbol,opened) in masked:valid=False;break
            if not valid:break
        if valid:eligible.append(decision)
        else:reasons["48h_history_or_24h_path_slot_failure"]+=1
        decision+=step
    selected=[];previous=None;cluster=int(c["cluster_connected_window_hours"])*HOUR_MS
    for value in eligible:
        if previous is None or value-previous>cluster:selected.append(value);previous=value
    if len(selected)<int(c["minimum_theoretical_eligible_24h_episodes"]):raise QualificationFailure(f"sample ceiling Gate failed: {len(selected)}")
    years=Counter(datetime.fromtimestamp(v/1000,tz=timezone.utc).year for v in selected)
    return {"orders":orders,"counts":{"same_reader_task_count":len(tasks),"missing_archive_count":orders[0]["missing_archive_count"],"eligible_structural_decisions":len(eligible),"maximum_independent_theoretical_24h_episodes":len(selected),"ineligible_reasons":dict(sorted(reasons.items())),"maximum_independent_episodes_by_year":{str(k):v for k,v in sorted(years.items())}}}
def qualify(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
    if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract drift")
    protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
    if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("critical_findings") or review.get("high_findings"):raise QualificationFailure("protocol/review drift")
    base_config=load_json(BASE_CONFIG)
    if base_config.get("content_hash")!=config["base_v4_qualification_contract_hash"]:raise QualificationFailure("base contract drift")
    bench=complexity(config);base=qualify_base(raw_root=raw_root,config=base_config);preflight=structural_preflight(raw_root,config);iso=config["isolation_contract"]
    result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":base["source_freeze_hash"],"v4_artifact_set_hash":base["v4_artifact_set_hash"],"manifest_hashes":base["manifest_hashes"],"source_orders":base["orders"],"same_reader_orders":preflight["orders"],"complexity_benchmark":bench,"counts":{**base["counts"],**preflight["counts"]},"isolation":{"is_start":iso["is_start"],"is_end_exclusive":iso["is_end_exclusive"],"oos_opened":False,"oos_archive_access":iso["oos_archive_access"],"oos_ohlcv_values_decoded":0,"price_fields_decoded_during_preflight":0,"common_path_rows_generated":0,"correlation_rows_generated":0,"candidate_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");p.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u16_cross_sectional_data_qualification_v1.json");a=p.parse_args();result=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n");print(f"U-16 qualification PASS ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
