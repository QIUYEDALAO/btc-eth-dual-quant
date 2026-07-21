#!/usr/bin/env python3
from __future__ import annotations

import json
import resource
import time

from btc_eth_dual_quant.data.u22_dispersion_expansion import DispersionLeaderDecision, evaluate_stream

DECISIONS = 2778
MEMBERS = 15
HISTORY_HOURS = 24
LOGICAL_ROWS = DECISIONS * MEMBERS * HISTORY_HOURS


def fixture():
    symbols = tuple(f"S{index:02d}USDT" for index in range(MEMBERS))
    paths = tuple(tuple(0.001 * horizon for horizon in (1, 2, 4, 8, 12, 24)) for _ in symbols)
    baseline = tuple(tuple((index - 7) * 0.0002 for _ in range(12)) for index in range(MEMBERS))
    recent = []
    for index in range(MEMBERS):
        if index == MEMBERS - 1:
            recent.append(tuple(0.0060 for _ in range(12)))
        else:
            recent.append(tuple((index - 7) * 0.00075 - 0.0003 for _ in range(12)))
    values = tuple(baseline[index] + recent[index] for index in range(MEMBERS))
    for decision in range(DECISIONS):
        yield DispersionLeaderDecision(decision * 3_600_000, symbols, values, paths)


def main() -> int:
    started = time.perf_counter()
    result = evaluate_stream(fixture())
    elapsed = time.perf_counter() - started
    peak_rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 if __import__("sys").platform != "darwin" else 1024 * 1024)
    payload = {
        "elapsed_seconds": f"{elapsed:.6f}",
        "peak_rss_mib": f"{peak_rss_mib:.3f}",
        "minimum_logical_hourly_member_rows": 1000000,
        "actual_logical_hourly_member_rows": LOGICAL_ROWS,
        "maximum_elapsed_seconds": 30,
        "maximum_peak_rss_mib": 1024,
        "result": result,
    }
    payload["pass"] = LOGICAL_ROWS >= 1000000 and elapsed <= 30 and peak_rss_mib <= 1024 and result["logical_hourly_member_rows"] == LOGICAL_ROWS
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
