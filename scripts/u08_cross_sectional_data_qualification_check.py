#!/usr/bin/env python3
from __future__ import annotations
import copy,sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
E=ROOT/"reports/m1/evidence/u08_cross_sectional_data_qualification_v1.json";REPORT=ROOT/"reports/m1/U08_CROSS_SECTIONAL_DATA_QUALIFICATION.md";HASH="1ec26ef74b80c2b46cfd0dcb231ee8863ae2bd0ff01fabf33dd4028b13807cb5";ORDER="ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa"
def validate(d:Mapping[str,Any],text:str)->list[str]:
 f=[]
 if identity_hash({k:v for k,v in d.items() if k!="qualification_content_hash"})!=d.get("qualification_content_hash") or d.get("qualification_content_hash")!=HASH:f.append("qualification hash drift")
 if d.get("status")!="pass" or d.get("contract_content_hash")!="0adc8d4928e245e05a981f6ad997be01cd1fea876c0717e6a8d85ee8ca31f51e":f.append("contract/status drift")
 c=d.get("counts",{});expected={"archive_count":27736,"manifests_exact":19,"membership_months":78,"membership_rows":1170,"rank_rows_verified":1170}
 if any(c.get(k)!=v for k,v in expected.items()):f.append("count drift")
 if len(d.get("orders",[]))!=3 or any(x.get("content_identity_hash")!=ORDER for x in d.get("orders",[])):f.append("order drift")
 i=d.get("isolation",{})
 if i.get("oos_opened") is not False or any(i.get(k)!=0 for k in ("oos_ohlc_values_decoded","membership_entry_rows_generated","event_rows_generated","path_rows_generated","return_rows_generated")):f.append("isolation drift")
 if [k for k,v in d.get("authorizations",{}).items() if v] != ["one_sealed_is_paper_observation"]:f.append("authorization drift")
 for m in ("Status: `pass`","27,736 frozen ZIP","OOS OHLC decoded, membership-entry events, paths and returns"):
  if m not in text:f.append(f"report marker missing: {m}")
 return f
def main()->int:
 d=load_json(E);f=validate(d,REPORT.read_text())
 if f:print("u08_cross_sectional_data_qualification_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u08_cross_sectional_data_qualification_check PASS hash={HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
