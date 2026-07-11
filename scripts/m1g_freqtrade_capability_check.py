#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "config" / "m1g_freqtrade_capability_mapping.json"


def load(path: Path = MAPPING) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(mapping: dict) -> list[str]:
    failures: list[str] = []
    expected = {
        "version": 1,
        "status": "capability_pass_with_mandatory_execution_audit",
        "candidate_id": "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION",
        "fixed_contract_id": "M1G-04-FIXED-RULE-V1",
        "freqtrade_runtime": "freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6",
    }
    for key, value in expected.items():
        if mapping.get(key) != value:
            failures.append(f"{key} changed")
    native = mapping.get("native_mapping", {})
    if native != {
        "completed_1h_signal_next_open": True, "timeframe_detail_5m": True,
        "stoploss_before_roi_same_detail_candle": True, "roi_target_0_minutes": "0.0180",
        "roi_timeout_1440_minutes": "-1", "maximum_open_trades": 1,
        "equity_fraction_via_tradable_balance_ratio": "0.25",
        "cross_pair_unique_ranking_via_informative_data": True,
        "global_cooldown_via_confirm_trade_entry_and_all_pair_closed_trade_proxy_hours": 72,
    }:
        failures.append("native Freqtrade mapping changed")
    differences = mapping.get("native_execution_differences", {})
    if differences.get("material") is not True or set(differences) != {"target_gap", "stop_gap", "material"}:
        failures.append("material native execution differences must remain disclosed")
    audit = mapping.get("mandatory_independent_audit", {})
    if audit != {
        "input": "freqtrade_exported_trade_lifecycle_plus_canonical_5m_ohlc",
        "target_gap_fill": "exact_target_threshold",
        "stop_gap_fill": "worse_of_stop_threshold_or_5m_open",
        "same_5m_target_and_stop_priority": "stop_first",
        "timeout_fill": "first_5m_open_at_or_after_24h",
        "signal_or_trade_selection_recomputed": False,
        "full_second_strategy_backtest": False,
        "approval_requires_freqtrade_and_contract_audit_gates": True,
    }:
        failures.append("mandatory execution audit changed or became a second strategy")
    if mapping.get("authorization") != {
        "strategy_implementation_after_merge": True, "performance_backtesting": False,
        "oos_access": False, "dry_run": False, "live": False, "m2": False,
    }:
        failures.append("capability review authorization changed")
    return failures


def main() -> int:
    failures = validate(load())
    if failures:
        print("m1g_freqtrade_capability_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_freqtrade_capability_check PASS")
    print("conclusion=pass_with_mandatory_execution_audit backtest=no oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
