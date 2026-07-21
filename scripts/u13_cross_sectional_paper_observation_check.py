#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u13_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED_RUN = "b94ffc31598899186a005ea1eaba28b274faac2ad9f3fae034e9f71d5868eb3d"
EXPECTED_ORDER = "54ebf66033d72a68e1a601875268d444923348dddfdf74a1dd3dd30a2d9fd460"
EXPECTED_MANIFESTS = {
    "accounting": "a0e7d85d78cd227f72b3c3c41b5fb2735048a3220b677a820c749a8ed6085214",
    "episodes": "3923c7392afb716abc8fb06f0b99be109612795bfb6f08056a7358d832d21d8c",
    "events": "4342bfb35375fac5508dfdf2fdeac4bb2fa3586c32357538d096144640ece709",
    "paths": "419c49927b40bd5622f558d7d0fbb8f3e7c6533b74b3b45bf8f8c947276af266",
}


def validate(run: Mapping[str, Any], manifests: Mapping[str, Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    body = {key: value for key, value in run.items() if key != "run_content_hash"}
    if run.get("run_content_hash") != EXPECTED_RUN or identity_hash(body) != EXPECTED_RUN:
        failures.append("run identity changed")
    if run.get("status") != "failed_feasibility" or run.get("protocol_content_hash") != "1cf6dade6e75900278ba5aeee30018d3f0ff93d83d982e212d58033800993288" or run.get("qualification_content_hash") != "5c4a61efc177415b1bd0a03697f4a3028f9ab8bed908adc12100bc03e9b90590":
        failures.append("status or authority changed")
    orders = run.get("orders", [])
    if len(orders) != 3 or {row.get("content_identity_hash") for row in orders} != {EXPECTED_ORDER} or any(row.get("manifest_hashes") != EXPECTED_MANIFESTS for row in orders):
        failures.append("three-order identity changed")
    for name, expected in EXPECTED_MANIFESTS.items():
        document = manifests.get(name, {})
        if document.get("content_hash") != expected or identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != expected:
            failures.append(f"{name} manifest changed")
    metrics = run.get("metrics", {})
    expected_metrics = {"complete_is_independent_episodes": 1, "distinct_event_symbols": 1, "distinct_event_months": 1, "median_24h_relative_lagged_diffusion": "-0.02882081340015003472958888745843479988669649607176", "median_24h_candidate_absolute_close_displacement": "-0.07154272528123611360145938740031027574002323170114", "fraction_complete_episodes_with_positive_24h_relative_lagged_diffusion": "0"}
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("frozen metrics changed")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    required_failed = {"complete_is_independent_episodes", "projected_full_independent_episodes", "projected_sealed_oos_independent_episodes", "years_with_twelve_complete_episodes", "maximum_single_year_episode_share", "maximum_single_symbol_episode_share", "distinct_event_symbols", "distinct_event_months", "median_24h_relative_lagged_diffusion", "median_24h_candidate_absolute_close_displacement", "fraction_positive_24h_relative_lagged_diffusion"}
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
        print("u13_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u13_cross_sectional_paper_observation_check PASS failed_feasibility run={EXPECTED_RUN} episodes=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
