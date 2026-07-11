"""IS-only M1E compression-expansion paper diagnostics."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Iterable, Mapping

import pandas as pd


HORIZONS = (1, 2, 4, 8, 12, 24)


@dataclass(frozen=True)
class PaperEvent:
    symbol: str
    event_open_time: int
    segment_id: int
    compression_score: float
    compression_threshold: float
    expansion_multiple: float
    horizon_displacements: tuple[tuple[int, float], ...]
    mae_24h: float
    mfe_24h: float


@dataclass(frozen=True)
class PaperResult:
    events: tuple[PaperEvent, ...]
    raw_candidates: int
    cluster_representatives: int
    right_censored: int
    canonical_sha256: str


def _frame(rows: Iterable[Mapping[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows))
    required = {"symbol", "open_time", "open", "high", "low", "close", "segment_id", "bars_since_segment_start"}
    if frame.empty or not required.issubset(frame.columns):
        raise ValueError("isolated 1h rows missing required fields")
    frame = frame.copy()
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["open_time"] = pd.to_numeric(frame["open_time"], errors="raise").astype("int64")
    frame["segment_id"] = pd.to_numeric(frame["segment_id"], errors="raise").astype("int64")
    frame["bars_since_segment_start"] = pd.to_numeric(frame["bars_since_segment_start"], errors="raise").astype("int64")
    if frame["open_time"].duplicated().any() or not frame["open_time"].is_monotonic_increasing:
        raise ValueError("isolated rows must be unique and increasing")
    return frame


def detect_events(rows: Iterable[Mapping[str, object]], protocol: Mapping[str, object]) -> PaperResult:
    frame = _frame(rows)
    event_cfg = protocol["diagnostic_event"]
    observation = protocol["observation"]
    window = int(event_cfg["compression_window_bars"])
    reference = int(event_cfg["compression_reference_bars"])
    quantile = float(event_cfg["compression_quantile"])
    expansion_required = float(event_cfg["expansion_true_range_multiple"])
    minimum_age = int(event_cfg["minimum_segment_age_bars"])
    cluster_ms = int(event_cfg["cluster_window_hours"]) * 60 * 60 * 1000
    path_horizon = int(observation["path_horizon_bars"])

    raw_candidates = 0
    representatives = 0
    censored = 0
    events: list[PaperEvent] = []
    for (_, segment_id), segment in frame.groupby(["symbol", "segment_id"], sort=False):
        segment = segment.reset_index(drop=True)
        prior_close = segment["close"].shift(1)
        true_range = pd.concat([
            segment["high"] - segment["low"],
            (segment["high"] - prior_close).abs(),
            (segment["low"] - prior_close).abs(),
        ], axis=1).max(axis=1)
        rolling_high = segment["high"].rolling(window).max()
        rolling_low = segment["low"].rolling(window).min()
        compression_score = (rolling_high - rolling_low) / segment["close"]
        prior_compression = compression_score.shift(1)
        compression_threshold = compression_score.shift(2).rolling(reference).quantile(quantile, interpolation="linear")
        prior_high = segment["high"].shift(1).rolling(window).max()
        prior_tr_median = true_range.shift(1).rolling(window).median()
        expansion_multiple = true_range / prior_tr_median
        candidate_mask = (
            (segment["bars_since_segment_start"] >= minimum_age)
            & (prior_compression <= compression_threshold)
            & (segment["close"] > prior_high)
            & (expansion_multiple >= expansion_required)
        ).fillna(False)
        candidate_indices = list(segment.index[candidate_mask])
        raw_candidates += len(candidate_indices)

        representative_indices: list[int] = []
        last_candidate_time: int | None = None
        for index in candidate_indices:
            timestamp = int(segment.at[index, "open_time"])
            if last_candidate_time is None or timestamp - last_candidate_time > cluster_ms:
                representative_indices.append(index)
            last_candidate_time = timestamp
        representatives += len(representative_indices)

        for index in representative_indices:
            if index + path_horizon >= len(segment):
                censored += 1
                continue
            future = segment.iloc[index + 1:index + path_horizon + 1]
            reference_price = float(segment.at[index, "close"])
            displacements = tuple(
                (horizon, float(segment.at[index + horizon, "close"]) / reference_price - 1.0)
                for horizon in HORIZONS
            )
            events.append(PaperEvent(
                symbol=str(segment.at[index, "symbol"]),
                event_open_time=int(segment.at[index, "open_time"]),
                segment_id=int(segment_id),
                compression_score=float(prior_compression.at[index]),
                compression_threshold=float(compression_threshold.at[index]),
                expansion_multiple=float(expansion_multiple.at[index]),
                horizon_displacements=displacements,
                mae_24h=float(future["low"].min()) / reference_price - 1.0,
                mfe_24h=float(future["high"].max()) / reference_price - 1.0,
            ))

    events.sort(key=lambda item: (item.event_open_time, item.symbol))
    digest = hashlib.sha256()
    for event in events:
        digest.update(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    return PaperResult(tuple(events), raw_candidates, representatives, censored, digest.hexdigest())


def summarize(results: Iterable[PaperResult], protocol: Mapping[str, object]) -> dict:
    result_list = list(results)
    events = sorted((event for result in result_list for event in result.events), key=lambda item: (item.event_open_time, item.symbol))
    if not events:
        raise ValueError("paper diagnostic produced no complete events")
    gates = protocol["paper_gates"]
    calendar = protocol["projection_calendar_days"]
    is_days = int(calendar["is"])
    complete = len(events)
    projected_full = math.floor(complete / is_days * int(calendar["full"]))
    projected_oos = math.floor(complete / is_days * int(calendar["oos"]))

    by_symbol: dict[str, dict] = {}
    for symbol in protocol["scope"]["symbols"]:
        selected = [event for event in events if event.symbol == symbol]
        by_symbol[symbol] = {
            "events": len(selected),
            "median_mfe_24h": median(event.mfe_24h for event in selected) if selected else None,
            "median_mae_24h": median(event.mae_24h for event in selected) if selected else None,
        }
    by_year: dict[str, int] = {}
    for event in events:
        year = str(datetime.fromtimestamp(event.event_open_time / 1000, tz=timezone.utc).year)
        by_year[year] = by_year.get(year, 0) + 1
    max_year_share = max(by_year.values()) / complete
    years_with_ten = sum(value >= 10 for value in by_year.values())

    horizon_stats: dict[str, dict] = {}
    for horizon in HORIZONS:
        values = [dict(event.horizon_displacements)[horizon] for event in events]
        series = pd.Series(values)
        horizon_stats[str(horizon)] = {
            "count": len(values),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "positive_rate": float((series > 0).mean()),
            "p05": float(series.quantile(0.05)),
            "p95": float(series.quantile(0.95)),
        }

    median_mfe = median(event.mfe_24h for event in events)
    gate_matrix = {
        "projected_full_events": projected_full >= int(gates["projected_full_events_minimum"]),
        "projected_oos_events": projected_oos >= int(gates["projected_oos_events_minimum"]),
        "combined_median_mfe": median_mfe >= float(gates["median_24h_mfe_minimum"]),
        "each_symbol_events": all(item["events"] >= int(gates["each_symbol_complete_events_minimum"]) for item in by_symbol.values()),
        "each_symbol_median_mfe": all(item["median_mfe_24h"] is not None and item["median_mfe_24h"] >= float(gates["each_symbol_median_24h_mfe_minimum"]) for item in by_symbol.values()),
        "year_distribution": years_with_ten >= int(gates["minimum_years_with_ten_events"]),
        "single_year_concentration": max_year_share <= float(gates["maximum_single_year_event_share"]),
        "quarantine_or_unrewarmed_events": True,
    }
    timestamps = [event.event_open_time for event in events]
    longest_sleep_hours = max((right - left) / 3_600_000 for left, right in zip(timestamps, timestamps[1:])) if len(timestamps) > 1 else 0.0
    return {
        "status": "pass" if all(gate_matrix.values()) else "failed_feasibility",
        "complete_events": complete,
        "raw_candidates": sum(result.raw_candidates for result in result_list),
        "cluster_representatives": sum(result.cluster_representatives for result in result_list),
        "right_censored": sum(result.right_censored for result in result_list),
        "projected_full_events": projected_full,
        "projected_oos_events": projected_oos,
        "median_mfe_24h": median_mfe,
        "median_mae_24h": median(event.mae_24h for event in events),
        "by_symbol": by_symbol,
        "by_year": by_year,
        "years_with_ten_events": years_with_ten,
        "maximum_single_year_share": max_year_share,
        "longest_sleep_hours": longest_sleep_hours,
        "horizon_stats": horizon_stats,
        "gate_matrix": gate_matrix,
        "event_sha256": hashlib.sha256("".join(result.canonical_sha256 for result in result_list).encode()).hexdigest(),
    }
