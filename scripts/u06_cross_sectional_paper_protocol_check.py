#!/usr/bin/env python3
"""Validate the frozen U-06 Paper protocol without reading outcomes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/u06_cross_sectional_paper_protocol_v1.json"
DESIGN_PATH = ROOT / "config/u06_cross_sectional_design_scope_v1.json"
REPORT_PATH = ROOT / "reports/m1/U06_CROSS_SECTIONAL_PAPER_PROTOCOL.md"
EXPECTED_HASH = "7b53860efa2a5c52d727f1d4d4694ddf39ff34517dfde6aaf4b6abe31f35f289"
EXPECTED_AUTH = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}


def load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8"))
def canonical_hash(value: Any) -> str: return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(p: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_top = {"schema_version", "status", "protocol_id", "candidate_id", "hypothesis_sha256", "design_content_hash", "authority_bindings", "scope", "point_in_time_universe", "volume_share_event", "episode_clustering", "observation_contract", "cost_reference_roundtrip", "projection", "paper_gates", "research_leakage_prevention", "authorizations", "content_hash", "generated_utc"}
    if set(p) != expected_top: failures.append("protocol schema changed or gained a result/fixed-rule field")
    identity = {k: v for k, v in p.items() if k not in {"content_hash", "generated_utc"}}
    if p.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH: failures.append("protocol content identity changed")
    design = load(DESIGN_PATH)
    if p.get("candidate_id") != "U06-CROSS-SECTIONAL-VOLUME-SHARE-ABSORPTION-REPRICING" or p.get("hypothesis_sha256") != design.get("hypothesis_sha256") or p.get("design_content_hash") != design.get("content_hash") or p.get("authority_bindings") != design.get("bindings"): failures.append("candidate, design or authority binding changed")
    scope = p.get("scope", {})
    if scope.get("signal_timeframe") != "1d" or scope.get("path_timeframe") != "5m" or scope.get("is_end_exclusive") != "2024-09-11T00:00:00Z" or scope.get("oos_opened") is not False: failures.append("timeframe, boundary or OOS seal changed")
    universe = p.get("point_in_time_universe", {})
    if universe.get("minimum_active_members") != 10 or universe.get("all_active_members_required_for_each_day") is not True or any(universe.get(k) is not False for k in ("replacement_member_allowed", "current_membership_backfill_allowed", "lifecycle_crossing_assumption_allowed")): failures.append("point-in-time universe guard changed")
    event = p.get("volume_share_event", {})
    expected_event = {"current_window_days": 1, "baseline_days": 30, "baseline_excludes_current_day": True, "share_ratio_minimum": "2.00", "absolute_quote_volume_ratio_minimum": "1.50", "relative_price_response_minimum_inclusive": "-0.0100", "relative_price_response_maximum_inclusive": "0.0100", "same_day_representatives": 1, "completed_information_only": True}
    if any(event.get(k) != v for k, v in expected_event.items()): failures.append("event baseline, thresholds or identity changed")
    cluster = p.get("episode_clustering", {})
    if cluster.get("connected_window_hours") != 72 or cluster.get("representative") != "first_event_only" or cluster.get("future_information_used") is not False: failures.append("episode definition changed")
    observation = p.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_decision_time" or observation.get("search_later_if_reference_missing") is not False or observation.get("horizon_hours") != [1,2,4,8,12,24,48,72] or observation.get("primary_horizon_hours") != 24: failures.append("reference or horizons changed")
    if observation.get("fill_position_exit_or_equity_model") is not False or observation.get("formal_strategy_return") is not False: failures.append("position or formal return enabled")
    gates = p.get("paper_gates", {})
    expected_gates = {"complete_is_independent_episodes_minimum": 60, "projected_full_independent_episodes_minimum": 80, "projected_sealed_oos_independent_episodes_minimum": 20, "minimum_years_with_eight_complete_episodes": 3, "maximum_single_year_episode_share": "0.45", "maximum_single_symbol_episode_share": "0.25", "minimum_distinct_event_symbols": 8, "combined_median_24h_relative_repricing_minimum": "0.0180", "combined_median_24h_candidate_absolute_close_displacement_minimum": "0.0180", "qualification_quarantine_lifecycle_or_order_mismatches_maximum": 0}
    if gates != expected_gates: failures.append("Paper Gates changed")
    if p.get("projection", {}).get("may_read_oos_events_prices_or_counts") is not False: failures.append("OOS leakage enabled")
    leakage = p.get("research_leakage_prevention", {})
    if not leakage or any(v is not False for k,v in leakage.items() if k != "protocol_change_after_result_creates_new_candidate") or leakage.get("protocol_change_after_result_creates_new_candidate") is not True: failures.append("leakage prevention changed")
    if p.get("authorizations") != EXPECTED_AUTH: failures.append("authorization matrix changed")
    return failures


def validate_report() -> list[str]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    markers = ("Public data read or event scan executed: no", "Path or return result accessed: no", "OOS opened: no", "Only an exact-head independent review may follow", "at least 2.00 times", "median 24h relative")
    return [f"report marker missing: {m}" for m in markers if m not in text]


def main() -> int:
    failures = validate(load(PROTOCOL_PATH)) + validate_report()
    if failures:
        print("u06_cross_sectional_paper_protocol_check FAIL")
        for f in failures: print(f"- {f}")
        return 1
    print(f"u06_cross_sectional_paper_protocol_check PASS protocol_hash={EXPECTED_HASH} next=exact_head_independent_review")
    print("data=no events=no returns=no oos=no trading=no m2=no")
    return 0
if __name__ == "__main__": raise SystemExit(main())
