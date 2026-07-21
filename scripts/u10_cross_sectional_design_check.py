#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
import yaml
ROOT=Path(__file__).resolve().parents[1];SCOPE=ROOT/"config/u10_cross_sectional_design_scope_v1.json";LEDGER=ROOT/"STRATEGY_TRIAL_LEDGER.yaml";AUTH=ROOT/"config/u10_design_authorization_v1.json";CORRECTION=ROOT/"reports/m1/evidence/u09_qualification_sample_ceiling_correction_v1.json";RESULTS=[ROOT/f"reports/m1/evidence/u0{i}_cross_sectional_paper_observation/run_manifest.json" for i in (8,7,6,5,4)];AUDIT=ROOT/"reports/m0/evidence/liquid_universe_v4_adr0015_independent_audit/audit_summary.json"
CANDIDATE="U10-CROSS-SECTIONAL-VOLUME-CONFIRMED-RELATIVE-TREND-CONTINUATION";HYPOTHESIS="U10-CROSS-SECTIONAL-VOLUME-CONFIRMED-RELATIVE-TREND-CONTINUATION: Binance spot USDT long/cash only; using only completed observations from the exact point-in-time active member set, asset-specific positive relative price trend accompanied by a persistent rise in cross-sectional quote-volume share may reflect scalable informed demand rather than thin-price noise and may continue after the next eligible open; no U-04/U-05/U-06/U-07/U-08 outcome inversion, U-09 protocol-defect reuse, current-membership hindsight, replacement members, shorting, leverage, loss adding, or lifecycle-crossing assumption.";HYP_HASH="5fc3529f7afa3df2344517f3bd567c5b3bf89a23bc0e071ff853bc80e50ec536";CONTENT_HASH="af9ac64043adacad08ef834567ff976b26723fb1468d1a7a0d43e6fa5eaa40e5"
def load(p):return json.loads(p.read_text())
def ch(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_scope(d:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
 if d.get("content_hash")!=CONTENT_HASH or ch(identity)!=CONTENT_HASH:f.append("design identity changed")
 if d.get("candidate_id")!=CANDIDATE or d.get("hypothesis_sha256")!=HYP_HASH:f.append("candidate identity changed")
 if d.get("economic_hypothesis",{}).get("family")!="cross_sectional_volume_confirmed_relative_trend_continuation" or len(d.get("economic_hypothesis",{}).get("failure_regimes",[]))!=9:f.append("mechanism coverage changed")
 for s in ("causal_and_membership_invariants","non_duplication"):
  if not d.get(s) or any(v is not True for v in d[s].values()):f.append(f"{s} changed")
 if len(d.get("unresolved_until_separate_protocol",[]))!=15:f.append("rules resolved prematurely")
 expected={"u10_paper_protocol_design":True,"event_scan":False,"signals":False,"returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if d.get("authorizations")!=expected:f.append("authorization matrix changed")
 return f
def validate_all()->list[str]:
 f=validate_scope(load(SCOPE));ledger=yaml.safe_load(LEDGER.read_text());matches=[x for x in ledger["candidates"] if str(x.get("id","")).startswith("U10-")]
 if len(matches)!=1 or matches[0].get("hypothesis")!=HYPOTHESIS or matches[0].get("sha256")!=HYP_HASH or hashlib.sha256(matches[0].get("hypothesis","").encode()).hexdigest()!=HYP_HASH or matches[0].get("status")!="declared_unopened" or matches[0].get("oos_opened") is not False:f.append("ledger identity changed")
 if load(AUTH).get("content_hash")!="e196cc0fdd20e8b8fc84872b440baa09ae69e0752c75005bebefb51a4060c7a0":f.append("authorization drift")
 if load(CORRECTION).get("status")!="failed_pre_observation_sample_ceiling":f.append("U-09 correction drift")
 for p in RESULTS:
  d=load(p)
  if d.get("status")!="failed_feasibility" or d.get("oos_opened") is not False or d.get("second_run_executed") is not False:f.append(f"prior result drift: {p.name}")
 if load(AUDIT).get("verdict")!="pass":f.append("audit drift")
 return f
def main()->int:
 f=validate_all()
 if f:print("u10_cross_sectional_design_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u10_cross_sectional_design_check PASS candidate={CANDIDATE} hash={CONTENT_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
