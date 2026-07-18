"""U-17 liquidity-risk candidate evaluator shared by preflight and Paper observation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil, isfinite
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class LiquidityCandidatePath:
    decision_ms: int
    candidate_symbol: str
    symbols: tuple[str, ...]
    daily_quote_volumes: tuple[tuple[float, ...], ...]
    path_displacements: tuple[float, ...]
    logical_input_rows: int


def daily_rank(candidate_symbol: str, symbols: tuple[str, ...], volumes: tuple[float, ...]) -> int | None:
    if len(symbols) < 10 or len(symbols) != len(volumes) or candidate_symbol not in symbols:
        return None
    if len(set(symbols)) != len(symbols) or any(not isfinite(value) or value <= 0 for value in volumes):
        return None
    ordered = sorted(zip(volumes, symbols))
    return next(index for index, (_, symbol) in enumerate(ordered, start=1) if symbol == candidate_symbol)


def evaluate_candidate(row: LiquidityCandidatePath) -> dict | None:
    if len(row.daily_quote_volumes) != 28 or len(row.path_displacements) != 5:
        return None
    if row.logical_input_rows <= 0 or any(not isfinite(value) for value in row.path_displacements):
        return None
    ranks: list[int] = []
    candidate_volumes: list[float] = []
    candidate_index = row.symbols.index(row.candidate_symbol) if row.candidate_symbol in row.symbols else -1
    if candidate_index < 0:
        return None
    for volumes in row.daily_quote_volumes:
        rank = daily_rank(row.candidate_symbol, row.symbols, volumes)
        if rank is None:
            return None
        ranks.append(rank)
        candidate_volumes.append(volumes[candidate_index])
    low_group_size = ceil(len(row.symbols) / 4)
    persistent_days = sum(rank <= low_group_size for rank in ranks)
    if persistent_days < 21:
        return None
    return {
        "decision_ms": row.decision_ms,
        "symbol": row.candidate_symbol,
        "persistent_low_liquidity_days": persistent_days,
        "median_daily_rank": f"{median(ranks):.12f}",
        "median_daily_quote_volume": f"{median(candidate_volumes):.12f}",
        "path": tuple(f"{value:.12f}" for value in row.path_displacements),
    }


def evaluate_stream(rows: Iterable[LiquidityCandidatePath]) -> dict:
    logical_rows = candidates = 0
    digest = hashlib.sha256()
    for row in rows:
        logical_rows += row.logical_input_rows
        event = evaluate_candidate(row)
        if event is not None:
            candidates += 1
            digest.update(json.dumps(event, sort_keys=True, separators=(",", ":")).encode())
    return {
        "input_rows": logical_rows,
        "candidate_events": candidates,
        "event_digest": digest.hexdigest(),
    }
