"""U-20 negative-coskewness evaluator shared by preflight and Paper work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from typing import Iterable, Sequence


@dataclass(frozen=True)
class NegativeCoskewnessCandidatePath:
    decision_ms: int
    symbol: str
    candidate_returns: Sequence[float]
    peer_common_returns: Sequence[float]
    path_displacements: Sequence[float]


def half_coskewness(candidate_returns: Sequence[float], common_returns: Sequence[float]) -> float | None:
    if len(candidate_returns) != 168 or len(common_returns) != 168:
        return None
    sx = sy = sx2 = sy2 = sxy = sxy2 = 0.0
    for candidate, common in zip(candidate_returns, common_returns):
        adjusted = candidate - common
        if not isfinite(adjusted) or not isfinite(common):
            return None
        common2 = common * common
        sx += adjusted
        sy += common
        sx2 += adjusted * adjusted
        sy2 += common2
        sxy += adjusted * common
        sxy2 += adjusted * common2
    n = 168.0
    mx = sx / n
    my = sy / n
    ex2 = sx2 / n
    ey2 = sy2 / n
    var_x = ex2 - mx * mx
    var_y = ey2 - my * my
    if not isfinite(var_x) or not isfinite(var_y) or var_x <= 0.0 or var_y <= 0.0:
        return None
    third_comoment = sxy2 / n - mx * ey2 - 2.0 * my * (sxy / n) + 2.0 * mx * my * my
    value = third_comoment / (sqrt(var_x) * var_y)
    return value if isfinite(value) else None


def candidate_statistics(row: NegativeCoskewnessCandidatePath) -> dict | None:
    if len(row.candidate_returns) != 336 or len(row.peer_common_returns) != 336 or len(row.path_displacements) != 6:
        return None
    if any(not isfinite(value) for value in row.path_displacements):
        return None
    first = half_coskewness(row.candidate_returns[:168], row.peer_common_returns[:168])
    second = half_coskewness(row.candidate_returns[168:], row.peer_common_returns[168:])
    if first is None or second is None:
        return None
    return {
        "decision_ms": row.decision_ms,
        "symbol": row.symbol,
        "first_value": first,
        "second_value": second,
        "minimum_value": min(first, second),
        "maximum_value": max(first, second),
        "path": tuple(f"{value:.12f}" for value in row.path_displacements),
    }


def evaluate_decision(rows: Sequence[NegativeCoskewnessCandidatePath]) -> dict | None:
    if len(rows) < 10 or len({row.symbol for row in rows}) != len(rows) or len({row.decision_ms for row in rows}) != 1:
        return None
    statistics = [candidate_statistics(row) for row in rows]
    eligible = [value for value in statistics if value is not None]
    if not eligible:
        return None
    rank_count = ceil(len(rows) / 4)
    first_symbols = {value["symbol"] for value in sorted(eligible, key=lambda value: (value["first_value"], value["symbol"]))[:rank_count]}
    second_symbols = {value["symbol"] for value in sorted(eligible, key=lambda value: (value["second_value"], value["symbol"]))[:rank_count]}
    admitted = [
        value
        for value in eligible
        if value["first_value"] <= -0.20
        and value["second_value"] <= -0.20
        and value["symbol"] in first_symbols
        and value["symbol"] in second_symbols
    ]
    if not admitted:
        return None
    selected = sorted(admitted, key=lambda value: (value["maximum_value"], value["minimum_value"], value["symbol"]))[0]
    return {
        "decision_ms": selected["decision_ms"],
        "symbol": selected["symbol"],
        "maximum_half_coskewness": f"{selected['maximum_value']:.12f}",
        "minimum_half_coskewness": f"{selected['minimum_value']:.12f}",
        "path": selected["path"],
    }


def evaluate_stream(rows: Iterable[NegativeCoskewnessCandidatePath]) -> dict:
    input_rows = decision_groups = candidate_events = independent_episodes = 0
    digest = hashlib.sha256()
    group: list[NegativeCoskewnessCandidatePath] = []
    current_decision: int | None = None
    previous_connected_event: int | None = None

    def consume(values: Sequence[NegativeCoskewnessCandidatePath]) -> None:
        nonlocal decision_groups, candidate_events, independent_episodes, previous_connected_event
        if not values:
            return
        decision_groups += 1
        event = evaluate_decision(values)
        if event is None:
            return
        candidate_events += 1
        decision_ms = int(event["decision_ms"])
        if previous_connected_event is None or decision_ms - previous_connected_event > 86_400_000:
            independent_episodes += 1
            digest.update(json.dumps(event, sort_keys=True, separators=(",", ":")).encode())
        previous_connected_event = decision_ms

    for row in rows:
        input_rows += 1
        if current_decision is None:
            current_decision = row.decision_ms
        if row.decision_ms != current_decision:
            consume(group)
            group = []
            current_decision = row.decision_ms
        group.append(row)
    consume(group)
    return {
        "input_rows": input_rows,
        "decision_groups": decision_groups,
        "candidate_events": candidate_events,
        "independent_episodes": independent_episodes,
        "event_digest": digest.hexdigest(),
    }
