"""Result-agnostic U-14 auction/event/path evaluator shared by fixtures and Paper research."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite, log
from statistics import median
from typing import Iterable, Iterator, Sequence


@dataclass(frozen=True, slots=True)
class AuctionPathRow:
    decision_ms: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    reference_open: float
    path_closes: tuple[float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class EvaluatedEvent:
    decision_ms: int
    symbol: str
    close_location_residual: float
    relative_paths: tuple[float, float, float, float, float, float]
    absolute_paths: tuple[float, float, float, float, float, float]


def _metrics(row: AuctionPathRow) -> tuple[float, float, float, float] | None:
    values = (row.open, row.high, row.low, row.close, row.reference_open, *row.path_closes)
    if any(not isfinite(value) or value <= 0 for value in values):
        return None
    if row.high < max(row.open, row.close) or row.low > min(row.open, row.close) or row.high <= row.low:
        return None
    return (
        log(row.close / row.open),
        (row.high - row.low) / row.open,
        row.low / row.open - 1.0,
        (row.close - row.low) / (row.high - row.low),
    )


def evaluate_decision(rows: Sequence[AuctionPathRow], minimum_members: int = 10) -> EvaluatedEvent | None:
    if len(rows) < minimum_members or len({row.symbol for row in rows}) != len(rows) or len({row.decision_ms for row in rows}) != 1:
        return None
    ordered = sorted(rows, key=lambda row: row.symbol)
    metrics = [_metrics(row) for row in ordered]
    if any(value is None for value in metrics):
        return None
    exact = [value for value in metrics if value is not None]
    returns = [value[0] for value in exact]
    if median(returns) > -0.0060 or sum(value < 0 for value in returns) * 10 < len(rows) * 7:
        return None
    close_locations = [value[3] for value in exact]
    candidates: list[tuple[float, float, float, float, str, int]] = []
    for index, (row, values) in enumerate(zip(ordered, exact)):
        log_return, normalized_range, downside, close_location = values
        peers = close_locations[:index] + close_locations[index + 1 :]
        residual = close_location - median(peers)
        if log_return <= 0.0 and normalized_range >= 0.0180 and downside <= -0.0120 and close_location >= 0.80 and residual >= 0.20:
            candidates.append((residual, close_location, downside, normalized_range, row.symbol, index))
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda value: (-value[0], -value[1], value[2], -value[3], value[4]))
    permitted = {value[4] for value in sorted(candidates, key=lambda value: (-value[0], value[4]))[: ceil(len(rows) / 4)]}
    chosen = next((value for value in ranked if value[4] in permitted), None)
    if chosen is None:
        return None
    residual, _, _, _, symbol, index = chosen
    candidate = ordered[index]
    absolute = tuple(close / candidate.reference_open - 1.0 for close in candidate.path_closes)
    peer_paths = []
    for horizon in range(6):
        peer_paths.append(median(row.path_closes[horizon] / row.reference_open - 1.0 for row in ordered if row.symbol != symbol))
    relative = tuple(value - peer for value, peer in zip(absolute, peer_paths))
    return EvaluatedEvent(candidate.decision_ms, symbol, residual, relative, absolute)


def grouped_rows(rows: Iterable[AuctionPathRow]) -> Iterator[list[AuctionPathRow]]:
    current: list[AuctionPathRow] = []
    decision: int | None = None
    for row in rows:
        if decision is not None and row.decision_ms != decision:
            yield current
            current = []
        decision = row.decision_ms
        current.append(row)
    if current:
        yield current


def evaluate_stream(rows: Iterable[AuctionPathRow], expected_members: int = 15) -> dict[str, object]:
    input_rows = decisions = incomplete = candidate_events = episodes = 0
    previous_connected: int | None = None
    event_digest_rows: list[tuple[int, str, str]] = []
    for group in grouped_rows(rows):
        input_rows += len(group)
        decisions += 1
        if len(group) != expected_members:
            incomplete += 1
            continue
        event = evaluate_decision(group)
        if event is None:
            continue
        candidate_events += 1
        if previous_connected is None or event.decision_ms - previous_connected > 24 * 3_600_000:
            episodes += 1
            event_digest_rows.append((event.decision_ms, event.symbol, f"{event.relative_paths[-1]:.12f}"))
        previous_connected = event.decision_ms
    return {"input_rows": input_rows, "decision_groups": decisions, "incomplete_groups": incomplete, "candidate_events": candidate_events, "episodes": episodes, "event_digest_rows": event_digest_rows}
