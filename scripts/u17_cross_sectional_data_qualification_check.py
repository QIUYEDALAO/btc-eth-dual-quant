#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u17_cross_sectional_data_qualification import CONFIG, canonical_hash

RESULT = ROOT / "reports/m1/evidence/u17_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "936e7ac34d3da3db729a8276813eae05b651b800b62dcece037008d189872fd5"
EXPECTED_RESULT = "434d8a58a19306e9ff340da3b8df0c85fe15848c2686ed15491dee05ac64af91"


def validate(config: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    if config.get("content_hash") != EXPECTED_CONTRACT or canonical_hash(config) != EXPECTED_CONTRACT:
        findings.append("contract identity changed")
    identity = {key: value for key, value in result.items() if key != "qualification_content_hash"}
    if result.get("qualification_content_hash") != EXPECTED_RESULT or identity_hash(identity) != EXPECTED_RESULT:
        findings.append("result identity changed")
    counts = result.get("counts", {})
    if result.get("status") != "failed_pre_result_sample_ceiling" or counts.get("archive_count") != 27736 or counts.get("manifests_exact") != 19:
        findings.append("source qualification changed")
    if counts.get("eligible_structural_decisions") != 13 or counts.get("maximum_independent_theoretical_28d_episodes") != 3:
        findings.append("structural ceiling changed")
    failed_gate = result.get("failed_gate", {})
    if failed_gate != {"name": "minimum_theoretical_eligible_28d_episodes", "required": 50, "observed": 3}:
        findings.append("failed Gate changed")
    for key in ("source_orders", "same_reader_orders"):
        rows = result.get(key, [])
        if len(rows) != 3 or len({row.get("content_identity_hash") for row in rows}) != 1:
            findings.append(f"{key} changed")
    benchmark = result.get("complexity_benchmark", {})
    passes = benchmark.get("passes", [])
    if benchmark.get("status") != "pass" or len(passes) != 3 or benchmark.get("market_outcomes_read") != 0 or len({row.get("output_hash") for row in passes}) != 1:
        findings.append("complexity identity changed")
    if any(row.get("fixture_rows") != 1000000 or float(row.get("elapsed_seconds", 31)) > 30 or float(row.get("peak_rss_mib", 1025)) > 1024 for row in passes):
        findings.append("complexity Gate changed")
    isolation = result.get("isolation", {})
    zeros = ("oos_ohlcv_values_decoded", "quote_volume_fields_decoded_during_preflight", "price_fields_decoded_during_preflight", "liquidity_rank_rows_generated", "candidate_rows_generated", "event_rows_generated", "path_rows_generated", "return_rows_generated")
    if isolation.get("oos_opened") is not False or any(isolation.get(key) != 0 for key in zeros):
        findings.append("isolation changed")
    if any(result.get("authorizations", {}).values()) or result.get("decision") != {"candidate_closed": True, "paper_observation_authorized": False, "second_qualification_attempt_for_admission_authorized": False}:
        findings.append("closure changed")
    return findings


def main() -> int:
    findings = validate(load_json(CONFIG), load_json(RESULT))
    if findings:
        print("u17_cross_sectional_data_qualification_check FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"u17_cross_sectional_data_qualification_check PASS failed_pre_result hash={EXPECTED_RESULT} ceiling=3/50")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
