#!/usr/bin/env python3
"""Run U-14 pre-result source qualification, structural preflight and synthetic complexity Gate."""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.u14_downside_rejection import AuctionPathRow, evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, build_membership, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG, ordered, read_open_times, required_tasks

CONFIG = ROOT / "config/u14_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u14_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u14_cross_sectional_paper_protocol_v1.json"
FOUR_HOURS_MS = 4 * 3_600_000


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def _rss_mib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024


def synthetic_rows(total: int, members: int) -> Iterator[AuctionPathRow]:
    symbols = tuple(f"S{index:02d}USDT" for index in range(members))
    for index in range(total):
        group, offset = divmod(index, members)
        decision = group * FOUR_HOURS_MS
        event_group = group % 100 == 0
        if event_group and offset == 0:
            yield AuctionPathRow(decision, symbols[offset], 100.0, 100.2, 98.0, 99.9, 100.0, (100.2, 100.4, 100.6, 101.0, 101.5, 102.0))
        elif event_group:
            yield AuctionPathRow(decision, symbols[offset], 100.0, 100.3, 98.5, 99.0, 100.0, (100.0, 100.0, 100.0, 100.0, 100.0, 100.0))
        else:
            yield AuctionPathRow(decision, symbols[offset], 100.0, 100.5, 99.5, 100.0, 100.0, (100.0, 100.0, 100.0, 100.0, 100.0, 100.0))


def run_complexity_benchmark(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["complexity_benchmark"]
    rows, members = int(contract["synthetic_fixture_rows"]), int(contract["synthetic_active_members"])
    passes = []
    expected_digest: str | None = None
    for pass_index in range(int(contract["benchmark_passes_required"])):
        started = time.perf_counter()
        result = evaluate_stream(synthetic_rows(rows, members), expected_members=members)
        elapsed = time.perf_counter() - started
        digest = identity_hash(result)
        peak = _rss_mib()
        if result["input_rows"] != rows or elapsed > float(contract["maximum_elapsed_seconds_per_pass"]) or peak > float(contract["maximum_peak_rss_mib"]):
            raise QualificationFailure(f"complexity benchmark Gate failed on pass {pass_index + 1}")
        if expected_digest is not None and digest != expected_digest:
            raise QualificationFailure("complexity benchmark output mismatch")
        expected_digest = digest
        passes.append({"pass": pass_index + 1, "fixture_rows": rows, "elapsed_seconds": f"{elapsed:.6f}", "peak_rss_mib": f"{peak:.3f}", "output_hash": digest})
    return {"status": "pass", "passes": passes, "same_code_path": contract["same_event_and_path_code_path"], "linear_streaming_no_decision_history_nested_scan": True, "market_outcomes_read": 0, "synthetic_output_hash": expected_digest}


def structural_preflight(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["structural_preflight"]
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
    decision = start + FOUR_HOURS_MS
    while decision <= end:
        block_start = decision - FOUR_HOURS_MS
        members = tuple(membership.get(month_for_ms(block_start), ()))
        if len(members) < int(contract["minimum_active_members"]):
            incomplete["membership_below_minimum"] += 1
        else:
            slots = range(block_start, decision, FIVE_MINUTES_MS)
            valid = True
            for symbol in members:
                values = primary.get(symbol, set())
                if any(opened not in values or (symbol, opened) in masked for opened in slots):
                    incomplete["4h_48_slot_or_mask_failure"] += 1
                    valid = False
                    break
            if valid:
                complete[decision] = members
        decision += FOUR_HOURS_MS

    eligible: list[int] = []
    horizon_steps = int(contract["primary_horizon_hours"]) // 4
    for decision, members in sorted(complete.items()):
        if decision < start or decision + int(contract["primary_horizon_hours"]) * 3_600_000 > end:
            continue
        if all(complete.get(decision + offset * FOUR_HOURS_MS) == members for offset in range(1, horizon_steps + 1)):
            eligible.append(decision)
    selected: list[int] = []
    previous: int | None = None
    cluster = int(contract["cluster_connected_window_hours"]) * 3_600_000
    for decision in eligible:
        if previous is None or decision - previous > cluster:
            selected.append(decision)
            previous = decision
    if len(selected) < int(contract["minimum_theoretical_eligible_24h_episodes"]):
        raise QualificationFailure(f"pre-result sample ceiling Gate failed: {len(selected)}")
    years = Counter(datetime.fromtimestamp(value / 1000, tz=timezone.utc).year for value in selected)
    return {"orders": order_results, "counts": {"same_reader_task_count": len(tasks), "missing_archive_count": order_results[0]["missing_archive_count"], "complete_active_member_4h_auctions": len(complete), "incomplete_auction_reasons": dict(sorted(incomplete.items())), "eligible_structural_decision_auctions": len(eligible), "maximum_independent_theoretical_24h_episodes": len(selected), "maximum_independent_episodes_by_year": {str(key): value for key, value in sorted(years.items())}}}


def qualify(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if canonical_hash(config) != config.get("content_hash"):
        raise QualificationFailure("contract hash drift")
    protocol = git_json(config["protocol_target_commit"], PROTOCOL_PATH)
    review = load_json(REVIEW)
    if protocol.get("content_hash") != config["protocol_content_hash"] or review.get("review_content_hash") != config["protocol_review_content_hash"] or review.get("verdict") != "approve" or review.get("remaining_critical_findings") or review.get("remaining_high_findings"):
        raise QualificationFailure("protocol/review binding drift")
    base_config = load_json(BASE_CONFIG)
    if base_config.get("content_hash") != config["base_v4_qualification_contract_hash"]:
        raise QualificationFailure("base qualification contract drift")
    benchmark = run_complexity_benchmark(config)
    base = qualify_base(raw_root=raw_root, config=base_config)
    preflight = structural_preflight(raw_root, config)
    if base["source_freeze_hash"] != config["authority_bindings"]["source_freeze_hash"] or base["v4_artifact_set_hash"] != config["authority_bindings"]["v4_artifact_set_hash"]:
        raise QualificationFailure("V4 authority drift")
    isolation = config["isolation_contract"]
    result = {"schema_version": 1, "qualification_id": config["qualification_id"], "status": "pass", "contract_content_hash": config["content_hash"], "protocol_target_commit": config["protocol_target_commit"], "protocol_content_hash": config["protocol_content_hash"], "protocol_review_content_hash": config["protocol_review_content_hash"], "source_freeze_hash": base["source_freeze_hash"], "v4_artifact_set_hash": base["v4_artifact_set_hash"], "manifest_hashes": base["manifest_hashes"], "source_orders": base["orders"], "same_reader_orders": preflight["orders"], "complexity_benchmark": benchmark, "counts": {**base["counts"], **preflight["counts"]}, "isolation": {"is_start": isolation["is_start"], "is_end_exclusive": isolation["is_end_exclusive"], "oos_opened": False, "oos_archive_access": isolation["oos_archive_access"], "oos_ohlcv_values_decoded": 0, "ohlcv_fields_decoded_during_preflight": 0, "common_state_rows_generated": 0, "candidate_rows_generated": 0, "event_rows_generated": 0, "path_rows_generated": 0, "return_rows_generated": 0}, "authorizations": {"one_sealed_is_paper_observation": True, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}, "network_accessed": False, "production_evidence_mutated": False}
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u14_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(args.raw_root, load_json(CONFIG))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-14 qualification PASS archives={result['counts']['archive_count']} ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
