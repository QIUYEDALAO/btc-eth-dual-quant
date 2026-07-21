#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"reports/expert/evidence/u10_cross_sectional_paper_protocol_review_v1.json";REPORT=ROOT/"reports/expert/U10_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md";TARGET="f468b7aeaaf02f803125b4ab6037086fb353776f";BASE="6f21347d37b5b0de2db18e826f66696c86d54bf6";REVIEW="e42d31706fe98fb089f148d563b010b4312e53e9b33ba1c33faafe7f63379009"
def h(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def blob(path:str)->bytes:return subprocess.run(["git","show",f"{TARGET}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
def validate(d:Mapping[str,Any],text:str)->list[str]:
 f=[];identity={k:v for k,v in d.items() if k not in {"review_content_hash","generated_utc"}}
 if d.get("review_content_hash")!=REVIEW or h(identity)!=REVIEW:f.append("review identity changed")
 if d.get("target_commit")!=TARGET or d.get("target_base_commit")!=BASE or d.get("protocol_content_hash")!="be205bf40dcab624667b97e43bc158ea2473fe15de2ce9846a6bb198575fa43b":f.append("target binding changed")
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
 if f:print("u10_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u10_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0");return 0
if __name__=="__main__":raise SystemExit(main())
