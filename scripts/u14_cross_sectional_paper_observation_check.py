#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import identity_hash, load_json

EVIDENCE = ROOT / "reports/m1/evidence/u14_cross_sectional_paper_observation"
RUN = EVIDENCE / "run_manifest.json"
EXPECTED_RUN = "3824731159e682d1fe0e249fc24a586ef87b8b2d53a4f716d42f66c9d72f1f5c"
EXPECTED_ORDER = "1436911ba8c6f4fd3adbba1c5ebf391f98d82d80987c7f8b2308b95c42414b69"


def validate(run: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in run.items() if key != "run_content_hash"}
    if run.get("run_content_hash") != EXPECTED_RUN or identity_hash(identity) != EXPECTED_RUN:
        failures.append("run identity changed")
    orders = run.get("orders", [])
    if len(orders) != 3 or {row.get("content_identity_hash") for row in orders} != {EXPECTED_ORDER}:
        failures.append("three-order identity changed")
    for name in ("events", "episodes", "paths", "accounting"):
        document = load_json(EVIDENCE / f"{name}.json")
        if identity_hash({key: value for key, value in document.items() if key != "content_hash"}) != document.get("content_hash"):
            failures.append(f"{name} manifest changed")
        if any(row.get("manifest_hashes", {}).get(name) != document.get("content_hash") for row in orders):
            failures.append(f"{name} order binding changed")
    metrics = run.get("metrics", {})
    if metrics.get("complete_is_independent_episodes") != 92 or metrics.get("median_24h_relative_rejection_persistence") != "0.001380259434304533953207550691" or metrics.get("median_24h_candidate_absolute_close_displacement") != "0.00773724142851497775358313756" or metrics.get("fraction_complete_episodes_with_positive_24h_relative_rejection_persistence") != "0.5434782608695652173913043478":
        failures.append("frozen metrics changed")
    failed = sorted(key for key, value in run.get("paper_gate_checks", {}).items() if not value)
    if failed != ["fraction_positive_24h_relative_rejection_persistence", "median_24h_candidate_absolute_close_displacement", "median_24h_relative_rejection_persistence"] or run.get("status") != "failed_feasibility":
        failures.append("truthful Gate verdict changed")
    if run.get("oos_opened") is not False or run.get("oos_rows_decoded") != 0 or run.get("formal_returns_computed") is not False or run.get("fills_positions_or_equity_generated") is not False or run.get("parameters_changed_after_result") is not False or run.get("second_run_executed") is not False:
        failures.append("isolation changed")
    if any(run.get("authorizations", {}).values()):
        failures.append("closed candidate authorization changed")
    return failures


def main() -> int:
    failures = validate(load_json(RUN))
    if failures:
        print("u14_cross_sectional_paper_observation_check FAIL")
        for failure in failures: print(f"- {failure}")
        return 1
    print(f"u14_cross_sectional_paper_observation_check PASS run={EXPECTED_RUN} failed_feasibility")
    return 0


if __name__ == "__main__": raise SystemExit(main())
