"""Exact U-22 dispersion-expansion statistic core for synthetic preflight and Paper work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil, isfinite, log
from statistics import median
from typing import Iterable, Sequence

HISTORY_HOURS = 24
BASELINE_HOURS = 12
RECENT_HOURS = 12
MINIMUM_ACTIVE_MEMBERS = 10
MAD_SCALE = 1.4826
MINIMUM_DISPERSION_RATIO = 1.50
MINIMUM_RECENT_DISPERSION = 0.0040
MINIMUM_RELATIVE_LOG_DISPLACEMENT = log(1.024)
MINIMUM_POSITIVE_RECENT_HOURS = 8
MAXIMUM_SINGLE_POSITIVE_CONTRIBUTION = 0.50
CLUSTER_MS = 86_400_000


@dataclass(frozen=True)
class DispersionLeaderDecision:
    decision_ms: int
    symbols: Sequence[str]
    completed_hourly_log_returns: Sequence[Sequence[float]]
    path_displacements: Sequence[Sequence[float]]


def _dispersion_and_residuals(values: Sequence[float]) -> tuple[float, tuple[float, ...]] | None:
    if len(values) < MINIMUM_ACTIVE_MEMBERS or any(not isfinite(value) for value in values):
        return None
    common = median(values)
    residuals = tuple(value - common for value in values)
    dispersion = MAD_SCALE * median(tuple(abs(value) for value in residuals))
    if not isfinite(dispersion):
        return None
    return dispersion, residuals


def evaluate_decision(row: DispersionLeaderDecision) -> dict | None:
    member_count = len(row.symbols)
    if member_count < MINIMUM_ACTIVE_MEMBERS or len(set(row.symbols)) != member_count:
        return None
    if len(row.completed_hourly_log_returns) != member_count or len(row.path_displacements) != member_count:
        return None
    if any(len(values) != HISTORY_HOURS for values in row.completed_hourly_log_returns):
        return None
    if any(len(values) != 6 or any(not isfinite(value) for value in values) for values in row.path_displacements):
        return None

    dispersions: list[float] = []
    residual_by_symbol = [[] for _ in range(member_count)]
    for hour in range(HISTORY_HOURS):
        result = _dispersion_and_residuals(tuple(row.completed_hourly_log_returns[index][hour] for index in range(member_count)))
        if result is None:
            return None
        dispersion, residuals = result
        dispersions.append(dispersion)
        for index, value in enumerate(residuals):
            residual_by_symbol[index].append(value)

    baseline = median(dispersions[:BASELINE_HOURS])
    recent = median(dispersions[BASELINE_HOURS:])
    if baseline <= 0.0 or recent < MINIMUM_RECENT_DISPERSION or recent / baseline < MINIMUM_DISPERSION_RATIO:
        return None

    statistics: list[dict] = []
    for index, symbol in enumerate(row.symbols):
        values = residual_by_symbol[index][BASELINE_HOURS:]
        total = sum(values)
        positive_values = [value for value in values if value > 0.0]
        positive_sum = sum(positive_values)
        maximum_share = max(positive_values, default=0.0) / positive_sum if positive_sum > 0.0 else 1.0
        statistics.append({
            "symbol": symbol,
            "total": total,
            "positive_hours": len(positive_values),
            "first_half": sum(values[:6]),
            "second_half": sum(values[6:]),
            "maximum_share": maximum_share,
            "path": tuple(f"{value:.12f}" for value in row.path_displacements[index]),
        })
    leader = sorted(statistics, key=lambda value: (-value["total"], value["symbol"]))[0]
    if (
        leader["total"] < MINIMUM_RELATIVE_LOG_DISPLACEMENT
        or leader["positive_hours"] < MINIMUM_POSITIVE_RECENT_HOURS
        or leader["first_half"] <= 0.0
        or leader["second_half"] <= 0.0
        or leader["maximum_share"] > MAXIMUM_SINGLE_POSITIVE_CONTRIBUTION
    ):
        return None
    return {
        "decision_ms": row.decision_ms,
        "symbol": leader["symbol"],
        "baseline_dispersion": f"{baseline:.12f}",
        "recent_dispersion": f"{recent:.12f}",
        "dispersion_ratio": f"{recent / baseline:.12f}",
        "relative_log_displacement": f"{leader['total']:.12f}",
        "positive_recent_hours": leader["positive_hours"],
        "maximum_single_positive_contribution": f"{leader['maximum_share']:.12f}",
        "path": leader["path"],
    }


def evaluate_stream(rows: Iterable[DispersionLeaderDecision]) -> dict:
    decision_groups = candidate_events = independent_episodes = logical_hourly_member_rows = 0
    previous_decision: int | None = None
    previous_connected_event: int | None = None
    digest = hashlib.sha256()
    for row in rows:
        decision_groups += 1
        logical_hourly_member_rows += len(row.symbols) * HISTORY_HOURS
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
        "logical_hourly_member_rows": logical_hourly_member_rows,
        "decision_groups": decision_groups,
        "candidate_events": candidate_events,
        "independent_episodes": independent_episodes,
        "event_digest": digest.hexdigest(),
    }
