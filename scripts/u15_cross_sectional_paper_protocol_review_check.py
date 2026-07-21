#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/"reports/expert/evidence/u15_cross_sectional_paper_protocol_review_v1.json";REVIEW_HASH="2686c3acc1f5d46d7b37295530c54268f314cca177197306db7358bb8aa38ceb"
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def target_bytes(head:str,path:str)->bytes:return subprocess.run(["git","show",f"{head}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
def validate_review(d:Mapping[str,Any],verify_git:bool=False)->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"review_content_hash","generated_utc"}}
    if d.get("review_content_hash")!=REVIEW_HASH or canonical_hash(identity)!=REVIEW_HASH:f.append("review identity changed")
    if d.get("verdict")!="approve" or d.get("critical_findings")!=0 or d.get("high_findings")!=0:f.append("verdict changed")
    target=d.get("target",{})
    if target.get("head_sha")!="5438dec609aaaed675e8ecba6f15ae9bb6f6da5a" or target.get("parent_sha")!="6c37a6096e1a6c147ae73483d7f33ecdf4cd4d91" or target.get("protocol_content_hash")!="3b58d6a23cc78e3b644d935599e625c04267317d42608adf2f0321ec51ab577a":f.append("target binding changed")
    if len(d.get("review_dimensions",{}))!=15 or any(v!="pass" for v in d.get("review_dimensions",{}).values()):f.append("review dimensions changed")
    expected={"data_field_qualification_complexity_and_preflight":True,"taker_state_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorization_after_review")!=expected:f.append("authorization changed")
    if verify_git:
        for path,want in target.get("files",{}).items():
            try:got=hashlib.sha256(target_bytes(target["head_sha"],path)).hexdigest()
            except Exception:f.append(f"target unavailable: {path}");continue
            if got!=want:f.append(f"target blob changed: {path}")
    return f
def main()->int:
    f=validate_review(json.loads(REVIEW.read_text()),True)
    if f:print("u15_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u15_cross_sectional_paper_protocol_review_check PASS hash={REVIEW_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
