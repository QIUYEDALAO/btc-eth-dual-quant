#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
EVIDENCE=ROOT/"reports/m1/evidence/u22_cross_sectional_paper_observation";RUN=EVIDENCE/"run_manifest.json";EXPECTED="12a756e2fa8a0fa2e2b87f69c8dc00559f3021a27368a0ac4efc8f5e8001531c";HASHES={"accounting":"868d527647e6dee67e6e9064c72b403c1782a8287e8c44c85a64692adb6f3fc0","episodes":"82c98aa488b5d3a74ddcf4795baa940df44d91968d8e2e9f85922811792be8fe","events":"0df408e0cc522bbcd88128cd2f44cdf2d93e84604ae9cba2714011c70c20d2f6","paths":"d81b3199b3e888809fb76f4eb7d8f85f5b8e7d4964a407df8ce0efdbb7e686bb"}
def validate(run:Mapping[str,Any])->list[str]:
 f=[];identity={k:v for k,v in run.items() if k!="run_content_hash"}
 if run.get("run_content_hash")!=EXPECTED or identity_hash(identity)!=EXPECTED:f.append("run identity")
 if run.get("status")!="failed_feasibility" or run.get("oos_opened") is not False or run.get("second_run_executed") is not False or run.get("formal_returns_computed") is not False:f.append("status/isolation")
 orders=run.get("orders",[])
 if len(orders)!=3 or len({r.get("content_identity_hash") for r in orders})!=1 or any(r.get("manifest_hashes")!=HASHES for r in orders):f.append("orders")
 m=run.get("metrics",{})
 if m.get("complete_is_independent_episodes")!=198 or m.get("median_24h_relative_leader_continuation")!="-0.001687854951459260169225285968" or m.get("median_24h_candidate_absolute_close_displacement")!="0.001114962219070440020390258450" or m.get("fraction_complete_episodes_with_positive_24h_relative_leader_continuation")!="0.4797979797979797979797979798":f.append("metrics")
 failed={k for k,v in run.get("paper_gate_checks",{}).items() if not v}
 if failed!={"median_24h_relative_leader_continuation","median_24h_candidate_absolute_close_displacement","fraction_positive_24h_relative_leader_continuation"}:f.append("failed Gates")
 if any(run.get("authorizations",{}).values()):f.append("authorization")
 for n,h in HASHES.items():
  d=load_json(EVIDENCE/f"{n}.json")
  if d.get("content_hash")!=h or identity_hash({k:v for k,v in d.items() if k!="content_hash"})!=h:f.append(n)
 return f
def main()->int:
 f=validate(load_json(RUN));print("u22_cross_sectional_paper_observation_check "+("PASS failed_feasibility" if not f else "FAIL")+f" hash={EXPECTED}");return bool(f)
if __name__=="__main__":raise SystemExit(main())
