#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reports/expert/evidence/u22_cross_sectional_paper_protocol_review_v1.json"
EXPECTED = "e2a920c29105a32764016d478d22efa0d234a2fc5362ce5cae17f4671218cd57"

def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate(review: Mapping[str, Any], verify_git: bool = False) -> list[str]:
    findings=[]; identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}}; target=review.get("target",{})
    if review.get("review_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED: findings.append("review identity changed")
    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0: findings.append("verdict changed")
    if target.get("head_sha") != "d4f254f876dfeab73494c79a48e90c86dfd0ee16" or target.get("parent_sha") != "df307b268dee177398452b79937a08a498e970ec" or target.get("protocol_content_hash") != "0fdc7eb264e5f9a24dbcb746bbee6af0b1af2218cc101d6674099769f5d1b4fa" or target.get("synthetic_feasibility_content_hash") != "4476d5b5cc38b23c3f031b2438e77224a8da3c80ee011dba719cf43b76e6940b": findings.append("target binding changed")
    if len(target.get("files",{})) != 9 or len(review.get("review_dimensions",{})) != 16 or any(v != "pass" for v in review.get("review_dimensions",{}).values()): findings.append("dimensions changed")
    expected={"data_qualification_and_preflight":True,"return_dispersion_leader_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if review.get("authorization_after_review") != expected: findings.append("authorization changed")
    if verify_git:
        for path,wanted in target.get("files",{}).items():
            try: data=subprocess.run(["git","show",f"{target['head_sha']}:{path}"],cwd=ROOT,check=True,capture_output=True).stdout
            except Exception: findings.append(f"target unavailable: {path}"); continue
            if hashlib.sha256(data).hexdigest()!=wanted: findings.append(f"target blob changed: {path}")
    return findings

def main()->int:
    findings=validate(json.loads(REVIEW.read_text()),True)
    if findings:
        print("u22_cross_sectional_paper_protocol_review_check FAIL"); [print(f"- {x}") for x in findings]; return 1
    print(f"u22_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}"); return 0
if __name__=="__main__": raise SystemExit(main())
