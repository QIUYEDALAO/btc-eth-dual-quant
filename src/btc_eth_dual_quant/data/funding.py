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


def _premium_index_interval(premium_index: Any, symbol: str) -> Decimal | None:
    if not premium_index:
        return None
    records = premium_index if isinstance(premium_index, list) else [premium_index]
    for record in records:
        if (
            record.get("symbol") in (symbol, None)
            and record.get("nextFundingTime") is not None
            and record.get("time") is not None
        ):
            delta_ms = _as_decimal(record["nextFundingTime"]) - _as_decimal(record["time"])
            if delta_ms > 0:
                return delta_ms / MS_PER_HOUR
    return None


def _history_interval(funding_rate_history: list[dict[str, Any]] | None, symbol: str) -> Decimal | None:
    if not funding_rate_history:
        return None
    times = sorted(
        int(record["fundingTime"])
        for record in funding_rate_history
        if record.get("symbol", symbol) == symbol and record.get("fundingTime") is not None
    )
    deltas = [cur - prev for prev, cur in zip(times, times[1:]) if cur > prev]
    if not deltas:
        return None
    delta_ms = Counter(deltas).most_common(1)[0][0]
    return Decimal(delta_ms) / MS_PER_HOUR


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
    premium_value = _premium_index_interval(premium_index, symbol)
    if premium_value is not None:
        candidates["premiumIndex.nextFundingTime"] = premium_value
    history_value = _history_interval(funding_rate_history, symbol)
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
        return FundingIntervalResult(conservative, "conflict_shorter_interval", warnings, candidates)
    return FundingIntervalResult(preferred_value, preferred_source, warnings, candidates)


def annualize_funding_rate(period_rate: Decimal | str | float, interval_hours: Decimal | str | float) -> Decimal:
    hours = _as_decimal(interval_hours)
    if hours <= 0:
        raise ValueError("interval_hours must be positive")
    return _as_decimal(period_rate) * (HOURS_PER_YEAR / hours)
