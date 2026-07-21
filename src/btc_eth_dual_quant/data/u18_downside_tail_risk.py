"""U-18 downside-tail evaluator shared by synthetic preflight and Paper observation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class TailRiskCandidatePath:
    decision_ms: int
    symbol: str
    candidate_returns: tuple[float, ...]
    peer_common_returns: tuple[float, ...]
    path_displacements: tuple[float, ...]


def tail_statistics(residuals: tuple[float, ...]) -> dict[str, float | int] | None:
    if len(residuals) != 84 or any(not isfinite(value) for value in residuals):
        return None
    center = median(residuals)
    scale = 1.4826 * median(tuple(abs(value - center) for value in residuals))
    if not isfinite(scale) or scale <= 0:
        return None
    tail = tuple(value for value in residuals if value <= center - 2.0 * scale)
    if len(tail) < 2:
        return None
    total_energy = sum((value - center) ** 2 for value in residuals)
    tail_energies = tuple((center - value) ** 2 for value in tail)
    tail_energy = sum(tail_energies)
    if total_energy <= 0 or tail_energy <= 0:
        return None
    energy_share = tail_energy / total_energy
    dominance = max(tail_energies) / tail_energy
    if energy_share < 0.25 or dominance > 0.65:
        return None
    return {
        "tail_count": len(tail),
        "tail_energy_share": energy_share,
        "tail_dominance": dominance,
        "minimum_standardized_tail": (min(tail) - center) / scale,
    }


def evaluate_candidate(row: TailRiskCandidatePath) -> dict | None:
    if len(row.candidate_returns) != 168 or len(row.peer_common_returns) != 168 or len(row.path_displacements) != 6:
        return None
    values = (*row.candidate_returns, *row.peer_common_returns, *row.path_displacements)
    if any(not isfinite(value) for value in values):
        return None
    residuals = tuple(candidate - peer for candidate, peer in zip(row.candidate_returns, row.peer_common_returns))
    first = tail_statistics(residuals[:84])
    second = tail_statistics(residuals[84:])
    if first is None or second is None:
        return None
    return {
        "decision_ms": row.decision_ms,
        "symbol": row.symbol,
        "first_tail_count": first["tail_count"],
        "second_tail_count": second["tail_count"],
        "minimum_tail_energy_share": f"{min(float(first['tail_energy_share']), float(second['tail_energy_share'])):.12f}",
        "maximum_tail_dominance": f"{max(float(first['tail_dominance']), float(second['tail_dominance'])):.12f}",
        "minimum_standardized_tail": f"{min(float(first['minimum_standardized_tail']), float(second['minimum_standardized_tail'])):.12f}",
        "path": tuple(f"{value:.12f}" for value in row.path_displacements),
    }


def evaluate_stream(rows: Iterable[TailRiskCandidatePath]) -> dict:
    count = candidates = 0
    digest = hashlib.sha256()
    for row in rows:
        count += 1
        event = evaluate_candidate(row)
        if event is not None:
            candidates += 1
            digest.update(json.dumps(event, sort_keys=True, separators=(",", ":")).encode())
    return {"input_rows": count, "candidate_events": candidates, "event_digest": digest.hexdigest()}
