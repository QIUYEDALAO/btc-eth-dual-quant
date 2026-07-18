#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u14_cross_sectional_data_qualification import CONFIG, canonical_hash

RESULT = ROOT / "reports/m1/evidence/u14_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "bea82ceabcab8ff22f8c5e0d8beab636886ab42e776bfe93be382e0719b45951"
EXPECTED_RESULT = "4db5eb7938cbf7f8063a00164fa6986d53629968ea0a8a4516de01e3a859dec5"


def validate(config: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if config.get("content_hash") != EXPECTED_CONTRACT or canonical_hash(config) != EXPECTED_CONTRACT:
        failures.append("contract identity changed")
    result_identity = {key: value for key, value in result.items() if key != "qualification_content_hash"}
    if result.get("qualification_content_hash") != EXPECTED_RESULT or identity_hash(result_identity) != EXPECTED_RESULT:
        failures.append("qualification identity changed")
    counts = result.get("counts", {})
    if result.get("status") != "pass" or counts.get("archive_count") != 27736 or counts.get("manifests_exact") != 19:
        failures.append("source qualification changed")
    if counts.get("complete_active_member_4h_auctions") != 10094 or counts.get("eligible_structural_decision_auctions") != 9690 or counts.get("maximum_independent_theoretical_24h_episodes") != 1405:
        failures.append("structural preflight or ceiling changed")
    for key in ("source_orders", "same_reader_orders"):
        orders = result.get(key, [])
        if len(orders) != 3 or len({row.get("content_identity_hash") for row in orders}) != 1:
            failures.append(f"{key} identity changed")
    benchmark = result.get("complexity_benchmark", {})
    passes = benchmark.get("passes", [])
    if benchmark.get("status") != "pass" or len(passes) != 3 or benchmark.get("market_outcomes_read") != 0 or benchmark.get("linear_streaming_no_decision_history_nested_scan") is not True:
        failures.append("complexity benchmark status changed")
    if any(row.get("fixture_rows") != 1000000 or float(row.get("elapsed_seconds", 31)) > 30 or float(row.get("peak_rss_mib", 1025)) > 1024 for row in passes):
        failures.append("complexity resource Gate changed")
    if len({row.get("output_hash") for row in passes}) != 1:
        failures.append("complexity deterministic output changed")
    isolation = result.get("isolation", {})
    forbidden = ("oos_ohlcv_values_decoded", "ohlcv_fields_decoded_during_preflight", "common_state_rows_generated", "candidate_rows_generated", "event_rows_generated", "path_rows_generated", "return_rows_generated")
    if isolation.get("oos_opened") is not False or any(isolation.get(key) != 0 for key in forbidden):
        failures.append("result isolation changed")
    if [key for key, value in result.get("authorizations", {}).items() if value] != ["one_sealed_is_paper_observation"]:
        failures.append("authorization changed")
    if result.get("network_accessed") is not False or result.get("production_evidence_mutated") is not False:
        failures.append("execution scope changed")
    return failures


def main() -> int:
    failures = validate(load_json(CONFIG), load_json(RESULT))
    if failures:
        print("u14_cross_sectional_data_qualification_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u14_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=1405 complexity=3/3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
