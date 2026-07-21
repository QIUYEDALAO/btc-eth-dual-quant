#!/usr/bin/env python3
"""Synthetic signal-equivalence and prefix-causality probe for one adapter."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path

import pandas as pd
from freqtrade.resolvers import StrategyResolver


def frame(path: Path) -> pd.DataFrame:
    values = json.loads(path.read_text())
    result = pd.DataFrame(values, columns=["date", "open", "high", "low", "close", "volume"])
    result["date"] = pd.to_datetime(result["date"], unit="ms", utc=True)
    return result


def evaluate(strategy, source: pd.DataFrame) -> pd.DataFrame:
    value = strategy.populate_indicators(source.copy(), {"pair": "BTC/USDT"})
    value = strategy.populate_entry_trend(value, {"pair": "BTC/USDT"})
    value = strategy.populate_exit_trend(value, {"pair": "BTC/USDT"})
    for name in ("enter_long", "exit_long"):
        if name not in value:
            value[name] = 0
        value[name] = value[name].fillna(0).astype(int)
    return value


def signal_hash(value: pd.DataFrame) -> str:
    rows = [
        [row.date.isoformat(), int(row.enter_long), int(row.exit_long)]
        for row in value[["date", "enter_long", "exit_long"]].itertuples(index=False)
    ]
    return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    config = {
        "strategy": args.candidate,
        "strategy_path": "/strategy",
        "user_data_dir": Path("/freqtrade/user_data"),
    }
    adapter = StrategyResolver.load_strategy(config)
    adapter.ft_load_hyper_params(False)
    original_class = getattr(importlib.import_module("original_source"), args.candidate)
    original = original_class(config)
    original.ft_load_hyper_params(False)
    source = frame(args.data_dir / "binance" / f"BTC_USDT-{args.timeframe}.json")

    normal = source.sort_values("date", kind="mergesort").reset_index(drop=True)
    reverse = source.iloc[::-1].sort_values("date", kind="mergesort").reset_index(drop=True)
    shuffled = source.sample(frac=1.0, random_state=1701).sort_values("date", kind="mergesort").reset_index(drop=True)
    adapter_values = [evaluate(adapter, value) for value in (normal, reverse, shuffled)]
    original_value = evaluate(original, normal)
    hashes = [signal_hash(value) for value in adapter_values]
    failures = []
    if len(set(hashes)) != 1:
        failures.append("input order changes signals")
    if hashes[0] != signal_hash(original_value):
        failures.append("adapter differs from original")
    minimum = max(int(getattr(adapter, "startup_candle_count", 0)), 30)
    endpoints = sorted({minimum + 50, len(normal) // 2, len(normal) - 1})
    prefix_checks = []
    full = adapter_values[0]
    diagnostics = {}
    if args.candidate == "UniversalMACD":
        diagnostics["umacd_min"] = float(full["umacd"].min())
        diagnostics["umacd_max"] = float(full["umacd"].max())
    if args.candidate == "Heracles":
        ratio = full["volatility_dcp"].shift(adapter.buy_indicator_shift.value).div(
            full["volatility_kcw"].shift(adapter.buy_crossed_indicator_shift.value)
        )
        diagnostics["entry_ratio_min"] = float(ratio.min())
        diagnostics["entry_ratio_max"] = float(ratio.max())
        diagnostics["entry_ratio_in_range"] = int(
            ratio.between(adapter.buy_div_min.value, adapter.buy_div_max.value).sum()
        )
    for endpoint in endpoints:
        prefix = evaluate(adapter, normal.iloc[: endpoint + 1])
        actual = [int(prefix.iloc[-1]["enter_long"]), int(prefix.iloc[-1]["exit_long"])]
        expected = [int(full.iloc[endpoint]["enter_long"]), int(full.iloc[endpoint]["exit_long"])]
        prefix_checks.append({"row": endpoint, "actual": actual, "expected": expected})
        if actual != expected:
            failures.append(f"future rows affect signal at {endpoint}")
    result = {
        "schema_version": "external-strategy-causal-probe-v1",
        "candidate_id": args.candidate,
        "timeframe": args.timeframe,
        "rows": len(normal),
        "normal_signal_hash": hashes[0],
        "reverse_signal_hash": hashes[1],
        "shuffled_signal_hash": hashes[2],
        "original_signal_hash": signal_hash(original_value),
        "entry_signals": int(full["enter_long"].sum()),
        "exit_signals": int(full["exit_long"].sum()),
        "prefix_checks": prefix_checks,
        "diagnostics": diagnostics,
        "status": "PASS" if not failures else "REJECT",
        "failures": failures,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
