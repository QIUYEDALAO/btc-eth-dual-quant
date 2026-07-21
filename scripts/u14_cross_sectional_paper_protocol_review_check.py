#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/expert/evidence/u14_cross_sectional_paper_protocol_review_v1.json"
REPORT = ROOT / "reports/expert/U14_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
TARGET = "dd8eb34aa0cae8455ba15163831b992820461ebf"
BASE = "9ea3a7cabbd06bc8209678ef3e35bb5402a74a74"
PROTOCOL = "a0b606d3996f0edd13790178f370bed92e3a6d06bf2298eea78ba8a46907ac57"
REVIEW = "873f4435909ebc550f898972714e43ffc553b386700068ad65cecc7bef2fbbc2"


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
    protocol = json.loads(target_blob("config/u14_cross_sectional_paper_protocol_v1.json"))
    protocol_identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != PROTOCOL or canonical_hash(protocol_identity) != PROTOCOL:
        failures.append("target protocol identity changed")
    auction = protocol.get("completed_auction_contract", {})
    selling = protocol.get("common_selling_pressure", {})
    event = protocol.get("event_identity", {})
    complexity = protocol.get("pre_result_complexity_benchmark", {})
    if auction.get("all_active_member_48_five_minute_rows_complete_required") is not True or auction.get("minimum_active_members") != 10:
        failures.append("completed auction contract changed")
    if selling.get("common_component_maximum") != "-0.0060" or selling.get("negative_breadth_integer_gate") != "negative_members_times_10_at_least_active_members_times_7":
        failures.append("common selling contract changed")
    if event.get("candidate_completed_close_to_open_log_return_maximum") != "0.0000" or event.get("absolute_positive_return_candidate_prohibited") is not True:
        failures.append("U-07 non-collapse constraint changed")
    expected_event = ("0.0180", "-0.0120", "0.80", "0.20")
    actual_event = (event.get("candidate_normalized_range_minimum"), event.get("candidate_downside_excursion_maximum"), event.get("candidate_close_location_minimum"), event.get("candidate_close_location_residual_minimum"))
    if actual_event != expected_event or event.get("representatives_per_decision_time") != 1:
        failures.append("event identity changed")
    if complexity.get("synthetic_fixture_rows") != 1000000 or complexity.get("benchmark_passes_required") != 3 or complexity.get("maximum_elapsed_seconds") != 30 or complexity.get("maximum_peak_rss_mib") != 1024 or complexity.get("same_event_and_path_code_path_required") is not True:
        failures.append("complexity benchmark changed")
    if len(document.get("dimensions", {})) != 15 or any(value != "pass" for value in document.get("dimensions", {}).values()):
        failures.append("review dimension failure")
    if document.get("verdict") != "approve" or document.get("remaining_critical_findings") != 0 or document.get("remaining_high_findings") != 0 or document.get("target_modified") is not False:
        failures.append("verdict changed")
    expected = {"data_qualification_complexity_and_preflight": True, "common_state_scan": False, "event_scan": False, "path_observation": False, "formal_returns": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
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
        print("u14_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u14_cross_sectional_paper_protocol_review_check PASS target={TARGET} review={REVIEW} approve 0/0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
