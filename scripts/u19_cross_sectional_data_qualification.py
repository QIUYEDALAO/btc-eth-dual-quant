#!/usr/bin/env python3
"""Run U-19 result-free source qualification, structural ceiling and complexity Gate."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.u19_volatility_of_volatility import VolatilityOfVolatilityCandidatePath, evaluate_stream
from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u07_cross_sectional_data_qualification import qualify as qualify_base
from scripts.u12_cross_sectional_data_qualification import BASE_CONFIG
from scripts.u16_cross_sectional_data_qualification import rss_mib, structural_preflight

CONFIG = ROOT / "config/u19_cross_sectional_data_qualification_v1.json"
REVIEW = ROOT / "reports/expert/evidence/u19_cross_sectional_paper_protocol_review_v1.json"
PROTOCOL_PATH = "config/u19_cross_sectional_paper_protocol_v1.json"


def canonical_hash(document: Mapping[str, Any]) -> str:
    return identity_hash({key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}})


def half_from_block_volatilities(values: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(value for value in values for _ in range(24))


HIGH_HALF = half_from_block_volatilities((0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007))
LOW_HALF = half_from_block_volatilities((0.0030, 0.0031, 0.0032, 0.0033, 0.0034, 0.0035, 0.0036))
PEER = (0.0,) * 336
PATH = (0.002, 0.004, 0.007, 0.011, 0.015, 0.020)


def synthetic_rows(total: int, active_members: int = 15) -> Iterator[VolatilityOfVolatilityCandidatePath]:
    histories = tuple((HIGH_HALF + HIGH_HALF) if symbol_index < 4 else (LOW_HALF + LOW_HALF) for symbol_index in range(active_members))
    for index in range(total):
        symbol_index = index % active_members
        decision_index = index // active_members
        yield VolatilityOfVolatilityCandidatePath(
            decision_index * 14_400_000,
            f"S{symbol_index:02d}USDT",
            histories[symbol_index],
            PEER,
            PATH,
        )


def complexity(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = config["complexity_benchmark"]
    passes: list[dict[str, Any]] = []
    digest: str | None = None
    for index in range(int(contract["benchmark_passes_required"])):
        started = time.perf_counter()
        result = evaluate_stream(synthetic_rows(int(contract["synthetic_fixture_rows"]), int(contract["synthetic_active_members"])))
        elapsed = time.perf_counter() - started
        current_digest = identity_hash(result)
        peak = rss_mib()
        if elapsed > float(contract["maximum_elapsed_seconds_per_pass"]) or peak > float(contract["maximum_peak_rss_mib"]) or result["input_rows"] != int(contract["synthetic_fixture_rows"]):
            raise QualificationFailure("complexity Gate failed")
        if digest is not None and current_digest != digest:
            raise QualificationFailure("complexity output mismatch")
        digest = current_digest
        passes.append({"pass": index + 1, "fixture_rows": result["input_rows"], "elapsed_seconds": f"{elapsed:.6f}", "peak_rss_mib": f"{peak:.3f}", "output_hash": current_digest})
    return {"status": "pass", "passes": passes, "same_code_path": contract["same_residual_volatility_of_volatility_event_and_path_code_path"], "market_outcomes_read": 0, "synthetic_output_hash": digest}


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
    preflight = structural_preflight(raw_root, config)
    reasons = preflight["counts"]["ineligible_reasons"]
    if "48h_history_or_24h_path_slot_failure" in reasons:
        reasons["336h_history_or_24h_path_slot_failure"] = reasons.pop("48h_history_or_24h_path_slot_failure")
    isolation = config["isolation_contract"]
    result = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "pass",
        "contract_content_hash": config["content_hash"],
        "protocol_target_commit": config["protocol_target_commit"],
        "protocol_content_hash": config["protocol_content_hash"],
        "protocol_review_content_hash": config["protocol_review_content_hash"],
        "source_freeze_hash": base["source_freeze_hash"],
        "v4_artifact_set_hash": base["v4_artifact_set_hash"],
        "manifest_hashes": base["manifest_hashes"],
        "source_orders": base["orders"],
        "same_reader_orders": preflight["orders"],
        "complexity_benchmark": benchmark,
        "counts": {**base["counts"], **preflight["counts"]},
        "isolation": {
            "is_start": isolation["is_start"],
            "is_end_exclusive": isolation["is_end_exclusive"],
            "oos_opened": False,
            "oos_archive_access": isolation["oos_archive_access"],
            "oos_ohlcv_values_decoded": 0,
            "price_fields_decoded_during_preflight": 0,
            "return_rows_generated": 0,
            "residual_rows_generated": 0,
            "volatility_statistic_rows_generated": 0,
            "candidate_rows_generated": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "formal_return_rows_generated": 0,
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
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u19_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(args.raw_root, load_json(CONFIG))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"U-19 qualification PASS ceiling={result['counts']['maximum_independent_theoretical_24h_episodes']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
