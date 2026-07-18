#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config/u13_cross_sectional_paper_protocol_v1.json"
REPORT = ROOT / "reports/m1/U13_CROSS_SECTIONAL_PAPER_PROTOCOL.md"
DESIGN = ROOT / "config/u13_cross_sectional_design_scope_v1.json"
EXPECTED_HASH = "1cf6dade6e75900278ba5aeee30018d3f0ff93d83d982e212d58033800993288"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(document: Mapping[str, Any], report: str) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if document.get("content_hash") != EXPECTED_HASH or canonical_hash(identity) != EXPECTED_HASH:
        failures.append("protocol identity changed")
    if document.get("candidate_id") != "U13-CROSS-SECTIONAL-COMMON-SHOCK-LAGGED-DIFFUSION" or document.get("design_content_hash") != "982cb95125a94dd10d5524dab0c241fbd7642639e1dd3461da760024d9fd3477":
        failures.append("candidate/design binding changed")
    shock = document.get("common_shock_contract", {})
    if shock.get("historical_training_common_log_return_minimum") != "0.0020" or shock.get("current_event_common_log_return_minimum") != "0.0060" or "times_7" not in shock.get("current_event_positive_breadth_integer_gate", ""):
        failures.append("shock identity changed")
    lag = document.get("lag_estimator_contract", {})
    expected_lag = {"lookback_completed_1h_observations": 2160, "chronological_halves_observations": [1080, 1080], "historical_shock_followup_hours": 4, "minimum_candidate_occurrences_full": 30, "minimum_candidate_occurrences_each_half": 12, "full_median_lagged_relative_response_minimum": "0.0040", "each_half_median_lagged_relative_response_minimum": "0.0020"}
    if any(lag.get(key) != value for key, value in expected_lag.items()) or "at_least_zero" not in lag.get("permanent_weakness_exclusion", ""):
        failures.append("lag estimator changed")
    event = document.get("event_identity", {})
    if event.get("candidate_current_absolute_log_return_minimum") != "0.0000" or event.get("candidate_current_residual_maximum") != "-0.0040" or event.get("representatives_per_decision_time") != 1:
        failures.append("event identity changed")
    if document.get("episode_clustering", {}).get("connected_window_hours") != 24 or document.get("pre_result_sample_ceiling", {}).get("minimum_theoretical_eligible_24h_episodes") != 400:
        failures.append("cluster or ceiling changed")
    preflight = document.get("implementation_data_scope_preflight", {})
    if not preflight.get("required_before_any_common_shock_event_or_path_scan") or preflight.get("oos_ohlcv_values_decoded") != 0 or preflight.get("common_component_event_path_or_return_rows_generated") != 0:
        failures.append("preflight changed")
    gates = document.get("paper_gates", {})
    if gates.get("complete_is_independent_episodes_minimum") != 90 or gates.get("combined_median_24h_relative_lagged_diffusion_minimum") != "0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_lagged_diffusion_minimum") != "0.60":
        failures.append("Paper Gates changed")
    expected_auth = {"paper_protocol_frozen": True, "exact_head_independent_review": True, "data_qualification_and_preflight": False, "common_component_scan": False, "event_scan": False, "path_observation": False, "signals": False, "formal_returns": False, "fixed_rule_contract": False, "freqtrade_strategy_code": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}
    if document.get("authorizations") != expected_auth:
        failures.append("authorization matrix changed")
    if EXPECTED_HASH not in report or "frozen_before_result_pending_exact_head_review" not in report:
        failures.append("report identity changed")
    return failures


def main() -> int:
    document = json.loads(PROTOCOL.read_text())
    failures = validate(document, REPORT.read_text())
    if json.loads(DESIGN.read_text()).get("content_hash") != document.get("design_content_hash"):
        failures.append("design file drift")
    if failures:
        print("u13_cross_sectional_paper_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"u13_cross_sectional_paper_protocol_check PASS hash={EXPECTED_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
