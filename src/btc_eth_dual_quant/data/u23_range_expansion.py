"""Exact U-23 range-expansion statistic core for synthetic preflight and Paper work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite, log
from statistics import median
from typing import Iterable, Sequence

HISTORY_BARS = 42
TOTAL_BARS = HISTORY_BARS + 1
MINIMUM_ACTIVE_MEMBERS = 10
MAD_SCALE = 1.4826
MINIMUM_CURRENT_LOG_RANGE = log(1.04)
MINIMUM_RANGE_RATIO = 2.0
MINIMUM_RANGE_ROBUST_Z = 3.0
MINIMUM_CLOSE_LOCATION = 0.90
MINIMUM_BODY_SHARE = 0.60
MINIMUM_PEER_RELATIVE_LOG_RETURN = log(1.025)
CLUSTER_MS = 86_400_000


@dataclass(frozen=True)
class RangeStrengthDecision:
    decision_ms: int
    symbols: Sequence[str]
    completed_ohlc: Sequence[Sequence[tuple[float, float, float, float]]]
    path_displacements: Sequence[Sequence[float]]


def _valid_bar(bar: Sequence[float]) -> bool:
    if len(bar) != 4 or any(not isfinite(value) or value <= 0.0 for value in bar):
        return False
    open_price, high, low, close = bar
    return high >= max(open_price, close) and low <= min(open_price, close) and high > low


def evaluate_decision(row: RangeStrengthDecision) -> dict | None:
    member_count = len(row.symbols)
    if member_count < MINIMUM_ACTIVE_MEMBERS or len(set(row.symbols)) != member_count:
        return None
    if len(row.completed_ohlc) != member_count or len(row.path_displacements) != member_count:
        return None
    if any(len(bars) != TOTAL_BARS or any(not _valid_bar(bar) for bar in bars) for bars in row.completed_ohlc):
        return None
    if any(len(values) != 6 or any(not isfinite(value) for value in values) for values in row.path_displacements):
        return None

    current_returns = tuple(log(bars[-1][3] / bars[-1][0]) for bars in row.completed_ohlc)
    peer_common = median(current_returns)
    statistics: list[dict] = []
    for index, symbol in enumerate(row.symbols):
        bars = row.completed_ohlc[index]
        prior_ranges = tuple(log(high / low) for _, high, low, _ in bars[:-1])
        baseline = median(prior_ranges)
        scale = MAD_SCALE * median(tuple(abs(value - baseline) for value in prior_ranges))
        open_price, high, low, close = bars[-1]
        current_range = log(high / low)
        if baseline <= 0.0 or scale <= 0.0 or not isfinite(scale):
            continue
        range_ratio = current_range / baseline
        range_z = (current_range - baseline) / scale
        close_location = (close - low) / (high - low)
        body_share = (close - open_price) / (high - low)
        relative_return = current_returns[index] - peer_common
        if (
            current_range < MINIMUM_CURRENT_LOG_RANGE
            or range_ratio < MINIMUM_RANGE_RATIO
            or range_z < MINIMUM_RANGE_ROBUST_Z
            or close_location < MINIMUM_CLOSE_LOCATION
            or body_share < MINIMUM_BODY_SHARE
            or relative_return < MINIMUM_PEER_RELATIVE_LOG_RETURN
        ):
            continue
        statistics.append({
            "symbol": symbol,
            "current_log_range": current_range,
            "baseline_log_range": baseline,
            "range_ratio": range_ratio,
            "range_robust_z": range_z,
            "close_location": close_location,
            "body_share": body_share,
            "peer_relative_log_return": relative_return,
            "path": tuple(f"{value:.12f}" for value in row.path_displacements[index]),
        })
    if not statistics:
        return None
    winner = sorted(statistics, key=lambda value: (-value["peer_relative_log_return"], -value["range_robust_z"], value["symbol"]))[0]
    return {
        "decision_ms": row.decision_ms,
        "symbol": winner["symbol"],
        "current_log_range": f"{winner['current_log_range']:.12f}",
        "baseline_log_range": f"{winner['baseline_log_range']:.12f}",
        "range_ratio": f"{winner['range_ratio']:.12f}",
        "range_robust_z": f"{winner['range_robust_z']:.12f}",
        "close_location": f"{winner['close_location']:.12f}",
        "body_share": f"{winner['body_share']:.12f}",
        "peer_relative_log_return": f"{winner['peer_relative_log_return']:.12f}",
        "path": winner["path"],
    }


def evaluate_stream(rows: Iterable[RangeStrengthDecision]) -> dict:
    decision_groups = candidate_events = independent_episodes = logical_ohlc_member_bars = 0
    previous_decision: int | None = None
    previous_connected_event: int | None = None
    digest = hashlib.sha256()
    for row in rows:
        decision_groups += 1
        logical_ohlc_member_bars += len(row.symbols) * TOTAL_BARS
        if previous_decision is not None and row.decision_ms <= previous_decision:
            raise ValueError("decision order must be strictly increasing")
        previous_decision = row.decision_ms
        event = evaluate_decision(row)
        if event is None:
            continue
        candidate_events += 1
        if previous_connected_event is None or row.decision_ms - previous_connected_event > CLUSTER_MS:
            independent_episodes += 1
            digest.update(json.dumps(event, sort_keys=True, separators=(",", ":")).encode())
        previous_connected_event = row.decision_ms
    return {
        "logical_ohlc_member_bars": logical_ohlc_member_bars,
        "decision_groups": decision_groups,
        "candidate_events": candidate_events,
        "independent_episodes": independent_episodes,
        "event_digest": digest.hexdigest(),
    }
