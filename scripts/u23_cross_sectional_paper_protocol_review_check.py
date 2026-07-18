#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reports/expert/evidence/u23_cross_sectional_paper_protocol_review_v1.json"
EXPECTED = "f2a8a5fdf770419bcc6f29abda3539d251b9e6e0f1dc97d5a4e824ab4f37c4a4"

def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate(review: Mapping[str, Any], verify_git: bool = False) -> list[str]:
    findings=[]; identity={k:v for k,v in review.items() if k not in {"review_content_hash","generated_utc"}}; target=review.get("target",{})
    if review.get("review_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED: findings.append("review identity changed")
    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0: findings.append("verdict changed")
    if target.get("head_sha") != "1d0b21282b1e499fdef0d9cab88e7a918a5d5913" or target.get("parent_sha") != "989bb94a6ac03af640c5e5a998ff7b7b6a068485" or target.get("protocol_content_hash") != "52807bd0e2c0bd2276c88e1d919a7e4a375c480f51fe479f0934d8c0063e5611" or target.get("synthetic_feasibility_content_hash") != "6010529c89627e8607919272af3c85c7dd5c3fdd4e48f549b8fe055e3245637e": findings.append("target binding changed")
    if len(target.get("files",{})) != 9 or len(review.get("review_dimensions",{})) != 16 or any(v != "pass" for v in review.get("review_dimensions",{}).values()): findings.append("dimensions changed")
    expected={"data_qualification_and_preflight":True,"ohlc_range_return_scan":False,"event_scan":False,"path_observation":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
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
        print("u23_cross_sectional_paper_protocol_review_check FAIL"); [print(f"- {x}") for x in findings]; return 1
    print(f"u23_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}"); return 0
if __name__=="__main__": raise SystemExit(main())
