#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash,load_json
from scripts.u06_cross_sectional_data_qualification import CONFIG,canonical_hash
RESULT=ROOT/"reports/m1/evidence/u06_cross_sectional_data_qualification_v1.json";REPORT=ROOT/"reports/m1/U06_CROSS_SECTIONAL_DATA_QUALIFICATION.md";EXPECTED="e6a4a0eb47af2d88f30ab827d4456969549f86c5c81b7affedb91b034cb95a67"
def validate(c:Mapping[str,Any],r:Mapping[str,Any],text:str)->list[str]:
 f=[]
 if canonical_hash(c)!=c.get("content_hash"):f.append("contract hash drift")
 if identity_hash({k:v for k,v in r.items() if k!="qualification_content_hash"})!=r.get("qualification_content_hash") or r.get("qualification_content_hash")!=EXPECTED:f.append("result hash drift")
 if r.get("status")!="pass" or r.get("protocol_target_commit")!=c.get("protocol_target_commit") or r.get("protocol_review_content_hash")!=c.get("protocol_review_content_hash"):f.append("protocol/review binding drift")
 counts=r.get("counts",{})
 for k,v in {"archive_count":27736,"manifests_exact":19,"quote_volume_authority_rows":1170,"bars_per_complete_day":288,"expected_five_minute_rows":10251360}.items():
  if counts.get(k)!=v:f.append(f"count drift: {k}")
 orders=r.get("orders",[])
 if [x.get("order") for x in orders]!=["normal","reverse","deterministic_shuffled"] or len({x.get("content_identity_hash") for x in orders})!=1:f.append("order identity drift")
 iso=r.get("isolation",{})
 if iso!={"is_start":"2020-01-01T00:00:00Z","is_end_exclusive":"2024-09-11T00:00:00Z","oos_opened":False,"oos_archive_access":"opaque_identity_and_crc_only","oos_ohlcv_values_decoded":0,"daily_signal_rows_generated":0,"event_rows_generated":0,"path_rows_generated":0,"return_rows_generated":0}:f.append("isolation drift")
 if r.get("authorizations",{}).get("one_sealed_is_paper_observation") is not True or any(r.get("authorizations",{}).get(k) is not False for k in ("event_scan_beyond_one_frozen_is_observation","strategy","backtesting","oos","api_trading","execution_live","m2")):f.append("authorization drift")
 for m in ("Status: `pass`","27,736/27,736","19/19","OOS OHLCV values decoded: `0`","one sealed-IS Paper observation","No strategy, backtest"):
  if m not in text:f.append(f"report marker missing: {m}")
 return f
def main()->int:
 f=validate(load_json(CONFIG),load_json(RESULT),REPORT.read_text())
 if f:print("u06_cross_sectional_data_qualification_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u06_cross_sectional_data_qualification_check PASS hash={EXPECTED} next=one sealed-IS observation");return 0
if __name__=="__main__":raise SystemExit(main())
