#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "m1g_fixed_rule_contract.json"


def load(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract: dict) -> list[str]:
    failures: list[str] = []
    fixed = {
        "version": 1, "contract_id": "M1G-04-FIXED-RULE-V1",
        "candidate_id": "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION",
        "hypothesis_sha256": "288d3c37b577f6523890155b3ab4e31e4150fea876e8c66bf5c0c69403c4f2fc",
        "paper_protocol_sha256": "b77feb6725ee80837f67a56513a67bf7f305ea043dc81f4087c762fc4a61e91d",
    }
    for key, value in fixed.items():
        if contract.get(key) != value:
            failures.append(f"{key} changed")
    if contract.get("market") != {
        "exchange": "binance", "trading_mode": "spot", "pairs": ["BTC/USDT", "ETH/USDT"],
        "direction": "long_cash_only", "leverage": "1.0", "signal_timeframe": "1h",
        "execution_detail_timeframe": "5m", "maximum_open_trades": 1,
    }:
        failures.append("market or one-position boundary changed")
    entry = contract.get("entry", {})
    if entry.get("event_definition") != "exact_M1G_02_frozen_protocol" or entry.get("earliest_fill") != "next_available_5m_open" or entry.get("same_bar_close_fill_allowed") is not False:
        failures.append("entry timing or event identity changed")
    if entry.get("simultaneous_pair_ranking") != ["absolute_return_multiple_descending", "true_range_multiple_descending", "BTCUSDT_before_ETHUSDT_exact_tie"]:
        failures.append("simultaneous pair ranking changed")
    exit_rule = contract.get("exit", {})
    expected_exit = {
        "profit_target_from_entry": "0.0180", "invalidation_stop_from_entry": "-0.0400",
        "maximum_holding_hours": 24, "target_evaluation": "first_post_entry_5m_high_touch",
        "stop_evaluation": "first_post_entry_5m_low_touch", "same_5m_target_and_stop_priority": "stop_first",
        "stop_gap_fill": "worse_of_stop_threshold_or_5m_open", "target_gap_fill": "target_threshold",
        "timeout_fill": "first_5m_open_at_or_after_24h", "trailing_stop": False, "roi_table": False,
    }
    if exit_rule != expected_exit:
        failures.append("exit contract changed")
    risk = contract.get("risk", {})
    if risk != {
        "maximum_position_fraction_of_equity": "0.25", "planned_stop_equity_risk": "0.01",
        "global_cooldown_hours_after_exit": 72, "position_adjustment": False,
        "averaging_down": False, "martingale": False, "grid": False,
    }:
        failures.append("risk contract changed")
    if contract.get("data_semantics") != {
        "continuous_1h_warmup_bars": 169, "gap_resets_warmup": True,
        "quarantine_events_allowed": False, "oos_start": "2024-09-11T00:00:00Z", "oos_opened": False,
    }:
        failures.append("data semantics or OOS seal changed")
    if contract.get("cost_scenarios_per_side") != {"base": "0.0015", "cost_x2": "0.0030", "stress_a": "0.0040", "stress_b": "0.0055"}:
        failures.append("cost scenarios changed")
    derivation = contract.get("derivation", {})
    if derivation.get("parameter_search_used") is not False or derivation.get("alternatives_evaluated") is not False:
        failures.append("parameter search or alternatives are prohibited")
    if contract.get("authorization") != {
        "contract_frozen": True, "strategy_code": False, "freqtrade_backtesting": False,
        "oos_access": False, "dry_run": False, "live": False, "m2": False,
    }:
        failures.append("contract task authorization changed")
    return failures


def main() -> int:
    failures = validate(load())
    if failures:
        print("m1g_fixed_rule_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_fixed_rule_check PASS")
    print("target=1.80pct stop=4.00pct cap=25pct timeout=24h cooldown=72h backtest=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
