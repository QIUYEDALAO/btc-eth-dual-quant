"""IS-only event-study primitives for short-horizon feasibility diagnostics.

Callers provide preregistered event timestamps. This module never detects
events, creates strategy signals, reads OOS prices, or performs execution.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


BAR_MS = 15 * 60 * 1000
HORIZONS = (1, 2, 4, 8, 12, 24)
CLUSTER_MS = 24 * 60 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000


class CostScenario(Enum):
    BASE = ("base", Decimal("0.0015"))
    COST_X2 = ("cost_x2", Decimal("0.0030"))
    EVENT_STRESS_A = ("event_stress_a", Decimal("0.0040"))
    EVENT_STRESS_B = ("event_stress_b", Decimal("0.0055"))

    @property
    def label(self) -> str:
        return str(self.value[0])

    @property
    def per_side(self) -> Decimal:
        return self.value[1]


@dataclass(frozen=True)
class CandidateIdentity:
    candidate_id: str
    hypothesis: str
    sha256: str
    status: str
    oos_opened: bool


@dataclass(frozen=True)
class ISWindow:
    start_ms: int
    end_exclusive_ms: int

    def __post_init__(self) -> None:
        if self.start_ms % BAR_MS or self.end_exclusive_ms % BAR_MS:
            raise ValueError("IS boundaries must align to UTC 15m opens")
        if self.end_exclusive_ms <= self.start_ms:
            raise ValueError("IS end must be after start")

    @property
    def duration_days(self) -> float:
        return (self.end_exclusive_ms - self.start_ms) / DAY_MS


@dataclass(frozen=True)
class EventReference:
    candidate_id: str
    symbol: str
    event_close_ms: int


@dataclass(frozen=True)
class HorizonObservation:
    horizon_bars: int
    exit_close_ms: int
    gross_return: float
    net_returns: tuple[tuple[str, float], ...]
    mae: float
    mfe: float


@dataclass(frozen=True)
class EventObservation:
    reference: EventReference
    entry_open_ms: int
    entry_price: float
    horizons: tuple[HorizonObservation, ...]
    right_censored_horizons: tuple[int, ...]
    input_sha256: str


@dataclass(frozen=True)
class HorizonSummary:
    horizon_bars: int
    samples: int
    gross_mean: float
    gross_median: float
    gross_std: float
    gross_win_rate: float
    gross_p5: float
    gross_p95: float
    cost_x2_mean: float
    mae_mean: float
    mfe_mean: float
    worst_path: float


@dataclass(frozen=True)
class ClusterDiagnostics:
    events: int
    clusters_24h: int
    largest_cluster_24h: int
    max_events_rolling_24h: int
    max_events_rolling_7d: int
    max_events_rolling_30d: int
    events_per_365_days: float
    events_by_utc_month: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class OccupancyDiagnostics:
    horizon_bars: int
    intervals: int
    occupancy_ratio: float
    overlapping_events: int
    max_concurrent_events: int
    longest_sleep_hours: float


@dataclass(frozen=True)
class SampleBudget:
    observed_events: int
    is_days: float
    annual_event_rate: float
    projected_full_events: float
    projected_oos_events: float
    full_days: int
    oos_days: int
    required_full_events: int
    required_oos_events: int
    required_oos_days: int
    full_event_gate: bool
    oos_event_gate: bool
    oos_calendar_gate: bool


@dataclass(frozen=True)
class FeasibilitySummary:
    horizons: tuple[HorizonSummary, ...]
    clustering: ClusterDiagnostics
    occupancy: tuple[OccupancyDiagnostics, ...]
    sample_budget: SampleBudget
    canonical_sha256: str


@dataclass(frozen=True)
class GoldenStructureProfile:
    rows: int
    first_open_ms: int
    last_open_ms: int
    canonical_sha256: str


def validate_candidate_identity(
    ledger_path: Path,
    *,
    candidate_id: str,
    expected_hypothesis: str,
    expected_sha256: str,
) -> CandidateIdentity:
    payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("hash_algorithm") != "sha256":
        raise ValueError("trial ledger must use sha256")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("trial ledger candidates must be a list")
    candidate_ids = [item.get("id") for item in candidates if isinstance(item, dict)]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("trial ledger contains duplicate candidate IDs")
    matches = [item for item in candidates if isinstance(item, dict) and item.get("id") == candidate_id]
    if len(matches) != 1:
        raise ValueError("candidate identity must resolve exactly once")
    candidate = matches[0]
    hypothesis = str(candidate.get("hypothesis", ""))
    digest = str(candidate.get("sha256", ""))
    calculated = hashlib.sha256(hypothesis.encode("utf-8")).hexdigest()
    if hypothesis != expected_hypothesis or digest != expected_sha256 or calculated != digest:
        raise ValueError("candidate hypothesis or hash differs from the preregistered identity")
    if candidate.get("oos_opened") is not False:
        raise ValueError("IS-only harness rejects candidates whose OOS is open")
    if candidate.get("status") != "declared_unopened":
        raise ValueError("IS-only harness requires declared_unopened candidate status")
    return CandidateIdentity(
        candidate_id=candidate_id,
        hypothesis=hypothesis,
        sha256=digest,
        status=str(candidate.get("status", "")),
        oos_opened=False,
    )


def net_return(entry_price: float, exit_price: float, scenario: CostScenario) -> float:
    if entry_price <= 0 or exit_price <= 0:
        raise ValueError("prices must be positive")
    cost = float(scenario.per_side)
    return exit_price * (1 - cost) / (entry_price * (1 + cost)) - 1.0


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_bars(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = [dict(row) for row in rows]
    timestamps = [int(row["open_time"]) for row in normalized]
    if timestamps != sorted(timestamps):
        raise ValueError("15m bars must be sorted")
    if len(timestamps) != len(set(timestamps)):
        raise ValueError("duplicate 15m bar timestamp")
    for index, row in enumerate(normalized):
        timestamp = int(row["open_time"])
        if timestamp % BAR_MS or int(row["close_time"]) != timestamp + BAR_MS - 1:
            raise ValueError("invalid 15m timestamp boundary")
        opened, high, low, close = (float(row[name]) for name in ("open", "high", "low", "close"))
        if min(opened, high, low, close) <= 0 or high < max(opened, close) or low > min(opened, close):
            raise ValueError("invalid 15m OHLC ordering")
        if index and timestamp != timestamps[index - 1] + BAR_MS:
            raise ValueError("15m bars must be contiguous")
    return normalized


def profile_golden_15m(rows: Sequence[Mapping[str, Any]]) -> GoldenStructureProfile:
    normalized = _validate_bars(rows)
    if not normalized:
        raise ValueError("golden 15m profile requires rows")
    return GoldenStructureProfile(
        rows=len(normalized),
        first_open_ms=int(normalized[0]["open_time"]),
        last_open_ms=int(normalized[-1]["open_time"]),
        canonical_sha256=_canonical_sha256(normalized),
    )


def observe_event(
    reference: EventReference,
    *,
    bars: Sequence[Mapping[str, Any]],
    is_window: ISWindow,
) -> EventObservation:
    if not reference.candidate_id or not reference.symbol:
        raise ValueError("event reference requires candidate and symbol")
    rows = _validate_bars(bars)
    event_indexes = [index for index, row in enumerate(rows) if int(row["close_time"]) == reference.event_close_ms]
    if len(event_indexes) != 1:
        raise ValueError("event close must match exactly one completed 15m bar")
    event_index = event_indexes[0]
    event_row = rows[event_index]
    if int(event_row["open_time"]) < is_window.start_ms or reference.event_close_ms >= is_window.end_exclusive_ms:
        raise ValueError("event is outside the IS window")
    if event_index + 1 >= len(rows):
        raise ValueError("event has no next-open entry bar")
    entry_row = rows[event_index + 1]
    entry_open_ms = int(entry_row["open_time"])
    if entry_open_ms != reference.event_close_ms + 1:
        raise ValueError("entry must be the first 15m open after event close")
    if entry_open_ms >= is_window.end_exclusive_ms:
        return EventObservation(reference, entry_open_ms, float(entry_row["open"]), (), HORIZONS, _canonical_sha256(asdict(reference)))

    entry_price = float(entry_row["open"])
    observations: list[HorizonObservation] = []
    censored: list[int] = []
    evidence_rows: list[dict[str, Any]] = [event_row]
    for horizon in HORIZONS:
        expected_exit_close_ms = entry_open_ms + horizon * BAR_MS - 1
        if expected_exit_close_ms >= is_window.end_exclusive_ms:
            censored.append(horizon)
            continue
        exit_index = event_index + horizon
        if exit_index >= len(rows):
            raise ValueError("golden bars end before the declared IS boundary")
        exit_row = rows[exit_index]
        if int(exit_row["close_time"]) != expected_exit_close_ms:
            raise ValueError("horizon close does not match contiguous 15m time semantics")
        path = rows[event_index + 1 : exit_index + 1]
        evidence_rows.extend(path)
        exit_price = float(exit_row["close"])
        gross = exit_price / entry_price - 1.0
        observations.append(
            HorizonObservation(
                horizon_bars=horizon,
                exit_close_ms=int(exit_row["close_time"]),
                gross_return=gross,
                net_returns=tuple((scenario.label, net_return(entry_price, exit_price, scenario)) for scenario in CostScenario),
                mae=min(float(row["low"]) / entry_price - 1.0 for row in path),
                mfe=max(float(row["high"]) / entry_price - 1.0 for row in path),
            )
        )
    evidence = {
        "reference": asdict(reference),
        "entry_open_ms": entry_open_ms,
        "rows": evidence_rows,
        "censored": censored,
    }
    return EventObservation(
        reference=reference,
        entry_open_ms=entry_open_ms,
        entry_price=entry_price,
        horizons=tuple(observations),
        right_censored_horizons=tuple(censored),
        input_sha256=_canonical_sha256(evidence),
    )


def _sample_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower, upper = math.floor(rank), math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_horizons(observations: Sequence[EventObservation]) -> tuple[HorizonSummary, ...]:
    result: list[HorizonSummary] = []
    for horizon in HORIZONS:
        rows = [item for observation in observations for item in observation.horizons if item.horizon_bars == horizon]
        gross = [item.gross_return for item in rows]
        cost_x2 = [dict(item.net_returns)[CostScenario.COST_X2.label] for item in rows]
        maes = [item.mae for item in rows]
        mfes = [item.mfe for item in rows]
        result.append(
            HorizonSummary(
                horizon_bars=horizon,
                samples=len(rows),
                gross_mean=sum(gross) / len(gross) if gross else 0.0,
                gross_median=_percentile(gross, 0.5),
                gross_std=_sample_std(gross),
                gross_win_rate=sum(value > 0 for value in gross) / len(gross) if gross else 0.0,
                gross_p5=_percentile(gross, 0.05),
                gross_p95=_percentile(gross, 0.95),
                cost_x2_mean=sum(cost_x2) / len(cost_x2) if cost_x2 else 0.0,
                mae_mean=sum(maes) / len(maes) if maes else 0.0,
                mfe_mean=sum(mfes) / len(mfes) if mfes else 0.0,
                worst_path=min(maes, default=0.0),
            )
        )
    return tuple(result)


def _max_in_window(timestamps: Sequence[int], window_ms: int) -> int:
    left = 0
    maximum = 0
    for right, timestamp in enumerate(timestamps):
        while timestamp - timestamps[left] >= window_ms:
            left += 1
        maximum = max(maximum, right - left + 1)
    return maximum


def cluster_diagnostics(observations: Sequence[EventObservation], is_window: ISWindow) -> ClusterDiagnostics:
    timestamps = sorted(item.reference.event_close_ms for item in observations)
    monthly: dict[str, int] = {}
    for timestamp in timestamps:
        key = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + 1
    clusters: list[int] = []
    current = 0
    previous: int | None = None
    for timestamp in timestamps:
        if previous is None or timestamp - previous <= CLUSTER_MS:
            current += 1
        else:
            clusters.append(current)
            current = 1
        previous = timestamp
    if current:
        clusters.append(current)
    return ClusterDiagnostics(
        events=len(timestamps),
        clusters_24h=len(clusters),
        largest_cluster_24h=max(clusters, default=0),
        max_events_rolling_24h=_max_in_window(timestamps, DAY_MS) if timestamps else 0,
        max_events_rolling_7d=_max_in_window(timestamps, 7 * DAY_MS) if timestamps else 0,
        max_events_rolling_30d=_max_in_window(timestamps, 30 * DAY_MS) if timestamps else 0,
        events_per_365_days=len(timestamps) * 365 / is_window.duration_days,
        events_by_utc_month=tuple(sorted(monthly.items())),
    )


def occupancy_diagnostics(observations: Sequence[EventObservation], is_window: ISWindow) -> tuple[OccupancyDiagnostics, ...]:
    output: list[OccupancyDiagnostics] = []
    for horizon in HORIZONS:
        intervals = sorted(
            (observation.entry_open_ms, item.exit_close_ms + 1)
            for observation in observations
            for item in observation.horizons
            if item.horizon_bars == horizon
        )
        merged: list[list[int]] = []
        overlapping = 0
        events: list[tuple[int, int]] = []
        for start, end in intervals:
            events.extend(((start, 1), (end, -1)))
            if merged and start < merged[-1][1]:
                overlapping += 1
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        occupied_ms = sum(end - start for start, end in merged)
        concurrent = maximum = 0
        for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
            concurrent += delta
            maximum = max(maximum, concurrent)
        sleep_spans: list[int] = []
        cursor = is_window.start_ms
        for start, end in merged:
            sleep_spans.append(max(0, start - cursor))
            cursor = max(cursor, end)
        sleep_spans.append(max(0, is_window.end_exclusive_ms - cursor))
        output.append(
            OccupancyDiagnostics(
                horizon_bars=horizon,
                intervals=len(intervals),
                occupancy_ratio=occupied_ms / (is_window.end_exclusive_ms - is_window.start_ms),
                overlapping_events=overlapping,
                max_concurrent_events=maximum,
                longest_sleep_hours=max(sleep_spans, default=0) / (60 * 60 * 1000),
            )
        )
    return tuple(output)


def project_sample_budget(
    *,
    observed_events: int,
    is_days: float,
    full_days: int,
    oos_days: int,
    required_full_events: int = 120,
    required_oos_events: int = 30,
    required_oos_days: int = 540,
) -> SampleBudget:
    if min(observed_events, is_days, full_days, oos_days) < 0 or is_days == 0:
        raise ValueError("sample-budget inputs must be non-negative with positive IS days")
    annual_rate = observed_events * 365 / is_days
    projected_full = observed_events / is_days * full_days
    projected_oos = observed_events / is_days * oos_days
    return SampleBudget(
        observed_events=observed_events,
        is_days=is_days,
        annual_event_rate=annual_rate,
        projected_full_events=projected_full,
        projected_oos_events=projected_oos,
        full_days=full_days,
        oos_days=oos_days,
        required_full_events=required_full_events,
        required_oos_events=required_oos_events,
        required_oos_days=required_oos_days,
        full_event_gate=projected_full >= required_full_events,
        oos_event_gate=projected_oos >= required_oos_events,
        oos_calendar_gate=oos_days >= required_oos_days,
    )


def build_feasibility_summary(
    observations: Sequence[EventObservation],
    *,
    is_window: ISWindow,
    full_days: int,
    oos_days: int,
) -> FeasibilitySummary:
    ordered = tuple(sorted(observations, key=lambda item: (item.reference.event_close_ms, item.reference.symbol)))
    if any(item.entry_open_ms < is_window.start_ms or item.entry_open_ms >= is_window.end_exclusive_ms for item in ordered):
        raise ValueError("observation falls outside IS")
    horizons = summarize_horizons(ordered)
    clustering = cluster_diagnostics(ordered, is_window)
    occupancy = occupancy_diagnostics(ordered, is_window)
    budget = project_sample_budget(
        observed_events=len(ordered),
        is_days=is_window.duration_days,
        full_days=full_days,
        oos_days=oos_days,
    )
    canonical = {
        "observations": [asdict(item) for item in ordered],
        "horizons": [asdict(item) for item in horizons],
        "clustering": asdict(clustering),
        "occupancy": [asdict(item) for item in occupancy],
        "sample_budget": asdict(budget),
    }
    return FeasibilitySummary(horizons, clustering, occupancy, budget, _canonical_sha256(canonical))
