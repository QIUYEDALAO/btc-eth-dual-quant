#!/usr/bin/env python3
"""Validate the frozen U-04 paper protocol without reading market outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/u04_cross_sectional_paper_protocol_v1.json"
DESIGN_PATH = ROOT / "config/u04_cross_sectional_design_scope_v1.json"
REPORT_PATH = ROOT / "reports/m1/U04_CROSS_SECTIONAL_PAPER_PROTOCOL.md"
EXPECTED_HASH = "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6"
EXPECTED_CANDIDATE = "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL"
EXPECTED_AUTHORIZATIONS = {
    "paper_protocol_frozen": True,
    "exact_head_independent_review": True,
    "data_qualification": False,
    "event_scan": False,
    "path_observation": False,
    "signals": False,
    "formal_returns": False,
    "fixed_rule_contract": False,
    "freqtrade_strategy_code": False,
    "backtesting": False,
    "oos": False,
    "api_trading": False,
    "execution_live": False,
    "m2": False,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def validate(protocol: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("protocol content identity changed")
    if protocol.get("protocol_id") != "U04-02-CROSS-SECTIONAL-RESIDUAL-REVERSAL-PAPER-V1":
        failures.append("protocol identity changed")
    if protocol.get("candidate_id") != EXPECTED_CANDIDATE:
        failures.append("candidate identity changed")
    if protocol.get("status") != "frozen_before_result_pending_exact_head_review":
        failures.append("protocol status changed")

    design = load(DESIGN_PATH)
    if protocol.get("hypothesis_sha256") != design.get("hypothesis_sha256"):
        failures.append("hypothesis binding changed")
    if protocol.get("design_content_hash") != design.get("content_hash"):
        failures.append("design binding changed")
    if protocol.get("authority_bindings") != design.get("bindings"):
        failures.append("frozen authority bindings changed")

    scope = protocol.get("scope", {})
    expected_scope = {
        "exchange": "binance", "market": "spot_usdt", "direction": "long_cash_only",
        "is_start": "2020-01-01T00:00:00Z", "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_start": "2024-09-11T00:00:00Z", "oos_end_exclusive": "2026-07-01T00:00:00Z",
        "is_calendar_days": 1715, "oos_calendar_days": 658, "full_calendar_days": 2373,
        "signal_timeframe": "1h", "path_timeframe": "5m", "oos_opened": False,
    }
    if scope != expected_scope:
        failures.append("range, timeframe or sealed-OOS scope changed")

    universe = protocol.get("point_in_time_universe", {})
    if universe.get("minimum_active_members") != 10 or universe.get("maximum_monthly_members") != 15:
        failures.append("active-member bounds changed")
    required_true = ("all_active_members_required", "current_and_previous_completed_1h_close_required")
    required_false = ("replacement_member_allowed", "current_membership_backfill_allowed", "lifecycle_crossing_assumption_allowed")
    if any(universe.get(key) is not True for key in required_true) or any(universe.get(key) is not False for key in required_false):
        failures.append("point-in-time completeness or no-replacement rules changed")

    event = protocol.get("residual_event", {})
    expected_event = {
        "common_component": "cross_sectional_median_member_log_return",
        "robust_scale": "1.4826_times_mad",
        "standardized_residual_maximum": "-3.0",
        "relative_simple_return_maximum": "-0.0180",
        "same_timestamp_representatives": 1,
    }
    if any(event.get(key) != value for key, value in expected_event.items()):
        failures.append("median/MAD event threshold or uniqueness changed")
    if event.get("absolute_decline_alone_allowed") is not False or event.get("completed_information_only") is not True:
        failures.append("relative-only or completed-information semantics changed")

    cluster = protocol.get("episode_clustering", {})
    if cluster.get("connected_window_hours") != 24 or cluster.get("representative") != "first_event_only" or cluster.get("future_information_used") is not False:
        failures.append("global 24h episode definition changed")

    observation = protocol.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_decision_time":
        failures.append("next-open reference changed")
    if observation.get("search_later_if_reference_missing") is not False:
        failures.append("later reference search was enabled")
    if observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("primary_horizon_hours") != 24:
        failures.append("observation horizons changed")
    if observation.get("fill_position_exit_or_equity_model") is not False or observation.get("formal_strategy_return") is not False:
        failures.append("position, fill, equity or formal return model was enabled")

    if protocol.get("cost_reference_roundtrip") != {
        "base": "0.0030", "cost_x2": "0.0060", "stress_a": "0.0080", "stress_b": "0.0110"
    }:
        failures.append("cost references changed")
    gates = protocol.get("paper_gates", {})
    expected_gates = {
        "complete_is_independent_episodes_minimum": 90,
        "projected_full_independent_episodes_minimum": 120,
        "projected_sealed_oos_independent_episodes_minimum": 30,
        "minimum_years_with_ten_complete_episodes": 3,
        "maximum_single_year_episode_share": "0.45",
        "maximum_single_symbol_episode_share": "0.25",
        "minimum_distinct_event_symbols": 8,
        "combined_median_24h_relative_recovery_minimum": "0.0180",
        "combined_median_24h_absolute_close_displacement_minimum": "0.0180",
        "qualification_quarantine_lifecycle_or_order_mismatches_maximum": 0,
    }
    if gates != expected_gates:
        failures.append("paper Gates changed")
    if protocol.get("projection", {}).get("may_read_oos_events_prices_or_counts") is not False:
        failures.append("sealed-OOS projection leakage was enabled")
    if protocol.get("authorizations") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    return failures


def validate_report() -> list[str]:
    report = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Public data read or event scan executed: no", "Path or return result accessed: no",
        "OOS opened: no", "Only an exact-head independent review may follow",
        "1.4826 × MAD", "Combined median 24h relative recovery and absolute close displacement",
    ]
    return [f"protocol report missing: {marker}" for marker in required if marker not in report]


def main() -> int:
    failures = validate(load(PROTOCOL_PATH)) + validate_report()
    if failures:
        print("u04_cross_sectional_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u04_cross_sectional_paper_protocol_check PASS")
    print(f"protocol_hash={EXPECTED_HASH} next=exact_head_independent_review")
    print("data=no events=no paths=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
