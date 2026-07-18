#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u20_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED = "587def88ac42d016a0ac5de97789164be6e6f1bf447b7a239eeed95137a9ede1"
EXPECTED_HASHES = {
    "accounting": "c20f2e160cc0269df25fb00837e7bff9fb8126440bd61b4473b881abc3593cc0",
    "episodes": "aa6e0b74cf7de2ea55ba2e4c2be78d1c8c5c77f4bd039856e6d897500b8b2dbb",
    "events": "f04a133fdfbd75d232b58e3c820fd7688a50904806b61f9140e85b381c143022",
    "paths": "0bd71863e3369095754d0decd11a70bf10229bf2d316f35ecc26835f8d057a59",
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
        metrics.get("complete_is_independent_episodes") != 110
        or metrics.get("median_24h_relative_negative_coskewness_risk_premium") != "-0.0003754158321982493350830023864"
        or metrics.get("median_24h_candidate_absolute_close_displacement") != "-0.002132740137685605583093262452"
        or metrics.get("fraction_complete_episodes_with_positive_24h_relative_negative_coskewness_risk_premium") != "0.4818181818181818181818181818"
    ):
        failures.append("metrics changed")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    expected_failed = {
        "median_24h_relative_negative_coskewness_risk_premium",
        "median_24h_candidate_absolute_close_displacement",
        "fraction_positive_24h_relative_negative_coskewness_risk_premium",
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
        print("u20_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u20_cross_sectional_paper_observation_check PASS failed_feasibility hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
