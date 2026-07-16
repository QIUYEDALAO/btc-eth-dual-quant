"""Independent, fixture-first primitives for the frozen U-03F V4 audit.

This module intentionally shares no production liquid-universe implementation.
It contains only independently specified parsing, integer-time, ranking, grid,
availability and aggregation primitives. Production JSON may be an input
specification or comparison target, never an execution oracle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any, Iterable, Mapping, Sequence


IDENTITY_METADATA_KEYS = frozenset({"generated_at", "generated_utc", "path", "worker", "workers"})
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite Decimal is forbidden")
        return format(value, "f")
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("NaN and Infinity are forbidden")
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key) not in IDENTITY_METADATA_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def audit_canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    )


def audit_content_hash(value: Any) -> str:
    return hashlib.sha256(audit_canonical_json(value).encode("utf-8")).hexdigest()


def milliseconds_from_utc(text: str) -> int:
    if not text.endswith("Z"):
        raise ValueError("timestamp must use UTC Z suffix")
    parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    delta = parsed - EPOCH
    return delta.days * 86_400_000 + delta.seconds * 1_000 + delta.microseconds // 1_000


def normalize_raw_timestamp(value: str | int) -> int:
    raw = int(value)
    if raw < 0:
        raise ValueError("negative epoch is forbidden")
    if raw >= 10**14:
        if raw % 1_000:
            raise ValueError("microsecond timestamp is not millisecond aligned")
        raw //= 1_000
    if raw >= 10**14 or raw < 10**11:
        raise ValueError("unsupported epoch unit")
    return raw


@dataclass(frozen=True)
class KlineRow:
    open_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    base_volume: Decimal
    close_time_ms: int
    quote_volume: Decimal
    trade_count: int
    taker_base_volume: Decimal
    taker_quote_volume: Decimal
    ignore: str
    raw_fields: tuple[str, ...]

    @classmethod
    def from_fields(cls, fields: Sequence[str]) -> "KlineRow":
        if len(fields) != 12:
            raise ValueError("Binance kline must contain exactly 12 fields")
        raw = tuple(str(item).strip() for item in fields)
        try:
            open_time = normalize_raw_timestamp(raw[0])
            close_time = normalize_raw_timestamp(raw[6])
            values = tuple(Decimal(raw[index]) for index in (1, 2, 3, 4, 5, 7, 9, 10))
            trades = int(raw[8])
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid kline field") from exc
        op, high, low, close, base, quote, taker_base, taker_quote = values
        if any(not item.is_finite() for item in values):
            raise ValueError("non-finite kline value")
        if high < max(op, close) or low > min(op, close) or high < low:
            raise ValueError("invalid OHLC ordering")
        if any(item < 0 for item in (base, quote, taker_base, taker_quote)) or trades < 0:
            raise ValueError("negative flow field")
        if close_time < open_time:
            raise ValueError("close precedes open")
        return cls(open_time, op, high, low, close, base, close_time, quote, trades, taker_base, taker_quote, raw[11], raw)

    def semantic_tuple(self) -> tuple[Any, ...]:
        return (
            self.open_time_ms, self.open, self.high, self.low, self.close,
            self.base_volume, self.close_time_ms, self.quote_volume,
            self.trade_count, self.taker_base_volume, self.taker_quote_volume,
        )


def reconcile_daily_authority(
    monthly: Sequence[KlineRow], daily: Sequence[KlineRow]
) -> tuple[tuple[KlineRow, ...], list[dict[str, Any]]]:
    monthly_by_time: dict[int, KlineRow] = {}
    for item in monthly:
        if item.open_time_ms in monthly_by_time:
            raise ValueError("unregistered monthly duplicate")
        monthly_by_time[item.open_time_ms] = item
    daily_by_time: dict[int, KlineRow] = {}
    for item in daily:
        if item.open_time_ms in daily_by_time:
            raise ValueError("unregistered daily duplicate")
        daily_by_time[item.open_time_ms] = item
    conflicts: list[dict[str, Any]] = []
    merged = dict(monthly_by_time)
    for timestamp, item in daily_by_time.items():
        primary = monthly_by_time.get(timestamp)
        if primary is None:
            merged[timestamp] = item
        elif primary.semantic_tuple() != item.semantic_tuple():
            conflicts.append({"open_time_ms": timestamp, "monthly": primary.raw_fields, "daily": item.raw_fields})
    return tuple(merged[key] for key in sorted(merged)), conflicts


def rank_membership(
    effective_month: str,
    daily_quote_volumes: Mapping[str, Sequence[Decimal]],
    *,
    target_size: int = 15,
) -> list[dict[str, Any]]:
    if len(effective_month) != 7 or effective_month[4] != "-":
        raise ValueError("effective month must be YYYY-MM")
    ranked: list[tuple[Decimal, str]] = []
    for symbol, values in daily_quote_volumes.items():
        if len(values) != 90:
            raise ValueError(f"{symbol} lacks the exact prior 90 complete days")
        if any(not value.is_finite() or value < 0 for value in values):
            raise ValueError("invalid ranking value")
        ranked.append((median(values), symbol))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        {"effective_month": effective_month, "rank": index, "symbol": symbol, "median_daily_quote_volume_90d": format(metric, "f")}
        for index, (metric, symbol) in enumerate(ranked[:target_size], start=1)
    ]


def expected_slots(
    start_ms: int,
    end_exclusive_ms: int,
    step_ms: int,
    *,
    availability_end_exclusive: int | None = None,
) -> tuple[int, ...]:
    if step_ms <= 0 or start_ms % step_ms or end_exclusive_ms % step_ms:
        raise ValueError("grid boundaries must be integer-aligned")
    limit = min(end_exclusive_ms, availability_end_exclusive) if availability_end_exclusive is not None else end_exclusive_ms
    if limit < start_ms:
        return ()
    return tuple(range(start_ms, limit, step_ms))


@dataclass(frozen=True)
class FiveMinuteBar:
    open_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def aggregate_one_hour(bars: Iterable[FiveMinuteBar]) -> list[dict[str, Any]]:
    ordered = sorted(bars, key=lambda item: item.open_time_ms)
    if len({bar.open_time_ms for bar in ordered}) != len(ordered):
        raise ValueError("duplicate 5m timestamp")
    grouped: dict[int, list[FiveMinuteBar]] = {}
    for bar in ordered:
        grouped.setdefault((bar.open_time_ms // 3_600_000) * 3_600_000, []).append(bar)
    output: list[dict[str, Any]] = []
    for hour, group in sorted(grouped.items()):
        if tuple(item.open_time_ms for item in group) != expected_slots(hour, hour + 3_600_000, 300_000):
            continue
        output.append({
            "open_time_ms": hour,
            "open": format(group[0].open, "f"),
            "high": format(max(item.high for item in group), "f"),
            "low": format(min(item.low for item in group), "f"),
            "close": format(group[-1].close, "f"),
            "volume": format(sum((item.volume for item in group), Decimal(0)), "f"),
        })
    return output


@dataclass(frozen=True)
class LifecycleEvent:
    event_id: str
    symbol: str
    known_at_ms: int
    effective_at_ms: int
    availability_end_exclusive_ms: int
    last_valid_market_time_ms: int
    source: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LifecycleEvent":
        if value.get("successor_authority") != "provenance_only":
            raise ValueError("successor cannot inherit history or rank")
        known = milliseconds_from_utc(str(value["known_at"]))
        effective = milliseconds_from_utc(str(value["effective_at"]))
        end = milliseconds_from_utc(str(value["availability_end_exclusive"]))
        last = milliseconds_from_utc(str(value["last_valid_market_time"]))
        if not known < effective or end != effective or last + 1 != end:
            raise ValueError("invalid lifecycle boundary")
        return cls(str(value["event_id"]), str(value["symbol"]), known, effective, end, last, dict(value))


def availability_state(event: LifecycleEvent, timestamp_ms: int) -> str:
    return "active_partial" if timestamp_ms < event.availability_end_exclusive_ms else "lifecycle_terminated"


def attribute_gap(members: set[str], missing_symbols: set[str]) -> str:
    if not missing_symbols:
        return "clean"
    if missing_symbols == members and members:
        return "global_outage"
    if missing_symbols <= members:
        return "symbol_month_quarantine"
    return "unresolved_blocked"
