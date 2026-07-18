#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reports/expert/evidence/u19_cross_sectional_paper_protocol_review_v1.json"
EXPECTED = "d215e444595036412cc680b83cc0adf8449edbe6c283ac82b632c67e623f4a91"


def identity_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(review: Mapping[str, Any], verify_git: bool = False) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in review.items() if key not in {"review_content_hash", "generated_utc"}}
    target = review.get("target", {})
    if review.get("review_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED:
        findings.append("review identity changed")
    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0:
        findings.append("verdict changed")
    if target.get("head_sha") != "8b8b03f0869463c046668e28fbb22618383addf4" or target.get("parent_sha") != "0f0474cbf52092771cd992512bcdfdf0345702a8" or target.get("protocol_content_hash") != "8f50ee407a79f2787de53e79b1a4a6de27af89c9ca1c58b5409271039ffd40f9":
        findings.append("target binding changed")
    if len(review.get("review_dimensions", {})) != 16 or any(value != "pass" for value in review.get("review_dimensions", {}).values()):
        findings.append("dimensions changed")
    expected = {"data_qualification_complexity_and_preflight": True, "return_residual_volatility_scan": False, "event_scan": False, "path_observation": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if review.get("authorization_after_review") != expected:
        findings.append("authorization changed")
    if verify_git:
        for path, wanted in target.get("files", {}).items():
            try:
                data = subprocess.run(["git", "show", f"{target['head_sha']}:{path}"], cwd=ROOT, check=True, capture_output=True).stdout
            except Exception:
                findings.append(f"target unavailable: {path}")
                continue
            if hashlib.sha256(data).hexdigest() != wanted:
                findings.append(f"target blob changed: {path}")
    return findings


def main() -> int:
    findings = validate(json.loads(REVIEW.read_text()), True)
    if findings:
        print("u19_cross_sectional_paper_protocol_review_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u19_cross_sectional_paper_protocol_review_check PASS hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
