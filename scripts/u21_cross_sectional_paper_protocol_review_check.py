#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reports/expert/evidence/u21_cross_sectional_paper_protocol_review_v1.json"
EXPECTED = "809dcdf63d096d8b2742c13004c83151780a7e8078dcde85da7cc65946a355ff"

def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate(review: Mapping[str, Any], verify_git: bool = False) -> list[str]:
    findings=[]; identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}}; target=review.get("target",{})
    if review.get("review_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED: findings.append("review identity changed")
    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0: findings.append("verdict changed")
    if target.get("head_sha") != "d76714752825f9018427e9cd55cdd69802928d42" or target.get("parent_sha") != "78e260c24ecc068181131d8e0898844e0e71f941" or target.get("protocol_content_hash") != "b8cad855459c0cb10cff0b1abb927c9bac84b9e54686cc2ea7277aac5f73551e": findings.append("target binding changed")
    if len(review.get("review_dimensions",{})) != 16 or any(v != "pass" for v in review.get("review_dimensions",{}).values()): findings.append("dimensions changed")
    expected={"data_qualification_complexity_and_preflight":True,"return_common_adjustment_cokurtosis_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
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
        print("u21_cross_sectional_paper_protocol_review_check FAIL"); [print(f"- {x}") for x in findings]; return 1
    print(f"u21_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}"); return 0
if __name__=="__main__": raise SystemExit(main())
