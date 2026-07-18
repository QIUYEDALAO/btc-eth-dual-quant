#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u13_cross_sectional_data_qualification import CONFIG, canonical_hash

RESULT = ROOT / "reports/m1/evidence/u13_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "e9b820855abbd5e5278d3f433ab3f06f7e17a73e792f04de924bed685a0e5ce7"
EXPECTED_RESULT = "5c4a61efc177415b1bd0a03697f4a3028f9ab8bed908adc12100bc03e9b90590"
EXPECTED_ORDER = "5dfc833dc7897f14a9cb691738c2e5fc4b7770254c36d3b1ac316d0cafc02af3"


def validate(config: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if config.get("content_hash") != EXPECTED_CONTRACT or canonical_hash(config) != EXPECTED_CONTRACT:
        failures.append("contract identity changed")
    body = {key: value for key, value in result.items() if key != "qualification_content_hash"}
    if result.get("qualification_content_hash") != EXPECTED_RESULT or identity_hash(body) != EXPECTED_RESULT:
        failures.append("result identity changed")
    counts = result.get("counts", {})
    if result.get("status") != "pass" or counts.get("archive_count") != 27736 or counts.get("manifests_exact") != 19:
        failures.append("qualification status/count changed")
    if counts.get("complete_active_member_1h_intervals") != 40383 or counts.get("eligible_structural_decision_hours") != 36716:
        failures.append("same-reader availability accounting changed")
    if counts.get("maximum_independent_theoretical_24h_episodes") != 1490 or counts.get("maximum_independent_theoretical_24h_episodes", 0) < 400:
        failures.append("sample ceiling changed or failed")
    source = result.get("source_orders", []); reader = result.get("same_reader_orders", [])
    if len(source) != 3 or len({row.get("content_identity_hash") for row in source}) != 1:
        failures.append("source traversal identity changed")
    if len(reader) != 3 or {row.get("content_identity_hash") for row in reader} != {EXPECTED_ORDER}:
        failures.append("same-reader traversal identity changed")
    isolation = result.get("isolation", {})
    forbidden = ("oos_ohlcv_values_decoded", "ohlcv_fields_decoded_during_preflight", "common_component_rows_generated", "candidate_rows_generated", "event_rows_generated", "path_rows_generated", "return_rows_generated")
    if isolation.get("oos_opened") is not False or any(isolation.get(key) != 0 for key in forbidden):
        failures.append("isolation changed")
    if [key for key, value in result.get("authorizations", {}).items() if value] != ["one_sealed_is_paper_observation"]:
        failures.append("authorization changed")
    return failures


def main() -> int:
    failures = validate(load_json(CONFIG), load_json(RESULT))
    if failures:
        print("u13_cross_sectional_data_qualification_check FAIL")
        for failure in failures: print(f"- {failure}")
        return 1
    print(f"u13_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=1490")
    return 0


if __name__ == "__main__": raise SystemExit(main())
