#!/usr/bin/env python3
"""Qualify U-13 hourly inputs without decoding outcomes or scanning events."""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, build_membership, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG, ordered, read_open_times, required_tasks

CONFIG = ROOT / "config/u13_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u13_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u13_cross_sectional_paper_protocol_v1.json"
ONE_HOUR_MS = 3_600_000


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def same_reader_preflight(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["hourly_input_preflight"]
    start, end = utc_ms(contract["is_start"]), utc_ms(contract["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    tasks = required_tasks(membership, end)
    order_results: list[dict[str, Any]] = []
    primary: dict[str, set[int]] | None = None
    for order in contract["traversal_orders"]:
        available: dict[str, set[int]] = defaultdict(set)
        missing: list[str] = []
        for month, symbol in ordered(tasks, order, int(contract["deterministic_shuffle_seed"])):
            rows = read_open_times(raw_root, symbol, month, end)
            if rows is None:
                missing.append(f"{symbol}:{month}")
            else:
                available[symbol].update(rows)
        canonical = {"available_open_time_hashes": {symbol: identity_hash(sorted(values)) for symbol, values in sorted(available.items())}, "missing_archives": sorted(missing)}
        order_results.append({"order": order, "content_identity_hash": identity_hash(canonical), "task_count": len(tasks), "missing_archive_count": len(missing)})
        if primary is None:
            primary = available
    if len({row["content_identity_hash"] for row in order_results}) != 1:
        raise QualificationFailure("same-reader traversal identity mismatch")
    assert primary is not None

    complete: dict[int, tuple[str, ...]] = {}
    incomplete: Counter[str] = Counter()
    hour = start
    while hour < end:
        members = tuple(membership.get(month_for_ms(hour), ()))
        if len(members) < int(contract["minimum_current_active_members"]):
            incomplete["membership_below_minimum"] += 1
        else:
            slots = tuple(range(hour, hour + ONE_HOUR_MS, FIVE_MINUTES_MS))
            valid = True
            for symbol in members:
                values = primary.get(symbol, set())
                if hour - FIVE_MINUTES_MS not in values:
                    incomplete["previous_boundary_close_missing"] += 1; valid = False; break
                if any(opened not in values or (symbol, opened) in masked for opened in slots):
                    incomplete["hourly_12_slot_or_mask_failure"] += 1; valid = False; break
            if valid:
                complete[hour] = members
        hour += ONE_HOUR_MS

    structurally_eligible: dict[str, list[int]] = defaultdict(list)
    for hour, members in sorted(complete.items()):
        if all(complete.get(hour + offset * ONE_HOUR_MS) == members for offset in range(1, int(contract["historical_followup_hours"]) + 1)):
            for symbol in members:
                structurally_eligible[symbol].append(hour)

    lookback = int(contract["lookback_completed_1h_observations"])
    half = int(contract["chronological_halves_observations"][0])
    followup = int(contract["historical_followup_hours"])
    path_hours = int(contract["primary_horizon_hours"])
    eligible: list[int] = []
    checked = 0
    decision = start + lookback * ONE_HOUR_MS
    while decision + path_hours * ONE_HOUR_MS < end:
        members = complete.get(decision)
        if members is None:
            decision += ONE_HOUR_MS; continue
        checked += 1
        if not all(complete.get(decision + offset * ONE_HOUR_MS) == members for offset in range(1, path_hours + 1)):
            decision += ONE_HOUR_MS; continue
        candidate_available = False
        first_start, split, last = decision - lookback * ONE_HOUR_MS, decision - half * ONE_HOUR_MS, decision - followup * ONE_HOUR_MS
        for symbol in members:
            values = structurally_eligible.get(symbol, [])
            full = bisect.bisect_right(values, last) - bisect.bisect_left(values, first_start)
            first = bisect.bisect_left(values, split) - bisect.bisect_left(values, first_start)
            second = bisect.bisect_right(values, last) - bisect.bisect_left(values, split)
            if full >= int(contract["minimum_structurally_available_occurrences_full"]) and first >= int(contract["minimum_structurally_available_occurrences_each_half"]) and second >= int(contract["minimum_structurally_available_occurrences_each_half"]):
                candidate_available = True; break
        if candidate_available:
            eligible.append(decision)
        decision += ONE_HOUR_MS

    selected: list[int] = []
    previous: int | None = None
    cluster = int(contract["cluster_connected_window_hours"]) * ONE_HOUR_MS
    for decision in eligible:
        if previous is None or decision - previous > cluster:
            selected.append(decision); previous = decision
    if len(selected) < int(contract["minimum_theoretical_eligible_episodes"]):
        raise QualificationFailure(f"pre-result sample ceiling Gate failed: {len(selected)}")
    years = Counter(datetime.fromtimestamp(value / 1000, tz=timezone.utc).year for value in selected)
    return {"orders": order_results, "counts": {"same_reader_task_count": len(tasks), "missing_archive_count": order_results[0]["missing_archive_count"], "complete_active_member_1h_intervals": len(complete), "incomplete_hour_reasons": dict(sorted(incomplete.items())), "decision_hours_structurally_checked": checked, "eligible_structural_decision_hours": len(eligible), "maximum_independent_theoretical_24h_episodes": len(selected), "maximum_independent_episodes_by_year": {str(k): v for k, v in sorted(years.items())}, "symbols_with_structural_history": len(structurally_eligible)}}


def qualify(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if canonical_hash(config) != config.get("content_hash"):
        raise QualificationFailure("contract hash drift")
    protocol = git_json(config["protocol_target_commit"], PROTOCOL_PATH)
    review = load_json(REVIEW)
    if protocol.get("content_hash") != config["protocol_content_hash"] or review.get("review_content_hash") != config["protocol_review_content_hash"] or review.get("verdict") != "approve" or review.get("remaining_critical_findings") or review.get("remaining_high_findings"):
        raise QualificationFailure("protocol/review binding drift")
    base_config = load_json(BASE_CONFIG)
    if base_config.get("content_hash") != config["base_v4_qualification_contract_hash"]:
        raise QualificationFailure("base contract drift")
    base = qualify_base(raw_root=raw_root, config=base_config)
    preflight = same_reader_preflight(raw_root, config)
    if base["source_freeze_hash"] != config["authority_bindings"]["source_freeze_hash"] or base["v4_artifact_set_hash"] != config["authority_bindings"]["v4_artifact_set_hash"]:
        raise QualificationFailure("V4 authority drift")
    isolation = config["isolation_contract"]
    result = {"schema_version": 1, "qualification_id": config["qualification_id"], "status": "pass", "contract_content_hash": config["content_hash"], "protocol_target_commit": config["protocol_target_commit"], "protocol_content_hash": config["protocol_content_hash"], "protocol_review_content_hash": config["protocol_review_content_hash"], "source_freeze_hash": base["source_freeze_hash"], "v4_artifact_set_hash": base["v4_artifact_set_hash"], "manifest_hashes": base["manifest_hashes"], "source_orders": base["orders"], "same_reader_orders": preflight["orders"], "counts": {**base["counts"], **preflight["counts"]}, "isolation": {"is_start": isolation["is_start"], "is_end_exclusive": isolation["is_end_exclusive"], "oos_opened": False, "oos_archive_access": isolation["oos_archive_access"], "oos_ohlcv_values_decoded": 0, "ohlcv_fields_decoded_during_preflight": 0, "common_component_rows_generated": 0, "candidate_rows_generated": 0, "event_rows_generated": 0, "path_rows_generated": 0, "return_rows_generated": 0}, "authorizations": {"one_sealed_is_paper_observation": True, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}, "network_accessed": False, "production_evidence_mutated": False}
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe"); parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u13_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args(); result = qualify(args.raw_root, load_json(CONFIG)); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-13 qualification PASS archives={result['counts']['archive_count']} ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
