#!/usr/bin/env python3
"""Execute the unique frozen U-24 sealed-IS Paper observation."""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal,localcontext
from pathlib import Path
from typing import Any,Mapping,Sequence
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from btc_eth_dual_quant.data.u24_lottery_demand import LotteryDecision,evaluate_decision
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json,utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE,ONE_HOUR_MS,ObservationFailure,build_membership,decimal_text,median,month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u14_cross_sectional_paper_observation import capture_paths,cluster_events
from scripts.u16_cross_sectional_paper_observation import build_hourly_closes
from scripts.u20_cross_sectional_paper_observation import observe_paths as observe_generic
FOUR_HOURS_MS=4*ONE_HOUR_MS;PROTOCOL_TARGET="cafbd5a90f5fd3a435d15ff03af0ecec2df98c3f";PROTOCOL_PATH="config/u24_cross_sectional_paper_protocol_v1.json";QUALIFICATION_HASH="02e1dd27ae4d04cf10c3cbd14578eb06b633b02ec749233eba22b72f9ada9627"
def select_events(closes:Mapping[tuple[str,int],Decimal],membership:Mapping[str,Sequence[str]],start:int,end:int,protocol_hash:str)->tuple[list[dict[str,Any]],dict[str,int]]:
 events=[];accounting={"decision_times_considered":0,"history_or_membership_ineligible":0,"lottery_threshold_or_rank_failed":0,"candidate_events":0};decision=start
 with localcontext() as context:
  context.prec=50
  while decision<end:
   symbols=tuple(membership.get(month_for_ms(decision-1),()))
   if len(symbols)<10:decision+=FOUR_HOURS_MS;continue
   accounting["decision_times_considered"]+=1;starts=range(decision-336*ONE_HOUR_MS,decision,ONE_HOUR_MS)
   if any(tuple(membership.get(month_for_ms(opened),()))!=symbols for opened in starts):accounting["history_or_membership_ineligible"]+=1;decision+=FOUR_HOURS_MS;continue
   endpoints=tuple(decision-(336-index)*ONE_HOUR_MS for index in range(337))
   if any((symbol,endpoint) not in closes for symbol in symbols for endpoint in endpoints):accounting["history_or_membership_ineligible"]+=1;decision+=FOUR_HOURS_MS;continue
   returns=tuple(tuple(float((closes[(symbol,endpoint)]/closes[(symbol,endpoint-ONE_HOUR_MS)]).ln()) for endpoint in endpoints[1:]) for symbol in symbols)
   selected=evaluate_decision(LotteryDecision(decision,symbols,returns,tuple((0.0,)*6 for _ in symbols)))
   if selected is None:accounting["lottery_threshold_or_rank_failed"]+=1;decision+=FOUR_HOURS_MS;continue
   symbol=str(selected["symbol"]);core={"decision_time_ms":decision-1,"reference_open_time_ms":decision,"symbol":symbol,"active_members":list(symbols),"active_member_count":len(symbols),"old_half_peak_residual":selected["old_half_peak_residual"],"new_half_peak_residual":selected["new_half_peak_residual"]};core["event_id"]=identity_hash({"protocol":protocol_hash,"qualification":QUALIFICATION_HASH,**core});events.append(core);accounting["candidate_events"]+=1;decision+=FOUR_HOURS_MS
 return events,accounting
def observe_paths(episodes,captured,censored):
 paths,counts=observe_generic(episodes,captured,censored)
 for row in paths:
  row["relative_lottery_demand_avoidance_premium"]=row.pop("relative_negative_coskewness_risk_premium");row["first_base_cost_relative_premium_minutes"]=row.pop("first_base_cost_relative_premium_minutes")
 return paths,counts
def evaluate_gates(paths:Sequence[Mapping[str,Any]],mismatch:int)->tuple[dict[str,Any],dict[str,bool]]:
 count=len(paths);years=Counter(datetime.fromtimestamp(int(r["decision_time_ms"])/1000,tz=timezone.utc).year for r in paths);symbols=Counter(str(r["symbol"]) for r in paths);months=Counter(datetime.fromtimestamp(int(r["decision_time_ms"])/1000,tz=timezone.utc).strftime("%Y-%m") for r in paths);projected_full=count*2373//1715;projected_oos=count*658//1715;relative=[Decimal(str(r["relative_lottery_demand_avoidance_premium"]["24"])) for r in paths];absolute=[Decimal(str(r["candidate_absolute_close_displacement"]["24"])) for r in paths];rm=median(relative) if paths else Decimal("NaN");am=median(absolute) if paths else Decimal("NaN");positive=Decimal(sum(v>0 for v in relative))/Decimal(count) if count else Decimal("NaN");ys=Decimal(max(years.values(),default=count or 1))/Decimal(count or 1);ss=Decimal(max(symbols.values(),default=count or 1))/Decimal(count or 1)
 metrics={"complete_is_independent_episodes":count,"projected_full_independent_episodes":projected_full,"projected_sealed_oos_independent_episodes":projected_oos,"years_with_twelve_complete_episodes":sum(v>=12 for v in years.values()),"episodes_by_year":{str(k):v for k,v in sorted(years.items())},"maximum_single_year_episode_share":decimal_text(ys),"episodes_by_symbol":dict(sorted(symbols.items())),"maximum_single_symbol_episode_share":decimal_text(ss),"distinct_event_symbols":len(symbols),"distinct_event_months":len(months),"median_24h_relative_lottery_demand_avoidance_premium":decimal_text(rm) if rm.is_finite() else None,"median_24h_candidate_absolute_close_displacement":decimal_text(am) if am.is_finite() else None,"fraction_complete_episodes_with_positive_24h_relative_lottery_demand_avoidance_premium":decimal_text(positive) if positive.is_finite() else None,"qualification_preflight_complexity_quarantine_lifecycle_or_order_mismatches":mismatch}
 checks={"complete_is_independent_episodes":count>=90,"projected_full_independent_episodes":projected_full>=120,"projected_sealed_oos_independent_episodes":projected_oos>=30,"years_with_twelve_complete_episodes":metrics["years_with_twelve_complete_episodes"]>=4,"maximum_single_year_episode_share":ys<=Decimal("0.35"),"maximum_single_symbol_episode_share":ss<=Decimal("0.25"),"distinct_event_symbols":len(symbols)>=8,"distinct_event_months":len(months)>=30,"median_24h_relative_lottery_demand_avoidance_premium":rm.is_finite() and rm>=Decimal("0.0180"),"median_24h_candidate_absolute_close_displacement":am.is_finite() and am>=Decimal("0.0180"),"fraction_positive_24h_relative_lottery_demand_avoidance_premium":positive.is_finite() and positive>=Decimal("0.60"),"authority_and_order_mismatches":mismatch==0};return metrics,checks
def wrap(name:str,content:Any)->dict[str,Any]:
 d={"schema_version":1,"manifest_type":f"u24_{name}_manifest","content":content};d["content_hash"]=identity_hash(d);return d
def run_order(raw_root:Path,protocol,qualification,order:str)->dict[str,Any]:
 if qualification.get("qualification_content_hash")!=QUALIFICATION_HASH:raise ObservationFailure("qualification binding changed")
 start,end=utc_ms(protocol["scope"]["is_start"]),utc_ms(protocol["scope"]["is_end_exclusive"]);membership=build_membership(load_json(EVIDENCE/"membership_manifest.json"));masked={(str(r["symbol"]),int(r["open_time_ms"])) for r in load_json(EVIDENCE/"invalid_interval_slot_mask_manifest.json")["content"]};closes=build_hourly_closes(raw_root=raw_root,membership=membership,masked=masked,start=start-336*ONE_HOUR_MS,end=end,order=order);events,scan=select_events(closes,membership,start,end,protocol["content_hash"]);episodes=cluster_events(events);captured,precensored=capture_paths(raw_root=raw_root,episodes=episodes,membership=membership,masked=masked,start=start,end=end,order=order);paths,censors=observe_paths(episodes,captured,precensored);content={"events":sorted(events,key=lambda r:int(r["decision_time_ms"])),"episodes":sorted(episodes,key=lambda r:int(r["decision_time_ms"])),"paths":sorted(paths,key=lambda r:int(r["decision_time_ms"])),"accounting":{**scan,"independent_episodes":len(episodes),"complete_24h_episodes":len(paths),"right_censored_episodes":len(episodes)-len(paths),"right_censor_reasons":dict(sorted(censors.items())),"oos_rows_decoded":0,"formal_returns_computed":0,"fills_positions_or_equity_rows":0}};manifests={name:wrap(name,content[name]) for name in content};hashes={name:manifests[name]["content_hash"] for name in sorted(manifests)};return {"order":order,"manifests":manifests,"manifest_hashes":hashes,"content_identity_hash":identity_hash(hashes)}
def execute(raw_root:Path)->dict[str,Any]:
 protocol=git_json(PROTOCOL_TARGET,PROTOCOL_PATH);qualification=load_json(ROOT/"reports/m1/evidence/u24_cross_sectional_data_qualification_v1.json");runs=[run_order(raw_root,protocol,qualification,o) for o in ("normal","reverse","deterministic_shuffled")];mismatch=0 if len({r["content_identity_hash"] for r in runs})==1 else 1;primary=runs[0];metrics,checks=evaluate_gates(primary["manifests"]["paths"]["content"],mismatch);status="pass" if all(checks.values()) else "failed_feasibility";summary={"schema_version":1,"run_id":"U24-06-SEALED-IS-PAPER-OBSERVATION-V1","status":status,"protocol_content_hash":protocol["content_hash"],"qualification_content_hash":QUALIFICATION_HASH,"orders":[{"order":r["order"],"content_identity_hash":r["content_identity_hash"],"manifest_hashes":r["manifest_hashes"]} for r in runs],"metrics":metrics,"paper_gate_checks":checks,"oos_opened":False,"oos_rows_decoded":0,"formal_returns_computed":False,"fills_positions_or_equity_generated":False,"parameters_changed_after_result":False,"second_run_executed":False,"network_accessed":False,"authorizations":{"paper_result_independent_review":status=="pass","lifecycle_or_fixed_rule_work":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}};summary["run_content_hash"]=identity_hash(summary);return {"summary":summary,"manifests":primary["manifests"]}
def render(result)->str:
 s=result["summary"];m=s["metrics"];return "\n".join(["# U-24 Sealed-IS Paper Observation","",f"- Status: `{s['status']}`",f"- Run hash: `{s['run_content_hash']}`",f"- Complete independent episodes: `{m['complete_is_independent_episodes']}`","","## Frozen Paper Gates","",*[f"- {k}: `{str(v).lower()}`" for k,v in s["paper_gate_checks"].items()],"","## Metrics","",f"- Projected full / sealed OOS episodes: `{m['projected_full_independent_episodes']} / {m['projected_sealed_oos_independent_episodes']}`",f"- Distinct symbols / months: `{m['distinct_event_symbols']} / {m['distinct_event_months']}`",f"- Median 24h relative lottery-demand avoidance premium: `{m['median_24h_relative_lottery_demand_avoidance_premium']}`",f"- Median 24h absolute displacement: `{m['median_24h_candidate_absolute_close_displacement']}`",f"- Positive relative-premium fraction: `{m['fraction_complete_episodes_with_positive_24h_relative_lottery_demand_avoidance_premium']}`","","## Isolation","","- OOS opened / rows decoded: `false / 0`","- Formal returns, fills, positions or equity generated: `false`","- Parameters changed or second run executed: `false / false`",""])
def write(result,evidence:Path,report:Path)->None:
 evidence.mkdir(parents=True,exist_ok=True)
 for name,d in result["manifests"].items():(evidence/f"{name}.json").write_text(json.dumps(d,sort_keys=True,separators=(",",":"))+"\n")
 (evidence/"run_manifest.json").write_text(json.dumps(result["summary"],sort_keys=True,separators=(",",":"))+"\n");report.write_text(render(result))
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--raw-root",type=Path,default=ROOT/"storage/raw/liquid_universe");p.add_argument("--evidence-dir",type=Path,default=ROOT/"reports/m1/evidence/u24_cross_sectional_paper_observation");p.add_argument("--report",type=Path,default=ROOT/"reports/m1/U24_CROSS_SECTIONAL_PAPER_OBSERVATION.md");a=p.parse_args()
 if (a.evidence_dir/"run_manifest.json").exists():print("U-24 is closed after its unique Paper observation; a second result-bearing run is not authorized.");return 2
 result=execute(a.raw_root);write(result,a.evidence_dir,a.report);print(json.dumps(result["summary"],sort_keys=True,separators=(",",":")));return 0 if result["summary"]["status"]=="pass" else 1
if __name__=="__main__":raise SystemExit(main())
