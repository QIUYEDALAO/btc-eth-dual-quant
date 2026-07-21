#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/expert/evidence/u13_cross_sectional_paper_protocol_review_v1.json"
REPORT = ROOT / "reports/expert/U13_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
TARGET = "6ef1024033aa9a86ef3c8f07558ba966270625a7"
BASE = "3c4aa926c2caaeb3adec8cf40bb2c9ff1a2436d5"
PROTOCOL = "1cf6dade6e75900278ba5aeee30018d3f0ff93d83d982e212d58033800993288"
REVIEW = "be552dad055234b0107810a7299656793ccea2a97f09a2cba22fa8ffc33ed5e0"


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
    protocol = json.loads(target_blob("config/u13_cross_sectional_paper_protocol_v1.json"))
    protocol_identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != PROTOCOL or canonical_hash(protocol_identity) != PROTOCOL:
        failures.append("target protocol identity changed")
    shock = protocol.get("common_shock_contract", {})
    lag = protocol.get("lag_estimator_contract", {})
    if shock.get("current_event_common_log_return_minimum") != "0.0060" or shock.get("minimum_active_members") != 10:
        failures.append("shock contract changed")
    if lag.get("lookback_completed_1h_observations") != 2160 or lag.get("historical_shock_followup_hours") != 4 or lag.get("historical_occurrence_must_finish_before_current_decision") is not True:
        failures.append("causal lag contract changed")
    preflight = protocol.get("implementation_data_scope_preflight", {})
    if preflight.get("required_before_any_common_shock_event_or_path_scan") is not True or preflight.get("verifies_2160h_history_and_4h_followup_input_availability_without_computing_returns") is not True or preflight.get("common_component_event_path_or_return_rows_generated") != 0:
        failures.append("preflight review changed")
    if len(document.get("dimensions", {})) != 15 or any(value != "pass" for value in document.get("dimensions", {}).values()):
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
        print("u13_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u13_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
