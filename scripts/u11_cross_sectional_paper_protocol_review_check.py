#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/expert/evidence/u11_cross_sectional_paper_protocol_review_v1.json"
REPORT = ROOT / "reports/expert/U11_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
TARGET = "e7f621ec400fcb24833038f9201df5ffa5fa166a"
BASE = "aacd8624fbac49020cb9aedb4ac80c142d334aac"
REVIEW = "4e8fea7a28e19742baab225f9b0e8b98be16749792b9a68b9416c7d287a4d9fc"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def target_blob(path: str) -> bytes:
    return subprocess.run(["git", "show", f"{TARGET}:{path}"], cwd=ROOT, check=True, capture_output=True).stdout


def validate(document: Mapping[str, Any], report: str) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"review_content_hash", "generated_utc"}}
    if document.get("review_content_hash") != REVIEW or canonical_hash(identity) != REVIEW:
        failures.append("review identity changed")
    if document.get("target_commit") != TARGET or document.get("target_base_commit") != BASE or document.get("protocol_content_hash") != "3d78bbc86049bf7f0a2b3e0b30a25c6a747640043868d76132cf2cf2324d42dc":
        failures.append("target binding changed")
    for path, expected in document.get("target_file_sha256", {}).items():
        if hashlib.sha256(target_blob(path)).hexdigest() != expected:
            failures.append(f"target blob drift: {path}")
    if len(document.get("dimensions", {})) != 13 or any(value != "pass" for value in document.get("dimensions", {}).values()):
        failures.append("review dimension failure")
    if document.get("verdict") != "approve" or document.get("remaining_critical_findings") != 0 or document.get("remaining_high_findings") != 0 or document.get("target_modified") is not False:
        failures.append("verdict changed")
    expected = {"data_qualification": True, "common_state_scan": False, "event_scan": False, "path_observation": False, "formal_returns": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected:
        failures.append("review authorization changed")
    for marker in ("Verdict: `approve`", TARGET, "Remaining critical/high findings: `0 / 0`", "Target modified: `false`"):
        if marker not in report:
            failures.append(f"report marker missing: {marker}")
    return failures


def main() -> int:
    document = json.loads(EVIDENCE.read_text())
    failures = validate(document, REPORT.read_text())
    if failures:
        print("u11_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u11_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
