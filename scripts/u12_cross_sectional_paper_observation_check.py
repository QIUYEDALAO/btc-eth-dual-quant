#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u12_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED_RUN = "b42a539c555e37b8b3871910bf5fc21397db3ea01044dee3bbfe3bf7902e7995"
EXPECTED_ORDER = "db4b8e740250a74dad348aa1b5b789cd03606e648b3c36456157fbfca72ea124"
EXPECTED_MANIFESTS = {
    "accounting": "41b9c9a51f635c8fc4c5f0b0b04b5acb9abaf7abf85eec8f7abe724b8efab4fc",
    "episodes": "016f99642a90c3e512f544113ab9b6384c9f8c7e98e5bae69d2e0d7d29f8b685",
    "events": "d38aa24e3c73bdc83ff68ce844a7123f5210eca190212722b034b325bc2a8b14",
    "paths": "4c1cb6c0fb0a04f20e231e7b7688fae0f7b92d8ff1452ce5f318f2252c47302e",
}


def validate(run: Mapping[str, Any], manifests: Mapping[str, Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    body = {key: value for key, value in run.items() if key != "run_content_hash"}
    if run.get("run_content_hash") != EXPECTED_RUN or identity_hash(body) != EXPECTED_RUN:
        failures.append("run identity changed")
    if run.get("status") != "failed_feasibility" or run.get("protocol_content_hash") != "a8cfc0b74e82bdf455bae5dda7a620bc5c0c53f1022d39494800f1053dd80b8a" or run.get("qualification_content_hash") != "c9a5b5480081ef0583604910ce2550029086b9c9f7bd0a147c723006859a0510":
        failures.append("status or authority changed")
    orders = run.get("orders", [])
    if len(orders) != 3 or {row.get("content_identity_hash") for row in orders} != {EXPECTED_ORDER} or any(row.get("manifest_hashes") != EXPECTED_MANIFESTS for row in orders):
        failures.append("three-order identity changed")
    for name, expected in EXPECTED_MANIFESTS.items():
        document = manifests.get(name, {})
        if document.get("content_hash") != expected or identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != expected:
            failures.append(f"{name} manifest changed")
    metrics = run.get("metrics", {})
    expected_metrics = {"complete_is_independent_episodes": 88, "distinct_event_symbols": 7, "distinct_event_months": 12, "median_24h_relative_calendar_flow_persistence": "0.001177628752703688706929802888", "median_24h_candidate_absolute_close_displacement": "0.003620753393619485368336276454", "fraction_complete_episodes_with_positive_24h_relative_calendar_flow_persistence": "0.5227272727272727272727272727"}
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("frozen metrics changed")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    required_failed = {"complete_is_independent_episodes", "years_with_twelve_complete_episodes", "maximum_single_year_episode_share", "maximum_single_symbol_episode_share", "distinct_event_symbols", "distinct_event_months", "median_24h_relative_calendar_flow_persistence", "median_24h_candidate_absolute_close_displacement", "fraction_positive_24h_relative_calendar_flow_persistence"}
    if failed != required_failed:
        failures.append("failed Gate set changed")
    if run.get("oos_opened") is not False or run.get("oos_rows_decoded") != 0 or run.get("formal_returns_computed") is not False or run.get("second_run_executed") is not False:
        failures.append("isolation changed")
    if any(run.get("authorizations", {}).values()):
        failures.append("failed candidate cannot authorize downstream work")
    return failures


def main() -> int:
    manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in EXPECTED_MANIFESTS}
    failures = validate(load_json(RUN), manifests)
    if failures:
        print("u12_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_cross_sectional_paper_observation_check PASS failed_feasibility run={EXPECTED_RUN} episodes=88")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
