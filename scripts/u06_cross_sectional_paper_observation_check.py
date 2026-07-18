#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
E=ROOT/"reports/m1/evidence/u06_cross_sectional_paper_observation";REPORT=ROOT/"reports/m1/U06_CROSS_SECTIONAL_PAPER_OBSERVATION.md";RUN="2f715394411ca260f9889304ddc84da926d37ec1dfc9d4316493f23f6881382a";ORDER="b60423c216a6a9a109ac47d645d5ccae5f3f7c3d0fb9a9ffd0df9204bcee762c";HASHES={"accounting":"a5f4a4a0eb5f197dbc59e69d5a7db05bf13ed2c3913e0e4d4da1bdefaef072fc","episodes":"949a01632ed17396bccaf898e681fef871a499bed4a448e6675614a673fff58c","events":"48d7aa9d3aea1f1b0262c5196fc2d0a9d1a5df8d08eb478b86a38b5ba2ecf5f7","paths":"475f6cdee7838a99a4dd569a8e546d5e38b0a0cdac306369961c8f380f6bb1db"}
def validate(s:Mapping[str,Any],m:Mapping[str,Mapping[str,Any]],text:str)->list[str]:
 f=[]
 if identity_hash({k:v for k,v in s.items() if k!="run_content_hash"})!=s.get("run_content_hash") or s.get("run_content_hash")!=RUN:f.append("run hash drift")
 for n,h in HASHES.items():
  d=m[n]
  if identity_hash({k:v for k,v in d.items() if k!="content_hash"})!=d.get("content_hash") or d.get("content_hash")!=h:f.append(f"manifest drift: {n}")
 if s.get("status")!="failed_feasibility":f.append("truthful status changed")
 if any(x.get("content_identity_hash")!=ORDER or x.get("manifest_hashes")!=HASHES for x in s.get("orders",[])):f.append("order identity drift")
 metrics=s.get("metrics",{})
 expected={"complete_is_independent_episodes":56,"projected_full_independent_episodes":77,"projected_sealed_oos_independent_episodes":21,"distinct_event_symbols":23,"median_24h_relative_repricing":"-0.001437523976085089153319753825","median_24h_candidate_absolute_close_displacement":"-0.0030291579131649309986646607","qualification_quarantine_lifecycle_or_order_mismatches":0}
 if any(metrics.get(k)!=v for k,v in expected.items()):f.append("metric drift")
 failed=sorted(k for k,v in s.get("paper_gate_checks",{}).items() if not v)
 if failed!=["complete_is_independent_episodes","median_24h_candidate_absolute_close_displacement","median_24h_relative_repricing","projected_full_independent_episodes"]:f.append("failed Gate set changed")
 if any(s.get(k) is not False for k in ("oos_opened","formal_returns_computed","fills_positions_or_equity_generated","parameters_changed_after_result","second_run_executed","network_accessed")) or any(s.get("authorizations",{}).values()):f.append("isolation or downstream authorization changed")
 for marker in ("Status: `failed_feasibility`","Complete independent episodes: `56`","OOS opened / rows decoded: `false / 0`","A failed Gate closes the candidate without tuning"):
  if marker not in text:f.append(f"report marker missing: {marker}")
 return f
def main()->int:
 s=load_json(E/"run_manifest.json");m={n:load_json(E/f"{n}.json") for n in HASHES};f=validate(s,m,REPORT.read_text())
 if f:print("u06_cross_sectional_paper_observation_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u06_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN}");return 0
if __name__=="__main__":raise SystemExit(main())
