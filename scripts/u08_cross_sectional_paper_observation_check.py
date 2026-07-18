#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
E=ROOT/"reports/m1/evidence/u08_cross_sectional_paper_observation";REPORT=ROOT/"reports/m1/U08_CROSS_SECTIONAL_PAPER_OBSERVATION.md";RUN="f6fbcdee846b855883a5e356ea49e6a98901bfcc6a9dbd5a2cbb07ebed9eca3e";ORDER="5e77484b1db6365787ea4e5acffc33e4d599b81fa7b95925257e7d2d6448b928";HASHES={"accounting":"da89e920f808a41b83409630a6b4e7647be076a55ecbb0e1fcb113cbfb76ce28","episodes":"a73135090fa42b60479dddf4e41402495f74e192670ea36195acd5043e5b092d","events":"02f7fcf7c9b2f0877d1656cf25971828579837d6514c605a08ad4390bb0c6dba","paths":"d3b644fc09497d80f8b3ab9a84481bbb1a387cff261d88411e972aa82c3e01b6"}
def validate(s:Mapping[str,Any],m:Mapping[str,Mapping[str,Any]],text:str)->list[str]:
 f=[]
 if identity_hash({k:v for k,v in s.items() if k!="run_content_hash"})!=s.get("run_content_hash") or s.get("run_content_hash")!=RUN:f.append("run hash drift")
 for n,h in HASHES.items():
  d=m[n]
  if identity_hash({k:v for k,v in d.items() if k!="content_hash"})!=d.get("content_hash") or d.get("content_hash")!=h:f.append(f"manifest drift: {n}")
 if s.get("status")!="failed_feasibility" or len(s.get("orders",[]))!=3 or any(x.get("content_identity_hash")!=ORDER or x.get("manifest_hashes")!=HASHES for x in s.get("orders",[])):f.append("status/order drift")
 metrics=s.get("metrics",{});expected={"complete_is_independent_episodes":44,"projected_full_independent_episodes":60,"projected_sealed_oos_independent_episodes":16,"distinct_event_symbols":30,"distinct_event_months":44,"median_336h_relative_persistence":"-0.004690053061224479018914325351","median_336h_candidate_absolute_close_displacement":"-0.03354318740899883968767093616","fraction_complete_episodes_with_positive_336h_relative_persistence":"0.4545454545454545454545454545","qualification_quarantine_lifecycle_or_order_mismatches":0}
 if any(metrics.get(k)!=v for k,v in expected.items()):f.append("metric drift")
 if sorted(k for k,v in s.get("paper_gate_checks",{}).items() if not v)!=["fraction_positive_336h_relative_persistence","median_336h_candidate_absolute_close_displacement","median_336h_relative_persistence"]:f.append("failed Gate set changed")
 if any(s.get(k) is not False for k in ("oos_opened","formal_returns_computed","fills_positions_or_equity_generated","parameters_changed_after_result","second_run_executed","network_accessed")) or any(s.get("authorizations",{}).values()):f.append("isolation/authorization drift")
 for marker in ("Status: `failed_feasibility`","Complete independent episodes: `44`","OOS opened / rows decoded: `false / 0`","A failed Gate closes U-08 without tuning"):
  if marker not in text:f.append(f"report marker missing: {marker}")
 return f
def main()->int:
 s=load_json(E/"run_manifest.json");m={n:load_json(E/f"{n}.json") for n in HASHES};f=validate(s,m,REPORT.read_text())
 if f:print("u08_cross_sectional_paper_observation_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u08_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN}");return 0
if __name__=="__main__":raise SystemExit(main())
