#!/usr/bin/env python3
"""Validate the independent exact-head review of the U-06 Paper protocol."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any, Mapping
ROOT=Path(__file__).resolve().parents[1]
REVIEW_PATH=ROOT/"reports/expert/evidence/u06_cross_sectional_paper_protocol_review_v1.json"
REPORT_PATH=ROOT/"reports/expert/U06_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
EXPECTED_TARGET="1bb59f1ac9d9e0fd5bacc8c55e572b9a1fbce8cd"; EXPECTED_BASE="175ffb82057e9bbdfae385f041ab02f959008f99"
EXPECTED_PROTOCOL_HASH="7b53860efa2a5c52d727f1d4d4694ddf39ff34517dfde6aaf4b6abe31f35f289"; EXPECTED_REVIEW_HASH="e4f0af0d817990d825081b7922b395dc3c76d05fc662e9c404fa82ce344e81b3"
EXPECTED_FILES={"config/u06_cross_sectional_paper_protocol_v1.json":"4a74ee0dfbc4a5f0fe8011424dff53cdffc2a020dcfcddae6512ece255f6f95a","reports/m1/U06_CROSS_SECTIONAL_PAPER_PROTOCOL.md":"db3624e886003c734ff64ab654e7cdb797cee368431b4b111799387e467dee01","scripts/u06_cross_sectional_paper_protocol_check.py":"5c6e9ef66060dd7da6c091e311a5fa18b887e2b2118bd32f8c9a02d18975295f","scripts/u06_cross_sectional_paper_protocol_validate.sh":"2c25d390c330356fbad4f9f7c462710469abddbba31ac0c143b5c8ff79340a1f","tests/test_u06_cross_sectional_paper_protocol.py":"8cdefe5ab8a91670f44fbc824e929d76f85f09ec203802cbc11be20999ec4100"}
EXPECTED_AUTH={"data_qualification":True,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
def load(p:Path)->dict[str,Any]: return json.loads(p.read_text())
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def git_bytes(c:str,p:str)->bytes:
 r=subprocess.run(["git","show",f"{c}:{p}"],cwd=ROOT,capture_output=True);
 if r.returncode: raise ValueError(f"target unavailable: {p}")
 return r.stdout
def validate(review:Mapping[str,Any],verify_git:bool=True)->list[str]:
 f=[]; identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}}
 if review.get("review_content_hash")!=EXPECTED_REVIEW_HASH or canonical_hash(identity)!=EXPECTED_REVIEW_HASH:f.append("review identity changed")
 t=review.get("target",{})
 if t.get("head_commit")!=EXPECTED_TARGET or t.get("base_commit")!=EXPECTED_BASE or t.get("protocol_content_hash")!=EXPECTED_PROTOCOL_HASH:f.append("exact target binding changed")
 if review.get("target_files")!=EXPECTED_FILES:f.append("target file bindings changed")
 dims=review.get("review_dimensions",[])
 if len(dims)!=13 or [x.get("id") for x in dims]!=[f"U06-PR-{i:02d}" for i in range(1,14)] or any(x.get("result")!="pass" for x in dims):f.append("review dimensions incomplete")
 if review.get("findings")!=[] or review.get("verdict")!="approve" or review.get("remaining_critical_findings")!=0 or review.get("remaining_high_findings")!=0:f.append("approve or zero-severity Gate changed")
 if review.get("target_modified_by_review") is not False or review.get("authorizations")!=EXPECTED_AUTH:f.append("target mutation or authorization expansion")
 if verify_git:
  parent=subprocess.run(["git","rev-parse",f"{EXPECTED_TARGET}^"],cwd=ROOT,text=True,capture_output=True)
  if parent.returncode or parent.stdout.strip()!=EXPECTED_BASE:f.append("target parent changed")
  for p,d in EXPECTED_FILES.items():
   try:a=hashlib.sha256(git_bytes(EXPECTED_TARGET,p)).hexdigest()
   except ValueError as e:f.append(str(e));continue
   if a!=d:f.append(f"target file drifted: {p}")
  try:protocol=json.loads(git_bytes(EXPECTED_TARGET,"config/u06_cross_sectional_paper_protocol_v1.json"))
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
  print("u06_cross_sectional_paper_protocol_review_check FAIL");[print(f"- {x}") for x in f];return 1
 print(f"u06_cross_sectional_paper_protocol_review_check PASS target={EXPECTED_TARGET} review={EXPECTED_REVIEW_HASH} approve 0/0");return 0
if __name__=="__main__":raise SystemExit(main())
