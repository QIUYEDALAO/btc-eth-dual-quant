#!/usr/bin/env python3
"""Validate the frozen U-05 Paper protocol without reading outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/u05_cross_sectional_paper_protocol_v1.json"
DESIGN_PATH = ROOT / "config/u05_cross_sectional_design_scope_v1.json"
REPORT_PATH = ROOT / "reports/m1/U05_CROSS_SECTIONAL_PAPER_PROTOCOL.md"
EXPECTED_HASH = "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214"
EXPECTED_CANDIDATE = "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE"
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
        "breadth_event", "episode_clustering", "observation_contract",
        "cost_reference_roundtrip", "projection", "paper_gates",
        "research_leakage_prevention", "authorizations", "content_hash", "generated_utc",
    }
    if set(protocol) != expected_top:
        failures.append("protocol schema changed or gained a result/fixed-rule field")
    identity = {key: value for key, value in protocol.items() if key not in {"content_hash", "generated_utc"}}
    if protocol.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("protocol content identity changed")
    if protocol.get("protocol_id") != "U05-03-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE-PAPER-V1" or protocol.get("candidate_id") != EXPECTED_CANDIDATE:
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
    required_true = (
        "all_active_members_required", "current_and_prior_completed_4h_close_required",
        "four_complete_constituent_1h_bars_required",
    )
    required_false = ("replacement_member_allowed", "current_membership_backfill_allowed", "lifecycle_crossing_assumption_allowed")
    if universe.get("minimum_active_members") != 10 or universe.get("maximum_monthly_members") != 15:
        failures.append("active-member bounds changed")
    if any(universe.get(key) is not True for key in required_true) or any(universe.get(key) is not False for key in required_false):
        failures.append("point-in-time completeness or no-replacement rules changed")

    event = protocol.get("breadth_event", {})
    expected_event = {
        "breadth_integer_gate": "positive_member_count_times_5_greater_than_or_equal_to_active_member_count_times_4",
        "breadth_fraction_minimum": "0.80", "common_move": "cross_sectional_median_member_simple_return",
        "common_move_minimum": "0.0120", "all_active_members_in_denominator": True,
        "isolated_asset_move_allowed": False, "completed_information_only": True,
        "same_timestamp_representatives": 1,
    }
    if any(event.get(key) != value for key, value in expected_event.items()):
        failures.append("breadth event identity or threshold changed")

    cluster = protocol.get("episode_clustering", {})
    if cluster.get("connected_window_hours") != 24 or cluster.get("representative") != "first_event_only" or cluster.get("future_information_used") is not False:
        failures.append("24h episode definition changed")
    observation = protocol.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_decision_time" or observation.get("search_later_if_reference_missing") is not False:
        failures.append("next-open reference or missing-reference action changed")
    if observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("primary_horizon_hours") != 24:
        failures.append("observation horizons changed")
    if observation.get("basket_members") != "event_time_exact_active_members" or observation.get("complete_event_time_basket_required_through_each_horizon") is not True:
        failures.append("event-time basket completeness changed")
    if observation.get("fill_position_exit_or_equity_model") is not False or observation.get("formal_strategy_return") is not False:
        failures.append("fill, position, equity or formal return was enabled")

    if protocol.get("cost_reference_roundtrip") != {"base": "0.0030", "cost_x2": "0.0060", "stress_a": "0.0080", "stress_b": "0.0110"}:
        failures.append("cost references changed")
    expected_gates = {
        "complete_is_independent_episodes_minimum": 90,
        "projected_full_independent_episodes_minimum": 120,
        "projected_sealed_oos_independent_episodes_minimum": 30,
        "minimum_years_with_ten_complete_episodes": 3,
        "maximum_single_year_episode_share": "0.45",
        "maximum_single_calendar_quarter_episode_share": "0.25",
        "minimum_distinct_event_months": 24,
        "combined_median_24h_common_demand_close_displacement_minimum": "0.0180",
        "combined_median_24h_positive_member_fraction_minimum": "0.60",
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
        "positive × 5 >= active × 4", "Median 24h common-demand close displacement",
    ]
    return [f"protocol report missing: {item}" for item in required if item not in report]


def main() -> int:
    failures = validate(load(PROTOCOL_PATH)) + validate_report()
    if failures:
        print("u05_cross_sectional_paper_protocol_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u05_cross_sectional_paper_protocol_check PASS")
    print(f"protocol_hash={EXPECTED_HASH} next=exact_head_independent_review")
    print("data=no events=no paths=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
