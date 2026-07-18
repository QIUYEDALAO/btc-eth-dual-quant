#!/usr/bin/env python3
"""Check the committed U-05 frozen-source qualification result."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import content_hash, identity_hash, load_json
CONFIG = ROOT / "config/u05_cross_sectional_data_qualification_v1.json"
RESULT = ROOT / "reports/m1/evidence/u05_cross_sectional_data_qualification_v1.json"
REPORT = ROOT / "reports/m1/U05_CROSS_SECTIONAL_DATA_QUALIFICATION.md"
EXPECTED_RESULT_HASH = "348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f"


def validate(config: Mapping[str, Any], result: Mapping[str, Any], report_text: str) -> list[str]:
    failures: list[str] = []
    if content_hash(config) != config.get("content_hash"):
        failures.append("qualification contract hash drift")
    unsigned = {key: value for key, value in result.items() if key != "qualification_content_hash"}
    if identity_hash(unsigned) != result.get("qualification_content_hash") or result.get("qualification_content_hash") != EXPECTED_RESULT_HASH:
        failures.append("qualification result hash drift")
    expected = {
        "status": "pass", "contract_content_hash": config.get("content_hash"),
        "protocol_target_commit": config.get("protocol_target_commit"),
        "protocol_content_hash": config.get("protocol_content_hash"),
        "protocol_review_content_hash": config.get("protocol_review_content_hash"),
        "source_freeze_hash": config.get("authority_bindings", {}).get("source_freeze_hash"),
        "v4_artifact_set_hash": config.get("authority_bindings", {}).get("v4_artifact_set_hash"),
        "network_accessed": False, "production_evidence_mutated": False,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            failures.append(f"qualification result binding changed: {key}")
    counts = result.get("counts", {})
    for key, value in {
        "archive_count": 27736, "grid_rows": 1170, "manifests_exact": 19,
        "membership_rows": 1170, "months": 78, "panel_rows": 1170,
    }.items():
        if counts.get(key) != value:
            failures.append(f"qualification count changed: {key}")
    if counts.get("expected_4h_member_blocks", 0) * 4 != counts.get("constituent_1h_rows"):
        failures.append("4h/1h accounting changed")
    orders = result.get("orders", [])
    if [item.get("order") for item in orders] != ["normal", "reverse", "deterministic_shuffled"]:
        failures.append("qualification traversal order changed")
    if len({item.get("content_identity_hash") for item in orders}) != 1 or any(item.get("archive_count") != 27736 for item in orders):
        failures.append("qualification traversal identity changed")
    isolation = result.get("isolation", {})
    expected_isolation = {
        "is_start": "2020-01-01T00:00:00Z", "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_opened": False, "oos_archive_access": "opaque_identity_and_crc_only",
        "oos_ohlc_values_decoded": 0, "breadth_rows_generated": 0,
        "event_rows_generated": 0, "path_rows_generated": 0, "return_rows_generated": 0,
    }
    if isolation != expected_isolation:
        failures.append("IS/OOS isolation evidence changed")
    auth = result.get("authorizations", {})
    if auth.get("one_sealed_is_paper_observation") is not True or any(
        auth.get(key) is not False
        for key in ("event_scan_beyond_one_frozen_is_observation", "strategy", "backtesting", "oos", "api_trading", "execution_live", "m2")
    ):
        failures.append("post-qualification authorization changed")
    for marker in (
        "Status: `pass`", "27,736/27,736", "19/19", "Completed 4h grid authority: `pass`",
        "OOS OHLC values decoded: `0`", "one sealed-IS Paper observation",
        "No strategy, backtest, OOS, API/trading, execution/live or M2",
    ):
        if marker not in report_text:
            failures.append(f"report marker missing: {marker}")
    return failures


def main() -> int:
    failures = validate(load_json(CONFIG), load_json(RESULT), REPORT.read_text(encoding="utf-8"))
    if failures:
        print("u05_cross_sectional_data_qualification_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u05_cross_sectional_data_qualification_check PASS hash={EXPECTED_RESULT_HASH}")
    print("authorized_next=one sealed-IS Paper observation; oos=no strategy=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
