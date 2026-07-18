#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u24_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED = "131266a00f2b3742dd3bb2963bc5184ba55ae5aef22b97cfb0f26d2d02c697dd"
IDENTITY = "0e8ae9785503f1fc59bbb419d031c31856ff90520a3432ff66306c1c7bc138e1"
HASHES = {
    "accounting": "a475ed67e45f4f0b6bf739941bc70cde9a246994b18fff0512d9780c0a8fd0a0",
    "episodes": "9727ada035deed7fbbc838cc2680b401b02a13da89cc184c58c77a94e885da05",
    "events": "f845a4bf3bb85dc658eb4c8c5b223e33e67fa6a5a7c31706ebc29646c2bc5c96",
    "paths": "90f8b5324172992d12e603527737f941c9b514588d29e18ac82d670ec49536af",
}
FAILED_GATES = {
    "complete_is_independent_episodes",
    "projected_full_independent_episodes",
    "projected_sealed_oos_independent_episodes",
    "median_24h_relative_lottery_demand_avoidance_premium",
    "median_24h_candidate_absolute_close_displacement",
    "fraction_positive_24h_relative_lottery_demand_avoidance_premium",
}


def validate(run: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    identity = {key: value for key, value in run.items() if key != "run_content_hash"}
    if run.get("run_content_hash") != EXPECTED or identity_hash(identity) != EXPECTED:
        findings.append("run identity")
    if (
        run.get("status") != "failed_feasibility"
        or run.get("oos_opened") is not False
        or run.get("oos_rows_decoded") != 0
        or run.get("second_run_executed") is not False
        or run.get("formal_returns_computed") is not False
        or run.get("fills_positions_or_equity_generated") is not False
        or run.get("parameters_changed_after_result") is not False
    ):
        findings.append("status/isolation")
    orders = run.get("orders", [])
    if (
        [item.get("order") for item in orders]
        != ["normal", "reverse", "deterministic_shuffled"]
        or any(item.get("content_identity_hash") != IDENTITY for item in orders)
        or any(item.get("manifest_hashes") != HASHES for item in orders)
    ):
        findings.append("orders")
    metrics = run.get("metrics", {})
    expected_metrics = {
        "complete_is_independent_episodes": 78,
        "projected_full_independent_episodes": 107,
        "projected_sealed_oos_independent_episodes": 29,
        "years_with_twelve_complete_episodes": 4,
        "distinct_event_symbols": 20,
        "distinct_event_months": 52,
        "maximum_single_symbol_episode_share": "0.1538461538461538461538461538",
        "maximum_single_year_episode_share": "0.2564102564102564102564102564",
        "median_24h_relative_lottery_demand_avoidance_premium": "0.003451638265937481372102744676",
        "median_24h_candidate_absolute_close_displacement": "-0.001052104938464466894353960344",
        "fraction_complete_episodes_with_positive_24h_relative_lottery_demand_avoidance_premium": "0.5769230769230769230769230769",
        "qualification_preflight_complexity_quarantine_lifecycle_or_order_mismatches": 0,
    }
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        findings.append("metrics")
    failed = {key for key, value in run.get("paper_gate_checks", {}).items() if not value}
    if failed != FAILED_GATES:
        findings.append("failed Gates")
    if any(run.get("authorizations", {}).values()):
        findings.append("authorization")
    for name, expected_hash in HASHES.items():
        manifest = load_json(EVIDENCE / f"{name}.json")
        actual = identity_hash({key: value for key, value in manifest.items() if key != "content_hash"})
        if manifest.get("content_hash") != expected_hash or actual != expected_hash:
            findings.append(name)
    return findings


def main() -> int:
    findings = validate(load_json(RUN))
    verdict = "PASS failed_feasibility" if not findings else "FAIL"
    print(f"u24_cross_sectional_paper_observation_check {verdict} hash={EXPECTED}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
