#!/usr/bin/env python3
"""Validate the frozen M1H paper protocol without reading market outcomes."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml


PROTOCOL_PATH = ROOT / "config/m1h_is_paper_protocol.json"
REPORT_PATH = ROOT / "reports/m1/M1H_PAPER_PROTOCOL.md"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
EXPECTED_CANDIDATE = "FUNDING-EXTREME-SPOT-CONTRARIAN"
EXPECTED_HASH = "f4caf96502aca9272d58faab20a6e2dc07eea4c69e49d9705272c00a46b814ed"


def load(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("M1H protocol must be a mapping")
    return value


def expected_reference_time(funding_time: datetime) -> datetime:
    if funding_time.tzinfo is None or funding_time.utcoffset() is None:
        raise ValueError("fundingTime must be timezone-aware")
    utc_value = funding_time.astimezone(timezone.utc)
    epoch = int(utc_value.timestamp())
    return datetime.fromtimestamp(((epoch // 300) + 1) * 300, tz=timezone.utc)


def validate_timing(funding_time: datetime, decision_time: datetime, reference_time: datetime) -> list[str]:
    if any(value.tzinfo is None or value.utcoffset() is None for value in (funding_time, decision_time, reference_time)):
        return ["all protocol timestamps must be timezone-aware"]
    failures: list[str] = []
    if decision_time < funding_time:
        failures.append("decision must not precede fundingTime")
    if reference_time != expected_reference_time(funding_time):
        failures.append("reference must be the first expected 5m open strictly after fundingTime")
    if reference_time <= funding_time:
        failures.append("same-timestamp or earlier reference is prohibited")
    return failures


def validate(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {
        "version": 1,
        "protocol_id": "M1H-02-FUNDING-EXTREME-SPOT-PAPER-V1",
        "status": "frozen_before_result",
        "candidate_id": EXPECTED_CANDIDATE,
        "hypothesis_sha256": EXPECTED_HASH,
    }
    for key, expected in identity.items():
        if protocol.get(key) != expected:
            failures.append(f"{key} changed")

    if protocol.get("scope") != {
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "market": "binance_spot",
        "position_family": "spot_long_cash_only",
        "is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_opened": False,
    }:
        failures.append("spot-only scope or sealed boundary changed")

    if protocol.get("funding_extreme_event") != {
        "dataset": "funding_rate_history",
        "settled_observations_only": True,
        "funding_rate_must_be_negative": True,
        "annualization": "fundingRate*(365*24/event_interval_hours)",
        "event_interval_source": "M0_per_event_inference_chain",
        "hardcoded_default_interval_allowed": False,
        "history_window_utc_days": 365,
        "history_excludes_current_event": True,
        "lower_tail_percentile": "0.05",
        "percentile_interpolation": "linear",
        "complete_interval_history_required": True,
        "same_symbol_cluster_hours": 24,
        "same_symbol_cluster_representative": "first_event_only",
        "cross_symbol_episode_hours": 24,
        "cross_symbol_episode_use": "sample_budget_only_keep_symbol_diagnostics",
        "spot_price_trigger_allowed": False,
        "classification": "frozen_event_identification_not_strategy_entry_or_optimization_parameter",
    }:
        failures.append("funding extreme event protocol changed")

    if protocol.get("timing_contract") != {
        "funding_visible_before_funding_time": False,
        "decision_not_before_funding_time": True,
        "reference_bar_timeframe": "5m",
        "reference_bar": "first_expected_canonical_open_strictly_after_fundingTime",
        "same_timestamp_bar_allowed": False,
        "search_later_for_missing_reference_allowed": False,
        "future_data_allowed": False,
        "missing_quarantine_or_is_boundary_crossing": "right_censored",
    }:
        failures.append("funding timing contract changed")

    if protocol.get("observation_contract") != {
        "purpose": "market_reaction_path_only_not_strategy_holding_or_exit",
        "fixed_horizon_hours": [1, 2, 4, 8, 12, 24],
        "horizon_optimization_allowed": False,
        "path_timeframe": "5m",
        "required_diagnostics": [
            "median_24h_mfe",
            "median_24h_close_displacement",
            "mae_distribution",
            "recovery_time_distribution",
        ],
        "mae_distribution_fields": ["minimum", "p05", "median", "p95"],
        "recovery_definition": "first_completed_5m_close_at_or_above_reference_open",
        "recovery_censor_hours": 24,
        "recovery_distribution_fields": ["recovered_share", "recovered_median", "recovered_p90", "unrecovered_count"],
        "formal_strategy_return": False,
        "fill_position_or_exit_model": False,
    }:
        failures.append("market-reaction observation contract changed")

    if protocol.get("paper_gates") != {
        "projected_full_independent_episodes_minimum": 120,
        "projected_sealed_oos_episodes_minimum": 30,
        "projection_may_read_oos_events_or_prices": False,
        "combined_median_24h_close_displacement_minimum": "0.0180",
        "each_symbol_complete_events_minimum": 20,
        "each_symbol_median_24h_close_displacement_minimum": "0.0180",
        "minimum_years_with_ten_independent_episodes": 3,
        "maximum_single_year_episode_share": "0.45",
        "invalid_lineage_interval_quarantine_or_unrewarmed_events_maximum": 0,
        "mfe_standalone_gate": False,
        "mfe_may_override_close_displacement_failure": False,
        "mae_and_recovery_are_mandatory_diagnostics_without_hard_gate": True,
    }:
        failures.append("paper Gates changed or MFE became a standalone Gate")

    leakage = protocol.get("research_leakage_prevention", {})
    expected_leakage = {
        "adjust_percentile_from_event_count": False,
        "adjust_event_from_path_diagnostics": False,
        "delete_years_from_performance": False,
        "change_definition_by_symbol_results": False,
        "change_horizons_from_feasibility": False,
        "reselect_interval_from_results": False,
        "add_spot_confirmation_from_results": False,
        "change_clustering_or_censoring_from_results": False,
        "protocol_change_requires_new_adr_and_new_protocol_identity": True,
    }
    if leakage != expected_leakage:
        failures.append("research leakage prevention changed")

    if protocol.get("non_duplication") != {
        "primary_signal": "settled_funding_tail_observation",
        "funding_use": "sentiment_signal_only",
        "spot_ohlc_may_trigger_event": False,
        "funding_carry_allowed": False,
        "funding_income_allowed": False,
        "basis_trade_allowed": False,
        "hedge_allowed": False,
        "perpetual_short_allowed": False,
        "two_leg_logic_allowed": False,
        "m1g_price_panic_decline_close_location_or_range_reuse_allowed": False,
    }:
        failures.append("M1B/M1G non-duplication contract changed")

    if protocol.get("execution_representability") != {
        "lifecycle_selected": False,
        "freqtrade_capability_review_required_before_implementation": True,
        "same_bar_optimism_allowed": False,
        "optimistic_gap_fill_allowed": False,
        "zero_mismatch_fixture_required": True,
        "freqtrade_single_leg_return_authority": True,
        "second_python_strategy_engine_allowed": False,
    }:
        failures.append("execution representability boundary changed")

    if protocol.get("next_task_data_qualification") != {
        "same_task_before_paper_feasibility": True,
        "allowed_checks": [
            "lineage", "funding_timestamp", "per_event_funding_interval",
            "settlement_availability", "missing_duplicate", "timezone", "data_completeness",
        ],
        "event_scan_allowed": False,
        "event_count_allowed": False,
        "path_diagnostics_allowed": False,
        "returns_allowed": False,
        "feasibility_decision_allowed": False,
    }:
        failures.append("next-task data qualification boundary changed")

    if protocol.get("authorization") != {
        "paper_protocol_frozen": True,
        "funding_data_qualification": False,
        "paper_feasibility": False,
        "event_scan": False,
        "formal_strategy_returns": False,
        "fixed_rule_contract": False,
        "strategy_code": False,
        "freqtrade_backtesting": False,
        "is_validation": False,
        "oos_access": False,
        "api_or_trading": False,
        "m2": False,
    }:
        failures.append("protocol task authorization changed")
    return failures


def validate_ledger(path: Path = LEDGER_PATH) -> list[str]:
    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if item.get("id") == EXPECTED_CANDIDATE]
    if len(matches) != 1:
        return ["M1H candidate identity must appear exactly once"]
    item = matches[0]
    digest = hashlib.sha256(str(item.get("hypothesis", "")).encode("utf-8")).hexdigest()
    failures: list[str] = []
    if digest != EXPECTED_HASH or item.get("sha256") != EXPECTED_HASH:
        failures.append("M1H hypothesis hash changed")
    if item.get("status") != "declared_unopened" or item.get("oos_opened") is not False:
        failures.append("M1H must remain declared_unopened with sealed OOS")
    return failures


def validate_report(path: Path = REPORT_PATH) -> list[str]:
    text = path.read_text(encoding="utf-8")
    required = [
        "- Status: frozen_before_result",
        "- Trial status: declared_unopened",
        "- Event scan executed: no",
        "- Formal strategy returns computed: no",
        "- Paper feasibility authorized: no",
        "- OOS opened: no",
        "MFE has no standalone pass Gate",
        "Every protocol change requires a new ADR",
    ]
    return [f"report missing required boundary: {item}" for item in required if item not in text]


def main() -> int:
    failures = validate(load()) + validate_ledger() + validate_report()
    if failures:
        print("m1h_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1h_paper_protocol_check PASS")
    print("protocol_frozen=yes event_scan=no returns=no oos_opened=no authorized_next=none_until_merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
