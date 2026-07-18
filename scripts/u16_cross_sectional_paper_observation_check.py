#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any,Mapping
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
EVIDENCE=ROOT/"reports/m1/evidence/u16_cross_sectional_paper_observation";RUN=EVIDENCE/"run_manifest.json";EXPECTED="322fda776158c5c035a30821460ac3acd7477a99b747aa6d08bfa68a55984d14"
def validate(run:Mapping[str,Any])->list[str]:
    f=[];identity={k:v for k,v in run.items() if k!="run_content_hash"}
    if run.get("run_content_hash")!=EXPECTED or identity_hash(identity)!=EXPECTED:f.append("run identity changed")
    if run.get("status")!="failed_feasibility" or run.get("oos_opened") is not False or run.get("second_run_executed") is not False or run.get("formal_returns_computed") is not False:f.append("status or isolation changed")
    orders=run.get("orders",[])
    if len(orders)!=3 or len({x.get("content_identity_hash") for x in orders})!=1:f.append("order identity changed")
    expected_hashes={"accounting":"27641261de7719176d21ac91c694dba1b76fc0fb14215121329adbd25e033b3a","episodes":"6cf26d5403576ed1f57d6592ccd5b77aef52fd0e71ebdc069b273a64ffc8ce3d","events":"9adafb56d90fb86da5fd4c7307b5943b5f4ee725893b767a7af9c655cc9f8ac3","paths":"042337e3db321ebb11382bf5cd2c8f3047c8c76e16d6c58093da3da8ca800d20"}
    if any(x.get("manifest_hashes")!=expected_hashes for x in orders):f.append("manifest hashes changed")
    m=run.get("metrics",{})
    if m.get("complete_is_independent_episodes")!=169 or m.get("median_24h_relative_information_persistence")!="0.0010025265182264580534731423602822784465997897076" or m.get("median_24h_candidate_absolute_close_displacement")!="-0.00042674253200568990042674253200568990042674253201" or m.get("fraction_complete_episodes_with_positive_24h_relative_information_persistence")!="0.5266272189349112426035502959":f.append("metrics changed")
    checks=run.get("paper_gate_checks",{});failed={k for k,v in checks.items() if not v}
    if failed!={"median_24h_relative_information_persistence","median_24h_candidate_absolute_close_displacement","fraction_positive_24h_relative_information_persistence"}:f.append("failed Gates changed")
    if any(run.get("authorizations",{}).values()):f.append("downstream authorization changed")
    for name,want in expected_hashes.items():
        document=load_json(EVIDENCE/f"{name}.json")
        if document.get("content_hash")!=want or identity_hash({k:v for k,v in document.items() if k!="content_hash"})!=want:f.append(f"{name} evidence changed")
    return f
def main()->int:
    f=validate(load_json(RUN))
    if f:print("u16_cross_sectional_paper_observation_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u16_cross_sectional_paper_observation_check PASS failed_feasibility hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
