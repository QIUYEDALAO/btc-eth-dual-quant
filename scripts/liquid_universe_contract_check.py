#!/usr/bin/env python3
"""Validate the immutable ADR-0011 point-in-time universe contract."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config/liquid_spot_universe_contract.json"

def canonical_hash(data: dict) -> str:
    clean = {k: v for k, v in data.items() if k != "canonical_hash"}
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def validate(data: dict) -> list[str]:
    failures = []
    m = data.get("membership", {})
    expected = {
        "frequency": "monthly_utc", "activation": "first_day_00:00_utc",
        "target_size": 15, "ranking_window_complete_days": 90,
        "ranking_metric": "median_daily_quote_volume",
        "ranking_window_excludes_effective_month": True,
        "tie_break": "symbol_ascending", "minimum_complete_history_days": 365,
        "allow_fewer_than_target": True,
    }
    if data.get("universe_id") != "LIQUID-SPOT-USDT-TOP15-V1" or m != expected:
        failures.append("membership contract changed")
    authority = data.get("data_authority", {})
    if authority.get("daily_primary") != "official_monthly_zip" or authority.get("daily_supplement") != "official_daily_zip_fill_missing_only": failures.append("ZIP authority changed")
    if authority.get("rest_role") != "sampled_evidence_never_overwrite" or authority.get("interpolation_allowed") is not False: failures.append("evidence or interpolation policy changed")
    if authority.get("current_exchange_info_is_historical_authority") is not False: failures.append("current exchangeInfo cannot be historical authority")
    policy = data.get("gap_handling_policy", {})
    expected_policy = {
        "exchange_wide_documented_or_synchronous_outage": "quarantine_isolate",
        "synchronous_outage_minimum_symbols": 2,
        "synchronous_outage_minimum_fraction": 0.8,
        "symbol_specific_confirmed_archive_gap": "quarantine_isolate_symbol_month_without_replacement",
        "symbol_specific_unexplained_gap": "blocked_unresolved",
        "processing_error": "blocked_until_fixed_and_revalidated",
        "manual_symbol_deletion_allowed": False,
        "synthetic_fill_or_interpolation_allowed": False,
    }
    if policy != expected_policy: failures.append("gap handling policy changed")
    categories = set(data.get("exclusions", {}).get("categories", []))
    if categories != {"stable_value", "fiat_pegged", "leveraged_token", "wrapped_or_pegged_duplicate"}: failures.append("exclusion categories changed")
    auth = data.get("authorizations", {})
    if auth.get("asset_data_qualification") is not True or any(v for k, v in auth.items() if k != "asset_data_qualification"): failures.append("downstream authorization enabled")
    if data.get("canonical_hash") != canonical_hash(data): failures.append("canonical hash mismatch")
    return failures

def main() -> int:
    failures = validate(json.loads(PATH.read_text()))
    if failures:
        print("liquid_universe_contract_check FAIL")
        for item in failures: print(f"- {item}")
        return 1
    print("liquid_universe_contract_check PASS")
    return 0
if __name__ == "__main__": raise SystemExit(main())
