#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "config" / "m1e_is_only_design_scope.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"

EXPECTED_CANDIDATE = "M1E-1H-TREND-BREAKOUT"
EXPECTED_HASH = "3668032467e2f46edff7f0ab27d358d0b918889518bfaf97276699cbc783ed15"
EXPECTED_FAILURES = [
    "range_bound_chop_and_repeated_false_expansion",
    "news_gap_or_liquidity_shock_with_unmodelled_slippage",
    "persistent_trend_without_a_preceding_compression_state",
    "exchange_outage_or_quarantine_rewarm_window",
    "high_cross_asset_correlation_that_concentrates_btc_eth_exposure",
]
EXPECTED_FORBIDDEN = ["SMA200", "Donchian55Entry", "Donchian20Exit", "ATR20x2Stop"]
EXPECTED_UNRESOLVED = [
    "four_hour_state_filter",
    "one_hour_compression_definition",
    "one_hour_expansion_definition",
    "exit_rule",
    "risk_stop",
    "position_cap",
    "cooldown",
    "indicator_warmup",
]


def load_scope(path: Path = SCOPE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_scope(scope: dict) -> list[str]:
    failures: list[str] = []

    expected_scalars = {
        ("status",): "economic_hypothesis_pass_isolation_only",
        ("candidate_id",): EXPECTED_CANDIDATE,
        ("hypothesis_sha256",): EXPECTED_HASH,
        ("research_scope", "market"): "binance_spot",
        ("research_scope", "direction"): "long_cash_only",
        ("research_scope", "signal_timeframe"): "completed_utc_1h",
        ("research_scope", "regime_timeframe"): "completed_utc_4h_only",
        ("research_scope", "future_execution_detail"): "next_available_5m_open",
        ("research_scope", "is_start"): "2020-07-01T00:00:00Z",
        ("research_scope", "is_end_exclusive"): "2024-09-11T00:00:00Z",
        ("research_scope", "oos_start"): "2024-09-11T00:00:00Z",
        ("research_scope", "oos_opened"): False,
        ("economic_hypothesis", "family"): "volatility_compression_then_directional_expansion",
        ("non_duplication", "m1a_family"): "daily_continuous_trend_following",
        ("non_duplication", "m1e_family"): "one_hour_state_transition_event",
        ("non_duplication", "m1a_timeframe_rescue_prohibited"): True,
        ("non_duplication", "fixed_channel_relabel_prohibited"): True,
    }
    for path, expected in expected_scalars.items():
        value: object = scope
        try:
            for key in path:
                value = value[key]  # type: ignore[index]
        except (KeyError, TypeError):
            value = None
        if value != expected:
            failures.append(f"{'.'.join(path)} must equal {expected!r}")

    if scope.get("research_scope", {}).get("symbols") != ["BTCUSDT", "ETHUSDT"]:
        failures.append("research_scope.symbols must remain BTCUSDT,ETHUSDT")
    if scope.get("economic_hypothesis", {}).get("failure_regimes") != EXPECTED_FAILURES:
        failures.append("economic_hypothesis.failure_regimes changed")
    if scope.get("non_duplication", {}).get("forbidden_combined_bundle") != EXPECTED_FORBIDDEN:
        failures.append("non_duplication.forbidden_combined_bundle changed")
    if scope.get("unresolved_until_later_gates") != EXPECTED_UNRESOLVED:
        failures.append("unresolved decisions were selected or changed prematurely")

    expected_authorization = {
        "m1e_05_is_data_isolator": True,
        "m1e_06_paper_diagnostics": False,
        "m1e_07_fixed_rule_contract": False,
        "strategy_code": False,
        "freqtrade_backtesting": False,
        "oos_access": False,
        "m2": False,
    }
    if scope.get("authorization") != expected_authorization:
        failures.append("authorization must permit only M1E-05 IS data isolation")
    return failures


def validate_ledger(path: Path = LEDGER_PATH) -> list[str]:
    ledger = yaml.safe_load(path.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if item.get("id") == EXPECTED_CANDIDATE]
    if len(matches) != 1:
        return ["M1E candidate identity must appear exactly once in the trial ledger"]
    candidate = matches[0]
    failures: list[str] = []
    digest = hashlib.sha256(candidate.get("hypothesis", "").encode("utf-8")).hexdigest()
    if digest != EXPECTED_HASH or candidate.get("sha256") != EXPECTED_HASH:
        failures.append("M1E hypothesis hash changed")
    if candidate.get("status") not in {"declared_unopened", "failed_feasibility"} or candidate.get("oos_opened") is not False:
        failures.append("M1E must remain unopened with sealed OOS")
    return failures


def main() -> int:
    failures = validate_scope(load_scope()) + validate_ledger()
    if failures:
        print("m1e_is_design_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1e_is_design_check PASS")
    print("authorized_next=M1E-05 candidate_evaluated=no oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
