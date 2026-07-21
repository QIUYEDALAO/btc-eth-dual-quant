#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u16_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH,validate_all as validate_design
PROTOCOL=ROOT/"config/u16_cross_sectional_paper_protocol_v1.json";CONTENT_HASH="18e302deb6a3d9fddf8b2b5b8866d39355a95519c91f609ce670d64168f5633a"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_protocol(d:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=CONTENT_HASH or h(identity)!=CONTENT_HASH:f.append("protocol identity changed")
    if d.get("design_content_hash")!=DESIGN_HASH or d.get("candidate_id")!="U16-CROSS-SECTIONAL-CORRELATION-BREAKDOWN-INFORMATION-PERSISTENCE":f.append("design binding changed")
    hist=d.get("history_contract",{});corr=d.get("correlation_contract",{});disp=d.get("positive_displacement_contract",{})
    if hist.get("history_hours")!=48 or hist.get("baseline_hours")!=36 or hist.get("recent_hours")!=12 or hist.get("all_48_completed_hourly_returns_for_every_decision_time_active_member_required") is not True:f.append("history changed")
    if corr.get("baseline_correlation_minimum")!="0.50" or corr.get("recent_correlation_maximum")!="0.10" or corr.get("correlation_drop_minimum")!="0.50":f.append("correlation thresholds changed")
    if disp.get("recent_relative_log_displacement_minimum")!="0.0240" or disp.get("positive_relative_hour_count_integer_gate")!="positive_relative_hours_at_least_7_of_12" or disp.get("maximum_absolute_single_candidate_hourly_log_return")!="0.0600" or disp.get("terminal_hour_relative_contribution_maximum_fraction")!="0.50":f.append("displacement changed")
    if d.get("scope",{}).get("oos_opened") is not False or d.get("observation_contract",{}).get("horizon_hours")!=[1,2,4,8,12,24] or d.get("observation_contract",{}).get("formal_strategy_return") is not False:f.append("scope or observation changed")
    if len(d.get("paper_gates",{}))!=12:f.append("paper Gates changed")
    expected={"paper_protocol_frozen":True,"exact_head_independent_review":True,"data_qualification_complexity_and_preflight":False,"common_path_scan":False,"correlation_scan":False,"event_scan":False,"path_observation":False,"signals":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected:f.append("authorization changed")
    return f
def validate_all()->list[str]:return validate_design()+validate_protocol(json.loads(PROTOCOL.read_text()))
def main()->int:
    f=validate_all()
    if f:print("u16_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u16_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
