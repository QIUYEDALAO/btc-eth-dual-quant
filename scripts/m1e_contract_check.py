#!/usr/bin/env python3
"""Validate the immutable M1E product/data contract without market access."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "m1e_1h_data_contract.json"
LEDGER_PATH = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
EXPECTED_HYPOTHESIS = (
    "M1E-1H-TREND-BREAKOUT: BTC/USDT and ETH/USDT Binance spot, long/cash only; "
    "completed UTC 1h candles define a trend-breakout candidate family distinct from M1A; "
    "entries may execute no earlier than the next available 5m open after the completed signal "
    "candle; completed 4h candles may be used only as a regime filter; no shorting or leverage."
)
EXPECTED_HASH = "3668032467e2f46edff7f0ab27d358d0b918889518bfaf97276699cbc783ed15"


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("contract must be a JSON object")
    return data


def validate_contract(contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = {
        "candidate_id": "M1E-1H-TREND-BREAKOUT",
        "hypothesis_sha256": EXPECTED_HASH,
        "market": "binance_spot",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "direction": "long_cash_only",
        "leverage_allowed": False,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            failures.append(f"{key} must equal {value!r}")

    checks = (
        (contract.get("timeframes", {}).get("signal_authority") == "1h", "1h signal authority"),
        (contract.get("timeframes", {}).get("execution_detail") == "5m", "5m execution detail"),
        (contract.get("timeframes", {}).get("regime_filter_only") == "4h", "4h regime only"),
        (contract.get("range", {}).get("start") == "2020-01-01", "fixed range start"),
        (contract.get("range", {}).get("end_policy") == "latest_complete_utc_month", "complete-month end"),
        (contract.get("liquidity", {}).get("maximum") == "0.0030", "fixed liquidity threshold"),
        (contract.get("liquidity", {}).get("callers_may_override") is False, "non-overridable liquidity"),
        (contract.get("aggregation", {}).get("one_hour_child_bars") == 12, "12x5m aggregation"),
        (contract.get("aggregation", {}).get("four_hour_child_bars") == 4, "4x1h aggregation"),
        (contract.get("aggregation", {}).get("fill_or_interpolate") is False, "no synthetic bars"),
        (contract.get("sample_budget", {}).get("minimum_full_days") == 1800, "1800-day minimum"),
        (contract.get("sample_budget", {}).get("minimum_oos_days") == 540, "540-day OOS minimum"),
        (contract.get("sample_budget", {}).get("oos_opened") is False, "sealed OOS"),
        (contract.get("authorization", {}).get("strategy_code") is False, "strategy code prohibited"),
        (contract.get("authorization", {}).get("candidate_oos_returns") is False, "OOS returns prohibited"),
        (contract.get("authorization", {}).get("freqtrade_backtesting") is False, "backtesting prohibited"),
        (contract.get("authorization", {}).get("m2") is False, "M2 prohibited"),
    )
    failures.extend(f"contract violation: {label}" for ok, label in checks if not ok)

    if contract.get("source_precedence") != [
        "official_monthly_zip",
        "official_daily_zip_fill_missing_only",
        "public_rest_compare_only",
    ]:
        failures.append("source precedence must be monthly, daily fill-only, REST compare-only")
    forbidden = set(contract.get("m1a_non_reuse", {}).get("forbidden_rule_bundle", []))
    required_forbidden = {"SMA200", "Donchian55Entry", "Donchian20Exit", "ATR20x2Stop"}
    if forbidden != required_forbidden:
        failures.append("M1A forbidden rule bundle is incomplete or changed")
    return failures


def validate_ledger_identity(path: Path = LEDGER_PATH) -> list[str]:
    sys.path.insert(0, str(ROOT / ".deps"))
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    entries = [item for item in data.get("candidates", []) if item.get("id") == "M1E-1H-TREND-BREAKOUT"]
    if len(entries) != 1:
        return ["trial ledger must contain exactly one M1E candidate"]
    entry = entries[0]
    failures: list[str] = []
    calculated = hashlib.sha256(EXPECTED_HYPOTHESIS.encode("utf-8")).hexdigest()
    if calculated != EXPECTED_HASH:
        failures.append("internal M1E hypothesis hash is inconsistent")
    if entry.get("hypothesis") != EXPECTED_HYPOTHESIS:
        failures.append("trial ledger M1E hypothesis differs from the registered text")
    if entry.get("sha256") != EXPECTED_HASH:
        failures.append("trial ledger M1E hash differs from the registered hash")
    if entry.get("status") != "declared_unopened" or entry.get("oos_opened") is not False:
        failures.append("M1E must remain declared_unopened with oos_opened=false")
    return failures


def main() -> int:
    failures = validate_contract(load_contract()) + validate_ledger_identity()
    if failures:
        print("m1e_contract_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1e_contract_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
