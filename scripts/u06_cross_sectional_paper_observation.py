#!/usr/bin/env python3
"""Execute the single preregistered U-06 sealed-IS Paper observation."""
from __future__ import annotations
import argparse,csv,json,sys,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation,localcontext
from pathlib import Path
from typing import Any,Iterable,Mapping,Sequence
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,FIVE_MINUTES_MS,ONE_HOUR_MS,ONE_DAY_MS,ObservationFailure,_archive_path,build_membership,decimal_text,median,month_for_ms,ordered
from scripts.u05_cross_sectional_data_qualification import git_json

PROTOCOL_TARGET="1bb59f1ac9d9e0fd5bacc8c55e572b9a1fbce8cd";PROTOCOL_PATH="config/u06_cross_sectional_paper_protocol_v1.json";QUALIFICATION_HASH="e6a4a0eb47af2d88f30ab827d4456969549f86c5c81b7affedb91b034cb95a67";HORIZONS=(1,2,4,8,12,24,48,72);PATH_MS=72*ONE_HOUR_MS

def read_rows(raw_root:Path,symbol:str,month:str,is_start_ms:int,is_end_ms:int)->Iterable[tuple[int,Decimal,Decimal,Decimal,Decimal,Decimal]]:
 path=_archive_path(raw_root,symbol,month)
 with zipfile.ZipFile(path) as z:
  files=[x for x in z.infolist() if not x.is_dir()]
  if len(files)!=1:raise ObservationFailure("archive member count changed")
  previous=None
  with z.open(files[0]) as h:
   for raw in h:
    first=raw.split(b",",1)[0]
    try:opened=int(first)
    except ValueError:
     if previous is None and first.strip().lower() in {b"open_time",b"opentime"}:continue
     raise ObservationFailure(f"malformed open time: {symbol}:{month}")
    if opened>=is_end_ms:break
    if opened<is_start_ms:continue
    if previous is not None and opened<=previous:raise ObservationFailure("non-increasing 5m row")
    previous=opened;fields=next(csv.reader([raw.decode().rstrip("\r\n")]))
    if len(fields)!=12:raise ObservationFailure("5m schema changed")
    try:o,hv,l,c,q=map(Decimal,(fields[1],fields[2],fields[3],fields[4],fields[7]))
    except InvalidOperation as e:raise ObservationFailure("invalid OHLCV") from e
    if opened%FIVE_MINUTES_MS or min(o,hv,l,c)<=0 or hv<max(o,c) or l>min(o,c) or not q.is_finite() or q<0:raise ObservationFailure("invalid 5m row")
    yield opened,o,hv,l,c,q

def build_daily(raw_root:Path,membership:Mapping[str,Sequence[str]],masked:set[tuple[str,int]],start:int,end:int,order:str)->dict[str,dict[int,dict[str,Decimal]]]:
 out:dict[str,dict[int,dict[str,Decimal]]]=defaultdict(dict);tasks=[(m,s) for m,ss in membership.items() for s in ss if utc_ms(f"{m}-01T00:00:00Z")<end]
 for month,symbol in ordered(tasks,order,key=lambda x:(x[0],x[1])):
  days:dict[int,list[tuple[int,Decimal,Decimal]]]=defaultdict(list)
  for opened,o,_h,_l,c,q in read_rows(raw_root,symbol,month,start,end):
   if (symbol,opened) not in masked:days[(opened//ONE_DAY_MS)*ONE_DAY_MS].append((opened,o,c,q))
  for day,rows in days.items():
   expected=[day+i*FIVE_MINUTES_MS for i in range(288)]
   if [x[0] for x in rows]==expected:out[symbol][day]={"open":rows[0][1],"close":rows[-1][2],"quote":sum((x[3] for x in rows),Decimal(0))}
 return out

def select_events(daily:Mapping[str,Mapping[int,Mapping[str,Decimal]]],membership:Mapping[str,Sequence[str]],start:int,end:int,protocol_hash:str,qualification_hash:str)->tuple[list[dict[str,Any]],dict[str,int]]:
 events=[];a={"days_considered":0,"days_evaluated":0,"cross_section_ineligible":0,"share_gate_failed":0,"absolute_volume_gate_failed":0,"muted_price_gate_failed":0,"simultaneous_candidates_discarded":0}
 day=((start+ONE_DAY_MS-1)//ONE_DAY_MS)*ONE_DAY_MS
 with localcontext() as ctx:
  ctx.prec=50
  while day+ONE_DAY_MS<=end:
   a["days_considered"]+=1;symbols=membership.get(month_for_ms(day));candidates=[]
   if symbols is None or len(symbols)<10:a["cross_section_ineligible"]+=1;day+=ONE_DAY_MS;continue
   current={s:daily.get(s,{}).get(day) for s in symbols}
   if any(v is None for v in current.values()):a["cross_section_ineligible"]+=1;day+=ONE_DAY_MS;continue
   a["days_evaluated"]+=1
   returns={s:current[s]["close"]/current[s]["open"]-1 for s in symbols};current_total=sum((current[s]["quote"] for s in symbols),Decimal(0))
   if current_total<=0:a["cross_section_ineligible"]+=1;day+=ONE_DAY_MS;continue
   for symbol in symbols:
    shares=[];volumes=[];eligible=True
    for offset in range(30,0,-1):
     prior=day-offset*ONE_DAY_MS;prior_symbols=membership.get(month_for_ms(prior))
     if prior_symbols is None or symbol not in prior_symbols:eligible=False;break
     rows={s:daily.get(s,{}).get(prior) for s in prior_symbols}
     if any(v is None for v in rows.values()):eligible=False;break
     total=sum((rows[s]["quote"] for s in prior_symbols),Decimal(0))
     if total<=0:eligible=False;break
     shares.append(rows[symbol]["quote"]/total);volumes.append(rows[symbol]["quote"])
    if not eligible or median(shares)<=0 or median(volumes)<=0:continue
    share_ratio=(current[symbol]["quote"]/current_total)/median(shares);volume_ratio=current[symbol]["quote"]/median(volumes)
    peer=median([returns[s] for s in symbols if s!=symbol]);relative=returns[symbol]-peer
    if share_ratio<Decimal("2.00"):a["share_gate_failed"]+=1;continue
    if volume_ratio<Decimal("1.50"):a["absolute_volume_gate_failed"]+=1;continue
    if relative<Decimal("-0.0100") or relative>Decimal("0.0100"):a["muted_price_gate_failed"]+=1;continue
    candidates.append((symbol,share_ratio,volume_ratio,relative,current[symbol]["quote"]/current_total))
   if candidates:
    candidates.sort(key=lambda x:(-x[1],-x[2],x[0]));a["simultaneous_candidates_discarded"]+=len(candidates)-1;symbol,sr,vr,relative,share=candidates[0]
    core={"decision_time_ms":day+ONE_DAY_MS-1,"reference_open_time_ms":day+ONE_DAY_MS,"symbol":symbol,"active_members":list(symbols),"active_member_count":len(symbols),"share_ratio":decimal_text(sr),"absolute_quote_volume_ratio":decimal_text(vr),"relative_price_response":decimal_text(relative),"current_quote_volume_share":decimal_text(share)}
    core["event_id"]=identity_hash({"protocol":protocol_hash,"qualification":qualification_hash,**core});events.append(core)
   day+=ONE_DAY_MS
 return events,a

def cluster_events(events:Sequence[Mapping[str,Any]])->list[dict[str,Any]]:
 out=[];previous=None;n=-1
 for e in sorted(events,key=lambda x:int(x["decision_time_ms"])):
  d=int(e["decision_time_ms"])
  if previous is None or d-previous>PATH_MS:n+=1;row=dict(e);row["episode_id"]=identity_hash({"episode":n,"event":e["event_id"]});out.append(row)
  previous=d
 return out

def lifecycle_ends()->dict[str,int]:
 return {str(r["symbol"]):utc_ms(str(r["end_exclusive"])) for r in load_json(EVIDENCE/"symbol_availability_manifest.json")["content"] if r.get("end_exclusive")}

def capture(raw_root:Path,episodes:Sequence[Mapping[str,Any]],membership:Mapping[str,Sequence[str]],masked:set[tuple[str,int]],start:int,end:int,order:str)->tuple[dict[tuple[str,int],tuple[Decimal,Decimal,Decimal,Decimal]],dict[str,str]]:
 required:dict[tuple[str,str],set[int]]=defaultdict(set);censored={};ends=lifecycle_ends()
 for e in episodes:
  eid=str(e["episode_id"]);ref=int(e["reference_open_time_ms"]);stop=ref+PATH_MS;active=tuple(e["active_members"])
  if stop>end:censored[eid]="sealed_is_boundary";continue
  if any(ref<=ends.get(s,stop+1)<stop for s in active):censored[eid]="lifecycle_intersection";continue
  times=list(range(ref,stop,FIVE_MINUTES_MS))
  if any(tuple(membership.get(month_for_ms(t),()))!=active for t in times):censored[eid]="membership_change";continue
  for t in times:
   for s in active:required[(s,month_for_ms(t))].add(t)
 rows={}
 for symbol,month in ordered(required,order,key=lambda x:(x[1],x[0])):
  wanted=required[(symbol,month)]
  for t,o,h,l,c,_q in read_rows(raw_root,symbol,month,start,end):
   if t in wanted and (symbol,t) not in masked:rows[(symbol,t)]=(o,h,l,c)
 return rows,censored

def observe_paths(episodes:Sequence[Mapping[str,Any]],captured:Mapping[tuple[str,int],tuple[Decimal,Decimal,Decimal,Decimal]],censored:Mapping[str,str])->tuple[list[dict[str,Any]],Counter[str]]:
 out=[];counts=Counter(censored.values())
 for e in episodes:
  eid=str(e["episode_id"])
  if eid in censored:continue
  ref=int(e["reference_open_time_ms"]);symbol=str(e["symbol"]);peers=[s for s in e["active_members"] if s!=symbol];times=[ref+i*FIVE_MINUTES_MS for i in range(864)]
  if any((s,t) not in captured for s in [symbol,*peers] for t in times):counts["missing_or_quarantined_5m"]+=1;continue
  opens={s:captured[(s,ref)][0] for s in [symbol,*peers]};absolute=[];relative=[]
  for t in times:
   a=captured[(symbol,t)][3]/opens[symbol]-1;p=median([captured[(s,t)][3]/opens[s]-1 for s in peers]);absolute.append(a);relative.append(a-p)
  out.append({"episode_id":eid,"event_id":e["event_id"],"symbol":symbol,"decision_time_ms":int(e["decision_time_ms"]),"reference_open_time_ms":ref,"candidate_absolute_close_displacement":{str(h):decimal_text(absolute[h*12-1]) for h in HORIZONS},"relative_repricing":{str(h):decimal_text(relative[h*12-1]) for h in HORIZONS},"maximum_favorable_excursion_72h":decimal_text(max(absolute)),"maximum_adverse_excursion_72h":decimal_text(min(absolute)),"first_base_cost_relative_repricing_minutes":next(((i+1)*5 for i,v in enumerate(relative) if v>=Decimal("0.0030")),None),"complete_72h":True})
 return out,counts

def evaluate_gates(paths:Sequence[Mapping[str,Any]],protocol:Mapping[str,Any],mismatch:int)->tuple[dict[str,Any],dict[str,bool]]:
 g=protocol["paper_gates"];n=len(paths);years=Counter(datetime.fromtimestamp(int(x["decision_time_ms"])/1000,tz=timezone.utc).year for x in paths);symbols=Counter(x["symbol"] for x in paths);full=n*2373//1715;oos=n*658//1715;rel=median([Decimal(x["relative_repricing"]["24"]) for x in paths]) if paths else Decimal("NaN");absolute=median([Decimal(x["candidate_absolute_close_displacement"]["24"]) for x in paths]) if paths else Decimal("NaN");ys=Decimal(max(years.values(),default=n or 1))/Decimal(n or 1);ss=Decimal(max(symbols.values(),default=n or 1))/Decimal(n or 1)
 m={"complete_is_independent_episodes":n,"projected_full_independent_episodes":full,"projected_sealed_oos_independent_episodes":oos,"years_with_eight_complete_episodes":sum(v>=8 for v in years.values()),"episodes_by_year":{str(k):v for k,v in sorted(years.items())},"maximum_single_year_episode_share":decimal_text(ys),"episodes_by_symbol":dict(sorted(symbols.items())),"maximum_single_symbol_episode_share":decimal_text(ss),"distinct_event_symbols":len(symbols),"median_24h_relative_repricing":decimal_text(rel) if rel.is_finite() else None,"median_24h_candidate_absolute_close_displacement":decimal_text(absolute) if absolute.is_finite() else None,"qualification_quarantine_lifecycle_or_order_mismatches":mismatch}
 c={"complete_is_independent_episodes":n>=g["complete_is_independent_episodes_minimum"],"projected_full_independent_episodes":full>=g["projected_full_independent_episodes_minimum"],"projected_sealed_oos_independent_episodes":oos>=g["projected_sealed_oos_independent_episodes_minimum"],"years_with_eight_complete_episodes":m["years_with_eight_complete_episodes"]>=g["minimum_years_with_eight_complete_episodes"],"maximum_single_year_episode_share":ys<=Decimal(g["maximum_single_year_episode_share"]),"maximum_single_symbol_episode_share":ss<=Decimal(g["maximum_single_symbol_episode_share"]),"distinct_event_symbols":len(symbols)>=g["minimum_distinct_event_symbols"],"median_24h_relative_repricing":rel.is_finite() and rel>=Decimal(g["combined_median_24h_relative_repricing_minimum"]),"median_24h_candidate_absolute_close_displacement":absolute.is_finite() and absolute>=Decimal(g["combined_median_24h_candidate_absolute_close_displacement_minimum"]),"authority_and_order_mismatches":mismatch<=g["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]};return m,c

def wrap(name:str,content:Any)->dict[str,Any]:d={"schema_version":1,"manifest_type":f"u06_{name}_manifest","content":content};d["content_hash"]=identity_hash(d);return d
def run_order(raw_root:Path,protocol:Mapping[str,Any],qualification:Mapping[str,Any],order:str)->dict[str,Any]:
 start=utc_ms(protocol["scope"]["is_start"]);end=utc_ms(protocol["scope"]["is_end_exclusive"]);membership=build_membership(load_json(EVIDENCE/"membership_manifest.json"));masked={(str(x["symbol"]),int(x["open_time_ms"])) for x in load_json(EVIDENCE/"invalid_interval_slot_mask_manifest.json")["content"]};daily=build_daily(raw_root,membership,masked,start,end,order);events,a=select_events(daily,membership,start,end,protocol["content_hash"],qualification["qualification_content_hash"]);episodes=cluster_events(events);captured,pre=capture(raw_root,episodes,membership,masked,start,end,order);paths,censors=observe_paths(episodes,captured,pre);content={"events":sorted(events,key=lambda x:int(x["decision_time_ms"])),"episodes":sorted(episodes,key=lambda x:int(x["decision_time_ms"])),"paths":sorted(paths,key=lambda x:int(x["decision_time_ms"])),"accounting":{**a,"candidate_events":len(events),"independent_episodes":len(episodes),"complete_72h_episodes":len(paths),"right_censored_episodes":len(episodes)-len(paths),"right_censor_reasons":dict(sorted(censors.items())),"oos_rows_decoded":0,"formal_returns_computed":0,"fills_positions_or_equity_rows":0}};manifests={n:wrap(n,content[n]) for n in ("events","episodes","paths","accounting")};hashes={n:manifests[n]["content_hash"] for n in sorted(manifests)};return {"order":order,"manifests":manifests,"manifest_hashes":hashes,"content_identity_hash":identity_hash(hashes)}

def execute(raw_root:Path)->dict[str,Any]:
 protocol=git_json(PROTOCOL_TARGET,PROTOCOL_PATH);qualification=load_json(ROOT/"reports/m1/evidence/u06_cross_sectional_data_qualification_v1.json")
 if qualification.get("qualification_content_hash")!=QUALIFICATION_HASH:raise ObservationFailure("qualification drift")
 runs=[run_order(raw_root,protocol,qualification,o) for o in ("normal","reverse","deterministic_shuffled")];mismatch=0 if len({r["content_identity_hash"] for r in runs})==1 else 1;primary=runs[0];metrics,checks=evaluate_gates(primary["manifests"]["paths"]["content"],protocol,mismatch);status="pass" if all(checks.values()) else "failed_feasibility";summary={"schema_version":1,"run_id":"U06-06-SEALED-IS-PAPER-OBSERVATION-V1","status":status,"protocol_content_hash":protocol["content_hash"],"qualification_content_hash":qualification["qualification_content_hash"],"is_start":protocol["scope"]["is_start"],"is_end_exclusive":protocol["scope"]["is_end_exclusive"],"orders":[{"order":r["order"],"content_identity_hash":r["content_identity_hash"],"manifest_hashes":r["manifest_hashes"]} for r in runs],"metrics":metrics,"paper_gate_checks":checks,"oos_opened":False,"oos_rows_decoded":0,"formal_returns_computed":False,"fills_positions_or_equity_generated":False,"parameters_changed_after_result":False,"second_run_executed":False,"network_accessed":False,"authorizations":{"paper_result_independent_review":status=="pass","lifecycle_or_fixed_rule_work":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}};summary["run_content_hash"]=identity_hash(summary);return {"summary":summary,"manifests":primary["manifests"]}
def render(r:Mapping[str,Any])->str:
 s=r["summary"];m=s["metrics"];lines=["# U-06 Sealed-IS Paper Observation","",f"- Status: `{s['status']}`",f"- Run hash: `{s['run_content_hash']}`",f"- Complete independent episodes: `{m['complete_is_independent_episodes']}`","","## Frozen Paper Gates",""]+[f"- {k}: `{str(v).lower()}`" for k,v in s["paper_gate_checks"].items()]+["","## Metrics","",f"- Projected full / sealed OOS episodes: `{m['projected_full_independent_episodes']} / {m['projected_sealed_oos_independent_episodes']}`",f"- Distinct event symbols: `{m['distinct_event_symbols']}`",f"- Median 24h relative repricing: `{m['median_24h_relative_repricing']}`",f"- Median 24h candidate absolute displacement: `{m['median_24h_candidate_absolute_close_displacement']}`","","## Isolation","","- OOS opened / rows decoded: `false / 0`","- Formal returns, fills, positions or equity generated: `false`","- Parameters changed or second run executed: `false / false`","","A failed Gate closes the candidate without tuning. A pass authorizes only independent Paper-result review.",""];return "\n".join(lines)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--evidence-dir",type=Path,default=ROOT/"reports/m1/evidence/u06_cross_sectional_paper_observation");ap.add_argument("--report",type=Path,default=ROOT/"reports/m1/U06_CROSS_SECTIONAL_PAPER_OBSERVATION.md");a=ap.parse_args();r=execute(a.raw_root);a.evidence_dir.mkdir(parents=True,exist_ok=True);[ (a.evidence_dir/f"{n}.json").write_text(json.dumps(d,sort_keys=True,separators=(",",":"))+"\n") for n,d in r["manifests"].items()];(a.evidence_dir/"run_manifest.json").write_text(json.dumps(r["summary"],sort_keys=True,separators=(",",":"))+"\n");a.report.write_text(render(r));print(json.dumps(r["summary"],sort_keys=True,separators=(",",":")));return 0 if r["summary"]["status"]=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
