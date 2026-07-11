#!/usr/bin/env python3
"""Validate the frozen candidate queue and common research Gates."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import yaml

QUEUE_PATH = ROOT / "config/strategy_candidate_queue.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"

EXPECTED_QUEUE = [
    (1, "M1E", "M1E-1H-TREND-BREAKOUT", "M1G"),
    (2, "M1G", "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION", "M1H"),
    (3, "M1H", "FUNDING-EXTREME-SPOT-CONTRARIAN", "STOP_BTC_ETH_TWO_ASSET_RESEARCH"),
]
EXPECTED_OPENED = ["M1A-DAILY-TREND", "M1B-FUNDING-ARBITRAGE", "M1C-BTC-ETH-ROTATION"]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return value


def validate(queue: dict[str, Any], ledger: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if queue.get("version") != 1 or queue.get("status") != "queue_frozen_design_only":
        failures.append("candidate queue version/status changed")
    items = queue.get("queue")
    actual = [] if not isinstance(items, list) else [
        (item.get("order"), item.get("alias"), item.get("candidate_id"), item.get("failure_transition"))
        for item in items if isinstance(item, dict)
    ]
    if actual != EXPECTED_QUEUE:
        failures.append("candidate queue order, identity, or transition changed")

    candidates = ledger.get("candidates", [])
    by_id = {item.get("id"): item for item in candidates if isinstance(item, dict)}
    opened = sorted(item.get("id") for item in candidates if isinstance(item, dict) and item.get("oos_opened") is True)
    if opened != sorted(EXPECTED_OPENED):
        failures.append(f"opened OOS trial ledger must equal {EXPECTED_OPENED!r}")
    history = queue.get("historical_opened_trials", {})
    if history.get("count") != len(EXPECTED_OPENED) or history.get("candidate_ids") != EXPECTED_OPENED:
        failures.append("historical trial count or ordered IDs changed")
    for _, alias, candidate_id, _ in EXPECTED_QUEUE:
        candidate = by_id.get(candidate_id)
        if not candidate or candidate.get("oos_opened") is not False:
            failures.append(f"{alias} must resolve to exactly one unopened ledger candidate")

    policy = queue.get("common_policy", {})
    costs = policy.get("costs_per_side", {})
    if costs != {"base": "0.0015", "cost_x2": "0.0030", "stress_a": "0.0040", "stress_b": "0.0055"}:
        failures.append("fixed cost scenarios changed")
    sealed = policy.get("sealed_oos", {})
    if sealed.get("fraction") != "0.30" or sealed.get("minimum_calendar_days") != 540 or sealed.get("minimum_full_calendar_days") != 1800:
        failures.append("sealed OOS calendar policy changed")
    paper = policy.get("paper_feasibility", {})
    if paper.get("projected_full_trades_minimum") != 120 or paper.get("projected_oos_trades_minimum") != 30:
        failures.append("paper sample budget changed")
    expected_gross = Decimal(costs.get("cost_x2", "NaN")) * 2 * Decimal(paper.get("gross_displacement_multiple_of_cost_x2_roundtrip_minimum", "NaN"))
    if expected_gross != Decimal("0.0180") or Decimal(paper.get("gross_displacement_minimum", "NaN")) != expected_gross:
        failures.append("paper gross-displacement cost multiple changed")
    gates = policy.get("numerical_gates", {})
    fixed_gates = {
        "complete_trades_full_minimum": 80,
        "complete_trades_oos_minimum": 20,
        "oos_daily_mtm_sharpe_minimum": "1.0",
        "oos_daily_mtm_psr_minimum": "0.95",
        "daily_mtm_max_drawdown_maximum": "0.15",
        "delete_best_three_return_minimum": "0.0",
        "unexplained_data_gaps_maximum": 0,
    }
    if any(gates.get(key) != value for key, value in fixed_gates.items()):
        failures.append("fixed numerical Gate changed")
    if not all(gates.get(key) is True for key in (
        "base_full_return_strictly_positive", "cost_x2_full_return_strictly_positive",
        "base_oos_return_strictly_positive", "cost_x2_oos_return_strictly_positive",
        "lookahead_analysis_required", "recursive_analysis_required",
    )):
        failures.append("required return or bias Gate disabled")
    benchmark = policy.get("risk_matched_benchmark_gates", {})
    if not benchmark or not all(value is True for value in benchmark.values()):
        failures.append("risk-matched benchmark Gate disabled")
    diagnostics = policy.get("mandatory_diagnostics", {})
    if diagnostics.get("stress_a_and_b") is not True or diagnostics.get("dsr_with_opened_trial_count") is not True or diagnostics.get("dsr_hard_threshold") is not None:
        failures.append("mandatory diagnostic policy changed")
    auth = queue.get("authorization", {})
    if not auth or any(value is not False for value in auth.values()):
        failures.append("governance task must not authorize downstream work")
    return failures


def main() -> int:
    failures = validate(load(QUEUE_PATH), load(LEDGER_PATH))
    if failures:
        print("candidate_queue_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("candidate_queue_check PASS")
    print("opened_oos_trials=3 queue=M1E,M1G,M1H downstream_authorized=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
