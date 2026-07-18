#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/"reports/expert/evidence/u24_cross_sectional_paper_protocol_review_v1.json";EXPECTED="b032f88ab2f8c6cfd42c15a7665ebc3122187c72bdcc14d1a319b03bcb57db17"
def identity_hash(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(review:Mapping[str,Any],verify_git:bool=False)->list[str]:
 findings=[];identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}};target=review.get("target",{})
 if review.get("review_content_hash")!=EXPECTED or identity_hash(identity)!=EXPECTED:findings.append("review identity changed")
 if review.get("verdict")!="approve" or review.get("critical_findings")!=0 or review.get("high_findings")!=0:findings.append("verdict changed")
 if target.get("head_sha")!="cafbd5a90f5fd3a435d15ff03af0ecec2df98c3f" or target.get("parent_sha")!="8794ef3d5d613efb42cc31b62bfc607db6353949" or target.get("protocol_content_hash")!="5110c3f455274f291391ed9b34affe6e5f61beb9198723d4fb0b8f07439c7ce7" or target.get("synthetic_feasibility_content_hash")!="ce8b0f7998cc1c8e3928c605cccd0da37087a620d37e8058ae55e02f26957484":findings.append("target binding changed")
 if len(target.get("files",{}))!=9 or len(review.get("review_dimensions",{}))!=16 or any(v!="pass" for v in review.get("review_dimensions",{}).values()):findings.append("dimensions changed")
 expected={"data_qualification_and_preflight":True,"return_common_adjustment_lottery_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if review.get("authorization_after_review")!=expected:findings.append("authorization changed")
 if verify_git:
  for path,wanted in target.get("files",{}).items():
   try:data=subprocess.run(["git","show",f"{target['head_sha']}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
   except Exception:findings.append(f"target unavailable: {path}");continue
   if hashlib.sha256(data).hexdigest()!=wanted:findings.append(f"target blob changed: {path}")
 return findings
def main()->int:
 findings=validate(json.loads(REVIEW.read_text()),True)
 if findings:print("u24_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in findings];return 1
 print(f"u24_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}");return 0
if __name__=="__main__":raise SystemExit(main())
