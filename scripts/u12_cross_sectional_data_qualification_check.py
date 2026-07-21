#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u12_cross_sectional_data_qualification import CONFIG, canonical_hash

RESULT = ROOT / "reports/m1/evidence/u12_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "a65aa923b256d83eeb79aa0afb4483525e33ad28eda9bc9adc823008fc324ed3"
EXPECTED_RESULT = "c9a5b5480081ef0583604910ce2550029086b9c9f7bd0a147c723006859a0510"
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
    if counts.get("complete_active_member_utc_days") != 1623 or counts.get("decisions_with_52_scheduled_same_weekday_cells_checked") != 1275 or counts.get("eligible_calendar_decision_days") != 1275:
        failures.append("same-reader availability accounting changed")
    if counts.get("maximum_independent_theoretical_24h_episodes") != 647 or counts.get("maximum_independent_theoretical_24h_episodes", 0) < 300:
        failures.append("sample ceiling changed or failed")
    source_orders = result.get("source_orders", [])
    if len(source_orders) != 3 or len({row.get("content_identity_hash") for row in source_orders}) != 1:
        failures.append("source traversal identity changed")
    reader_orders = result.get("same_reader_orders", [])
    if len(reader_orders) != 3 or {row.get("content_identity_hash") for row in reader_orders} != {EXPECTED_ORDER}:
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
        print("u12_cross_sectional_data_qualification_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=647")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
