#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u18_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED = "213c303dc81f23f0f8bb0d37c1f114636ca0cbd76c0bae1f3c432a5b2cf9c3cd"
EXPECTED_HASHES = {
    "accounting": "0bc54d43a52976f45e97a78463f56e62cc934bc85282b359d493cfcd8b309dd1",
    "episodes": "8dbc8a1dcd6b4c06f3a5c5c863f32a695f3837bc090973c4434457057d31a7a6",
    "events": "73100a0672483b472692ee13395b11f24e16679a4f9040c0322c2557f95bbf32",
    "paths": "2bed2d724fda52b383e52a1cd561b36cd54c765adc62653c4337eceebc45efdc",
}


def validate(run: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in run.items() if key != "run_content_hash"}
    if run.get("run_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED:
        failures.append("run identity changed")
    if run.get("status") != "failed_feasibility" or run.get("oos_opened") is not False or run.get("second_run_executed") is not False or run.get("formal_returns_computed") is not False:
        failures.append("status or isolation changed")
    orders = run.get("orders", [])
    if len(orders) != 3 or len({row.get("content_identity_hash") for row in orders}) != 1:
        failures.append("order identity changed")
    if any(row.get("manifest_hashes") != EXPECTED_HASHES for row in orders):
        failures.append("manifest hashes changed")
    metrics = run.get("metrics", {})
    if (
        metrics.get("complete_is_independent_episodes") != 157
        or metrics.get("median_24h_relative_downside_tail_risk_premium") != "-0.0012453014163554798489821906695580157498865088123"
        or metrics.get("median_24h_candidate_absolute_close_displacement") != "-0.00337837837837837837837837837837837837837837837838"
        or metrics.get("fraction_complete_episodes_with_positive_24h_relative_downside_tail_risk_premium") != "0.4777070063694267515923566879"
    ):
        failures.append("metrics changed")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    expected_failed = {
        "median_24h_relative_downside_tail_risk_premium",
        "median_24h_candidate_absolute_close_displacement",
        "fraction_positive_24h_relative_downside_tail_risk_premium",
    }
    if failed != expected_failed:
        failures.append("failed Gates changed")
    if any(run.get("authorizations", {}).values()):
        failures.append("downstream authorization changed")
    for name, expected_hash in EXPECTED_HASHES.items():
        document = load_json(EVIDENCE / f"{name}.json")
        if document.get("content_hash") != expected_hash or identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != expected_hash:
            failures.append(f"{name} evidence changed")
    return failures


def main() -> int:
    failures = validate(load_json(RUN))
    if failures:
        print("u18_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u18_cross_sectional_paper_observation_check PASS failed_feasibility hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
