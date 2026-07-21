#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config/u11_cross_sectional_paper_protocol_v1.json"
EXPECTED = "3d78bbc86049bf7f0a2b3e0b30a25c6a747640043868d76132cf2cf2324d42dc"


def load() -> dict[str, Any]:
    return json.loads(PATH.read_text())


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED or canonical_hash(identity) != EXPECTED:
        failures.append("protocol identity changed")
    if document.get("candidate_id") != "U11-CROSS-SECTIONAL-ASYMMETRIC-MARKET-CAPTURE-QUALITY-PERSISTENCE" or document.get("design_content_hash") != "0572daf7511c673a89dff6e737ad12528dde6c40845b672d62bbd3b1aeca9e4c":
        failures.append("candidate binding changed")
    estimator = document.get("estimator_contract", {})
    expected_estimator = {
        "lookback_completed_4h_observations": 360,
        "persistence_halves_completed_4h_observations": [180, 180],
        "minimum_current_active_members": 10,
        "minimum_full_positive_states": 60,
        "minimum_full_negative_states": 60,
        "minimum_each_half_positive_states": 24,
        "minimum_each_half_negative_states": 24,
        "candidate_must_be_active_and_complete_for_all_360_observations": True,
        "each_historical_common_component_uses_that_observations_exact_active_members": True,
        "all_historical_active_member_rows_complete_required": True,
        "current_membership_backfill_allowed": False,
        "replacement_member_allowed": False,
        "future_or_outcome_data_used": False,
    }
    if any(estimator.get(key) != value for key, value in expected_estimator.items()):
        failures.append("estimator contract changed")
    event = document.get("event_identity", {})
    if event.get("full_upside_capture_minimum") != "0.80" or event.get("full_downside_capture_maximum") != "0.70" or event.get("full_asymmetric_capture_score_minimum") != "0.30" or event.get("representatives_per_decision_time") != 1:
        failures.append("event identity changed")
    ceiling = document.get("pre_result_sample_ceiling", {})
    if ceiling.get("minimum_theoretical_eligible_72h_episodes") != 200 or ceiling.get("frozen_complete_is_episode_gate") != 90 or ceiling.get("must_pass_before_any_common_state_event_or_path_scan") is not True:
        failures.append("pre-result sample ceiling changed")
    observation = document.get("observation_contract", {})
    if observation.get("reference") != "first_expected_5m_open_strictly_after_completed_4h_decision" or observation.get("search_later_if_reference_missing") is not False or observation.get("horizon_hours") != [1, 2, 4, 8, 12, 24, 48, 72] or observation.get("formal_strategy_return") is not False:
        failures.append("causal observation contract changed")
    gates = document.get("paper_gates", {})
    expected_gates = {
        "complete_is_independent_episodes_minimum": 90,
        "projected_full_independent_episodes_minimum": 120,
        "projected_sealed_oos_independent_episodes_minimum": 30,
        "combined_median_72h_relative_quality_persistence_minimum": "0.0180",
        "combined_median_72h_candidate_absolute_close_displacement_minimum": "0.0180",
        "fraction_complete_episodes_with_positive_72h_relative_quality_persistence_minimum": "0.60",
        "qualification_quarantine_lifecycle_or_order_mismatches_maximum": 0,
    }
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
        print("u11_cross_sectional_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u11_cross_sectional_paper_protocol_check PASS hash={EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
