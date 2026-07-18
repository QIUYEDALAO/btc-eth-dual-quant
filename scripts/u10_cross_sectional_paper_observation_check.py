#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u10_cross_sectional_paper_observation"
REPORT = ROOT / "reports/m1/U10_CROSS_SECTIONAL_PAPER_OBSERVATION.md"
RUN_HASH = "9972a95fe662ac65f7e0e2c0bb4d88eb9743097beb9c7c536f3507d9a316d22f"
ORDER_HASH = "83540c78bf6afed742fa09254b7e6c172014f2f599215335944fdeb9a67de11d"
MANIFEST_HASHES = {
    "accounting": "c2006c0e87ce326890f84c18df60249ee53311aef3ae69e80787f6436e83d582",
    "episodes": "962810f9e3355e6c3d3775320f19284bc558725d0a0ab66e6518dbf82e811b80",
    "events": "a67101f3bd0c1ab2271d1c362926d5cd61bac6fc019d0d0884fe3dd2519573d5",
    "paths": "c1ca182a15294ef72d3cdfd13bd7984231423a0524fbe9566891603d6e00a23d",
}


def validate(summary: Mapping[str, Any], manifests: Mapping[str, Mapping[str, Any]], report: str) -> list[str]:
    failures: list[str] = []
    if identity_hash({key: value for key, value in summary.items() if key != "run_content_hash"}) != summary.get("run_content_hash") or summary.get("run_content_hash") != RUN_HASH:
        failures.append("run hash drift")
    for name, expected in MANIFEST_HASHES.items():
        document = manifests[name]
        if identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != document.get("content_hash") or document.get("content_hash") != expected:
            failures.append(f"manifest drift: {name}")
    orders = summary.get("orders", [])
    if summary.get("status") != "failed_feasibility" or len(orders) != 3 or any(row.get("content_identity_hash") != ORDER_HASH or row.get("manifest_hashes") != MANIFEST_HASHES for row in orders):
        failures.append("status/order drift")
    metrics = summary.get("metrics", {})
    expected_metrics = {
        "complete_is_independent_episodes": 7,
        "projected_full_independent_episodes": 9,
        "projected_sealed_oos_independent_episodes": 2,
        "distinct_event_symbols": 6,
        "distinct_event_months": 7,
        "median_72h_relative_continuation": "0.007971619522185805237735347941231168470184480243915",
        "median_72h_candidate_absolute_close_displacement": "0.0228120258210529022966334902142324409124810328421",
        "fraction_complete_episodes_with_positive_72h_relative_continuation": "0.7142857142857142857142857143",
        "qualification_quarantine_lifecycle_or_order_mismatches": 0,
    }
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("metric drift")
    expected_failed = [
        "complete_is_independent_episodes", "distinct_event_months", "distinct_event_symbols",
        "maximum_single_symbol_episode_share", "maximum_single_year_episode_share",
        "median_72h_relative_continuation", "projected_full_independent_episodes",
        "projected_sealed_oos_independent_episodes", "years_with_twelve_complete_episodes",
    ]
    if sorted(key for key, value in summary.get("paper_gate_checks", {}).items() if not value) != expected_failed:
        failures.append("failed Gate set changed")
    if any(summary.get(key) is not False for key in ("oos_opened", "formal_returns_computed", "fills_positions_or_equity_generated", "parameters_changed_after_result", "second_run_executed", "network_accessed")) or any(summary.get("authorizations", {}).values()):
        failures.append("isolation/authorization drift")
    accounting = manifests["accounting"].get("content", {})
    if accounting.get("candidate_events") != 179 or accounting.get("independent_episodes") != 39 or accounting.get("complete_72h_episodes") != 7 or accounting.get("right_censor_reasons") != {"membership_change": 32}:
        failures.append("accounting drift")
    for marker in ("Status: `failed_feasibility`", "Complete independent episodes: `7`", "OOS opened / rows decoded: `false / 0`", "A failed Gate closes the candidate without tuning"):
        if marker not in report:
            failures.append(f"report marker missing: {marker}")
    return failures


def main() -> int:
    summary = load_json(EVIDENCE / "run_manifest.json")
    manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in MANIFEST_HASHES}
    failures = validate(summary, manifests, REPORT.read_text())
    if failures:
        print("u10_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u10_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
