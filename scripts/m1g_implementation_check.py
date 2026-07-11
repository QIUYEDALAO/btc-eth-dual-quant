#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRATEGY = ROOT / "freqtrade_lab/user_data/strategies/M1GPanicDislocationMeanReversion.py"
CONFIG = ROOT / "freqtrade_lab/user_data/configs/config.m1g-research.json"


def validate() -> list[str]:
    failures: list[str] = []
    source = STRATEGY.read_text(encoding="utf-8")
    ast.parse(source)
    required = {
        'timeframe = "1h"',
        "stoploss = -0.04",
        'minimal_roi = {"0": 0.018, "1440": -1}',
        "max_open_trades = 1",
        "reference_window = 168",
        "minimum_segment_age = 169",
        "close_return_maximum = -0.024",
        "absolute_return_multiple_minimum = 3.0",
        "true_range_multiple_minimum = 2.5",
        "close_location_maximum = 0.25",
        "cluster_hours = 24",
        "global_cooldown_hours = 72",
    }
    for marker in required:
        if marker not in source:
            failures.append(f"strategy contract marker missing: {marker}")
    for forbidden in ("hyperopt", "leverage(", "position_adjustment_enable = True", "can_short = True"):
        if forbidden in source:
            failures.append(f"forbidden strategy feature: {forbidden}")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("tradable_balance_ratio") != 0.25 or config.get("max_open_trades") != 1:
        failures.append("research config violates the fixed position contract")
    if config.get("timeframe") != "1h" or config.get("dataformat_ohlcv") != "jsongz":
        failures.append("research config timeframe or format changed")
    if config.get("api_server", {}).get("enabled") is not False:
        failures.append("API server must remain disabled")
    exchange = config.get("exchange", {})
    if "key" in exchange or "secret" in exchange:
        failures.append("research config contains credential fields")

    for path in (ROOT / "freqtrade_lab/scripts/ft_lookahead_m1g.sh", ROOT / "freqtrade_lab/scripts/ft_recursive_m1g.sh"):
        text = path.read_text(encoding="utf-8")
        if "20200701-20240911" not in text or "20240911-" in text:
            failures.append(f"{path.name} does not remain inside sealed IS")
        if "freqtrade" + " trade" in text:
            failures.append(f"{path.name} contains a trading command")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("m1g_implementation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_implementation_check PASS")
    print("performance_backtest=no oos_opened=no execution_audit=implemented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
