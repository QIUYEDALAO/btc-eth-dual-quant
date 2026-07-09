#!/usr/bin/env python3
"""Validate the immutable M1C design contract without loading Freqtrade."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "freqtrade_lab" / "m1c-btc-eth-rotation-contract.json"
EVIDENCE_PATH = ROOT / "freqtrade_lab" / "m1c-freqtrade-capability-evidence.json"
SPEC_PATH = ROOT / "docs" / "superpowers" / "specs" / "2026-07-10-m1c-btc-eth-rotation-design.md"
REPORT_PATH = ROOT / "reports" / "m1" / "M1C_FREQTRADE_CAPABILITY_REVIEW.md"


def validate_design() -> list[str]:
    failures: list[str] = []
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    expected = {
        "design_status": "design_pass",
        "framework": "freqtrade",
        "market": "binance_spot",
        "pairs": ["BTC/USDT", "ETH/USDT"],
        "timeframe": "1d",
        "timezone": "UTC",
        "decision_weekday": 6,
        "decision_after_completed_close": True,
        "fill_rule": "next_bar_open",
        "absolute_sma_window": 200,
        "relative_return_window": 90,
        "tie_breaker": "BTC/USDT",
        "missing_cross_pair_action": "cash",
        "max_open_trades": 1,
        "stake_amount": "unlimited",
        "tradable_balance_ratio": 0.5,
        "minimum_cash_ratio": 0.5,
        "stoploss": -0.2,
        "can_short": False,
        "leverage": 1.0,
        "position_adjustment": False,
        "trailing_stop": False,
        "hyperopt_allowed": False,
        "parameter_search_allowed": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            failures.append(f"contract {key} must be {value!r}")

    if contract.get("minimal_roi") != {"0": 100.0}:
        failures.append("contract minimal_roi must disable forced ROI exits")

    expected_gates = {
        "complete_trades_min": 80,
        "oos_complete_trades_min": 20,
        "oos_sharpe_min": 1.0,
        "max_drawdown_max": 0.15,
        "delete_best_3_return_min": 0.0,
        "positive_is_segments_min": 3,
        "is_segments": 4,
        "unexplained_data_gaps_max": 0,
    }
    gates = contract.get("gates", {})
    for key, value in expected_gates.items():
        if gates.get(key) != value:
            failures.append(f"contract gate {key} must be {value!r}")

    authorization = contract.get("authorization", {})
    for key in ("m2", "dry_run", "live", "api_keys"):
        if authorization.get(key) is not False:
            failures.append(f"authorization {key} must be false")

    observations = evidence.get("observations", {})
    for key in (
        "signal_columns_shifted_one_candle",
        "pairs_with_open_trades_processed_first",
        "closed_trade_releases_slot_immediately",
        "different_pair_can_enter_same_timestamp_after_exit",
        "runtime_fixture_required_in_p2",
    ):
        if observations.get(key) is not True:
            failures.append(f"capability evidence missing: {key}")
    if evidence.get("release") != "2026.6":
        failures.append("capability evidence must target pinned Freqtrade 2026.6")

    spec = SPEC_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    for marker in (
        "Design status: design_pass",
        "blocked_framework_capability",
        "next daily candle open",
        "no custom single-leg backtester",
    ):
        if marker.casefold() not in (spec + "\n" + report).casefold():
            failures.append(f"design evidence missing marker: {marker}")

    state_text = (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    strategy_path = ROOT / "freqtrade_lab" / "user_data" / "strategies" / "BTCETHRelativeStrengthRotation.py"
    if "current_phase: P1 " in state_text and strategy_path.exists():
        failures.append("P1 design phase must not contain the P2 strategy implementation")

    return failures


def main() -> int:
    failures = validate_design()
    if failures:
        print("m1c_design_validate FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1c_design_validate PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
