"""Funding interval inference and annualization."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


MS_PER_HOUR = Decimal("3600000")
HOURS_PER_YEAR = Decimal(365 * 24)


@dataclass(frozen=True)
class FundingIntervalResult:
    hours: Decimal
    source: str
    warnings: list[str]
    candidates: dict[str, Decimal]
    event_intervals: dict[int, Decimal]


def _as_decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _funding_info_interval(funding_info: Any, symbol: str) -> Decimal | None:
    if not funding_info:
        return None
    records = funding_info if isinstance(funding_info, list) else [funding_info]
    for record in records:
        if record.get("symbol") in (symbol, None) and record.get("fundingIntervalHours") is not None:
            return _as_decimal(record["fundingIntervalHours"])
    return None


def _premium_index_interval(
    premium_index: Any,
    symbol: str,
    funding_rate_history: list[dict[str, Any]] | None,
) -> Decimal | None:
    if not premium_index:
        return None
    records = premium_index if isinstance(premium_index, list) else [premium_index]
    next_times = sorted(
        {
            int(record["nextFundingTime"])
            for record in records
            if isinstance(record, dict)
            and record.get("symbol") in (symbol, None)
            and record.get("nextFundingTime") is not None
        }
    )
    next_deltas = [cur - prev for prev, cur in zip(next_times, next_times[1:]) if cur > prev]
    if next_deltas:
        delta_ms = Counter(next_deltas).most_common(1)[0][0]
        return Decimal(delta_ms) / MS_PER_HOUR

    # A single snapshot only reports time remaining until the next settlement.
    # It becomes a full-period candidate only when paired with the immediately
    # preceding observed settlement timestamp.
    if len(next_times) == 1 and funding_rate_history:
        historical_times = sorted(
            {
                int(record["fundingTime"])
                for record in funding_rate_history
                if record.get("symbol", symbol) == symbol and record.get("fundingTime") is not None
            }
        )
        previous = [time_ms for time_ms in historical_times if time_ms < next_times[0]]
        if previous:
            delta_ms = next_times[0] - previous[-1]
            historical_deltas = [cur - prev for prev, cur in zip(historical_times, historical_times[1:]) if cur > prev]
            if not historical_deltas or delta_ms <= max(historical_deltas):
                return Decimal(delta_ms) / MS_PER_HOUR
    return None


def _history_intervals(
    funding_rate_history: list[dict[str, Any]] | None,
    symbol: str,
) -> tuple[Decimal | None, dict[int, Decimal]]:
    if not funding_rate_history:
        return None, {}
    times = sorted(
        int(record["fundingTime"])
        for record in funding_rate_history
        if record.get("symbol", symbol) == symbol and record.get("fundingTime") is not None
    )
    deltas = [cur - prev for prev, cur in zip(times, times[1:]) if cur > prev]
    if not deltas:
        return None, {}
    delta_ms = Counter(deltas).most_common(1)[0][0]
    event_intervals: dict[int, Decimal] = {times[0]: Decimal(deltas[0]) / MS_PER_HOUR}
    for prev, cur in zip(times, times[1:]):
        if cur > prev:
            event_intervals[cur] = Decimal(cur - prev) / MS_PER_HOUR
    return Decimal(delta_ms) / MS_PER_HOUR, event_intervals


def infer_funding_interval_hours(
    symbol: str,
    funding_info: Any = None,
    premium_index: Any = None,
    funding_rate_history: list[dict[str, Any]] | None = None,
) -> FundingIntervalResult:
    """Infer interval without assuming an 8-hour period."""

    candidates: dict[str, Decimal] = {}
    info_value = _funding_info_interval(funding_info, symbol)
    if info_value is not None:
        candidates["fundingInfo.fundingIntervalHours"] = info_value
    premium_value = _premium_index_interval(premium_index, symbol, funding_rate_history)
    if premium_value is not None:
        candidates["premiumIndex.nextFundingTime"] = premium_value
    history_value, event_intervals = _history_intervals(funding_rate_history, symbol)
    if history_value is not None:
        candidates["fundingRate.fundingTime"] = history_value

    if not candidates:
        raise ValueError(f"cannot infer funding interval for {symbol}")

    preferred_order = [
        "fundingInfo.fundingIntervalHours",
        "premiumIndex.nextFundingTime",
        "fundingRate.fundingTime",
    ]
    preferred_source = next(source for source in preferred_order if source in candidates)
    preferred_value = candidates[preferred_source]
    unique_values = set(candidates.values())
    warnings: list[str] = []
    if len(unique_values) > 1:
        conservative = min(unique_values)
        warnings.append(
            f"funding interval conflict for {symbol}: {candidates}; using shorter {conservative}h"
        )
        return FundingIntervalResult(
            conservative,
            "conflict_shorter_interval",
            warnings,
            candidates,
            event_intervals,
        )
    return FundingIntervalResult(preferred_value, preferred_source, warnings, candidates, event_intervals)


def annualize_funding_rate(period_rate: Decimal | str | float, interval_hours: Decimal | str | float) -> Decimal:
    hours = _as_decimal(interval_hours)
    if hours <= 0:
        raise ValueError("interval_hours must be positive")
    return _as_decimal(period_rate) * (HOURS_PER_YEAR / hours)
