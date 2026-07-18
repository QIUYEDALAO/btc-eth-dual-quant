#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/".deps"));import yaml
SCOPE=ROOT/"config/u24_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTHORIZATION=ROOT/"config/u24_design_authorization_v1.json";FAILURE=ROOT/"reports/m1/evidence/u23_cross_sectional_paper_observation/run_manifest.json";AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U24-CROSS-SECTIONAL-LOTTERY-DEMAND-AVOIDANCE-PREMIUM"
HYPOTHESIS="U24-CROSS-SECTIONAL-LOTTERY-DEMAND-AVOIDANCE-PREMIUM: Binance spot USDT long/cash only; using only completed prior observations from the exact point-in-time active member set, an asset whose common-component-adjusted return distribution persistently offers less idiosyncratic right-tail lottery payoff than active peers may attract less preference-driven overpricing, so a relative premium may accrue after the next eligible open; no U-04 through U-23 outcome, defect or failure reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption."
HYPOTHESIS_HASH="0b420693a6206504c4ab6644b2f8e3c9194300bfe096b831d80c12762b18ff34";CONTENT_HASH="c99f7002b006d635d5c03936055e8d4bc498ace02b45551af52cdf80dd14d0c1"
def load(path:Path)->Any:return json.loads(path.read_text())
def identity_hash(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(scope:Mapping[str,Any])->list[str]:
 findings=[];identity={k:v for k,v in scope.items() if k not in {"content_hash","generated_utc"}}
 if scope.get("content_hash")!=CONTENT_HASH or identity_hash(identity)!=CONTENT_HASH:findings.append("design identity changed")
 if scope.get("candidate_id")!=CANDIDATE or scope.get("hypothesis_sha256")!=HYPOTHESIS_HASH:findings.append("candidate identity changed")
 economics=scope.get("economic_hypothesis",{})
 if economics.get("family")!="cross_sectional_lottery_demand_avoidance_premium" or len(economics.get("mechanism",[]))!=5 or len(economics.get("failure_regimes",[]))!=9:findings.append("mechanism coverage changed")
 for section in ("causal_and_membership_invariants","non_duplication"):
  if not scope.get(section) or any(value is not True for value in scope[section].values()):findings.append(f"{section} changed")
 if len(scope.get("unresolved_until_separate_protocol",[]))!=21:findings.append("rules resolved prematurely")
 expected={"u24_paper_protocol_design":True,"synthetic_only_exact_core_feasibility":True,"public_data_read":False,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if scope.get("authorizations")!=expected:findings.append("authorization matrix changed")
 return findings
def validate_all()->list[str]:
 findings=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[item for item in ledger["candidates"] if item.get("id")==CANDIDATE]
 if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYPOTHESIS_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYPOTHESIS_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:findings.append("ledger identity changed")
 if load(AUTHORIZATION).get("content_hash")!="745152692cdada8dad9e0abaf5ea171fb3a1d55d70dbfab32b66c7d2edbdfac5":findings.append("authorization drift")
 failure=load(FAILURE)
 if failure.get("run_content_hash")!="771ce48d80dc48fd2d8f984528541c8a8c1cef4f756892647d66f49b9ffb2604" or failure.get("status")!="failed_feasibility" or failure.get("oos_opened") is not False or failure.get("second_run_executed") is not False:findings.append("U-23 failure drift")
 if load(AUDIT).get("verdict")!="pass":findings.append("audit drift")
 return findings
def main()->int:
 findings=validate_all()
 if findings:
  print("u24_cross_sectional_design_check FAIL");[print(f"- {x}") for x in findings];return 1
 print(f"u24_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
