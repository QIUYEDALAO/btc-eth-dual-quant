"""U-19 volatility-of-volatility evaluator shared by preflight and Paper work."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class VolatilityOfVolatilityCandidatePath:
    decision_ms: int
    symbol: str
    candidate_returns: Sequence[float]
    peer_common_returns: Sequence[float]
    path_displacements: Sequence[float]


def half_statistics(residuals: Sequence[float]) -> dict[str, float] | None:
    if len(residuals) != 168:
        return None
    blocks = tuple(
        sqrt(sum(value * value for value in residuals[start : start + 24]) / 24.0)
        for start in range(0, 168, 24)
    )
    base = median(blocks)
    if not isfinite(base) or base <= 0:
        return None
    variability = 1.4826 * median(tuple(abs(value - base) for value in blocks)) / base
    if not isfinite(variability) or variability <= 0:
        return None
    return {"base_volatility": base, "normalized_volatility_of_volatility": variability}


def candidate_statistics(row: VolatilityOfVolatilityCandidatePath) -> dict | None:
    if len(row.candidate_returns) != 336 or len(row.peer_common_returns) != 336 or len(row.path_displacements) != 6:
        return None
    if any(not isfinite(value) for value in row.path_displacements):
        return None
    residuals = tuple(candidate - peer for candidate, peer in zip(row.candidate_returns, row.peer_common_returns))
    first = half_statistics(residuals[:168])
    second = half_statistics(residuals[168:])
    if first is None or second is None:
        return None
    first_value = float(first["normalized_volatility_of_volatility"])
    second_value = float(second["normalized_volatility_of_volatility"])
    return {
        "decision_ms": row.decision_ms,
        "symbol": row.symbol,
        "first_value": first_value,
        "second_value": second_value,
        "minimum_value": min(first_value, second_value),
        "maximum_value": max(first_value, second_value),
        "path": tuple(f"{value:.12f}" for value in row.path_displacements),
    }


def evaluate_decision(rows: Sequence[VolatilityOfVolatilityCandidatePath]) -> dict | None:
    if len(rows) < 10 or len({row.symbol for row in rows}) != len(rows) or len({row.decision_ms for row in rows}) != 1:
        return None
    statistics = [candidate_statistics(row) for row in rows]
    eligible = [value for value in statistics if value is not None]
    if not eligible:
        return None
    rank_count = ceil(len(rows) / 4)
    first_symbols = {value["symbol"] for value in sorted(eligible, key=lambda value: (-value["first_value"], value["symbol"]))[:rank_count]}
    second_symbols = {value["symbol"] for value in sorted(eligible, key=lambda value: (-value["second_value"], value["symbol"]))[:rank_count]}
    admitted = [
        value
        for value in eligible
        if value["first_value"] >= 0.25
        and value["second_value"] >= 0.25
        and value["symbol"] in first_symbols
        and value["symbol"] in second_symbols
    ]
    if not admitted:
        return None
    selected = sorted(admitted, key=lambda value: (-value["minimum_value"], -value["maximum_value"], value["symbol"]))[0]
    return {
        "decision_ms": selected["decision_ms"],
        "symbol": selected["symbol"],
        "minimum_normalized_volatility_of_volatility": f"{selected['minimum_value']:.12f}",
        "maximum_normalized_volatility_of_volatility": f"{selected['maximum_value']:.12f}",
        "path": selected["path"],
    }


def evaluate_stream(rows: Iterable[VolatilityOfVolatilityCandidatePath]) -> dict:
    input_rows = decision_groups = candidate_events = independent_episodes = 0
    digest = hashlib.sha256()
    group: list[VolatilityOfVolatilityCandidatePath] = []
    current_decision: int | None = None
    previous_connected_event: int | None = None

    def consume(values: Sequence[VolatilityOfVolatilityCandidatePath]) -> None:
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
