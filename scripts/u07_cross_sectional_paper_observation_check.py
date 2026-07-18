#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u07_cross_sectional_paper_observation"
REPORT = ROOT / "reports/m1/U07_CROSS_SECTIONAL_PAPER_OBSERVATION.md"
RUN_HASH = "8c637a3f13dad4410beb446094af011582ab2cde0ac449e32d044cbaa709352c"
ORDER_HASH = "2714c2bf0fee08ddd9531eeac2ef531904c7c416eb4c809a666f5f75e4cf00ee"
MANIFEST_HASHES = {
    "accounting": "11cffba3d6afacc70e8aba5e42d37327e8461f256e77c2bdc47d8573e547c139",
    "episodes": "d5407ac401f42017c93725a3d9bcff5a4641a3ed64447e5ce9f2c8b4a2f35f0a",
    "events": "be54d0044c585bb81e40580fb410a41cc1c1c0f795857577021638a28e51d0dd",
    "paths": "95abaeed4ce985284459569b4361a47f487832274e7d28d37c29fb970789147c",
}


def validate(
    summary: Mapping[str, Any], manifests: Mapping[str, Mapping[str, Any]], report: str,
) -> list[str]:
    failures: list[str] = []
    if identity_hash({key: value for key, value in summary.items() if key != "run_content_hash"}) != summary.get("run_content_hash") or summary.get("run_content_hash") != RUN_HASH:
        failures.append("run content hash drift")
    for name, expected_hash in MANIFEST_HASHES.items():
        document = manifests[name]
        if identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != document.get("content_hash") or document.get("content_hash") != expected_hash:
            failures.append(f"manifest hash drift: {name}")
    if summary.get("status") != "failed_feasibility":
        failures.append("truthful status changed")
    if len(summary.get("orders", [])) != 3 or any(
        row.get("content_identity_hash") != ORDER_HASH or row.get("manifest_hashes") != MANIFEST_HASHES
        for row in summary.get("orders", [])
    ):
        failures.append("order identity drift")
    metrics = summary.get("metrics", {})
    expected_metrics = {
        "complete_is_independent_episodes": 82,
        "projected_full_independent_episodes": 113,
        "projected_sealed_oos_independent_episodes": 31,
        "distinct_event_symbols": 33,
        "distinct_event_months": 40,
        "median_24h_relative_continuation": "0.004287821384236292564275564571",
        "median_24h_candidate_absolute_close_displacement": "0.01160736483333721153810826070",
        "fraction_complete_episodes_with_positive_24h_relative_continuation": "0.5243902439024390243902439024",
        "qualification_quarantine_lifecycle_or_order_mismatches": 0,
    }
    if any(metrics.get(key) != value for key, value in expected_metrics.items()):
        failures.append("metric drift")
    failed = sorted(key for key, value in summary.get("paper_gate_checks", {}).items() if not value)
    if failed != [
        "fraction_positive_24h_relative_continuation",
        "median_24h_candidate_absolute_close_displacement",
        "median_24h_relative_continuation",
    ]:
        failures.append("failed Gate set changed")
    if any(summary.get(key) is not False for key in (
        "oos_opened", "formal_returns_computed", "fills_positions_or_equity_generated",
        "parameters_changed_after_result", "second_run_executed", "network_accessed",
    )) or any(summary.get("authorizations", {}).values()):
        failures.append("isolation or downstream authorization changed")
    accounting = manifests["accounting"].get("content", {})
    if accounting.get("candidate_events") != 125 or accounting.get("independent_episodes") != 92 or accounting.get("complete_48h_episodes") != 82 or accounting.get("right_censored_episodes") != 10:
        failures.append("accounting drift")
    for marker in (
        "Status: `failed_feasibility`",
        "Complete independent episodes: `82`",
        "Median 24h relative continuation: `0.004287821384236292564275564571`",
        "OOS opened / rows decoded: `false / 0`",
        "A failed Gate closes U-07 without tuning",
    ):
        if marker not in report:
            failures.append(f"report marker missing: {marker}")
    return failures


def main() -> int:
    summary = load_json(EVIDENCE / "run_manifest.json")
    manifests = {name: load_json(EVIDENCE / f"{name}.json") for name in MANIFEST_HASHES}
    failures = validate(summary, manifests, REPORT.read_text(encoding="utf-8"))
    if failures:
        print("u07_cross_sectional_paper_observation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u07_cross_sectional_paper_observation_check PASS status=failed_feasibility hash={RUN_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
