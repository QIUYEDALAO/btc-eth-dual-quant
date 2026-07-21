#!/usr/bin/env python3
"""Run U-17 result-free source qualification, structural ceiling and complexity Gate."""
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

from btc_eth_dual_quant.data.u17_liquidity_risk import LiquidityCandidatePath, evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, build_membership, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG, ordered, read_open_times, required_tasks

CONFIG = ROOT / "config/u17_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u17_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u17_cross_sectional_paper_protocol_v1.json"
DAY_MS = 86_400_000


class SampleCeilingFailure(QualificationFailure):
    def __init__(self, preflight: Mapping[str, Any]) -> None:
        self.preflight = dict(preflight)
        super().__init__(f"sample ceiling Gate failed: {preflight['counts']['maximum_independent_theoretical_28d_episodes']}")


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def rss_mib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024


def synthetic_rows(total: int) -> Iterator[LiquidityCandidatePath]:
    symbols = tuple(f"S{index:02d}USDT" for index in range(15))
    volumes = tuple(float(index + 1) for index in range(15))
    history = tuple(volumes for _ in range(28))
    path = (0.001, 0.003, 0.007, 0.012, 0.020)
    remaining = total
    index = 0
    while remaining:
        logical_rows = min(420, remaining)
        yield LiquidityCandidatePath(
            decision_ms=index * DAY_MS,
            candidate_symbol=symbols[0] if index % 100 == 0 else symbols[-1],
            symbols=symbols,
            daily_quote_volumes=history,
            path_displacements=path,
            logical_input_rows=logical_rows,
        )
        remaining -= logical_rows
        index += 1


def complexity(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["complexity_benchmark"]
    passes: list[dict[str, Any]] = []
    digest: str | None = None
    for index in range(int(contract["benchmark_passes_required"])):
        started = time.perf_counter()
        result = evaluate_stream(synthetic_rows(int(contract["synthetic_fixture_rows"])))
        elapsed = time.perf_counter() - started
        current_digest = identity_hash(result)
        peak = rss_mib()
        if elapsed > float(contract["maximum_elapsed_seconds_per_pass"]) or peak > float(contract["maximum_peak_rss_mib"]) or result["input_rows"] != int(contract["synthetic_fixture_rows"]):
            raise QualificationFailure("complexity Gate failed")
        if digest is not None and current_digest != digest:
            raise QualificationFailure("complexity output mismatch")
        digest = current_digest
        passes.append({"pass": index + 1, "fixture_rows": result["input_rows"], "elapsed_seconds": f"{elapsed:.6f}", "peak_rss_mib": f"{peak:.3f}", "output_hash": current_digest})
    return {"status": "pass", "passes": passes, "same_code_path": contract["same_history_rank_event_and_path_code_path"], "market_outcomes_read": 0, "synthetic_output_hash": digest}


def structural_preflight(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["structural_preflight"]
    start, end = utc_ms(contract["is_start"]), utc_ms(contract["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    tasks = required_tasks(membership, end)
    orders: list[dict[str, Any]] = []
    primary: dict[str, set[int]] | None = None
    for order_name in contract["traversal_orders"]:
        available: defaultdict[str, set[int]] = defaultdict(set)
        missing: list[str] = []
        for month, symbol in ordered(tasks, order_name, int(contract["deterministic_shuffle_seed"])):
            rows = read_open_times(raw_root, symbol, month, end)
            if rows is None:
                missing.append(f"{symbol}:{month}")
            else:
                available[symbol].update(rows)
        canonical = {"available_open_time_hashes": {symbol: identity_hash(sorted(values)) for symbol, values in sorted(available.items())}, "missing_archives": sorted(missing)}
        orders.append({"order": order_name, "content_identity_hash": identity_hash(canonical), "task_count": len(tasks), "missing_archive_count": len(missing)})
        if primary is None:
            primary = dict(available)
    if len({row["content_identity_hash"] for row in orders}) != 1:
        raise QualificationFailure("same-reader order mismatch")
    assert primary is not None
    history_ms = int(contract["history_days"]) * DAY_MS
    future_ms = int(contract["future_path_days"]) * DAY_MS
    step = int(contract["decision_step_days"]) * DAY_MS
    eligible: list[int] = []
    reasons: Counter[str] = Counter()
    decision = start
    while decision + future_ms <= end:
        members = tuple(membership.get(month_for_ms(decision - 1), ()))
        if len(members) < int(contract["minimum_active_members"]):
            reasons["membership_below_minimum"] += 1
            decision += step
            continue
        membership_constant = all(tuple(membership.get(month_for_ms(point), ())) == members for point in range(decision - history_ms, decision + future_ms, DAY_MS))
        if not membership_constant:
            reasons["history_or_future_membership_change"] += 1
            decision += step
            continue
        valid = True
        for symbol in members:
            values = primary.get(symbol, set())
            for opened in range(decision - history_ms, decision + future_ms, FIVE_MINUTES_MS):
                if opened not in values or (symbol, opened) in masked:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            eligible.append(decision)
        else:
            reasons["28d_history_or_28d_path_slot_failure"] += 1
        decision += step
    selected: list[int] = []
    previous: int | None = None
    cluster = int(contract["cluster_connected_window_days"]) * DAY_MS
    for value in eligible:
        if previous is None or value - previous > cluster:
            selected.append(value)
            previous = value
    years = Counter(datetime.fromtimestamp(value / 1000, tz=timezone.utc).year for value in selected)
    preflight = {"orders": orders, "counts": {"same_reader_task_count": len(tasks), "missing_archive_count": orders[0]["missing_archive_count"], "eligible_structural_decisions": len(eligible), "maximum_independent_theoretical_28d_episodes": len(selected), "ineligible_reasons": dict(sorted(reasons.items())), "maximum_independent_episodes_by_year": {str(key): value for key, value in sorted(years.items())}}}
    if len(selected) < int(contract["minimum_theoretical_eligible_28d_episodes"]):
        raise SampleCeilingFailure(preflight)
    return preflight


def qualify(raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if canonical_hash(config) != config.get("content_hash"):
        raise QualificationFailure("contract drift")
    protocol = git_json(config["protocol_target_commit"], PROTOCOL_PATH)
    review = load_json(REVIEW)
    if protocol.get("content_hash") != config["protocol_content_hash"] or review.get("review_content_hash") != config["protocol_review_content_hash"] or review.get("verdict") != "approve" or review.get("critical_findings") or review.get("high_findings"):
        raise QualificationFailure("protocol/review drift")
    base_config = load_json(BASE_CONFIG)
    if base_config.get("content_hash") != config["base_v4_qualification_contract_hash"]:
        raise QualificationFailure("base contract drift")
    benchmark = complexity(config)
    base = qualify_base(raw_root=raw_root, config=base_config)
    isolation = config["isolation_contract"]
    try:
        preflight = structural_preflight(raw_root, config)
    except SampleCeilingFailure as failure:
        result = {"schema_version": 1, "qualification_id": config["qualification_id"], "status": "failed_pre_result_sample_ceiling", "contract_content_hash": config["content_hash"], "protocol_target_commit": config["protocol_target_commit"], "protocol_content_hash": config["protocol_content_hash"], "protocol_review_content_hash": config["protocol_review_content_hash"], "source_freeze_hash": base["source_freeze_hash"], "v4_artifact_set_hash": base["v4_artifact_set_hash"], "manifest_hashes": base["manifest_hashes"], "source_orders": base["orders"], "same_reader_orders": failure.preflight["orders"], "complexity_benchmark": benchmark, "counts": {**base["counts"], **failure.preflight["counts"]}, "failed_gate": {"name": "minimum_theoretical_eligible_28d_episodes", "required": int(config["structural_preflight"]["minimum_theoretical_eligible_28d_episodes"]), "observed": failure.preflight["counts"]["maximum_independent_theoretical_28d_episodes"]}, "isolation": {"is_start": isolation["is_start"], "is_end_exclusive": isolation["is_end_exclusive"], "oos_opened": False, "oos_archive_access": isolation["oos_archive_access"], "oos_ohlcv_values_decoded": 0, "quote_volume_fields_decoded_during_preflight": 0, "price_fields_decoded_during_preflight": 0, "liquidity_rank_rows_generated": 0, "candidate_rows_generated": 0, "event_rows_generated": 0, "path_rows_generated": 0, "return_rows_generated": 0}, "decision": {"candidate_closed": True, "paper_observation_authorized": False, "second_qualification_attempt_for_admission_authorized": False}, "authorizations": {"one_sealed_is_paper_observation": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}, "network_accessed": False, "production_evidence_mutated": False}
        result["qualification_content_hash"] = identity_hash(result)
        return result
    result = {"schema_version": 1, "qualification_id": config["qualification_id"], "status": "pass", "contract_content_hash": config["content_hash"], "protocol_target_commit": config["protocol_target_commit"], "protocol_content_hash": config["protocol_content_hash"], "protocol_review_content_hash": config["protocol_review_content_hash"], "source_freeze_hash": base["source_freeze_hash"], "v4_artifact_set_hash": base["v4_artifact_set_hash"], "manifest_hashes": base["manifest_hashes"], "source_orders": base["orders"], "same_reader_orders": preflight["orders"], "complexity_benchmark": benchmark, "counts": {**base["counts"], **preflight["counts"]}, "isolation": {"is_start": isolation["is_start"], "is_end_exclusive": isolation["is_end_exclusive"], "oos_opened": False, "oos_archive_access": isolation["oos_archive_access"], "oos_ohlcv_values_decoded": 0, "quote_volume_fields_decoded_during_preflight": 0, "price_fields_decoded_during_preflight": 0, "liquidity_rank_rows_generated": 0, "candidate_rows_generated": 0, "event_rows_generated": 0, "path_rows_generated": 0, "return_rows_generated": 0}, "authorizations": {"one_sealed_is_paper_observation": True, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}, "network_accessed": False, "production_evidence_mutated": False}
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u17_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(args.raw_root, load_json(CONFIG))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-17 qualification {result['status']} ceiling={result['counts']['maximum_independent_theoretical_28d_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
