#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, ONE_HOUR_MS, build_membership, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base

CONFIG = ROOT / "config/u11_cross_sectional_data_qualification_v1.json"
BASE_CONFIG = ROOT / "config/u07_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u11_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u11_cross_sectional_paper_protocol_v1.json"


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def verify_ceiling(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["sample_ceiling_contract"]
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    start = utc_ms(contract["is_start"])
    end = utc_ms(contract["is_end_exclusive"])
    step = int(contract["decision_step_hours"]) * ONE_HOUR_MS
    lookback = int(contract["lookback_completed_4h_observations"])
    horizon = int(contract["primary_horizon_hours"]) * ONE_HOUR_MS
    eligible: list[int] = []
    decision = start + lookback * step
    while decision + horizon <= end:
        current = tuple(membership.get(month_for_ms(decision - 1), ()))
        history_months = {month_for_ms(decision - offset * step) for offset in range(1, lookback + 1)}
        continuous = set(current)
        for month in history_months:
            continuous.intersection_update(membership.get(month, ()))
        path_constant = tuple(membership.get(month_for_ms(decision + horizon - 1), ())) == current
        if len(current) >= 10 and len(continuous) >= int(contract["minimum_continuously_active_current_members"]) and path_constant:
            eligible.append(decision)
        decision += step
    selected: list[int] = []
    previous: int | None = None
    for decision in eligible:
        if previous is None or decision - previous > horizon:
            selected.append(decision)
            previous = decision
    if len(eligible) != contract["eligible_history_and_constant_path_decision_times"] or len(selected) != contract["maximum_independent_theoretical_episodes"]:
        raise QualificationFailure("sample ceiling identity drift")
    if len(selected) < contract["protocol_minimum_theoretical_episodes"] or len(selected) < contract["paper_complete_is_episode_gate"]:
        raise QualificationFailure("sample ceiling Gate failed")
    years = Counter(datetime.fromtimestamp(value / 1000, tz=timezone.utc).year for value in selected)
    return {
        "eligible_history_and_constant_path_decision_times": len(eligible),
        "maximum_independent_theoretical_episodes": len(selected),
        "maximum_independent_episodes_by_year": {str(key): value for key, value in sorted(years.items())},
    }


def qualify(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if canonical_hash(config) != config.get("content_hash"):
        raise QualificationFailure("contract hash drift")
    protocol = git_json(config["protocol_target_commit"], PROTOCOL_PATH)
    review = load_json(REVIEW)
    if protocol.get("content_hash") != config["protocol_content_hash"] or review.get("review_content_hash") != config["protocol_review_content_hash"] or review.get("verdict") != "approve" or review.get("remaining_critical_findings") != 0 or review.get("remaining_high_findings") != 0:
        raise QualificationFailure("protocol/review binding drift")
    base_config = load_json(BASE_CONFIG)
    if base_config.get("content_hash") != config["base_v4_qualification_contract_hash"]:
        raise QualificationFailure("base contract drift")
    base_result = qualify_base(raw_root=raw_root, config=base_config)
    ceiling = verify_ceiling(config)
    if base_result["source_freeze_hash"] != config["authority_bindings"]["source_freeze_hash"] or base_result["v4_artifact_set_hash"] != config["authority_bindings"]["v4_artifact_set_hash"]:
        raise QualificationFailure("V4 authority drift")
    isolation = config["isolation_contract"]
    result = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "pass",
        "contract_content_hash": config["content_hash"],
        "protocol_target_commit": config["protocol_target_commit"],
        "protocol_content_hash": config["protocol_content_hash"],
        "protocol_review_content_hash": config["protocol_review_content_hash"],
        "source_freeze_hash": base_result["source_freeze_hash"],
        "v4_artifact_set_hash": base_result["v4_artifact_set_hash"],
        "manifest_hashes": base_result["manifest_hashes"],
        "orders": base_result["orders"],
        "counts": {**base_result["counts"], **ceiling},
        "isolation": {
            "is_start": isolation["is_start"],
            "is_end_exclusive": isolation["is_end_exclusive"],
            "oos_opened": False,
            "oos_ohlcv_values_decoded": 0,
            "common_state_rows_generated": 0,
            "capture_rows_generated": 0,
            "candidate_rows_generated": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "return_rows_generated": 0,
        },
        "authorizations": {"one_sealed_is_paper_observation": True, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False},
        "network_accessed": False,
        "production_evidence_mutated": False,
    }
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u11_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(args.raw_root, load_json(CONFIG))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-11 qualification PASS archives={result['counts']['archive_count']} ceiling={result['counts']['maximum_independent_theoretical_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
