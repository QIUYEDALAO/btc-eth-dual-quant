#!/usr/bin/env python3
"""Run U-15 official-field qualification and result-blind preflight."""
from __future__ import annotations
import argparse,hashlib,json,resource,sys,time,zipfile
from decimal import Decimal,InvalidOperation
from pathlib import Path
from typing import Any,Iterator,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from btc_eth_dual_quant.data.u15_taker_buy_absorption import TakerAuctionPathRow,evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure,identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,FIVE_MINUTES_MS,build_membership
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG,ordered,required_tasks
from scripts.u14_cross_sectional_data_qualification import structural_preflight
CONFIG=ROOT/"config/u15_cross_sectional_data_qualification_v1.json";REVIEW=ROOT/"reports/expert/evidence/u15_cross_sectional_paper_protocol_review_v1.json";PROTOCOL_PATH="config/u15_cross_sectional_paper_protocol_v1.json";FOUR_HOURS_MS=14_400_000
def canonical_hash(d:Mapping[str,Any])->str:return identity_hash({k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}})
def rss_mib()->float:
    v=float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);return v/(1024*1024) if sys.platform=="darwin" else v/1024
def synthetic_rows(total:int,members:int)->Iterator[TakerAuctionPathRow]:
    symbols=tuple(f"S{i:02d}USDT" for i in range(members))
    for i in range(total):
        group,offset=divmod(i,members);decision=group*FOUR_HOURS_MS;special=group%100==0
        share=.72 if special and offset==0 else .48+offset*.002
        close=99.9 if special and offset==0 else 100.0
        yield TakerAuctionPathRow(decision,symbols[offset],100.0,close,1000.0,1000.0*share,100.0,(100.1,100.2,100.4,100.7,101.1,102.0))
def complexity(config:Mapping[str,Any])->dict[str,Any]:
    c=config["complexity_benchmark"];passes=[];digest=None
    for index in range(int(c["benchmark_passes_required"])):
        started=time.perf_counter();result=evaluate_stream(synthetic_rows(int(c["synthetic_fixture_rows"]),int(c["synthetic_active_members"])),int(c["synthetic_active_members"]));elapsed=time.perf_counter()-started;got=identity_hash(result);peak=rss_mib()
        if elapsed>float(c["maximum_elapsed_seconds_per_pass"]) or peak>float(c["maximum_peak_rss_mib"]) or result["input_rows"]!=int(c["synthetic_fixture_rows"]):raise QualificationFailure("complexity Gate failed")
        if digest is not None and got!=digest:raise QualificationFailure("complexity output mismatch")
        digest=got;passes.append({"pass":index+1,"fixture_rows":result["input_rows"],"elapsed_seconds":f"{elapsed:.6f}","peak_rss_mib":f"{peak:.3f}","output_hash":got})
    return {"status":"pass","passes":passes,"same_code_path":c["same_event_and_path_code_path"],"market_outcomes_read":0,"synthetic_output_hash":digest}
def field_scan(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
    c=config["field_qualification"];start,end=utc_ms(c["is_start"]),utc_ms(c["is_end_exclusive"]);membership=build_membership(load_json(EVIDENCE/"membership_manifest.json"));tasks=required_tasks(membership,end);orders=[];primary=None
    for order in c["traversal_orders"]:
        records=[];row_count=0;missing=[]
        for month,symbol in ordered(tasks,order,int(c["deterministic_shuffle_seed"])):
            rel=Path(f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip");path=raw_root/rel
            if not path.is_file():missing.append(f"{symbol}:{month}");continue
            digest=hashlib.sha256();archive_rows=0
            with zipfile.ZipFile(path) as archive:
                members=[x for x in archive.infolist() if not x.is_dir()]
                if len(members)!=1:raise QualificationFailure(f"archive member count: {rel}")
                with archive.open(members[0]) as handle:
                    for raw in handle:
                        parts=raw.rstrip(b"\r\n").split(b",")
                        try:opened=int(parts[0])
                        except (ValueError,IndexError):
                            if archive_rows==0 and parts and parts[0].lower() in {b"open_time",b"opentime"}:continue
                            raise QualificationFailure(f"malformed open time: {symbol}:{month}")
                        if opened>=end:break
                        if opened<start:continue
                        if len(parts)!=int(c["expected_columns"]):raise QualificationFailure(f"column count: {symbol}:{month}:{opened}")
                        try:q=Decimal(parts[int(c["quote_volume_column"])].decode());tb=Decimal(parts[int(c["taker_buy_base_volume_column"])].decode());tq=Decimal(parts[int(c["taker_buy_quote_volume_column"])].decode())
                        except (InvalidOperation,UnicodeDecodeError):raise QualificationFailure(f"numeric field: {symbol}:{month}:{opened}")
                        if not all(x.is_finite() for x in (q,tb,tq)) or q<=0 or tb<0 or tq<0 or tq>q:raise QualificationFailure(f"taker field invariant: {symbol}:{month}:{opened}")
                        digest.update(str(opened).encode()+b","+parts[7]+b","+parts[9]+b","+parts[10]+b"\n");archive_rows+=1;row_count+=1
            records.append({"archive":rel.as_posix(),"qualified_rows":archive_rows,"field_hash":digest.hexdigest()})
        canonical={"records":sorted(records,key=lambda x:x["archive"]),"missing_archives":sorted(missing)};ident=identity_hash(canonical);orders.append({"order":order,"content_identity_hash":ident,"task_count":len(tasks),"available_archive_count":len(records),"missing_archive_count":len(missing),"qualified_is_row_count":row_count})
        if primary is None:primary=canonical
    if len({x["content_identity_hash"] for x in orders})!=1:raise QualificationFailure("field traversal mismatch")
    return {"status":"pass","orders":orders,"qualified_is_row_count":orders[0]["qualified_is_row_count"],"invalid_field_rows":0,"expected_columns":int(c["expected_columns"]),"primary_field_identity_hash":orders[0]["content_identity_hash"]}
def qualify(raw_root:Path,config:Mapping[str,Any])->dict[str,Any]:
    if canonical_hash(config)!=config.get("content_hash"):raise QualificationFailure("contract drift")
    protocol=git_json(config["protocol_target_commit"],PROTOCOL_PATH);review=load_json(REVIEW)
    if protocol.get("content_hash")!=config["protocol_content_hash"] or review.get("review_content_hash")!=config["protocol_review_content_hash"] or review.get("verdict")!="approve" or review.get("critical_findings") or review.get("high_findings"):raise QualificationFailure("protocol/review drift")
    base_config=load_json(BASE_CONFIG);base=qualify_base(raw_root=raw_root,config=base_config);fields=field_scan(raw_root,config);preflight=structural_preflight(raw_root,config);bench=complexity(config)
    isolation=config["isolation_contract"]
    result={"schema_version":1,"qualification_id":config["qualification_id"],"status":"pass","contract_content_hash":config["content_hash"],"protocol_target_commit":config["protocol_target_commit"],"protocol_content_hash":config["protocol_content_hash"],"protocol_review_content_hash":config["protocol_review_content_hash"],"source_freeze_hash":base["source_freeze_hash"],"v4_artifact_set_hash":base["v4_artifact_set_hash"],"manifest_hashes":base["manifest_hashes"],"source_orders":base["orders"],"field_qualification":fields,"same_reader_orders":preflight["orders"],"complexity_benchmark":bench,"counts":{**base["counts"],**preflight["counts"],"qualified_is_taker_field_rows":fields["qualified_is_row_count"],"invalid_taker_field_rows":0},"isolation":{"is_start":isolation["is_start"],"is_end_exclusive":isolation["is_end_exclusive"],"oos_opened":False,"oos_archive_access":isolation["oos_archive_access"],"oos_values_decoded":0,"taker_state_rows_generated":0,"candidate_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0},"authorizations":{"one_sealed_is_paper_observation":True,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False},"network_accessed":False,"production_evidence_mutated":False};result["qualification_content_hash"]=identity_hash(result);return result
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");p.add_argument("--output",type=Path,default=ROOT/"reports/m1/evidence/u15_cross_sectional_data_qualification_v1.json");a=p.parse_args();result=qualify(a.raw_root,load_json(CONFIG));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n");print(f"U-15 qualification PASS rows={result['counts']['qualified_is_taker_field_rows']} ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}");return 0
if __name__=="__main__":raise SystemExit(main())
