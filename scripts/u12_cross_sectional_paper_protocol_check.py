#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config/u12_cross_sectional_paper_protocol_v1.json"
EXPECTED = "a8cfc0b74e82bdf455bae5dda7a620bc5c0c53f1022d39494800f1053dd80b8a"


def load() -> dict[str, Any]:
    return json.loads(PATH.read_text())


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED or canonical_hash(identity) != EXPECTED:
        failures.append("protocol identity changed")
    if document.get("candidate_id") != "U12-CROSS-SECTIONAL-RECURRING-CALENDAR-FLOW-SEASONALITY" or document.get("design_content_hash") != "e53003e7c9255fc11d976a646f8700532cc98ad6fd1c410b00647957daa6d5dc":
        failures.append("candidate binding changed")
    calendar = document.get("calendar_state_contract", {})
    if calendar.get("family") != "utc_weekday_of_target_day" or calendar.get("states") != ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] or any(calendar.get(key) is not False for key in ("daylight_saving_adjustment", "holiday_or_region_specific_exception", "alternative_calendar_family_or_granularity", "post_result_state_selection")):
        failures.append("calendar state changed")
    estimator = document.get("estimator_contract", {})
    expected_estimator = {"prior_same_weekday_opportunities": 52, "chronological_halves_opportunities": [26, 26], "minimum_current_active_members": 10, "minimum_candidate_completed_occurrences_full": 40, "minimum_candidate_completed_occurrences_each_half": 18, "candidate_must_be_active_at_decision": True, "historical_candidate_occurrence_requires_candidate_active_then": True, "each_historical_common_component_uses_that_days_exact_active_members": True, "all_historical_active_member_daily_rows_complete_required": True, "current_membership_backfill_allowed": False, "replacement_member_allowed": False, "future_target_day_or_outcome_data_used": False}
    if any(estimator.get(key) != value for key, value in expected_estimator.items()):
        failures.append("estimator contract changed")
    event = document.get("event_identity", {})
    if event.get("full_median_asset_specific_value_minimum") != "0.0060" or event.get("each_half_median_asset_specific_value_minimum") != "0.0030" or event.get("representatives_per_decision_time") != 1:
        failures.append("event identity changed")
    preflight = document.get("implementation_data_scope_preflight", {})
    required_preflight = ("required_before_any_event_or_path_scan", "runs_during_frozen_source_qualification_only", "uses_same_archive_membership_lifecycle_mask_and_daily_assembly_paths_as_future_observation", "verifies_previous_boundary_close_for_every_requested_daily_interval_including_month_transitions", "verifies_all_288_expected_5m_slots_per_unmasked_complete_utc_day", "verifies_historical_same_weekday_cell_availability_without_computing_returns", "verifies_normal_reverse_and_deterministic_shuffled_input_identity")
    if any(preflight.get(key) is not True for key in required_preflight) or preflight.get("oos_ohlcv_values_decoded") != 0 or preflight.get("common_component_event_path_or_return_rows_generated") != 0:
        failures.append("pre-result implementation/data-scope preflight changed")
    ceiling = document.get("pre_result_sample_ceiling", {})
    if ceiling.get("minimum_theoretical_eligible_24h_episodes") != 300 or ceiling.get("frozen_complete_is_episode_gate") != 90 or ceiling.get("must_pass_before_any_common_component_event_or_path_scan") is not True:
        failures.append("pre-result sample ceiling changed")
    observation = document.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_utc_day_boundary_decision" or observation.get("search_later_if_reference_missing") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24] or observation.get("formal_strategy_return") is not False:
        failures.append("causal observation contract changed")
    gates = document.get("paper_gates", {})
    expected_gates = {"complete_is_independent_episodes_minimum": 90, "projected_full_independent_episodes_minimum": 120, "projected_sealed_oos_independent_episodes_minimum": 30, "combined_median_24h_relative_calendar_flow_persistence_minimum": "0.0180", "combined_median_24h_candidate_absolute_close_displacement_minimum": "0.0180", "fraction_complete_episodes_with_positive_24h_relative_calendar_flow_persistence_minimum": "0.60", "qualification_preflight_quarantine_lifecycle_or_order_mismatches_maximum": 0}
    if any(gates.get(key) != value for key, value in expected_gates.items()):
        failures.append("Paper Gates changed")
    if document.get("scope", {}).get("oos_opened") is not False or document.get("projection", {}).get("may_read_oos_events_prices_or_counts") is not False:
        failures.append("OOS seal changed")
    if [key for key, value in document.get("authorizations", {}).items() if value] != ["paper_protocol_frozen", "exact_head_independent_review"]:
        failures.append("authorization matrix changed")
    return failures


def main() -> int:
    failures = validate(load())
    if failures:
        print("u12_cross_sectional_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u12_cross_sectional_paper_protocol_check PASS hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
