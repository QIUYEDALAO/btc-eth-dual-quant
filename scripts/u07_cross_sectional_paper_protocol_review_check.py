#!/usr/bin/env python3
"""Validate the independent exact-head review of the U-07 Paper protocol."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any, Mapping
ROOT=Path(__file__).resolve().parents[1]
REVIEW_PATH=ROOT/"reports/expert/evidence/u07_cross_sectional_paper_protocol_review_v1.json"
REPORT_PATH=ROOT/"reports/expert/U07_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
EXPECTED_TARGET="3aed4c337ff984b3e07ad9a4c7cda898425b3791"; EXPECTED_BASE="f282f45229dbab3fd20767b2097a07a481e50d09"
EXPECTED_PROTOCOL_HASH="d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195"; EXPECTED_REVIEW_HASH="fa9d90f7ebb30d4072662a9d8a733760a703eb04031abda23f3b6b0846bc70b6"
EXPECTED_FILES={"config/u07_cross_sectional_paper_protocol_v1.json":"0bdf0a8dbf8e6c9d36bfa428b4f95557b62b75c4818a55c0e9aac72d1c60abb9","reports/m1/U07_CROSS_SECTIONAL_PAPER_PROTOCOL.md":"a32e2aa8b63987035a694bdbaf31e0d8a77a57021c6fa9fdbbef8f2bbc130878","scripts/u07_cross_sectional_paper_protocol_check.py":"7e6d9ca705a02443040c6230f8d5db40de720f37e071f02a5e7f300081a51628","scripts/u07_cross_sectional_paper_protocol_validate.sh":"d23839f3c3d30ada42ad7fa074470a7edd11d976b28f94050cd57337254e70cf","tests/test_u07_cross_sectional_paper_protocol.py":"933764a6194272b361c035ca0557069a818e876353e1014a61c0a2a7c2cfae11"}
EXPECTED_AUTH={"data_qualification":True,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
def load(p:Path)->dict[str,Any]: return json.loads(p.read_text())
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def git_bytes(c:str,p:str)->bytes:
 r=subprocess.run(["git","show",f"{c}:{p}"],cwd=ROOT,capture_output=True)
 if r.returncode: raise ValueError(f"target unavailable: {p}")
 return r.stdout
def validate(review:Mapping[str,Any],verify_git:bool=True)->list[str]:
 f=[]; identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}}
 if review.get("review_content_hash")!=EXPECTED_REVIEW_HASH or canonical_hash(identity)!=EXPECTED_REVIEW_HASH:f.append("review identity changed")
 t=review.get("target",{})
 if t.get("head_commit")!=EXPECTED_TARGET or t.get("base_commit")!=EXPECTED_BASE or t.get("protocol_content_hash")!=EXPECTED_PROTOCOL_HASH:f.append("exact target binding changed")
 if review.get("target_files")!=EXPECTED_FILES:f.append("target file bindings changed")
 dims=review.get("review_dimensions",[])
 if len(dims)!=13 or [x.get("id") for x in dims]!=[f"U07-PR-{i:02d}" for i in range(1,14)] or any(x.get("result")!="pass" for x in dims):f.append("review dimensions incomplete")
 if review.get("findings")!=[] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:f.append("approve or zero-severity Gate changed")
 if review.get("target_modified_by_review") is not False or review.get("authorizations")!=EXPECTED_AUTH:f.append("target mutation or authorization expansion")
 if verify_git:
  parent=subprocess.run(["git","rev-parse",f"{EXPECTED_TARGET}^"],cwd=ROOT,text=True,capture_output=True)
  if parent.returncode or parent.stdout.strip()!=EXPECTED_BASE:f.append("target parent changed")
  for p,d in EXPECTED_FILES.items():
   try:a=hashlib.sha256(git_bytes(EXPECTED_TARGET,p)).hexdigest()
   except ValueError as e:f.append(str(e));continue
   if a!=d:f.append(f"target file drifted: {p}")
  try:protocol=json.loads(git_bytes(EXPECTED_TARGET,"config/u07_cross_sectional_paper_protocol_v1.json"))
  except Exception as e:f.append(f"protocol unavailable: {e}")
  else:
   if protocol.get("content_hash")!=EXPECTED_PROTOCOL_HASH or protocol.get("scope",{}).get("oos_opened") is not False:f.append("protocol hash or OOS seal changed")
   if {k for k,v in protocol.get("authorizations",{}).items() if v}!={"paper_protocol_frozen","exact_head_independent_review"}:f.append("target authorization expanded")
 return f
def validate_report()->list[str]:
 text=REPORT_PATH.read_text(); markers=(f"Target: `{EXPECTED_TARGET}`","Verdict: `approve`","Remaining critical/high findings: `0 / 0`","Target modified by review: no","authorizes only a separate frozen-source data-qualification")
 return [f"report marker missing: {m}" for m in markers if m not in text]
def main()->int:
 f=validate(load(REVIEW_PATH))+validate_report()
 if f:
  print("u07_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u07_cross_sectional_paper_protocol_review_check PASS target={EXPECTED_TARGET} review={EXPECTED_REVIEW_HASH} approve 0/0");return 0
if __name__=="__main__":raise SystemExit(main())
