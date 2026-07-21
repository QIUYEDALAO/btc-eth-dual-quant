#!/usr/bin/env python3
"""Validate the immutable failed U-05 sealed-IS Paper observation."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u05_cross_sectional_paper_observation"
REPORT = ROOT / "reports/m1/U05_CROSS_SECTIONAL_PAPER_OBSERVATION.md"
EXPECTED_HASHES = {
    "accounting": "cdc51ff7cf2cd5d0d3a0f32c010620d07dc237e787d8e3010683fd43508def72",
    "episodes": "ffc38cd8ad4a4eb9ce0009c06e7237e779e0a7ed497ac780300e847c016c636f",
    "events": "1ba4a2ebf6b634dcfc830670b3024884d46222a5a32c2a4ed534e4c25b7c36e6",
    "paths": "a0e971cf8994ef396f2bd56c5616ad8d68feb65ef7d0f8201f9f3b2811da6edc",
}
RUN_HASH = "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a"
ORDER_HASH = "ac4b36ac2c04d55c25f9db62f9d59598bac8bb1861b97d4e01f701be398267b0"


def validate(summary: Mapping[str, Any], manifests: Mapping[str, Mapping[str, Any]], report_text: str) -> list[str]:
    failures: list[str] = []
    unsigned = {key: value for key, value in summary.items() if key != "run_content_hash"}
    if summary.get("run_content_hash") != identity_hash(unsigned) or summary.get("run_content_hash") != RUN_HASH:
        failures.append("run content hash drift")
    for name, expected in EXPECTED_HASHES.items():
        document = manifests.get(name, {})
        unsigned_manifest = {key: value for key, value in document.items() if key != "content_hash"}
        if document.get("content_hash") != identity_hash(unsigned_manifest) or document.get("content_hash") != expected:
            failures.append(f"manifest hash drift: {name}")
    if summary.get("status") != "failed_feasibility":
        failures.append("truthful failed_feasibility status changed")
    if summary.get("protocol_content_hash") != "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214" or summary.get("qualification_content_hash") != "348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f":
        failures.append("protocol or qualification binding drift")
    orders = summary.get("orders", [])
    if [row.get("order") for row in orders] != ["normal", "reverse", "deterministic_shuffled"] or any(row.get("content_identity_hash") != ORDER_HASH or row.get("manifest_hashes") != EXPECTED_HASHES for row in orders):
        failures.append("three-order identity drift")
    metrics = summary.get("metrics", {})
    expected_metrics = {
        "complete_is_independent_episodes": 490,
        "projected_full_independent_episodes": 678,
        "projected_sealed_oos_independent_episodes": 188,
        "years_with_ten_complete_episodes": 5,
        "maximum_single_year_episode_share": "0.2183673469387755102040816327",
        "maximum_single_calendar_quarter_episode_share": "0.06326530612244897959183673469",
        "distinct_event_months": 57,
        "median_24h_common_demand_close_displacement": "0.0007591260524623880214213314285",
        "median_24h_positive_member_fraction": "0.5333333333333333333333333335",
        "qualification_quarantine_lifecycle_or_order_mismatches": 0,
    }
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("frozen Paper metric drift")
    failed = sorted(key for key, value in summary.get("paper_gate_checks", {}).items() if value is not True)
    if failed != ["median_24h_common_demand_close_displacement", "median_24h_positive_member_fraction"]:
        failures.append("failed Gate set changed")
    accounting = manifests.get("accounting", {}).get("content", {})
    expected_accounting = {
        "candidate_events": 1488, "independent_episodes": 509,
        "complete_24h_episodes": 490, "right_censored_episodes": 19,
        "oos_rows_decoded": 0, "formal_returns_computed": 0,
        "fills_positions_or_equity_rows": 0,
    }
    if any(accounting.get(key) != value for key, value in expected_accounting.items()):
        failures.append("Paper accounting drift")
    if any(summary.get(key) is not False for key in ("oos_opened", "formal_returns_computed", "fills_positions_or_equity_generated", "parameters_changed_after_result", "second_run_executed", "network_accessed")):
        failures.append("isolation or no-rerun claim changed")
    if any(summary.get("authorizations", {}).values()):
        failures.append("failed result authorizes downstream work")
    for marker in (
        "Status: `failed_feasibility`", "Complete independent episodes: `490`",
        "median_24h_common_demand_close_displacement: `false`", "median_24h_positive_member_fraction: `false`",
        "OOS opened / rows decoded: `false / 0`", "A failed Gate closes the candidate without tuning",
    ):
        if marker not in report_text:
            failures.append(f"report marker missing: {marker}")
    return failures


def main() -> int:
    summary = load_json(EVIDENCE / "run_manifest.json")
    manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in EXPECTED_HASHES}
    failures = validate(summary, manifests, REPORT.read_text(encoding="utf-8"))
    if failures:
        print("u05_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u05_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN_HASH}")
    print("failed_gates=24h_common_demand_displacement,positive_member_fraction; oos=no rerun=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
