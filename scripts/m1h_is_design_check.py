#!/usr/bin/env python3
"""Validate the M1H design-only contract and sealed candidate identity."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml


SCOPE_PATH = ROOT / "config/m1h_is_only_design_scope.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
REGISTRY_PATH = ROOT / "data_registry.yaml"
EXPECTED_CANDIDATE = "FUNDING-EXTREME-SPOT-CONTRARIAN"
EXPECTED_HASH = "f4caf96502aca9272d58faab20a6e2dc07eea4c69e49d9705272c00a46b814ed"
EXPECTED_FAILURES = [
    "negative_funding_correctly_reflects_persistent_adverse_information_instead_of_temporary_crowding",
    "funding_extremes_are_too_sparse_for_the_frozen_sample_budget",
    "funding_cadence_or_publication_semantics_are_incomplete_or_inconsistent",
    "spot_rebound_displacement_cannot_cover_the_frozen_stressed_roundtrip_cost",
    "btc_eth_events_are_one_correlated_market_stress_episode",
    "future_exit_family_cannot_be_represented_without_intrabar_or_gap_optimism",
]
EXPECTED_UNRESOLVED = [
    "negative_funding_extreme_definition",
    "funding_history_normalization_lookback",
    "interval_aware_signal_normalization",
    "post_settlement_spot_confirmation",
    "signal_and_execution_timeframe",
    "entry_bar_definition",
    "exit_family",
    "maximum_holding_horizon",
    "risk_invalidation_stop",
    "position_cap",
    "event_cluster_cooldown",
    "indicator_warmup",
]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return value


def validate_timing(funding_time: datetime, decision_time: datetime, entry_time: datetime) -> list[str]:
    values = (funding_time, decision_time, entry_time)
    if any(value.tzinfo is None or value.utcoffset() is None for value in values):
        return ["all M1H timestamps must be timezone-aware"]
    failures: list[str] = []
    if decision_time < funding_time:
        failures.append("settled funding must not be used before fundingTime")
    if entry_time <= funding_time:
        failures.append("entry must be strictly after fundingTime")
    if entry_time < decision_time:
        failures.append("entry must not precede the decision timestamp")
    return failures


def validate_scope(scope: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_identity = {
        "version": 1,
        "status": "economic_hypothesis_pass_paper_protocol_only",
        "candidate_id": EXPECTED_CANDIDATE,
        "hypothesis_sha256": EXPECTED_HASH,
    }
    for key, expected in expected_identity.items():
        if scope.get(key) != expected:
            failures.append(f"{key} must equal {expected!r}")

    research = scope.get("research_scope", {})
    expected_research = {
        "market": "binance_spot",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "direction": "spot_long_cash_only",
        "primary_signal_family": "settled_negative_funding_extreme",
        "funding_use": "public_derivatives_crowding_sentiment_input_only",
        "futures_position": False,
        "funding_cashflow_return": False,
        "two_leg_execution": False,
        "is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_start": "2024-09-11T00:00:00Z",
        "oos_opened": False,
    }
    if research != expected_research:
        failures.append("M1H spot-only scope, funding role, or sealed boundary changed")

    economic = scope.get("economic_hypothesis", {})
    if economic.get("family") != "settlement_aligned_negative_funding_crowding_then_spot_contrarian_observation":
        failures.append("M1H economic family changed")
    if economic.get("return_source") != "spot_price_appreciation_after_derivatives_short_crowding_unwinds":
        failures.append("M1H return source changed")
    if economic.get("failure_regimes") != EXPECTED_FAILURES:
        failures.append("M1H failure regimes changed")

    lineage = scope.get("data_lineage", {})
    primary = lineage.get("primary_observation", {})
    if primary != {
        "dataset": "funding_rate_history",
        "endpoint": "GET /fapi/v1/fundingRate",
        "fields": ["symbol", "fundingRate", "fundingTime", "markPrice"],
        "public_only": True,
        "available_no_earlier_than": "fundingTime",
    }:
        failures.append("primary public funding lineage changed")
    interval = lineage.get("interval_metadata", {})
    if interval != {
        "priority": [
            "fundingInfo.fundingIntervalHours",
            "multiple_premiumIndex.nextFundingTime_cadence",
            "adjacent_fundingRate.fundingTime",
        ],
        "single_premium_snapshot_is_complete_interval": False,
        "hardcoded_default_interval": False,
        "per_event_interval_required": True,
    }:
        failures.append("funding interval lineage or no-hardcode policy changed")
    if lineage.get("private_income_or_commission_used") is not False or lineage.get("network_access_in_design_review") is not False:
        failures.append("private data or network access entered the design review")

    if scope.get("time_semantics") != {
        "funding_event_visible_before_settlement": False,
        "decision_may_use_event_at_or_after_funding_time": True,
        "entry_must_be_strictly_after_funding_time": True,
        "same_timestamp_entry_prohibited": True,
        "entry_must_not_precede_decision": True,
        "future_bar_data_prohibited": True,
    }:
        failures.append("settlement visibility or next-entry timing changed")

    nondup = scope.get("non_duplication", {})
    required_nondup = {
        "price_only_panic_trigger_prohibited",
        "funding_cashflow_capture_prohibited",
        "perpetual_short_leg_prohibited",
        "basis_hedge_prohibited",
        "m1g_threshold_or_exit_reuse_prohibited",
        "m1b_entry_or_payback_rule_reuse_prohibited",
        "failed_candidate_outcome_derived_rule_prohibited",
    }
    if any(nondup.get(key) is not True for key in required_nondup):
        failures.append("M1B/M1G non-duplication guard changed")
    if nondup.get("m1h_primary_source") != "settled_public_funding_observation":
        failures.append("M1H primary signal source changed")

    representability = scope.get("execution_representability", {})
    if representability != {
        "freqtrade_remains_single_leg_return_authority": True,
        "external_single_leg_strategy_engine_prohibited": True,
        "exit_family_selected": False,
        "same_bar_double_touch_dependency_allowed": False,
        "optimistic_gap_fill_dependency_allowed": False,
        "zero_mismatch_fixture_required_before_implementation": True,
        "capability_review_required_before_fixed_rule_implementation": True,
    }:
        failures.append("execution representability Gate changed or an exit was selected")

    if scope.get("unresolved_until_later_gates") != EXPECTED_UNRESOLVED:
        failures.append("M1H rule decisions were selected or changed prematurely")
    if scope.get("authorization") != {
        "m1h_paper_protocol_design": True,
        "m1h_paper_diagnostic_run": False,
        "fixed_rule_contract": False,
        "strategy_code": False,
        "freqtrade_backtesting": False,
        "oos_access": False,
        "private_data": False,
        "dry_run": False,
        "live": False,
        "m2": False,
    }:
        failures.append("only M1H paper-protocol design may be authorized")
    return failures


def validate_ledger(path: Path = LEDGER_PATH) -> list[str]:
    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if item.get("id") == EXPECTED_CANDIDATE]
    if len(matches) != 1:
        return ["M1H candidate identity must appear exactly once"]
    candidate = matches[0]
    digest = hashlib.sha256(candidate.get("hypothesis", "").encode("utf-8")).hexdigest()
    failures: list[str] = []
    if digest != EXPECTED_HASH or candidate.get("sha256") != EXPECTED_HASH:
        failures.append("M1H registered hypothesis hash changed")
    if candidate.get("status") not in {"declared_unopened", "failed_feasibility"} or candidate.get("oos_opened") is not False:
        failures.append("M1H must remain pre-OOS or failed_feasibility with sealed OOS")
    return failures


def validate_registry(path: Path = REGISTRY_PATH) -> list[str]:
    registry = load_json(path)
    by_name = {item.get("name"): item for item in registry.get("datasets", []) if isinstance(item, dict)}
    failures: list[str] = []
    required = {
        "funding_rate_history": {"symbol", "fundingRate", "fundingTime", "markPrice"},
        "premium_index": {"lastFundingRate", "nextFundingTime", "time"},
        "funding_info": {"fundingIntervalHours"},
        "spot_klines": {"open_time", "open", "high", "low", "close", "close_time"},
    }
    for name, fields in required.items():
        item = by_name.get(name)
        if not item or item.get("enabled") is not True or not fields.issubset(set(item.get("fields", []))):
            failures.append(f"M0 public registry lineage incomplete for {name}")
    return failures


def main() -> int:
    failures = validate_scope(load_json(SCOPE_PATH)) + validate_ledger() + validate_registry()
    if failures:
        print("m1h_is_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1h_is_design_check PASS")
    print("authorized_next=paper_protocol_design events_evaluated=no returns=no oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
