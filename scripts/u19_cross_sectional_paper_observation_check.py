#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u19_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED = "38daffb0834c28a769108c74f256b601f08667c7076d107bc97f48925b63f3d4"
EXPECTED_HASHES = {
    "accounting": "f4e7f653dbc455f44db517f73ba690730ce05909ee3d99b5ab0d3929d2da2117",
    "episodes": "73ff479bc9a24dcc2b6a2be33c7bc82d2998a24aaab7b956cb6719af7bd75313",
    "events": "daa9895a5d2e823ea2137a46813832372e4d1fa86ca333baf8d28b5276b80dd9",
    "paths": "f7e36c6ae1ae25f804301f65fbc59710715c2c2f88f04c3e98b8ddc0e80d0346",
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
        metrics.get("complete_is_independent_episodes") != 54
        or metrics.get("median_24h_relative_volatility_of_volatility_risk_premium") != "-0.005662930782679990644577366795"
        or metrics.get("median_24h_candidate_absolute_close_displacement") != "-0.007465514604395529545951321365"
        or metrics.get("fraction_complete_episodes_with_positive_24h_relative_volatility_of_volatility_risk_premium") != "0.3703703703703703703703703704"
    ):
        failures.append("metrics changed")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    expected_failed = {
        "complete_is_independent_episodes",
        "projected_full_independent_episodes",
        "projected_sealed_oos_independent_episodes",
        "years_with_twelve_complete_episodes",
        "median_24h_relative_volatility_of_volatility_risk_premium",
        "median_24h_candidate_absolute_close_displacement",
        "fraction_positive_24h_relative_volatility_of_volatility_risk_premium",
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
        print("u19_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u19_cross_sectional_paper_observation_check PASS failed_feasibility hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
