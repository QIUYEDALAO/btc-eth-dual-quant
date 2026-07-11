#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config" / "m1g_is_only_design_scope.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
EXPECTED_CANDIDATE = "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION"
EXPECTED_HASH = "288d3c37b577f6523890155b3ab4e31e4150fea876e8c66bf5c0c69403c4f2fc"
EXPECTED_FAILURES = [
    "permanent_information_shock_or_structural_repricing",
    "continued_liquidation_cascade_and_serial_correlated_events",
    "event_time_spread_and_slippage_above_the_frozen_cost_model",
    "weak_rebound_that_cannot_cover_stressed_roundtrip_cost",
    "exchange_outage_quarantine_or_incomplete_rewarm_window",
    "btc_eth_correlation_that_turns_two_events_into_one_risk_exposure",
]
EXPECTED_UNRESOLVED = [
    "one_hour_panic_dislocation_definition", "forced_selling_price_only_confirmation",
    "four_hour_regime_filter", "reversion_target", "maximum_holding_horizon",
    "risk_invalidation_stop", "position_cap", "event_cluster_cooldown", "indicator_warmup",
]


def load_scope(path: Path = SCOPE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_scope(scope: dict) -> list[str]:
    failures: list[str] = []
    expected = {
        "version": 1,
        "status": "economic_hypothesis_pass_paper_protocol_only",
        "candidate_id": EXPECTED_CANDIDATE,
        "hypothesis_sha256": EXPECTED_HASH,
    }
    for key, value in expected.items():
        if scope.get(key) != value:
            failures.append(f"{key} must equal {value!r}")
    research = scope.get("research_scope", {})
    fixed_research = {
        "market": "binance_spot", "symbols": ["BTCUSDT", "ETHUSDT"],
        "direction": "long_cash_only", "signal_timeframe": "completed_utc_1h",
        "regime_timeframe": "completed_utc_4h_optional_price_only",
        "future_execution_detail": "next_available_5m_open",
        "is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_start": "2024-09-11T00:00:00Z", "oos_opened": False,
        "canonical_fields": ["open", "high", "low", "close"],
        "reuse_existing_sealed_is_snapshot": True,
    }
    if research != fixed_research:
        failures.append("research scope, sealed boundary, or canonical fields changed")
    economic = scope.get("economic_hypothesis", {})
    if economic.get("family") != "forced_selling_dislocation_then_short_horizon_mean_reversion":
        failures.append("economic family changed")
    if economic.get("failure_regimes") != EXPECTED_FAILURES:
        failures.append("failure regimes changed")
    nondup = scope.get("non_duplication", {})
    if set(nondup) != {
        "m1e_family", "m1g_family", "m1e_protocol_reuse_prohibited",
        "m1e_outcome_derived_rule_prohibited", "m1d_15m_timeframe_rescue_prohibited",
        "daily_panic_threshold_rescaling_prohibited", "m1a_combined_bundle_prohibited",
    } or any(nondup.get(key) is not True for key in (
        "m1e_protocol_reuse_prohibited", "m1e_outcome_derived_rule_prohibited",
        "m1d_15m_timeframe_rescue_prohibited", "daily_panic_threshold_rescaling_prohibited",
        "m1a_combined_bundle_prohibited",
    )):
        failures.append("non-duplication boundary changed")
    if scope.get("unresolved_until_later_gates") != EXPECTED_UNRESOLVED:
        failures.append("rule decisions were selected or changed prematurely")
    if scope.get("authorization") != {
        "m1g_paper_protocol_design": True, "m1g_paper_diagnostic_run": False,
        "fixed_rule_contract": False, "strategy_code": False,
        "freqtrade_backtesting": False, "oos_access": False, "m2": False,
    }:
        failures.append("only M1G paper protocol design may be authorized")
    return failures


def validate_ledger(path: Path = LEDGER_PATH) -> list[str]:
    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if item.get("id") == EXPECTED_CANDIDATE]
    if len(matches) != 1:
        return ["M1G candidate identity must appear exactly once"]
    candidate = matches[0]
    digest = hashlib.sha256(candidate.get("hypothesis", "").encode("utf-8")).hexdigest()
    failures = []
    if digest != EXPECTED_HASH or candidate.get("sha256") != EXPECTED_HASH:
        failures.append("M1G hypothesis hash changed")
    if candidate.get("status") != "declared_unopened" or candidate.get("oos_opened") is not False:
        failures.append("M1G must remain declared_unopened with sealed OOS")
    return failures


def main() -> int:
    failures = validate_scope(load_scope()) + validate_ledger()
    if failures:
        print("m1g_is_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_is_design_check PASS")
    print("authorized_next=paper_protocol_design events_evaluated=no oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
