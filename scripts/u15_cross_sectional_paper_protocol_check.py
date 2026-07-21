#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts.u15_cross_sectional_design_check import CONTENT_HASH as DESIGN_HASH,validate_all as validate_design
PROTOCOL=ROOT/"config/u15_cross_sectional_paper_protocol_v1.json"
CONTENT_HASH="3b58d6a23cc78e3b644d935599e625c04267317d42608adf2f0321ec51ab577a"
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_protocol(d:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=CONTENT_HASH or canonical_hash(identity)!=CONTENT_HASH:f.append("protocol identity changed")
    if d.get("design_content_hash")!=DESIGN_HASH or d.get("candidate_id")!="U15-CROSS-SECTIONAL-TAKER-BUY-ABSORPTION-PERSISTENCE":f.append("design binding changed")
    fields=d.get("official_field_contract",{})
    if len(fields.get("required_columns",[]))!=12 or fields.get("independent_semantic_and_availability_qualification_required_before_event_scan") is not True or fields.get("infer_from_total_volume_price_or_trade_count_allowed") is not False or fields.get("fill_repair_or_cross_field_substitution_allowed") is not False:f.append("field authority contract changed")
    event=d.get("event_identity",{})
    expected={"candidate_taker_buy_share_minimum":"0.6000","candidate_taker_buy_share_z_minimum":"2.0000","candidate_relative_return_minimum":"-0.0040","candidate_relative_return_maximum":"0.0000","candidate_absolute_close_to_open_log_return_maximum":"0.0060"}
    if any(event.get(k)!=v for k,v in expected.items()):f.append("event threshold changed")
    if d.get("scope",{}).get("oos_opened") is not False or d.get("scope",{}).get("signal_timeframe")!="4h_utc_from_complete_5m":f.append("scope changed")
    if d.get("observation_contract",{}).get("horizon_hours")!=[1,2,4,8,12,24] or d.get("observation_contract",{}).get("formal_strategy_return") is not False:f.append("observation contract changed")
    if len(d.get("paper_gates",{}))!=12:f.append("paper Gates changed")
    expected_auth={"paper_protocol_frozen":True,"exact_head_independent_review":True,"data_field_qualification_complexity_and_preflight":False,"taker_state_scan":False,"event_scan":False,"path_observation":False,"signals":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected_auth:f.append("authorization matrix changed")
    if any(v is not False for v in d.get("research_leakage_prevention",{}).values() if v is not True):f.append("leakage prevention changed")
    return f
def validate_all()->list[str]:
    f=validate_design();d=json.loads(PROTOCOL.read_text());f.extend(validate_protocol(d));return f
def main()->int:
    f=validate_all()
    if f:print("u15_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u15_cross_sectional_paper_protocol_check PASS hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
