#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"reports/expert/evidence/u09_cross_sectional_paper_protocol_review_v1.json";REPORT=ROOT/"reports/expert/U09_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md";TARGET="1bee65ff9dcdf0b9b3e49e37601140068cc968c8";BASE="29018d811a53abd2f96377c8ac3ab25981965824";REVIEW="dd6779dab8be86fffa17d08a6a64b3085963e3e89b1889b24b6f125f64bb2947"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def blob(path:str)->bytes:return subprocess.run(["git","show",f"{TARGET}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
def validate(d:Mapping[str,Any],text:str)->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"review_content_hash","generated_utc"}}
 if d.get("review_content_hash")!=REVIEW or h(identity)!=REVIEW:f.append("review identity changed")
 if d.get("target_commit")!=TARGET or d.get("target_base_commit")!=BASE or d.get("protocol_content_hash")!="874b93ce7c300c14663147041d351efae7dd22a4a20ab76d837474ca6b2584ae":f.append("target binding changed")
 for path,expected in d.get("target_file_sha256",{}).items():
  if hashlib.sha256(blob(path)).hexdigest()!=expected:f.append(f"target blob drift: {path}")
 if len(d.get("dimensions",{}))!=13 or any(v!="pass" for v in d.get("dimensions",{}).values()):f.append("review dimension failure")
 if d.get("verdict")!="approve" or d.get("remaining_critical_findings")!=0 or d.get("remaining_high_findings")!=0 or d.get("target_modified") is not False:f.append("verdict changed")
 expected={"data_qualification":True,"event_scan":False,"path_observation":False,"formal_returns":False,"strategy":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
 if d.get("authorizations")!=expected:f.append("review authorization changed")
 for marker in ("Verdict: `approve`",TARGET,"Remaining critical/high findings: `0 / 0`","Target modified: `false`"):
  if marker not in text:f.append(f"report marker missing: {marker}")
 return f
def main()->int:
 d=json.loads(E.read_text());f=validate(d,REPORT.read_text())
 if f:print("u09_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u09_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0");return 0
if __name__=="__main__":raise SystemExit(main())
