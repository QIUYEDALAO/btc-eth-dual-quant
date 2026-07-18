#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import yaml
ROOT=Path(__file__).resolve().parents[1];SCOPE=ROOT/"config/u16_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTHORIZATION=ROOT/"config/u16_design_authorization_v1.json";FAILURE=ROOT/"reports/m1/evidence/u15_taker_buy_field_qualification_failure_v1.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U16-CROSS-SECTIONAL-CORRELATION-BREAKDOWN-INFORMATION-PERSISTENCE";HYPOTHESIS="U16-CROSS-SECTIONAL-CORRELATION-BREAKDOWN-INFORMATION-PERSISTENCE: Binance spot USDT long/cash only; using only completed observations from the exact point-in-time active member set, an asset that develops positive relative price displacement while its prior-only return path decouples from the contemporaneous peer common component may reflect asset-specific information being incorporated gradually and may continue after the next eligible open; no U-04 through U-15 outcome, defect or field-failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption.";HYPOTHESIS_HASH="781093529714314144be705cef84c0563a59630e71243827950b47cf6c15f2f1";CONTENT_HASH="8574e5c5aa068f10a561d8cfae26d4a45d5b9eb17287156912fa4d8b5fd075d1"
def load(p:Path)->Any:return json.loads(p.read_text())
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(d:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=CONTENT_HASH or h(identity)!=CONTENT_HASH:f.append("design identity changed")
    if d.get("candidate_id")!=CANDIDATE or d.get("hypothesis_sha256")!=HYPOTHESIS_HASH:f.append("candidate identity changed")
    e=d.get("economic_hypothesis",{})
    if e.get("family")!="cross_sectional_correlation_breakdown_information_persistence" or len(e.get("mechanism",[]))!=5 or len(e.get("failure_regimes",[]))!=10:f.append("mechanism coverage changed")
    for section in ("causal_and_membership_invariants","non_duplication"):
        if not d.get(section) or any(v is not True and not (section=="causal_and_membership_invariants" and k=="volume_or_taker_field_required" and v is False) for k,v in d[section].items()):f.append(f"{section} changed")
    if len(d.get("unresolved_until_separate_protocol",[]))!=20:f.append("rules resolved prematurely")
    expected={"u16_paper_protocol_design":True,"public_data_read":False,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected:f.append("authorization matrix changed")
    return f
def validate_all()->list[str]:
    f=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[x for x in ledger["candidates"] if x.get("id")==CANDIDATE]
    if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYPOTHESIS_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:f.append("ledger identity changed")
    if load(AUTHORIZATION).get("content_hash")!="05346312b0e47168a17a77cd19d1a73525b17eb9f64de29b2b157a5c673528fc":f.append("authorization drift")
    failure=load(FAILURE)
    if failure.get("content_hash")!="83eb8ac2ec1726884f9b3f37bcfe0c13620bca06e98e7539a0e79466d8d63c28" or failure.get("decision",{}).get("candidate_closed") is not True:f.append("U-15 failure drift")
    if load(AUDIT).get("verdict")!="pass":f.append("audit drift")
    return f
def main()->int:
    f=validate_all()
    if f:print("u16_cross_sectional_design_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u16_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
