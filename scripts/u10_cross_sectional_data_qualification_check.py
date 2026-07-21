#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
E=ROOT/"reports/m1/evidence/u10_cross_sectional_data_qualification_v1.json";REPORT=ROOT/"reports/m1/U10_CROSS_SECTIONAL_DATA_QUALIFICATION.md";HASH="0029def278eeadf6b3951e1e1f62d16b0919889950eb68e0cdd3fe97fe727ee2";ORDER="ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa"
def validate(d:Mapping[str,Any],text:str)->list[str]:
 f=[]
 if identity_hash({k:v for k,v in d.items() if k!="qualification_content_hash"})!=d.get("qualification_content_hash") or d.get("qualification_content_hash")!=HASH:f.append("qualification hash drift")
 if d.get("status")!="pass" or d.get("contract_content_hash")!="c47701dca14ffab10b94efe2a855dd85c68ab01647c2feede3b8db86c80661bf":f.append("contract/status drift")
 c=d.get("counts",{});expected={"archive_count":27736,"manifests_exact":19,"quote_volume_authority_rows":1170,"bars_per_complete_day":288,"eligible_constant_membership_decision_days":1603,"maximum_independent_constant_membership_episodes":418}
 if any(c.get(k)!=v for k,v in expected.items()):f.append("count drift")
 if len(d.get("orders",[]))!=3 or any(x.get("content_identity_hash")!=ORDER for x in d.get("orders",[])):f.append("order drift")
 i=d.get("isolation",{})
 if i.get("oos_opened") is not False or any(i.get(k)!=0 for k in ("oos_ohlcv_values_decoded","daily_signal_rows_generated","candidate_rows_generated","event_rows_generated","path_rows_generated","return_rows_generated")):f.append("isolation drift")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["one_sealed_is_paper_observation"]:f.append("authorization drift")
 for m in ("Status: `pass`","27,736 frozen ZIP","maximum 418"):
  if m not in text:f.append(f"report marker missing: {m}")
 return f
def main()->int:
 d=load_json(E);f=validate(d,REPORT.read_text())
 if f:print("u10_cross_sectional_data_qualification_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u10_cross_sectional_data_qualification_check PASS hash={HASH} ceiling=418");return 0
if __name__=="__main__":raise SystemExit(main())
