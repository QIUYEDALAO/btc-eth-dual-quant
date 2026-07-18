#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import yaml
ROOT=Path(__file__).resolve().parents[1];SCOPE=ROOT/"config/u15_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTHORIZATION=ROOT/"config/u15_design_authorization_v1.json";U14_RESULT=ROOT/"reports/m1/evidence/u14_cross_sectional_paper_observation/run_manifest.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U15-CROSS-SECTIONAL-TAKER-BUY-ABSORPTION-PERSISTENCE"
HYPOTHESIS="U15-CROSS-SECTIONAL-TAKER-BUY-ABSORPTION-PERSISTENCE: Binance spot USDT long/cash only; using only a completed observation and exact point-in-time active members, unusually high aggressive taker-buy participation combined with muted contemporaneous relative price response may reveal urgent buy demand absorbed by finite passive sell inventory and may produce positive relative adjustment after the next eligible open if that inventory exhausts; required taker-buy fields must be independently qualified before any event scan; no U-04 through U-14 outcome reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH="5b99a5d830f40a6d9a5744771dafd3e85a64a55ea172b107465c46b10de115dd";CONTENT_HASH="14ba25a0d8f3c50b3acd6a1ae50720dd4a113554d3bdc17776bf190b51b57b1c"
def load(p:Path)->Any:return json.loads(p.read_text())
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(d:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=CONTENT_HASH or canonical_hash(identity)!=CONTENT_HASH:f.append("design identity changed")
    if d.get("candidate_id")!=CANDIDATE or d.get("hypothesis_sha256")!=HYPOTHESIS_HASH:f.append("candidate identity changed")
    h=d.get("economic_hypothesis",{})
    if h.get("family")!="cross_sectional_taker_buy_absorption_persistence" or len(h.get("failure_regimes",[]))!=10 or len(h.get("mechanism",[]))!=5:f.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants","non_duplication"):
        if not d.get(section) or any(v is not True for v in d[section].values()):f.append(f"{section} changed")
    if len(d.get("unresolved_until_separate_protocol",[]))!=19:f.append("rules resolved prematurely")
    expected={"u15_paper_protocol_design":True,"public_data_read":False,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected:f.append("authorization matrix changed")
    return f
def validate_all()->list[str]:
    f=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[x for x in ledger["candidates"] if str(x.get("id",""))==CANDIDATE]
    if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYPOTHESIS_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:f.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash")!="98d4ec9049d3b40ded8f98c045405eda8a010c783b5597653586853a825b7e68":f.append("authorization drift")
    result=load(U14_RESULT)
    if result.get("run_content_hash")!="3824731159e682d1fe0e249fc24a586ef87b8b2d53a4f716d42f66c9d72f1f5c" or result.get("oos_opened") is not False or result.get("second_run_executed") is not False:f.append("U-14 result drift")
    if load(AUDIT).get("verdict")!="pass":f.append("audit drift")
    return f
def main()->int:
    f=validate_all()
    if f:print("u15_cross_sectional_design_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u15_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
