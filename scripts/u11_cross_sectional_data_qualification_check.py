#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u11_cross_sectional_data_qualification import CONFIG, canonical_hash, verify_ceiling

RESULT = ROOT / "reports/m1/evidence/u11_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "b376f6c8250a6810a32dd2ceca5cca94431f7e5cf0e1249ded364700940ccfcc"
EXPECTED_RESULT = "b0476b5e8cdd60769f49312e682329376daf5fa6f4163358d9bd4c84f0ca05b6"


def validate(config: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if config.get("content_hash") != EXPECTED_CONTRACT or canonical_hash(config) != EXPECTED_CONTRACT:
        failures.append("contract identity changed")
    if result.get("qualification_content_hash") != EXPECTED_RESULT or identity_hash({key: value for key, value in result.items() if key != "qualification_content_hash"}) != EXPECTED_RESULT:
        failures.append("result identity changed")
    if result.get("status") != "pass" or result.get("counts", {}).get("archive_count") != 27736 or result.get("counts", {}).get("manifests_exact") != 19:
        failures.append("qualification status/count changed")
    counts = result.get("counts", {})
    if counts.get("eligible_history_and_constant_path_decision_times") != 8690 or counts.get("maximum_independent_theoretical_episodes") != 473:
        failures.append("sample ceiling changed")
    orders = result.get("orders", [])
    if len(orders) != 3 or len({row.get("content_identity_hash") for row in orders}) != 1:
        failures.append("traversal identity changed")
    isolation = result.get("isolation", {})
    forbidden_counts = ("oos_ohlcv_values_decoded", "common_state_rows_generated", "capture_rows_generated", "candidate_rows_generated", "event_rows_generated", "path_rows_generated", "return_rows_generated")
    if isolation.get("oos_opened") is not False or any(isolation.get(key) != 0 for key in forbidden_counts):
        failures.append("isolation changed")
    if [key for key, value in result.get("authorizations", {}).items() if value] != ["one_sealed_is_paper_observation"]:
        failures.append("authorization changed")
    return failures


def main() -> int:
    config = load_json(CONFIG)
    result = load_json(RESULT)
    failures = validate(config, result)
    if failures:
        print("u11_cross_sectional_data_qualification_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u11_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=473")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
