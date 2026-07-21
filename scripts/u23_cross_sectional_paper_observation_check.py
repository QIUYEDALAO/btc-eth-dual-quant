#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
EVIDENCE=ROOT/"reports/m1/evidence/u23_cross_sectional_paper_observation";RUN=EVIDENCE/"run_manifest.json";EXPECTED="771ce48d80dc48fd2d8f984528541c8a8c1cef4f756892647d66f49b9ffb2604";HASHES={"accounting":"cbaa366c995750a3ec928177b36a97b3f8ea2e354cd2da2c4695d9d5d8fb064b","episodes":"639d7952610fdec2573efb0fbb04b906cb4b60a5a660b7885163656b1aee4ac9","events":"8f450e61cac43f966e8737a000911273784752440e342512964082cdd8474497","paths":"b10a27f333f911cd975de9be6de70622f5b7c3ec52d62b874881388dae6bfb24"}
def validate(run:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in run.items() if k!="run_content_hash"}
 if run.get("run_content_hash")!=EXPECTED or identity_hash(identity)!=EXPECTED:f.append("run identity")
 if run.get("status")!="failed_feasibility" or run.get("oos_opened") is not False or run.get("second_run_executed") is not False or run.get("formal_returns_computed") is not False:f.append("status/isolation")
 orders=run.get("orders",[])
 if len(orders)!=3 or len({r.get("content_identity_hash") for r in orders})!=1 or any(r.get("manifest_hashes")!=HASHES for r in orders):f.append("orders")
 m=run.get("metrics",{})
 if m.get("complete_is_independent_episodes")!=178 or m.get("median_24h_relative_close_strength_continuation")!="-0.01195215777238291818366680124" or m.get("median_24h_candidate_absolute_close_displacement")!="-0.009181371869888384699633004195" or m.get("fraction_complete_episodes_with_positive_24h_relative_close_strength_continuation")!="0.3483146067415730337078651685":f.append("metrics")
 failed={k for k,v in run.get("paper_gate_checks",{}).items() if not v}
 if failed!={"median_24h_relative_close_strength_continuation","median_24h_candidate_absolute_close_displacement","fraction_positive_24h_relative_close_strength_continuation"}:f.append("failed Gates")
 if any(run.get("authorizations",{}).values()):f.append("authorization")
 for n,h in HASHES.items():
  d=load_json(EVIDENCE/f"{n}.json")
  if d.get("content_hash")!=h or identity_hash({k:v for k,v in d.items() if k!="content_hash"})!=h:f.append(n)
 return f
def main()->int:
 f=validate(load_json(RUN));print("u23_cross_sectional_paper_observation_check "+("PASS failed_feasibility" if not f else "FAIL")+f" hash={EXPECTED}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
