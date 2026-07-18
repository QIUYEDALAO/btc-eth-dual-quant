#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from decimal import Decimal,localcontext
from pathlib import Path
from typing import Any,Mapping,Sequence
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,FIVE_MINUTES_MS,ONE_HOUR_MS,ObservationFailure,decimal_text,median,month_for_ms,ordered,read_five_minute_rows
from scripts.u05_cross_sectional_data_qualification import git_json
TARGET="a516efb32f2058b603918365a6eeaef0fe509361";PROTOCOL_PATH="config/u08_cross_sectional_paper_protocol_v1.json";QUALIFICATION_HASH="1ec26ef74b80c2b46cfd0dcb231ee8863ae2bd0ff01fabf33dd4028b13807cb5";PATH_MS=336*ONE_HOUR_MS;HORIZONS=(24,72,168,336)
def membership_rows()->dict[str,list[dict[str,Any]]]:
 out=defaultdict(list)
 for row in load_json(EVIDENCE/"membership_manifest.json")["content"]:
  if row.get("eligibility_status")=="qualified":out[str(row["effective_month"])[:7]].append(row)
 return {m:sorted(rows,key=lambda x:(int(x["rank"]),str(x["symbol"]))) for m,rows in out.items()}
def select_events(rows:Mapping[str,Sequence[Mapping[str,Any]]],start:int,end:int,protocol_hash:str,qualification_hash:str)->tuple[list[dict[str,Any]],dict[str,int]]:
 events=[];a={"membership_months_considered":0,"genesis_months_excluded":0,"months_without_entry":0,"simultaneous_entries_discarded":0}
 months=sorted(rows)
 for index,month in enumerate(months):
  effective=utc_ms(f"{month}-01T00:00:00Z")
  if not(start<=effective<end):continue
  a["membership_months_considered"]+=1
  if index==0:a["genesis_months_excluded"]+=1;continue
  prior={str(x["symbol"]) for x in rows[months[index-1]]};entries=[x for x in rows[month] if str(x["symbol"]) not in prior]
  if not entries:a["months_without_entry"]+=1;continue
  entries=sorted(entries,key=lambda x:(int(x["rank"]),str(x["symbol"])));a["simultaneous_entries_discarded"]+=len(entries)-1;winner=entries[0];active=[str(x["symbol"]) for x in rows[month]]
  core={"decision_time_ms":effective,"reference_open_time_ms":effective+FIVE_MINUTES_MS,"effective_month":month,"symbol":str(winner["symbol"]),"current_membership_rank":int(winner["rank"]),"active_members":active,"active_member_count":len(active),"simultaneous_entry_count":len(entries),"simultaneous_entry_symbols":[str(x["symbol"]) for x in entries]};core["event_id"]=identity_hash({"protocol":protocol_hash,"qualification":qualification_hash,**core});events.append(core)
 return events,a
def cluster_events(events:Sequence[Mapping[str,Any]])->list[dict[str,Any]]:
 out=[];previous=None;n=-1
 for event in sorted(events,key=lambda x:int(x["decision_time_ms"])):
  t=int(event["decision_time_ms"])
  if previous is None or t-previous>PATH_MS:n+=1;row=dict(event);row["episode_id"]=identity_hash({"episode":n,"event":event["event_id"]});out.append(row)
  previous=t
 return out
def lifecycle_ends()->dict[str,int]:return {str(x["symbol"]):utc_ms(str(x["end_exclusive"])) for x in load_json(EVIDENCE/"symbol_availability_manifest.json")["content"] if x.get("end_exclusive")}
def observe_episode(raw_root:Path,event:Mapping[str,Any],membership:Mapping[str,Sequence[Mapping[str,Any]]],masked:set[tuple[str,int]],start:int,end:int,order:str)->tuple[dict[str,Any]|None,str|None]:
 ref=int(event["reference_open_time_ms"]);stop=ref+PATH_MS;active=[str(x) for x in event["active_members"]];candidate=str(event["symbol"]);peers=[x for x in active if x!=candidate]
 if stop>end:return None,"sealed_is_boundary"
 ends=lifecycle_ends()
 if any(ref<=ends.get(s,stop+1)<stop for s in active):return None,"lifecycle_intersection"
 times=[ref+i*FIVE_MINUTES_MS for i in range(4032)]
 if any(tuple(str(x["symbol"]) for x in membership.get(month_for_ms(t),()))!=tuple(active) for t in times):return None,"membership_change"
 series={}
 for symbol in ordered(active,order,key=lambda x:x):
  month=month_for_ms(ref);values=[]
  for t,o,h,l,c in read_five_minute_rows(raw_root,symbol,month,is_start_ms=start,is_end_ms=end):
   if ref<=t<stop and (symbol,t) not in masked:values.append((t,o,h,l,c))
  if [x[0] for x in values]!=times:return None,"missing_or_quarantined_5m"
  series[symbol]=values
 with localcontext() as ctx:
  ctx.prec=50;opens={s:series[s][0][1] for s in active};absolute=[];peer_medians=[];relative=[]
  for i in range(4032):
   a=series[candidate][i][4]/opens[candidate]-1;p=median([series[s][i][4]/opens[s]-1 for s in peers]);absolute.append(a);peer_medians.append(p);relative.append(a-p)
 return {"episode_id":event["episode_id"],"event_id":event["event_id"],"symbol":candidate,"effective_month":event["effective_month"],"decision_time_ms":int(event["decision_time_ms"]),"reference_open_time_ms":ref,"peer_count":len(peers),"candidate_absolute_close_displacement":{str(h):decimal_text(absolute[h*12-1]) for h in HORIZONS},"peer_median_close_displacement":{str(h):decimal_text(peer_medians[h*12-1]) for h in HORIZONS},"relative_persistence":{str(h):decimal_text(relative[h*12-1]) for h in HORIZONS},"candidate_maximum_favorable_excursion_336h":decimal_text(max(absolute)),"candidate_maximum_adverse_excursion_336h":decimal_text(min(absolute)),"first_base_cost_relative_persistence_minutes":next(((i+1)*5 for i,v in enumerate(relative) if v>=Decimal("0.0030")),None),"complete_336h":True},None
def evaluate_gates(paths:Sequence[Mapping[str,Any]],protocol:Mapping[str,Any],mismatch:int)->tuple[dict[str,Any],dict[str,bool]]:
 g=protocol["paper_gates"];n=len(paths);years=Counter(datetime.fromtimestamp(int(x["decision_time_ms"])/1000,tz=timezone.utc).year for x in paths);symbols=Counter(x["symbol"] for x in paths);months=Counter(x["effective_month"] for x in paths);full=n*2373//1715;oos=n*658//1715;rel=[Decimal(x["relative_persistence"]["336"]) for x in paths];absolute=[Decimal(x["candidate_absolute_close_displacement"]["336"]) for x in paths];rm=median(rel) if rel else Decimal("NaN");am=median(absolute) if absolute else Decimal("NaN");pf=Decimal(sum(x>0 for x in rel))/Decimal(n) if n else Decimal("NaN");ys=Decimal(max(years.values(),default=n or 1))/Decimal(n or 1);ss=Decimal(max(symbols.values(),default=n or 1))/Decimal(n or 1)
 m={"complete_is_independent_episodes":n,"projected_full_independent_episodes":full,"projected_sealed_oos_independent_episodes":oos,"years_with_six_complete_episodes":sum(v>=6 for v in years.values()),"episodes_by_year":{str(k):v for k,v in sorted(years.items())},"maximum_single_year_episode_share":decimal_text(ys),"episodes_by_symbol":dict(sorted(symbols.items())),"maximum_single_symbol_episode_share":decimal_text(ss),"distinct_event_symbols":len(symbols),"distinct_event_months":len(months),"median_336h_relative_persistence":decimal_text(rm) if rm.is_finite() else None,"median_336h_candidate_absolute_close_displacement":decimal_text(am) if am.is_finite() else None,"fraction_complete_episodes_with_positive_336h_relative_persistence":decimal_text(pf) if pf.is_finite() else None,"qualification_quarantine_lifecycle_or_order_mismatches":mismatch}
 c={"complete_is_independent_episodes":n>=g["complete_is_independent_episodes_minimum"],"projected_full_independent_episodes":full>=g["projected_full_independent_episodes_minimum"],"projected_sealed_oos_independent_episodes":oos>=g["projected_sealed_oos_independent_episodes_minimum"],"years_with_six_complete_episodes":m["years_with_six_complete_episodes"]>=g["minimum_years_with_six_complete_episodes"],"maximum_single_year_episode_share":ys<=Decimal(g["maximum_single_year_episode_share"]),"maximum_single_symbol_episode_share":ss<=Decimal(g["maximum_single_symbol_episode_share"]),"distinct_event_symbols":len(symbols)>=g["minimum_distinct_event_symbols"],"distinct_event_months":len(months)>=g["minimum_distinct_event_months"],"median_336h_relative_persistence":rm.is_finite() and rm>=Decimal(g["combined_median_336h_relative_persistence_minimum"]),"median_336h_candidate_absolute_close_displacement":am.is_finite() and am>=Decimal(g["combined_median_336h_candidate_absolute_close_displacement_minimum"]),"fraction_positive_336h_relative_persistence":pf.is_finite() and pf>=Decimal(g["fraction_complete_episodes_with_positive_336h_relative_persistence_minimum"]),"authority_and_order_mismatches":mismatch<=g["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]};return m,c
def wrap(n:str,c:Any)->dict[str,Any]:d={"schema_version":1,"manifest_type":f"u08_{n}_manifest","content":c};d["content_hash"]=identity_hash(d);return d
def run_order(raw_root:Path,protocol:Mapping[str,Any],qualification:Mapping[str,Any],order:str)->dict[str,Any]:
 start=utc_ms(protocol["scope"]["is_start"]);end=utc_ms(protocol["scope"]["is_end_exclusive"]);membership=membership_rows();events,a=select_events(membership,start,end,protocol["content_hash"],qualification["qualification_content_hash"]);episodes=cluster_events(events);masked={(str(x["symbol"]),int(x["open_time_ms"])) for x in load_json(EVIDENCE/"invalid_interval_slot_mask_manifest.json")["content"]};paths=[];censors=Counter()
 for event in ordered(episodes,order,key=lambda x:int(x["decision_time_ms"])):
  row,reason=observe_episode(raw_root,event,membership,masked,start,end,order)
  if row:paths.append(row)
  else:censors[reason]+=1
 content={"events":sorted(events,key=lambda x:int(x["decision_time_ms"])),"episodes":sorted(episodes,key=lambda x:int(x["decision_time_ms"])),"paths":sorted(paths,key=lambda x:int(x["decision_time_ms"])),"accounting":{**a,"candidate_events":len(events),"independent_episodes":len(episodes),"complete_336h_episodes":len(paths),"right_censored_episodes":len(episodes)-len(paths),"right_censor_reasons":dict(sorted(censors.items())),"oos_rows_decoded":0,"formal_returns_computed":0,"fills_positions_or_equity_rows":0}};manifests={n:wrap(n,content[n]) for n in ("events","episodes","paths","accounting")};hashes={n:manifests[n]["content_hash"] for n in sorted(manifests)};return {"order":order,"manifests":manifests,"manifest_hashes":hashes,"content_identity_hash":identity_hash(hashes)}
def execute(raw_root:Path)->dict[str,Any]:
 protocol=git_json(TARGET,PROTOCOL_PATH);qualification=load_json(ROOT/"reports/m1/evidence/u08_cross_sectional_data_qualification_v1.json")
 if qualification.get("qualification_content_hash")!=QUALIFICATION_HASH:raise ObservationFailure("qualification drift")
 runs=[run_order(raw_root,protocol,qualification,o) for o in ("normal","reverse","deterministic_shuffled")];mismatch=0 if len({r["content_identity_hash"] for r in runs})==1 else 1;primary=runs[0];metrics,checks=evaluate_gates(primary["manifests"]["paths"]["content"],protocol,mismatch);status="pass" if all(checks.values()) else "failed_feasibility";summary={"schema_version":1,"run_id":"U08-06-SEALED-IS-PAPER-OBSERVATION-V1","status":status,"protocol_content_hash":protocol["content_hash"],"qualification_content_hash":qualification["qualification_content_hash"],"is_start":protocol["scope"]["is_start"],"is_end_exclusive":protocol["scope"]["is_end_exclusive"],"orders":[{"order":r["order"],"content_identity_hash":r["content_identity_hash"],"manifest_hashes":r["manifest_hashes"]} for r in runs],"metrics":metrics,"paper_gate_checks":checks,"oos_opened":False,"oos_rows_decoded":0,"formal_returns_computed":False,"fills_positions_or_equity_generated":False,"parameters_changed_after_result":False,"second_run_executed":False,"network_accessed":False,"authorizations":{"paper_result_independent_review":status=="pass","lifecycle_or_fixed_rule_work":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}};summary["run_content_hash"]=identity_hash(summary);return {"summary":summary,"manifests":primary["manifests"]}
def render(r:Mapping[str,Any])->str:
 s=r["summary"];m=s["metrics"];lines=["# U-08 Sealed-IS Paper Observation","",f"- Status: `{s['status']}`",f"- Run hash: `{s['run_content_hash']}`",f"- Complete independent episodes: `{m['complete_is_independent_episodes']}`","","## Frozen Paper Gates",""]+[f"- {k}: `{str(v).lower()}`" for k,v in s["paper_gate_checks"].items()]+["","## Metrics","",f"- Projected full / sealed OOS: `{m['projected_full_independent_episodes']} / {m['projected_sealed_oos_independent_episodes']}`",f"- Distinct symbols / months: `{m['distinct_event_symbols']} / {m['distinct_event_months']}`",f"- Median 336h relative persistence: `{m['median_336h_relative_persistence']}`",f"- Median 336h absolute displacement: `{m['median_336h_candidate_absolute_close_displacement']}`",f"- Positive relative-persistence fraction: `{m['fraction_complete_episodes_with_positive_336h_relative_persistence']}`","","## Isolation","","- OOS opened / rows decoded: `false / 0`","- Formal returns, fills, positions or equity generated: `false`","- Parameters changed or second run executed: `false / false`","","A failed Gate closes U-08 without tuning. A pass authorizes only independent Paper-result review.",""];return "\n".join(lines)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");ap.add_argument("--evidence-dir",type=Path,default=ROOT/"reports/m1/evidence/u08_cross_sectional_paper_observation");ap.add_argument("--report",type=Path,default=ROOT/"reports/m1/U08_CROSS_SECTIONAL_PAPER_OBSERVATION.md");a=ap.parse_args();r=execute(a.raw_root);a.evidence_dir.mkdir(parents=True,exist_ok=True);[(a.evidence_dir/f"{n}.json").write_text(json.dumps(d,sort_keys=True,separators=(",",":"))+"\n") for n,d in r["manifests"].items()];(a.evidence_dir/"run_manifest.json").write_text(json.dumps(r["summary"],sort_keys=True,separators=(",",":"))+"\n");a.report.write_text(render(r));print(json.dumps(r["summary"],sort_keys=True,separators=(",",":")));return 0 if r["summary"]["status"]=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
