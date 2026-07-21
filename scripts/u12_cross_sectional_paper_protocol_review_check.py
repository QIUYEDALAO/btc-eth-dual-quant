#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/expert/evidence/u12_cross_sectional_paper_protocol_review_v1.json"
REPORT = ROOT / "reports/expert/U12_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
TARGET = "11caf6f5160bfd03a127b6fc3565ad0b84c43d82"
BASE = "2167029546bec5fc028c9fc8262db3a27ebf1d40"
PROTOCOL = "a8cfc0b74e82bdf455bae5dda7a620bc5c0c53f1022d39494800f1053dd80b8a"
REVIEW = "81262bf19b2c32d7cfb37a6d42106ec7bc21bd674a4d0d106b3e0ccfd58b8813"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def target_blob(path: str) -> bytes:
    return subprocess.run(["git", "show", f"{TARGET}:{path}"], cwd=ROOT, check=True, capture_output=True).stdout


def validate(document: Mapping[str, Any], report: str) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"review_content_hash", "generated_utc"}}
    if document.get("review_content_hash") != REVIEW or canonical_hash(identity) != REVIEW:
        failures.append("review identity changed")
    if document.get("target_commit") != TARGET or document.get("target_base_commit") != BASE or document.get("protocol_content_hash") != PROTOCOL:
        failures.append("target binding changed")
    for path, expected in document.get("target_file_sha256", {}).items():
        if hashlib.sha256(target_blob(path)).hexdigest() != expected:
            failures.append(f"target blob drift: {path}")
    protocol = json.loads(target_blob("config/u12_cross_sectional_paper_protocol_v1.json"))
    protocol_identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != PROTOCOL or canonical_hash(protocol_identity) != PROTOCOL:
        failures.append("target protocol identity changed")
    if protocol.get("calendar_state_contract", {}).get("family") != "utc_weekday_of_target_day" or protocol.get("estimator_contract", {}).get("prior_same_weekday_opportunities") != 52:
        failures.append("calendar or estimator review changed")
    preflight = protocol.get("implementation_data_scope_preflight", {})
    if preflight.get("required_before_any_event_or_path_scan") is not True or preflight.get("verifies_previous_boundary_close_for_every_requested_daily_interval_including_month_transitions") is not True or preflight.get("common_component_event_path_or_return_rows_generated") != 0:
        failures.append("preflight review changed")
    if len(document.get("dimensions", {})) != 14 or any(value != "pass" for value in document.get("dimensions", {}).values()):
        failures.append("review dimension failure")
    if document.get("verdict") != "approve" or document.get("remaining_critical_findings") != 0 or document.get("remaining_high_findings") != 0 or document.get("target_modified") is not False:
        failures.append("verdict changed")
    expected = {"data_qualification_and_preflight": True, "common_component_scan": False, "event_scan": False, "path_observation": False, "formal_returns": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
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
        print("u12_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
