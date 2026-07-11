#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config/m1g_is_validation_protocol.json"
ARTIFACTS = {
    "strategy": ROOT / "freqtrade_lab/user_data/strategies/M1GPanicDislocationMeanReversion.py",
    "research_config": ROOT / "freqtrade_lab/user_data/configs/config.m1g-research.json",
    "execution_audit": ROOT / "src/btc_eth_dual_quant/audit/m1g_execution_repricing.py",
    "fixed_rule_contract": ROOT / "config/m1g_fixed_rule_contract.json",
    "runtime_evidence": ROOT / "config/m1g_runtime_evidence.json",
    "data_authority_report": ROOT / "reports/m1/M1E_CANONICAL_5M_REQUALIFICATION_REPORT.md",
}


def load(path: Path = PROTOCOL) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(protocol: dict, *, verify_files: bool = True) -> list[str]:
    failures: list[str] = []
    if protocol.get("status") != "frozen_before_is_result" or protocol.get("protocol_id") != "M1G-08-IS-VALIDATION-V1":
        failures.append("IS protocol identity or status changed")
    if protocol.get("range") != {
        "is_start": "2020-07-01T00:00:00Z", "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_start": "2024-09-11T00:00:00Z", "oos_opened": False,
    }:
        failures.append("IS/OOS boundary changed or OOS opened")
    if protocol.get("costs_per_side") != {"base": "0.0015", "cost_x2": "0.0030", "stress_a": "0.0040", "stress_b": "0.0055"}:
        failures.append("cost matrix changed")
    expected_gates = {
        "complete_trades_minimum": 56,
        "base_total_return_strictly_positive": True,
        "cost_x2_total_return_strictly_positive": True,
        "daily_mtm_sharpe_minimum": "1.0",
        "daily_mtm_psr_minimum": "0.95",
        "daily_mtm_max_drawdown_maximum": "0.15",
        "delete_best_three_return_minimum": "0.0",
        "contiguous_segments": 4,
        "positive_segments_minimum": 3,
        "strategy_sharpe_not_below_benchmark": True,
        "strategy_drawdown_not_worse_than_benchmark": True,
        "strategy_total_return_strictly_above_benchmark": True,
        "lookahead_analysis_required": True,
        "recursive_analysis_required": True,
        "unexplained_data_gaps_maximum": 0,
        "native_and_conservative_audit_must_both_pass": True,
    }
    if protocol.get("is_gates") != expected_gates:
        failures.append("IS Gate matrix changed")
    diagnostics = protocol.get("diagnostics", {})
    if diagnostics.get("stress_hard_gate", "changed") is not None or diagnostics.get("dsr_opened_trial_count") != 3:
        failures.append("stress/DSR diagnostics changed after paper freeze")
    if protocol.get("authorization") != {
        "is_performance_after_merge": True, "parameter_change": False, "oos_access": False,
        "dry_run": False, "live": False, "m2": False,
    }:
        failures.append("protocol authorization changed")
    if protocol.get("audit") != {
        "input": "freqtrade_exported_trade_lifecycle_plus_canonical_5m_ohlc",
        "signal_selection_allowed": False, "exit_bar_timestamp_must_match": True,
        "numeric_tolerance": "1e-8",
    }:
        failures.append("independent audit scope changed")
    if protocol.get("benchmark") != {
        "definition": "quarter_btc_quarter_eth_half_cash_monday_open_rebalance",
        "same_cost_scenario": True,
        "daily_mtm": True,
    }:
        failures.append("risk-matched benchmark definition changed")
    if verify_files:
        hashes = protocol.get("artifact_sha256", {})
        for name, path in ARTIFACTS.items():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if hashes.get(name) != actual:
                failures.append(f"frozen artifact hash changed: {name}")
    return failures


def main() -> int:
    failures = validate(load())
    if failures:
        print("m1g_is_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_is_protocol_check PASS")
    print("is_run=authorized_after_merge oos_opened=no trial_count=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
