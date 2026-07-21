#!/usr/bin/env python3
"""Run U-21 result-free source qualification, structural ceiling and complexity Gate."""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
from typing import Any,Iterator,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"src")]
from btc_eth_dual_quant.data.u21_systematic_cokurtosis import CokurtosisCandidatePath,evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,identity_hash,load_json
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG
from scripts.u16_cross_sectional_data_qualification import rss_mib,structural_preflight
CONFIG=ROOT/"config/u21_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u21_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u21_cross_sectional_paper_protocol_v1.json"
def canonical_hash(d:Mapping[str,Any])->str:return identity_hash({k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}})
COMMON_HALF=tuple(((i%7)-3)*.002 for i in range(168)); HIGH_ADJUSTED_HALF=COMMON_HALF; NEUTRAL_ADJUSTED_HALF=tuple(.001 if i%2 else -.001 for i in range(168))
def candidate_half(a):return tuple(c+x for c,x in zip(COMMON_HALF,a))
HIGH_HISTORY=candidate_half(HIGH_ADJUSTED_HALF)*2;NEUTRAL_HISTORY=candidate_half(NEUTRAL_ADJUSTED_HALF)*2;COMMON=COMMON_HALF*2;PATH=(.002,.004,.007,.011,.015,.020)
def synthetic_rows(total:int,active_members:int=15)->Iterator[CokurtosisCandidatePath]:
    histories=tuple(HIGH_HISTORY if i<4 else NEUTRAL_HISTORY for i in range(active_members))
    for index in range(total):
        s=index%active_members;yield CokurtosisCandidatePath(index//active_members*14_400_000,f"S{s:02d}USDT",histories[s],COMMON,PATH)
def complexity(config):
    c=config["complexity_benchmark"];passes=[];digest=None
    for i in range(c["benchmark_passes_required"]):
        started=time.perf_counter();result=evaluate_stream(synthetic_rows(c["synthetic_fixture_rows"],c["synthetic_active_members"]));elapsed=time.perf_counter()-started;current=identity_hash(result);peak=rss_mib()
        if elapsed>c["maximum_elapsed_seconds_per_pass"] or peak>c["maximum_peak_rss_mib"] or result["input_rows"]!=c["synthetic_fixture_rows"]:raise QualificationFailure("complexity Gate failed")
        if digest is not None and current!=digest:raise QualificationFailure("complexity output mismatch")
        digest=current;passes.append({"pass":i+1,"fixture_rows":result["input_rows"],"elapsed_seconds":f"{elapsed:.6f}","peak_rss_mib":f"{peak:.3f}","output_hash":current})
    return {"status":"pass","passes":passes,"same_code_path":c["same_common_adjustment_cokurtosis_event_and_path_code_path"],"market_outcomes_read":0,"synthetic_output_hash":digest}
def qualify(raw_root:Path,config):
    if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract drift")
    protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
    if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("critical_findings") or review.get("high_findings"):raise QualificationFailure("protocol/review drift")
    base_config=load_json(BASE_CONFIG)
    if base_config.get("content_hash")!=config["base_v4_qualification_contract_hash"]:raise QualificationFailure("base contract drift")
    benchmark=complexity(config);base=qualify_base(raw_root=raw_root,config=base_config);preflight=structural_preflight(raw_root,config);reasons=preflight["counts"]["ineligible_reasons"]
    if "48h_history_or_24h_path_slot_failure" in reasons:reasons["336h_history_or_24h_path_slot_failure"]=reasons.pop("48h_history_or_24h_path_slot_failure")
    isolation=config["isolation_contract"]
    result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":base["source_freeze_hash"],"v4_artifact_set_hash":base["v4_artifact_set_hash"],"manifest_hashes":base["manifest_hashes"],"source_orders":base["orders"],"same_reader_orders":preflight["orders"],"complexity_benchmark":benchmark,"counts":{**base["counts"],**preflight["counts"]},"isolation":{"is_start":isolation["is_start"],"is_end_exclusive":isolation["is_end_exclusive"],"oos_opened":False,"oos_archive_access":isolation["oos_archive_access"],"oos_ohlcv_values_decoded":0,"price_fields_decoded_during_preflight":0,"return_rows_generated":0,"common_adjusted_return_rows_generated":0,"cokurtosis_statistic_rows_generated":0,"candidate_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"formal_return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False}
    result["qualification_content_hash"]=identity_hash(result);return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");p.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u21_cross_sectional_data_qualification_v1.json");a=p.parse_args();r=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n");print(f"U-21 qualification PASS ceiling={r['counts']['maximum_independent_theoretical_24h_episodes']} hash={r['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
