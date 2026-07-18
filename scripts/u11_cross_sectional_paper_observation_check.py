#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
E=ROOT/"reports/m1/evidence/u11_cross_sectional_paper_observation";ADJ=ROOT/"reports/m1/U11_PAPER_OBSERVATION_ADJUDICATION.md";RUN="0a55b61c83daea4c2f7c61e35db06b50c563a108c23cb74d35b1cb55888a9521";ORDER="558f4af6858315d3355d5c8cc42975b5799a620249d4e3108ed020c64b4226c8";HASHES={"accounting":"4b13f32116eb1fe8908be396ce41ef880a2c796f8e2b3f7bbb4b1a6a96d24077","episodes":"298b468285a0858a37932a12e00543ce4e0f45636247074a9de285c7cb21d1f8","events":"4e7b00dc6eca54f22ccbb8e5d71b0332f28f2510ae88f99c9e4f677a85f41731","paths":"f044a7b863eddf7696c2e5f6fc0ec4cdf5d75d639e6a2d3c7144a56249fb2217"}
def validate(s,m,text):
 f=[]
 if s.get("run_content_hash")!=RUN or identity_hash({k:v for k,v in s.items() if k!="run_content_hash"})!=RUN:f.append("attempt drift")
 if len(s.get("orders",[]))!=3 or any(x.get("content_identity_hash")!=ORDER or x.get("manifest_hashes")!=HASHES for x in s["orders"]):f.append("order drift")
 for n,h in HASHES.items():
  if m[n].get("content_hash")!=h or identity_hash({k:v for k,v in m[n].items() if k!="content_hash"})!=h:f.append(f"manifest drift:{n}")
 a=m["accounting"]["content"]
 if a.get("decision_times_considered")!=9931 or a.get("cross_section_ineligible")!=9925 or a.get("candidate_events")!=0:f.append("defect accounting drift")
 if any(s.get(k) is not False for k in ("oos_opened","formal_returns_computed","second_run_executed","network_accessed")):f.append("isolation drift")
 for marker in ("failed_execution_invalid_observation",RUN,"Retry authorized: `false`"):
  if marker not in text:f.append(f"adjudication marker missing:{marker}")
 return f
def main():
 s=load_json(E/"run_manifest.json");m={n:load_json(E/f"{n}.json") for n in HASHES};f=validate(s,m,ADJ.read_text())
 if f:print("u11_cross_sectional_paper_observation_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u11_cross_sectional_paper_observation_check PASS invalid_attempt={RUN} retry=false");return 0
if __name__=="__main__":raise SystemExit(main())
