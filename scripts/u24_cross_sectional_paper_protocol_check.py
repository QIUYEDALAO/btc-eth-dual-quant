#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from scripts.u24_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH,validate_all as validate_design
PROTOCOL=ROOT/"config/u24_cross_sectional_paper_protocol_v1.json";FEASIBILITY=ROOT/"reports/m1/evidence/u24_synthetic_core_feasibility_v1.json";CORE=ROOT/"src/btc_eth_dual_quant/data/u24_lottery_demand.py"
CONTENT_HASH="5110c3f455274f291391ed9b34affe6e5f61beb9198723d4fb0b8f07439c7ce7";FEASIBILITY_HASH="ce8b0f7998cc1c8e3928c605cccd0da37087a620d37e8058ae55e02f26957484";CORE_HASH="9817e4ad55399146eff2ae4f7b08e175a18400a68290d8dea2f1ec6100fae7cd"
def identity_hash(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_feasibility(value:Mapping[str,Any])->list[str]:
 findings=[];identity={k:v for k,v in value.items() if k not in {"content_hash","generated_utc"}}
 if value.get("content_hash")!=FEASIBILITY_HASH or identity_hash(identity)!=FEASIBILITY_HASH:findings.append("feasibility identity changed")
 passes=value.get("passes",[])
 if value.get("status")!="pass_before_protocol_freeze" or len(passes)!=3 or value.get("actual_logical_hourly_member_returns_per_pass",0)<1_000_000:findings.append("feasibility Gate changed")
 if any(float(item.get("elapsed_seconds",31))>30 or float(item.get("peak_rss_mib",1025))>1024 for item in passes) or len({item.get("event_digest") for item in passes})!=1:findings.append("feasibility result changed")
 if value.get("public_data_read") is not False or value.get("frozen_source_archives_opened")!=0 or value.get("market_outcome_rows")!=0 or value.get("oos_values_decoded")!=0:findings.append("feasibility isolation changed")
 if hashlib.sha256(CORE.read_bytes()).hexdigest()!=CORE_HASH or value.get("core_sha256")!=CORE_HASH:findings.append("exact core changed")
 return findings
def validate_protocol(protocol:Mapping[str,Any])->list[str]:
 findings=[];identity={k:v for k,v in protocol.items() if k not in {"content_hash","generated_utc"}}
 if protocol.get("content_hash")!=CONTENT_HASH or identity_hash(identity)!=CONTENT_HASH:findings.append("protocol identity changed")
 if protocol.get("design_content_hash")!=DESIGN_HASH or protocol.get("candidate_id")!="U24-CROSS-SECTIONAL-LOTTERY-DEMAND-AVOIDANCE-PREMIUM":findings.append("design binding changed")
 b=protocol.get("authority_bindings",{})
 if b.get("u24_design_authorization_hash")!="745152692cdada8dad9e0abaf5ea171fb3a1d55d70dbfab32b66c7d2edbdfac5" or b.get("u23_run_content_hash")!="771ce48d80dc48fd2d8f984528541c8a8c1cef4f756892647d66f49b9ffb2604" or b.get("synthetic_core_feasibility_hash")!=FEASIBILITY_HASH or b.get("exact_core_sha256")!=CORE_HASH:findings.append("authority binding changed")
 history=protocol.get("history_contract",{});lottery=protocol.get("lottery_payoff_contract",{})
 if history.get("history_hours")!=336 or history.get("half_window_hours")!=168 or history.get("all_336_completed_hourly_returns_for_every_decision_time_active_member_required") is not True:findings.append("history changed")
 if lottery.get("maximum_half_lottery_payoff")!="0.0769610411361284" or lottery.get("required_rank_per_half")!="lowest_ceiling_active_member_count_divided_by_four" or lottery.get("both_halves_must_pass_absolute_and_rank_gates") is not True:findings.append("lottery contract changed")
 if lottery.get("mean_return_volatility_downside_tail_coskewness_cokurtosis_or_current_return_gate_used") is not False:findings.append("outcome proxy gate added")
 if protocol.get("episode_clustering",{}).get("connected_window_hours")!=24:findings.append("clustering changed")
 observation=protocol.get("observation_contract",{})
 if protocol.get("scope",{}).get("oos_opened") is not False or observation.get("horizon_hours")!=[1,2,4,8,12,24] or observation.get("formal_strategy_return") is not False:findings.append("scope or observation changed")
 gates=protocol.get("paper_gates",{})
 if len(gates)!=12 or gates.get("complete_is_independent_episodes_minimum")!=90 or gates.get("combined_median_24h_relative_lottery_demand_avoidance_premium_minimum")!="0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_lottery_demand_avoidance_premium_minimum")!="0.60":findings.append("paper Gates changed")
 expected={"paper_protocol_frozen":True,"exact_head_independent_review":True,"data_qualification_complexity_and_preflight":False,"return_common_adjustment_lottery_scan":False,"event_scan":False,"path_observation":False,"signals":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if protocol.get("authorizations")!=expected:findings.append("authorization changed")
 return findings
def validate_all()->list[str]:return validate_design()+validate_feasibility(json.loads(FEASIBILITY.read_text()))+validate_protocol(json.loads(PROTOCOL.read_text()))
def main()->int:
 findings=validate_all()
 if findings:print("u24_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in findings];return 1
 print(f"u24_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
