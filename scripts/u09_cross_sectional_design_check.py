#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import yaml
ROOT=Path(__file__).resolve().parents[1];SCOPE=ROOT/"config/u09_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTH=ROOT/"config/u09_design_authorization_v1.json"
RESULTS=[ROOT/f"reports/m1/evidence/u0{i}_cross_sectional_paper_observation/run_manifest.json" for i in (8,7,6,5,4)]
AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U09-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-QUALITY-PERSISTENCE";HYPOTHESIS="U09-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-QUALITY-PERSISTENCE: Binance spot USDT long/cash only; using only completed observations from the exact point-in-time active member set, an asset with persistently lower asset-specific volatility after removing the contemporaneous common market component may reflect deeper liquidity, lower disagreement and broader capital eligibility that can preserve relative quality after the next eligible open; no U-04/U-05/U-06/U-07/U-08 outcome inversion, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption.";HYP_HASH="cb91d77d11b0f877007848330df7e05e1d4e9257142fce4d339edefe75e14c92";CONTENT_HASH="4830e361b66cd434e54a5ed284d0ad1e85c1e9270d3542dacf3efec5f4eee6f2"
def load(p):return json.loads(p.read_text())
def ch(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(d:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=CONTENT_HASH or ch(identity)!=CONTENT_HASH:f.append("design identity changed")
 if d.get("candidate_id")!=CANDIDATE or d.get("hypothesis_sha256")!=HYP_HASH:f.append("candidate identity changed")
 if d.get("economic_hypothesis",{}).get("family")!="cross_sectional_idiosyncratic_volatility_quality_persistence" or len(d.get("economic_hypothesis",{}).get("failure_regimes",[]))!=9:f.append("mechanism coverage changed")
 for s in ("causal_and_membership_invariants","non_duplication"):
  if not d.get(s) or any(v is not True for v in d[s].values()):f.append(f"{s} changed")
 if len(d.get("unresolved_until_separate_protocol",[]))!=15:f.append("rules resolved prematurely")
 expected={"u09_paper_protocol_design":True,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if d.get("authorizations")!=expected:f.append("authorization matrix changed")
 return f
def validate_all()->list[str]:
 f=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[x for x in ledger["candidates"] if str(x.get("id","")).startswith("U09-")]
 if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYP_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYP_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:f.append("ledger identity changed")
 if load(AUTH).get("content_hash")!="2d643678e00575c93dad0331fff089fd620b214f658ca8d174dfe9bbcc06e477":f.append("authorization drift")
 for p in RESULTS:
  d=load(p)
  if d.get("status")!="failed_feasibility" or d.get("oos_opened") is not False or d.get("second_run_executed") is not False:f.append(f"prior result drift: {p.name}")
 if load(AUDIT).get("verdict")!="pass":f.append("audit drift")
 return f
def main()->int:
 f=validate_all()
 if f:print("u09_cross_sectional_design_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u09_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
