#!/usr/bin/env python3
"""Qualify U-12 daily inputs without decoding outcomes or scanning events."""
from __future__ import annotations

import argparse
import json
import random
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, ONE_DAY_MS, build_membership, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base

CONFIG = ROOT / "config/u12_cross_sectional_data_qualification_v1.json"
BASE_CONFIG = ROOT / "config/u07_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u12_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u12_cross_sectional_paper_protocol_v1.json"


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def ordered(values: Iterable[tuple[str, str]], order: str, seed: int) -> list[tuple[str, str]]:
    rows = sorted(values)
    if order == "reverse":
        rows.reverse()
    elif order == "deterministic_shuffled":
        random.Random(seed).shuffle(rows)
    elif order != "normal":
        raise QualificationFailure(f"unknown traversal order: {order}")
    return rows


def previous_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    if number == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{number - 1:02d}"


def read_open_times(raw_root: Path, symbol: str, month: str, end_ms: int) -> tuple[int, ...] | None:
    relative = Path(f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip")
    path = raw_root / relative
    if not path.is_file():
        return None
    output: list[int] = []
    with zipfile.ZipFile(path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) != 1:
            raise QualificationFailure(f"archive member count changed: {relative.as_posix()}")
        with archive.open(members[0]) as handle:
            for raw_line in handle:
                first = raw_line.split(b",", 1)[0].strip()
                try:
                    opened = int(first)
                except ValueError:
                    if not output and first.lower() in {b"open_time", b"opentime"}:
                        continue
                    raise QualificationFailure(f"malformed open time: {symbol}:{month}")
                if opened >= end_ms:
                    break
                if opened % FIVE_MINUTES_MS:
                    raise QualificationFailure(f"off-grid open time: {symbol}:{month}:{opened}")
                if output and opened <= output[-1]:
                    raise QualificationFailure(f"non-increasing open time: {symbol}:{month}")
                output.append(opened)
    return tuple(output)


def required_tasks(membership: Mapping[str, Sequence[str]], end_ms: int) -> set[tuple[str, str]]:
    tasks: set[tuple[str, str]] = set()
    for month, symbols in membership.items():
        if utc_ms(f"{month}-01T00:00:00Z") >= end_ms:
            continue
        for symbol in symbols:
            tasks.add((month, symbol))
            tasks.add((previous_month(month), symbol))
    return tasks


def same_reader_preflight(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["daily_input_preflight"]
    start = utc_ms(contract["is_start"])
    end = utc_ms(contract["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    tasks = required_tasks(membership, end)
    order_results: list[dict[str, Any]] = []
    primary_available: dict[str, set[int]] | None = None
    for order in contract["traversal_orders"]:
        available: dict[str, set[int]] = defaultdict(set)
        missing_archives: list[str] = []
        for month, symbol in ordered(tasks, order, int(contract["deterministic_shuffle_seed"])):
            rows = read_open_times(raw_root, symbol, month, end)
            if rows is None:
                missing_archives.append(f"{symbol}:{month}")
                continue
            available[symbol].update(opened for opened in rows if opened < end)
        canonical = {
            "available_open_time_hashes": {symbol: identity_hash(sorted(values)) for symbol, values in sorted(available.items())},
            "missing_archives": sorted(missing_archives),
        }
        order_results.append({"order": order, "content_identity_hash": identity_hash(canonical), "task_count": len(tasks), "missing_archive_count": len(missing_archives)})
        if primary_available is None:
            primary_available = available
    if len({row["content_identity_hash"] for row in order_results}) != 1:
        raise QualificationFailure("same-reader traversal identity mismatch")
    assert primary_available is not None

    complete_days: dict[int, tuple[str, ...]] = {}
    incomplete_reasons: Counter[str] = Counter()
    day = start
    expected_slots = int(contract["expected_5m_slots_per_utc_day"])
    while day < end:
        members = tuple(membership.get(month_for_ms(day), ()))
        if len(members) < int(contract["minimum_current_active_members"]):
            incomplete_reasons["membership_below_minimum"] += 1
            day += ONE_DAY_MS
            continue
        expected = range(day, day + ONE_DAY_MS, FIVE_MINUTES_MS)
        complete = True
        for symbol in members:
            available = primary_available.get(symbol, set())
            if day - FIVE_MINUTES_MS not in available:
                incomplete_reasons["previous_boundary_close_missing"] += 1
                complete = False
                break
            slots = [opened for opened in expected if opened in available and (symbol, opened) not in masked]
            if len(slots) != expected_slots:
                incomplete_reasons["daily_288_slot_or_mask_failure"] += 1
                complete = False
                break
        if complete:
            complete_days[day] = members
        day += ONE_DAY_MS

    eligible: list[int] = []
    decisions_with_52_scheduled_cells_checked = 0
    candidate_history_counts: Counter[str] = Counter()
    decision = start + 52 * 7 * ONE_DAY_MS
    while decision + ONE_DAY_MS <= end:
        current = complete_days.get(decision)
        if current is None:
            decision += ONE_DAY_MS
            continue
        history_days = [decision - offset * 7 * ONE_DAY_MS for offset in range(52, 0, -1)]
        decisions_with_52_scheduled_cells_checked += 1
        candidates: list[str] = []
        for symbol in current:
            presence = [value in complete_days and symbol in complete_days[value] for value in history_days]
            full = sum(presence)
            first = sum(presence[:26])
            second = sum(presence[26:])
            if full >= int(contract["minimum_candidate_completed_occurrences_full"]) and first >= int(contract["minimum_candidate_completed_occurrences_each_half"]) and second >= int(contract["minimum_candidate_completed_occurrences_each_half"]):
                candidates.append(symbol)
                candidate_history_counts[symbol] += 1
        if candidates:
            eligible.append(decision)
        decision += ONE_DAY_MS

    selected: list[int] = []
    previous: int | None = None
    cluster_ms = int(contract["cluster_connected_window_hours"]) * 3_600_000
    for decision in eligible:
        if previous is None or decision - previous > cluster_ms:
            selected.append(decision)
            previous = decision
    if len(selected) < int(contract["minimum_theoretical_eligible_episodes"]) or len(selected) < int(contract["paper_complete_is_episode_gate"]):
        raise QualificationFailure("pre-result sample ceiling Gate failed")
    years = Counter(datetime.fromtimestamp(value / 1000, tz=timezone.utc).year for value in selected)
    return {
        "orders": order_results,
        "counts": {
            "same_reader_task_count": len(tasks),
            "missing_archive_count": order_results[0]["missing_archive_count"],
            "complete_active_member_utc_days": len(complete_days),
            "incomplete_day_reasons": dict(sorted(incomplete_reasons.items())),
            "decisions_with_52_scheduled_same_weekday_cells_checked": decisions_with_52_scheduled_cells_checked,
            "eligible_calendar_decision_days": len(eligible),
            "maximum_independent_theoretical_24h_episodes": len(selected),
            "maximum_independent_episodes_by_year": {str(year): count for year, count in sorted(years.items())},
            "symbols_with_eligible_history": len(candidate_history_counts),
        },
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
    preflight = same_reader_preflight(raw_root, config)
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
        "source_orders": base_result["orders"],
        "same_reader_orders": preflight["orders"],
        "counts": {**base_result["counts"], **preflight["counts"]},
        "isolation": {
            "is_start": isolation["is_start"],
            "is_end_exclusive": isolation["is_end_exclusive"],
            "oos_opened": False,
            "oos_archive_access": isolation["oos_archive_access"],
            "oos_ohlcv_values_decoded": 0,
            "ohlcv_fields_decoded_during_preflight": 0,
            "common_component_rows_generated": 0,
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
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u12_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(args.raw_root, load_json(CONFIG))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-12 qualification PASS archives={result['counts']['archive_count']} ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
