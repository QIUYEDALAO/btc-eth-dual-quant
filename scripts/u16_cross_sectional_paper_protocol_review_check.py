#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/"reports/expert/evidence/u16_cross_sectional_paper_protocol_review_v1.json";EXPECTED="2f708c0f6ac7b4e79428a4a7b1e9850182120c2dfcb3b06b53f973123f5c34e3"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],verify_git:bool=False)->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"review_content_hash","generated_utc"}};target=d.get("target",{})
    if d.get("review_content_hash")!=EXPECTED or h(identity)!=EXPECTED:f.append("review identity changed")
    if d.get("verdict")!="approve" or d.get("critical_findings")!=0 or d.get("high_findings")!=0:f.append("verdict changed")
    if target.get("head_sha")!="9cafb08dbe59faa48c948458151eb7cb7d6c1ddb" or target.get("parent_sha")!="0466766defc0dbd716392e5b9a35e1dabf514017" or target.get("protocol_content_hash")!="18e302deb6a3d9fddf8b2b5b8866d39355a95519c91f609ce670d64168f5633a":f.append("target binding changed")
    if len(d.get("review_dimensions",{}))!=16 or any(v!="pass" for v in d.get("review_dimensions",{}).values()):f.append("dimensions changed")
    expected={"data_qualification_complexity_and_preflight":True,"common_path_scan":False,"correlation_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorization_after_review")!=expected:f.append("authorization changed")
    if verify_git:
        for path,want in target.get("files",{}).items():
            try:data=subprocess.run(["git","show",f"{target['head_sha']}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
            except Exception:f.append(f"target unavailable: {path}");continue
            if hashlib.sha256(data).hexdigest()!=want:f.append(f"target blob changed: {path}")
    return f
def main()->int:
    f=validate(json.loads(REVIEW.read_text()),True)
    if f:print("u16_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u16_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
