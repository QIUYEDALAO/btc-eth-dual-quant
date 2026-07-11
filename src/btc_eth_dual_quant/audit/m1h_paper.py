"""M1H funding-data qualification and sealed-IS path observations.

This module is deliberately not a strategy or backtest engine.  It validates
settled public funding observations and measures the frozen post-settlement
spot path without constructing positions, fills, fees, returns, or equity.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from statistics import median
from typing import Iterable, Mapping, Sequence


IS_START_MS = int(datetime(2020, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
IS_END_EXCLUSIVE_MS = int(datetime(2024, 9, 11, tzinfo=timezone.utc).timestamp() * 1000)
HOUR_MS = 3_600_000
FIVE_MINUTE_MS = 300_000
DAY_MS = 86_400_000
HORIZONS = (1, 2, 4, 8, 12, 24)
SYMBOLS = ("BTCUSDT", "ETHUSDT")
PROHIBITED_RESEARCH_SEMANTICS = (
    "funding arbitrage",
    "funding income",
    "basis trade",
    "perpetual short",
    "panic trigger",
    "close-location trigger",
    "range-expansion trigger",
)


@dataclass(frozen=True)
class FundingPoint:
    symbol: str
    funding_time_ms: int
    funding_rate: str
    interval_hours: str
    source_sha256: str


@dataclass(frozen=True)
class FundingQualification:
    symbol: str
    points: tuple[FundingPoint, ...]
    source_hashes: tuple[str, ...]
    raw_rows: int
    identical_duplicates: int
    conflicting_duplicates: int
    invalid_rows: int
    invalid_intervals: int
    missing_settlements: int
    oos_values_parsed: int
    first_time_ms: int
    last_time_ms: int
    canonical_sha256: str

    @property
    def passed(self) -> bool:
        return not any((
            self.conflicting_duplicates,
            self.invalid_rows,
            self.invalid_intervals,
            self.missing_settlements,
            self.oos_values_parsed,
        ))


@dataclass(frozen=True)
class SpotBar:
    symbol: str
    open_time_ms: int
    close_time_ms: int
    open: str
    high: str
    low: str
    close: str


@dataclass(frozen=True)
class FundingEvent:
    symbol: str
    funding_time_ms: int
    annualized_rate: str
    threshold: str
    reference_time_ms: int
    reference_open: str
    horizon_displacements: tuple[tuple[int, float], ...]
    mae_24h: float
    mfe_24h: float
    recovery_minutes: int | None


@dataclass(frozen=True)
class PaperObservationResult:
    complete_events: tuple[FundingEvent, ...]
    raw_extremes: int
    symbol_cluster_representatives: int
    right_censored: int
    invalid_observations: int
    canonical_sha256: str


def validate_research_scope_text(text: str) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in PROHIBITED_RESEARCH_SEMANTICS if phrase in lowered]


def _decimal(value: object) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite decimal")
    return result


def _normalized_interval_hours(delta_ms: int) -> Decimal:
    if delta_ms <= 0:
        raise ValueError("funding timestamps must increase")
    hours = Decimal(delta_ms) / Decimal(HOUR_MS)
    nearest = hours.quantize(Decimal("1"))
    if abs(hours - nearest) <= Decimal("0.0167"):
        hours = nearest
    return hours


def qualify_funding_rows(
    *,
    symbol: str,
    rows: Iterable[Mapping[str, object]],
    source_hashes: Sequence[str],
    raw_rows: int | None = None,
    oos_values_parsed: int = 0,
) -> FundingQualification:
    """Canonicalize qualified pre-OOS funding rows without a fixed cadence."""

    if symbol not in SYMBOLS:
        raise ValueError("M1H supports only BTCUSDT and ETHUSDT")
    by_time: dict[int, tuple[str, str, str]] = {}
    duplicate_count = 0
    conflicts = 0
    invalid_rows = 0
    observed_rows = 0
    for source in rows:
        observed_rows += 1
        try:
            row_symbol = str(source["symbol"]).upper()
            time_ms = int(source["fundingTime"])
            rate = _decimal(source["fundingRate"])
            declared_interval = _decimal(source["fundingIntervalHours"])
            source_hash = str(source.get("source_sha256") or "")
            if row_symbol != symbol or not source_hash or time_ms >= IS_END_EXCLUSIVE_MS:
                raise ValueError("row identity or sealed boundary invalid")
            if declared_interval <= 0 or declared_interval > 24:
                raise ValueError("declared interval invalid")
        except (KeyError, TypeError, ValueError, InvalidOperation):
            invalid_rows += 1
            continue
        value = (str(rate), str(declared_interval), source_hash)
        prior = by_time.get(time_ms)
        if prior is None:
            by_time[time_ms] = value
        elif prior[:2] == value[:2]:
            duplicate_count += 1
        else:
            conflicts += 1

    if len(by_time) < 2:
        raise ValueError(f"insufficient funding history for {symbol}")
    times = sorted(by_time)
    derived: dict[int, Decimal] = {}
    first_interval = _normalized_interval_hours(times[1] - times[0])
    derived[times[0]] = first_interval
    for previous, current in zip(times, times[1:]):
        derived[current] = _normalized_interval_hours(current - previous)

    invalid_intervals = 0
    missing_settlements = 0
    points: list[FundingPoint] = []
    for time_ms in times:
        rate, declared_text, source_hash = by_time[time_ms]
        declared = _decimal(declared_text)
        interval = derived[time_ms]
        if interval <= 0 or interval > 24 or interval != interval.quantize(Decimal("1")):
            invalid_intervals += 1
        if interval != declared:
            missing_settlements += 1
        points.append(FundingPoint(symbol, time_ms, rate, str(interval), source_hash))

    digest = hashlib.sha256()
    for point in points:
        digest.update(json.dumps(asdict(point), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    return FundingQualification(
        symbol=symbol,
        points=tuple(points),
        source_hashes=tuple(sorted(set(source_hashes))),
        raw_rows=raw_rows if raw_rows is not None else observed_rows,
        identical_duplicates=duplicate_count,
        conflicting_duplicates=conflicts,
        invalid_rows=invalid_rows,
        invalid_intervals=invalid_intervals,
        missing_settlements=missing_settlements,
        oos_values_parsed=oos_values_parsed,
        first_time_ms=times[0],
        last_time_ms=times[-1],
        canonical_sha256=digest.hexdigest(),
    )


def validate_spot_bars(symbol: str, rows: Iterable[Mapping[str, object]]) -> tuple[SpotBar, ...]:
    bars: list[SpotBar] = []
    prior: int | None = None
    for source in rows:
        try:
            opened = int(source["open_time"])
            closed = int(source["close_time"])
            values = tuple(_decimal(source[key]) for key in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise ValueError("invalid canonical 5m row") from exc
        if opened < IS_START_MS or opened >= IS_END_EXCLUSIVE_MS:
            raise ValueError("spot bar outside sealed IS")
        if opened % FIVE_MINUTE_MS or closed != opened + FIVE_MINUTE_MS - 1:
            raise ValueError("spot bar is off-grid or incomplete")
        opened_price, high, low, close = values
        if min(values) <= 0 or high < max(opened_price, low, close) or low > min(opened_price, high, close):
            raise ValueError("invalid canonical 5m OHLC")
        if prior is not None and opened <= prior:
            raise ValueError("canonical 5m rows must be unique and ordered")
        bars.append(SpotBar(symbol, opened, closed, *(str(value) for value in values)))
        prior = opened
    if not bars:
        raise ValueError(f"canonical 5m data unavailable for {symbol}")
    return tuple(bars)


def expected_reference_time(funding_time_ms: int) -> int:
    return ((funding_time_ms // FIVE_MINUTE_MS) + 1) * FIVE_MINUTE_MS


def _linear_quantile(values: Sequence[Decimal], probability: Decimal) -> Decimal:
    if not values:
        raise ValueError("quantile requires history")
    ordered = sorted(values)
    rank = Decimal(len(ordered) - 1) * probability
    lower = int(rank.to_integral_value(rounding=ROUND_FLOOR))
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _prior_complete_utc_days(points: Sequence[FundingPoint], event: FundingPoint, days: int) -> list[FundingPoint]:
    event_dt = datetime.fromtimestamp(event.funding_time_ms / 1000, tz=timezone.utc)
    current_day = datetime(event_dt.year, event_dt.month, event_dt.day, tzinfo=timezone.utc)
    start_ms = int((current_day - timedelta(days=days)).timestamp() * 1000)
    end_ms = int(current_day.timestamp() * 1000)
    return [point for point in points if start_ms <= point.funding_time_ms < end_ms]


def prior_funding_threshold(
    points: Sequence[FundingPoint],
    event: FundingPoint,
    *,
    days: int,
    probability: Decimal,
) -> Decimal:
    history = _prior_complete_utc_days(points, event, days)
    if not history:
        raise ValueError("funding threshold requires prior complete UTC-day history")
    return _linear_quantile(
        [_decimal(item.funding_rate) * Decimal(365 * 24) / _decimal(item.interval_hours) for item in history],
        probability,
    )


def identify_extremes(points: Sequence[FundingPoint], protocol: Mapping[str, object]) -> tuple[list[FundingPoint], int]:
    cfg = protocol["funding_extreme_event"]
    window_days = int(cfg["history_window_utc_days"])
    probability = _decimal(cfg["lower_tail_percentile"])
    candidates: list[FundingPoint] = []
    for point in points:
        if point.funding_time_ms < IS_START_MS or point.funding_time_ms >= IS_END_EXCLUSIVE_MS:
            continue
        rate = _decimal(point.funding_rate)
        if rate >= 0:
            continue
        history = _prior_complete_utc_days(points, point, window_days)
        if not history:
            continue
        first_day = datetime.fromtimestamp(point.funding_time_ms / 1000, tz=timezone.utc)
        day_start = datetime(first_day.year, first_day.month, first_day.day, tzinfo=timezone.utc) - timedelta(days=window_days)
        if min(item.funding_time_ms for item in history) >= int((day_start + timedelta(days=1)).timestamp() * 1000):
            continue
        annualized = rate * Decimal(365 * 24) / _decimal(point.interval_hours)
        threshold = prior_funding_threshold(points, point, days=window_days, probability=probability)
        if annualized <= threshold:
            candidates.append(point)

    cluster_ms = int(cfg["same_symbol_cluster_hours"]) * HOUR_MS
    representatives: list[FundingPoint] = []
    last_candidate: int | None = None
    for point in candidates:
        if last_candidate is None or point.funding_time_ms - last_candidate > cluster_ms:
            representatives.append(point)
        last_candidate = point.funding_time_ms
    return representatives, len(candidates)


def observe_events(
    *,
    symbol: str,
    points: Sequence[FundingPoint],
    bars: Sequence[SpotBar],
    protocol: Mapping[str, object],
) -> PaperObservationResult:
    representatives, raw_extremes = identify_extremes(points, protocol)
    by_time = {bar.open_time_ms: bar for bar in bars}
    events: list[FundingEvent] = []
    right_censored = 0
    invalid = 0
    for point in representatives:
        reference_time = expected_reference_time(point.funding_time_ms)
        reference = by_time.get(reference_time)
        if reference is None:
            invalid += 1
            continue
        path_times = [reference_time + offset * FIVE_MINUTE_MS for offset in range(24 * 12)]
        path = [by_time.get(timestamp) for timestamp in path_times]
        if any(bar is None for bar in path):
            right_censored += 1
            continue
        complete_path = [bar for bar in path if bar is not None]
        reference_open = _decimal(reference.open)
        displacements: list[tuple[int, float]] = []
        for horizon in HORIZONS:
            close_bar = complete_path[horizon * 12 - 1]
            displacements.append((horizon, float(_decimal(close_bar.close) / reference_open - 1)))
        mae = float(min(_decimal(bar.low) for bar in complete_path) / reference_open - 1)
        mfe = float(max(_decimal(bar.high) for bar in complete_path) / reference_open - 1)
        recovery = next(
            (index * 5 + 5 for index, bar in enumerate(complete_path) if _decimal(bar.close) >= reference_open),
            None,
        )
        rate = _decimal(point.funding_rate)
        annualized = rate * Decimal(365 * 24) / _decimal(point.interval_hours)
        history = _prior_complete_utc_days(points, point, int(protocol["funding_extreme_event"]["history_window_utc_days"]))
        threshold = prior_funding_threshold(
            points,
            point,
            days=int(protocol["funding_extreme_event"]["history_window_utc_days"]),
            probability=_decimal(protocol["funding_extreme_event"]["lower_tail_percentile"]),
        )
        events.append(FundingEvent(
            symbol=symbol,
            funding_time_ms=point.funding_time_ms,
            annualized_rate=str(annualized),
            threshold=str(threshold),
            reference_time_ms=reference_time,
            reference_open=str(reference_open),
            horizon_displacements=tuple(displacements),
            mae_24h=mae,
            mfe_24h=mfe,
            recovery_minutes=recovery,
        ))
    digest = hashlib.sha256()
    for event in events:
        digest.update(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
    return PaperObservationResult(
        tuple(events), raw_extremes, len(representatives), right_censored, invalid, digest.hexdigest()
    )


def _cluster_market_episodes(events: Sequence[FundingEvent], hours: int) -> list[FundingEvent]:
    ordered = sorted(events, key=lambda item: (item.funding_time_ms, item.symbol))
    cluster_ms = hours * HOUR_MS
    episodes: list[FundingEvent] = []
    last_time: int | None = None
    for event in ordered:
        if last_time is None or event.funding_time_ms - last_time > cluster_ms:
            episodes.append(event)
        last_time = event.funding_time_ms
    return episodes


def _quantile_float(values: Sequence[float], probability: float) -> float:
    return float(_linear_quantile([Decimal(str(value)) for value in values], Decimal(str(probability))))


def summarize(results: Sequence[PaperObservationResult], protocol: Mapping[str, object]) -> dict[str, object]:
    events = sorted(
        (event for result in results for event in result.complete_events),
        key=lambda item: (item.funding_time_ms, item.symbol),
    )
    if not events:
        raise ValueError("M1H paper observation produced no complete events")
    episodes = _cluster_market_episodes(events, int(protocol["funding_extreme_event"]["cross_symbol_episode_hours"]))
    gates = protocol["paper_gates"]
    is_days = (IS_END_EXCLUSIVE_MS - IS_START_MS) // DAY_MS
    full_days = 2191
    oos_days = 658
    projected_full = math.floor(len(episodes) / is_days * full_days)
    projected_oos = math.floor(len(episodes) / is_days * oos_days)
    close_24h = [dict(event.horizon_displacements)[24] for event in events]
    mae = [event.mae_24h for event in events]
    mfe = [event.mfe_24h for event in events]
    recovered = [event.recovery_minutes for event in events if event.recovery_minutes is not None]

    by_symbol: dict[str, dict[str, object]] = {}
    for symbol in protocol["scope"]["symbols"]:
        selected = [event for event in events if event.symbol == symbol]
        values = [dict(event.horizon_displacements)[24] for event in selected]
        by_symbol[symbol] = {
            "complete_events": len(selected),
            "median_24h_close_displacement": median(values) if values else None,
            "median_24h_mfe": median([event.mfe_24h for event in selected]) if selected else None,
        }
    by_year: dict[str, int] = {}
    for event in episodes:
        year = str(datetime.fromtimestamp(event.funding_time_ms / 1000, tz=timezone.utc).year)
        by_year[year] = by_year.get(year, 0) + 1
    years_with_ten = sum(count >= 10 for count in by_year.values())
    maximum_year_share = max(by_year.values()) / len(episodes)
    invalid = sum(result.invalid_observations for result in results)

    horizon_stats: dict[str, dict[str, float | int]] = {}
    for horizon in HORIZONS:
        values = [dict(event.horizon_displacements)[horizon] for event in events]
        horizon_stats[str(horizon)] = {
            "count": len(values),
            "median": median(values),
            "p05": _quantile_float(values, 0.05),
            "p95": _quantile_float(values, 0.95),
            "positive_share": sum(value > 0 for value in values) / len(values),
        }
    gate_matrix = {
        "projected_full_independent_episodes": projected_full >= int(gates["projected_full_independent_episodes_minimum"]),
        "projected_sealed_oos_episodes": projected_oos >= int(gates["projected_sealed_oos_episodes_minimum"]),
        "combined_median_24h_close_displacement": median(close_24h) >= float(gates["combined_median_24h_close_displacement_minimum"]),
        "each_symbol_complete_events": all(item["complete_events"] >= int(gates["each_symbol_complete_events_minimum"]) for item in by_symbol.values()),
        "each_symbol_median_24h_close_displacement": all(
            item["median_24h_close_displacement"] is not None
            and item["median_24h_close_displacement"] >= float(gates["each_symbol_median_24h_close_displacement_minimum"])
            for item in by_symbol.values()
        ),
        "year_distribution": years_with_ten >= int(gates["minimum_years_with_ten_independent_episodes"]),
        "single_year_concentration": maximum_year_share <= float(gates["maximum_single_year_episode_share"]),
        "invalid_data_events": invalid <= int(gates["invalid_lineage_interval_quarantine_or_unrewarmed_events_maximum"]),
    }
    return {
        "status": "paper_feasibility_pass" if all(gate_matrix.values()) else "failed_feasibility",
        "raw_extremes": sum(result.raw_extremes for result in results),
        "symbol_cluster_representatives": sum(result.symbol_cluster_representatives for result in results),
        "complete_symbol_events": len(events),
        "independent_market_episodes": len(episodes),
        "right_censored": sum(result.right_censored for result in results),
        "invalid_observations": invalid,
        "projected_full_independent_episodes": projected_full,
        "projected_sealed_oos_episodes": projected_oos,
        "median_24h_mfe": median(mfe),
        "median_24h_close_displacement": median(close_24h),
        "mae_distribution": {
            "minimum": min(mae),
            "p05": _quantile_float(mae, 0.05),
            "median": median(mae),
            "p95": _quantile_float(mae, 0.95),
        },
        "recovery_time_distribution": {
            "recovered_share": len(recovered) / len(events),
            "recovered_median_minutes": median(recovered) if recovered else None,
            "recovered_p90_minutes": _quantile_float([float(value) for value in recovered], 0.90) if recovered else None,
            "unrecovered_count": len(events) - len(recovered),
        },
        "horizon_stats": horizon_stats,
        "by_symbol": by_symbol,
        "by_year": by_year,
        "years_with_ten_episodes": years_with_ten,
        "maximum_single_year_share": maximum_year_share,
        "gate_matrix": gate_matrix,
        "event_sha256": hashlib.sha256("".join(result.canonical_sha256 for result in results).encode("ascii")).hexdigest(),
    }
