#!/usr/bin/env python3
"""Validate the frozen U-07 Paper protocol without reading outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/u07_cross_sectional_paper_protocol_v1.json"
DESIGN_PATH = ROOT / "config/u07_cross_sectional_design_scope_v1.json"
REPORT_PATH = ROOT / "reports/m1/U07_CROSS_SECTIONAL_PAPER_PROTOCOL.md"
EXPECTED_HASH = "d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195"
EXPECTED_CANDIDATE = "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION"
EXPECTED_AUTHORIZATIONS = {
    "paper_protocol_frozen": True, "exact_head_independent_review": True,
    "data_qualification": False, "event_scan": False, "path_observation": False,
    "signals": False, "formal_returns": False, "fixed_rule_contract": False,
    "freqtrade_strategy_code": False, "backtesting": False, "oos": False,
    "api_trading": False, "execution_live": False, "m2": False,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(protocol: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_top = {
        "schema_version", "status", "protocol_id", "candidate_id", "hypothesis_sha256",
        "design_content_hash", "authority_bindings", "scope", "point_in_time_universe",
        "market_stress_event", "relative_resilience_candidate", "episode_clustering",
        "observation_contract", "cost_reference_roundtrip", "projection", "paper_gates",
        "research_leakage_prevention", "authorizations", "content_hash", "generated_utc",
    }
    if set(protocol) != expected_top:
        failures.append("protocol schema changed or gained a result/fixed-rule field")
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("protocol content identity changed")
    if protocol.get("protocol_id") != "U07-03-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-PAPER-V1" or protocol.get("candidate_id") != EXPECTED_CANDIDATE:
        failures.append("protocol or candidate identity changed")
    if protocol.get("status") != "frozen_before_result_pending_exact_head_review":
        failures.append("protocol status changed")
    design = load(DESIGN_PATH)
    if protocol.get("hypothesis_sha256") != design.get("hypothesis_sha256") or protocol.get("design_content_hash") != design.get("content_hash"):
        failures.append("design or hypothesis binding changed")
    if protocol.get("authority_bindings") != design.get("bindings"):
        failures.append("frozen authority bindings changed")
    expected_scope = {
        "exchange": "binance", "market": "spot_usdt", "direction": "long_cash_only",
        "is_start": "2020-01-01T00:00:00Z", "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_start": "2024-09-11T00:00:00Z", "oos_end_exclusive": "2026-07-01T00:00:00Z",
        "is_calendar_days": 1715, "oos_calendar_days": 658, "full_calendar_days": 2373,
        "signal_timeframe": "4h", "signal_alignment": "utc_blocks_ending_at_00_04_08_12_16_20",
        "path_timeframe": "5m", "oos_opened": False,
    }
    if protocol.get("scope") != expected_scope:
        failures.append("range, alignment, timeframe or sealed-OOS scope changed")
    universe = protocol.get("point_in_time_universe", {})
    if universe.get("minimum_active_members") != 10 or universe.get("maximum_monthly_members") != 15 or universe.get("all_active_members_required") is not True:
        failures.append("active-member bounds or completeness changed")
    for key in ("replacement_member_allowed", "current_membership_backfill_allowed", "lifecycle_crossing_assumption_allowed"):
        if universe.get(key) is not False:
            failures.append(f"point-in-time prohibition changed: {key}")
    stress = protocol.get("market_stress_event", {})
    expected_stress = {
        "common_move": "cross_sectional_median_member_simple_return",
        "common_move_maximum": "-0.0250",
        "negative_breadth_integer_gate": "negative_member_count_times_5_greater_than_or_equal_to_active_member_count_times_4",
        "negative_breadth_fraction_minimum": "0.80",
        "all_active_members_in_common_move_and_breadth": True,
        "completed_information_only": True,
    }
    if any(stress.get(key) != value for key, value in expected_stress.items()):
        failures.append("market-stress identity or threshold changed")
    resilience = protocol.get("relative_resilience_candidate", {})
    expected_resilience = {
        "relative_residual_minimum": "0.0200", "candidate_simple_return_minimum": "-0.0050",
        "same_timestamp_representatives": 1,
        "winner_order": ["relative_residual_descending", "member_simple_return_descending", "symbol_ascending"],
        "candidate_must_be_active_member": True, "post_outcome_selection_allowed": False,
    }
    if any(resilience.get(key) != value for key, value in expected_resilience.items()):
        failures.append("relative-resilience candidate identity or threshold changed")
    cluster = protocol.get("episode_clustering", {})
    if cluster.get("connected_window_hours") != 48 or cluster.get("representative") != "first_event_only" or cluster.get("future_information_used") is not False:
        failures.append("48h episode definition changed")
    observation = protocol.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_decision_time" or observation.get("search_later_if_reference_missing") is not False:
        failures.append("next-open reference or missing-reference action changed")
    if observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24, 48] or observation.get("primary_horizon_hours") != 24:
        failures.append("observation horizons changed")
    if observation.get("peer_members") != "event_time_exact_active_members_excluding_candidate" or observation.get("complete_candidate_and_all_event_time_peers_required_through_each_horizon") is not True:
        failures.append("event-time peer completeness changed")
    if observation.get("fill_position_exit_or_equity_model") is not False or observation.get("formal_strategy_return") is not False:
        failures.append("fill, position, equity or formal return was enabled")
    if protocol.get("cost_reference_roundtrip") != {"base": "0.0030", "cost_x2": "0.0060", "stress_a": "0.0080", "stress_b": "0.0110"}:
        failures.append("cost references changed")
    expected_gates = {
        "complete_is_independent_episodes_minimum": 60,
        "projected_full_independent_episodes_minimum": 80,
        "projected_sealed_oos_independent_episodes_minimum": 20,
        "minimum_years_with_eight_complete_episodes": 3,
        "maximum_single_year_episode_share": "0.45",
        "maximum_single_symbol_episode_share": "0.25",
        "minimum_distinct_event_symbols": 8,
        "minimum_distinct_event_months": 18,
        "combined_median_24h_relative_continuation_minimum": "0.0180",
        "combined_median_24h_candidate_absolute_close_displacement_minimum": "0.0180",
        "fraction_complete_episodes_with_positive_24h_relative_continuation_minimum": "0.60",
        "qualification_quarantine_lifecycle_or_order_mismatches_maximum": 0,
    }
    if protocol.get("paper_gates") != expected_gates:
        failures.append("Paper Gates changed")
    if protocol.get("projection", {}).get("may_read_oos_events_prices_or_counts") is not False:
        failures.append("sealed-OOS projection leakage was enabled")
    leakage = protocol.get("research_leakage_prevention", {})
    if not leakage or any(value is not False for key, value in leakage.items() if key != "protocol_change_after_result_creates_new_candidate") or leakage.get("protocol_change_after_result_creates_new_candidate") is not True:
        failures.append("research leakage prevention changed")
    if protocol.get("authorizations") != EXPECTED_AUTHORIZATIONS:
        failures.append("authorization matrix changed")
    return failures


def validate_report() -> list[str]:
    report = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "Public data read or event scan executed: no", "Path or return result accessed: no",
        "OOS opened: no", "Only an exact-head independent review may follow",
        "negative × 5 >= active × 4", "Median 24h relative continuation",
    ]
    return [f"protocol report missing: {item}" for item in required if item not in report]


def main() -> int:
    failures = validate(load(PROTOCOL_PATH)) + validate_report()
    if failures:
        print("u07_cross_sectional_paper_protocol_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u07_cross_sectional_paper_protocol_check PASS")
    print(f"protocol_hash={EXPECTED_HASH} next=exact_head_independent_review")
    print("data=no events=no paths=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
