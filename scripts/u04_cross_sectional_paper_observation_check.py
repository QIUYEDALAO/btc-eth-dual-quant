#!/usr/bin/env python3
"""Validate the immutable failed U-04 sealed-IS paper observation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json


EVIDENCE = ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation"
REPORT = ROOT / "reports/m1/U04_CROSS_SECTIONAL_PAPER_OBSERVATION.md"
EXPECTED_HASHES = {
    "accounting": "8f6f91218032456d15dfa04dd8d8813aa88537d84f842df13ccb0cf1ad8d4b97",
    "episodes": "81cd99f43b0bfe629feab0110a959a7536d35fecbaa85780b943d6a9a26a3961",
    "events": "4c3a197836f0b52759e0b64fdaa7f9b096a6c65009446f647d2a00130317fbdf",
    "paths": "ef74a3b10204acb8a4b99aee543d946c03f36afee669bd8a27c921e5ceab780d",
}
RUN_HASH = "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2"
ORDER_HASH = "4c512f5900b15969cf13c1481317e388d94d3ac6c2b26dc576914863b5201b42"


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
    if summary.get("protocol_content_hash") != "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6" or summary.get("qualification_content_hash") != "4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c":
        failures.append("protocol or qualification binding drift")
    orders = summary.get("orders", [])
    if [row.get("order") for row in orders] != ["normal", "reverse", "deterministic_shuffled"] or any(row.get("content_identity_hash") != ORDER_HASH or row.get("manifest_hashes") != EXPECTED_HASHES for row in orders):
        failures.append("three-order identity drift")
    expected_metrics = {
        "complete_is_independent_episodes": 397,
        "projected_full_independent_episodes": 549,
        "projected_sealed_oos_independent_episodes": 152,
        "years_with_ten_complete_episodes": 5,
        "maximum_single_year_episode_share": "0.244332493703",
        "maximum_single_symbol_episode_share": "0.065491183879",
        "distinct_event_symbols": 47,
        "median_24h_relative_recovery": "-0.008556398568655178767341556211667999570187556831814",
        "median_24h_absolute_close_displacement": "-0.00794575696578027333403962284140269096302574425257",
        "qualification_quarantine_lifecycle_or_order_mismatches": 0,
    }
    metrics = summary.get("metrics", {})
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("frozen paper metric drift")
    checks = summary.get("paper_gate_checks", {})
    failed = sorted(key for key, value in checks.items() if value is not True)
    if failed != ["median_24h_absolute_close_displacement", "median_24h_relative_recovery"]:
        failures.append("failed Gate set changed")
    accounting = manifests.get("accounting", {}).get("content", {})
    expected_accounting = {
        "candidate_events": 2890, "independent_episodes": 420,
        "complete_24h_episodes": 397, "right_censored_episodes": 23,
        "oos_rows_decoded": 0, "formal_returns_computed": 0,
        "fills_positions_or_equity_rows": 0,
    }
    if any(accounting.get(key) != value for key, value in expected_accounting.items()):
        failures.append("paper accounting drift")
    if any(summary.get(key) is not False for key in ("oos_opened", "formal_returns_computed", "fills_positions_or_equity_generated", "parameters_changed_after_result", "second_run_executed", "network_accessed")):
        failures.append("isolation or no-rerun claim changed")
    if any(summary.get("authorizations", {}).values()):
        failures.append("failed result authorizes downstream work")
    for marker in (
        "Status: `failed_feasibility`", "Complete independent episodes: `397`",
        "median_24h_relative_recovery: `false`", "median_24h_absolute_close_displacement: `false`",
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
        print("u04_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u04_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN_HASH}")
    print("failed_gates=24h_relative_recovery,24h_absolute_displacement; oos=no rerun=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
