#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json
from scripts.u18_cross_sectional_data_qualification import CONFIG, canonical_hash

RESULT = ROOT / "reports/m1/evidence/u18_cross_sectional_data_qualification_v1.json"
EXPECTED_CONTRACT = "9da995a6bb271147aa31a0fa81bf582bfa442e4a5d67bf59ca2753e209828338"
EXPECTED_RESULT = "088ebed218ce7960621ebeda539ec78c5aeebbef5b98f608a4f044f78e3dc6e0"


def validate(config: Mapping[str, Any], result: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if config.get("content_hash") != EXPECTED_CONTRACT or canonical_hash(config) != EXPECTED_CONTRACT:
        failures.append("contract identity changed")
    identity = {key: value for key, value in result.items() if key != "qualification_content_hash"}
    if result.get("qualification_content_hash") != EXPECTED_RESULT or identity_hash(identity) != EXPECTED_RESULT:
        failures.append("result identity changed")
    counts = result.get("counts", {})
    if result.get("status") != "pass" or counts.get("archive_count") != 27736 or counts.get("manifests_exact") != 19:
        failures.append("source qualification changed")
    if counts.get("eligible_structural_decisions") != 7278 or counts.get("maximum_independent_theoretical_24h_episodes") != 1054:
        failures.append("structural ceiling changed")
    if counts.get("maximum_independent_theoretical_24h_episodes", 0) < 400:
        failures.append("preflight Gate failed")
    for key in ("source_orders", "same_reader_orders"):
        rows = result.get(key, [])
        if len(rows) != 3 or len({row.get("content_identity_hash") for row in rows}) != 1:
            failures.append(f"{key} changed")
    benchmark = result.get("complexity_benchmark", {})
    passes = benchmark.get("passes", [])
    if benchmark.get("status") != "pass" or len(passes) != 3 or benchmark.get("market_outcomes_read") != 0 or len({row.get("output_hash") for row in passes}) != 1:
        failures.append("complexity identity changed")
    if any(row.get("fixture_rows") != 1000000 or float(row.get("elapsed_seconds", 31)) > 30 or float(row.get("peak_rss_mib", 1025)) > 1024 for row in passes):
        failures.append("complexity Gate changed")
    isolation = result.get("isolation", {})
    zero_fields = (
        "oos_ohlcv_values_decoded",
        "price_fields_decoded_during_preflight",
        "return_rows_generated",
        "residual_rows_generated",
        "tail_statistic_rows_generated",
        "candidate_rows_generated",
        "event_rows_generated",
        "path_rows_generated",
        "formal_return_rows_generated",
    )
    if isolation.get("oos_opened") is not False or any(isolation.get(key) != 0 for key in zero_fields):
        failures.append("isolation changed")
    if [key for key, value in result.get("authorizations", {}).items() if value] != ["one_sealed_is_paper_observation"]:
        failures.append("authorization changed")
    if result.get("network_accessed") is not False or result.get("production_evidence_mutated") is not False:
        failures.append("scope changed")
    return failures


def main() -> int:
    failures = validate(load_json(CONFIG), load_json(RESULT))
    if failures:
        print("u18_cross_sectional_data_qualification_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u18_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT} ceiling=1054 complexity=3/3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
