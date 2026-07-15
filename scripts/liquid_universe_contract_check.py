#!/usr/bin/env python3
"""Validate the preregistered V2 universe contract and exclusion registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from btc_eth_dual_quant.data.liquid_universe import content_hash, validate_registry

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config/liquid_spot_universe_contract_v2.json"
REGISTRY_PATH = ROOT / "config/liquid_spot_asset_eligibility_v2.json"
EXPECTED_CONTRACT_HASH = "c66f68574d5b595d2ccde13250007fb2dd8dcb73c0dfad6bf9f5bf7fea687b33"
EXPECTED_REGISTRY_HASH = "2b23f64a92dec9b597c2f9399f4661cb62073ff54b90e851bc285626d31ad202"
CONFIRMED_GAPS_PATH = ROOT / "config/liquid_spot_confirmed_archive_gaps_v2.json"
EXPECTED_CONFIRMED_GAPS_HASH = "0e5d66a3968e0bb6ad89f81db9be8201b97f7e8fe8e257f648db0b5e2ba08f87"


def canonical_hash(data: dict[str, Any]) -> str:
    return content_hash(data)


def validate(data: dict[str, Any], registry: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    membership = data.get("membership", {})
    expected_membership = {
        "frequency": "monthly_utc",
        "activation": "first_day_00:00_utc",
        "target_size": 15,
        "ranking_window_complete_days": 90,
        "ranking_metric": "median_daily_quote_volume",
        "ranking_window_excludes_effective_month": True,
        "tie_break": "symbol_ascending",
        "minimum_complete_history_days": 365,
        "history_must_be_immediately_preceding_complete_days": True,
        "allow_fewer_than_target": True,
        "replacement_allowed": False,
    }
    if data.get("schema_version") != 2 or data.get("universe_id") != "LIQUID-SPOT-USDT-TOP15-V2":
        failures.append("V2 contract identity mismatch")
    if data.get("status") != "active_for_qualification_only" or data.get("supersedes") != "LIQUID-SPOT-USDT-TOP15-V1":
        failures.append("contract activation state mismatch")
    if data.get("market") != "binance_spot" or data.get("quote_asset") != "USDT":
        failures.append("market contract changed")
    if data.get("research_start") != "2020-01-01" or data.get("frozen_end_month") != "2026-06":
        failures.append("research range changed")
    if membership != expected_membership:
        failures.append("membership contract changed")
    expected_authority = {
        "daily_primary": "official_monthly_zip",
        "daily_supplement": "official_daily_zip_fill_missing_only",
        "daily_conflict_action": "blocked",
        "same_authority_duplicate_action": "blocked",
        "rest_role": "sampled_evidence_never_overwrite",
        "checksum_preference": "official_checksum_else_zip_crc_and_sha256",
        "detail_timeframe": "5m",
        "derived_timeframe": "1h",
        "complete_grid_required": True,
        "interpolation_allowed": False,
        "current_exchange_info_is_historical_authority": False,
    }
    if data.get("data_authority") != expected_authority:
        failures.append("data authority changed")
    expected_gap = {
        "default_classification": "unresolved",
        "exchange_wide_documented_or_synchronous_outage": "quarantine_global_window_all_members",
        "synchronous_outage_minimum_symbols": 2,
        "synchronous_outage_minimum_fraction": 0.8,
        "verified_archive_required_for_synchronous_classification": True,
        "symbol_specific_confirmed_archive_gap": "quarantine_entire_symbol_month_without_replacement",
        "symbol_specific_unexplained_gap": "blocked_unresolved",
        "processing_error": "blocked_until_fixed_and_revalidated",
        "manual_symbol_deletion_allowed": False,
        "synthetic_fill_or_interpolation_allowed": False,
    }
    if data.get("gap_handling_policy") != expected_gap:
        failures.append("gap policy changed")
    expected_roles = {
        "BTC": ["eligible_trade_asset", "market_regime_benchmark", "risk_benchmark"],
        "ETH": ["eligible_trade_asset", "market_regime_benchmark", "risk_benchmark"],
    }
    if data.get("asset_roles") != expected_roles:
        failures.append("asset roles changed")
    authorizations = data.get("authorizations", {})
    if authorizations.get("asset_data_qualification") is not True or any(
        value for key, value in authorizations.items() if key != "asset_data_qualification"
    ):
        failures.append("downstream authorization enabled")
    registry_ref = data.get("exclusion_registry", {})
    if registry_ref != {
        "path": "config/liquid_spot_asset_eligibility_v2.json",
        "registry_id": "LIQUID-SPOT-ASSET-ELIGIBILITY-V2",
        "registry_version": "2026-07-14.1",
        "registry_hash": EXPECTED_REGISTRY_HASH,
    }:
        failures.append("exclusion registry reference changed")
    if data.get("canonical_hash") != EXPECTED_CONTRACT_HASH or content_hash(data) != EXPECTED_CONTRACT_HASH:
        failures.append("preregistered contract hash mismatch")
    if registry is not None:
        failures.extend(validate_registry(registry))
        if registry.get("canonical_hash") != EXPECTED_REGISTRY_HASH:
            failures.append("preregistered registry hash mismatch")
        if data.get("exclusion_registry", {}).get("registry_hash") != registry.get("canonical_hash"):
            failures.append("contract/registry binding mismatch")
    return failures


def main() -> int:
    contract = json.loads(PATH.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    failures = validate(contract, registry)
    confirmed_gaps = json.loads(CONFIRMED_GAPS_PATH.read_text(encoding="utf-8"))
    if (
        confirmed_gaps.get("canonical_hash") != EXPECTED_CONFIRMED_GAPS_HASH
        or content_hash(confirmed_gaps) != EXPECTED_CONFIRMED_GAPS_HASH
    ):
        failures.append("preregistered confirmed-gap registry hash mismatch")
    if failures:
        print("liquid_universe_contract_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("liquid_universe_contract_check PASS")
    print(f"contract_hash={EXPECTED_CONTRACT_HASH}")
    print(f"registry_hash={EXPECTED_REGISTRY_HASH}")
    print(f"confirmed_gaps_hash={EXPECTED_CONFIRMED_GAPS_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
