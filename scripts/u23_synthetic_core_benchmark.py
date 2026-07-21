#!/usr/bin/env python3
from __future__ import annotations

import json
import resource
import time

from btc_eth_dual_quant.data.u23_range_expansion import HISTORY_BARS, RangeStrengthDecision, evaluate_stream

DECISIONS = 1551
MEMBERS = 15
TOTAL_BARS = HISTORY_BARS + 1
LOGICAL_ROWS = DECISIONS * MEMBERS * TOTAL_BARS


def _history(index: int):
    bars = []
    for offset in range(HISTORY_BARS):
        center = 100.0 + index + (offset % 3) * 0.01
        half = 0.45 + (offset % 7) * 0.025
        bars.append((center, center + half, center - half, center + 0.02))
    return tuple(bars)


def fixture():
    symbols = tuple(f"S{index:02d}USDT" for index in range(MEMBERS))
    paths = tuple(tuple(0.001 * horizon for horizon in (1, 2, 4, 8, 12, 24)) for _ in symbols)
    values = []
    for index in range(MEMBERS):
        current = (100.0, 100.8, 99.6, 100.2)
        if index == MEMBERS - 1:
            current = (100.0, 108.0, 99.5, 107.5)
        values.append(_history(index) + (current,))
    completed = tuple(values)
    for decision in range(DECISIONS):
        yield RangeStrengthDecision(decision * 14_400_000, symbols, completed, paths)


def main() -> int:
    started = time.perf_counter()
    result = evaluate_stream(fixture())
    elapsed = time.perf_counter() - started
    peak_rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 if __import__("sys").platform != "darwin" else 1024 * 1024)
    payload = {
        "elapsed_seconds": f"{elapsed:.6f}",
        "peak_rss_mib": f"{peak_rss_mib:.3f}",
        "minimum_logical_ohlc_member_bars": 1000000,
        "actual_logical_ohlc_member_bars": LOGICAL_ROWS,
        "maximum_elapsed_seconds": 30,
        "maximum_peak_rss_mib": 1024,
        "result": result,
    }
    payload["pass"] = LOGICAL_ROWS >= 1000000 and elapsed <= 30 and peak_rss_mib <= 1024 and result["logical_ohlc_member_bars"] == LOGICAL_ROWS and result["candidate_events"] == DECISIONS
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
