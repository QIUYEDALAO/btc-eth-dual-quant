#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import yaml
ROOT=Path(__file__).resolve().parents[1];SCOPE=ROOT/"config/u14_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTHORIZATION=ROOT/"config/u14_design_authorization_v1.json";U13_RESULT=ROOT/"reports/m1/evidence/u13_cross_sectional_paper_observation/run_manifest.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U14-CROSS-SECTIONAL-DOWNSIDE-REJECTION-PERSISTENCE"
HYPOTHESIS="U14-CROSS-SECTIONAL-DOWNSIDE-REJECTION-PERSISTENCE: Binance spot USDT long/cash only; using only a completed common selling-pressure observation and exact point-in-time active members, an asset that absorbs intraperiod selling and closes unusually high within its own completed range relative to peers may reveal latent demand and continue outperforming after the next eligible open; no U-04 through U-13 outcome reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH="b88f2321269863e385129465c93fbee8ecd35fa0dc6bc19e10bacf12d851b87d";CONTENT_HASH="a6c3cc47c3cadf33e5673e59ce47c639d6df1d49c57f88c51cc1c8579b446691"
def load(p:Path)->Any:return json.loads(p.read_text())
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(d:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=CONTENT_HASH or canonical_hash(identity)!=CONTENT_HASH:f.append("design identity changed")
    if d.get("candidate_id")!=CANDIDATE or d.get("hypothesis_sha256")!=HYPOTHESIS_HASH:f.append("candidate identity changed")
    h=d.get("economic_hypothesis",{})
    if h.get("family")!="cross_sectional_completed_range_downside_rejection_demand_absorption" or len(h.get("failure_regimes",[]))!=10 or len(h.get("mechanism",[]))!=5:f.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants","non_duplication"):
        if not d.get(section) or any(v is not True for v in d[section].values()):f.append(f"{section} changed")
    if len(d.get("unresolved_until_separate_protocol",[]))!=18:f.append("rules resolved prematurely")
    expected={"u14_paper_protocol_design":True,"public_data_read":False,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected:f.append("authorization matrix changed")
    return f
def validate_all()->list[str]:
    f=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[x for x in ledger["candidates"] if str(x.get("id","")).startswith("U14-")]
    if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYPOTHESIS_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:f.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash")!="ebcf8b78a75911a2567bf84d58363d3c4bd554ec0495bb63457c4d593e34e640":f.append("authorization drift")
    result=load(U13_RESULT)
    if result.get("run_content_hash")!="b94ffc31598899186a005ea1eaba28b274faac2ad9f3fae034e9f71d5868eb3d" or result.get("oos_opened") is not False or result.get("second_run_executed") is not False:f.append("U-13 result drift")
    if load(AUDIT).get("verdict")!="pass":f.append("audit drift")
    return f
def main()->int:
    f=validate_all()
    if f:print("u14_cross_sectional_design_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u14_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
