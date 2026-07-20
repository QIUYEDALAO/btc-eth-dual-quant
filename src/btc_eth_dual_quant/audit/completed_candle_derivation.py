"""Result-free completed-candle derivation for the ADR-0016 route.

The functions operate on already qualified synthetic or canonical 5m rows.
They do not read storage, select signals, calculate performance, or execute
orders.  Missing, masked, or lifecycle-ineligible constituents are never
filled and never searched past.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping


FIVE_MINUTE_MS = 300_000
WINDOWS = {"15m": 3, "1h": 12, "4h": 48}


@dataclass(frozen=True)
class FiveMinuteCandle:
    symbol: str
    open_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class CompletedCandle:
    symbol: str
    timeframe: str
    open_time_ms: int
    close_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    constituent_count: int


def canonical_candle_hash(rows: Iterable[CompletedCandle]) -> str:
    payload = [asdict(row) for row in sorted(rows, key=lambda item: (item.symbol, item.timeframe, item.open_time_ms))]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def derive_completed_candles(
    rows: Iterable[FiveMinuteCandle],
    *,
    timeframe: str,
    eligible_slots: Mapping[tuple[str, int], bool],
) -> tuple[CompletedCandle, ...]:
    if timeframe not in WINDOWS:
        raise ValueError("unsupported completed-candle timeframe")
    count = WINDOWS[timeframe]
    width = FIVE_MINUTE_MS * count
    ordered = sorted(rows, key=lambda item: (item.symbol, item.open_time_ms))
    identities = [(item.symbol, item.open_time_ms) for item in ordered]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate 5m candle")
    for item in ordered:
        values = (item.open, item.high, item.low, item.close, item.volume)
        if item.open_time_ms % FIVE_MINUTE_MS or any(not math.isfinite(value) for value in values):
            raise ValueError("invalid 5m candle")
        if item.low > min(item.open, item.close) or item.high < max(item.open, item.close) or item.volume < 0:
            raise ValueError("illegal 5m OHLCV")

    groups: dict[tuple[str, int], list[FiveMinuteCandle]] = {}
    for item in ordered:
        groups.setdefault((item.symbol, item.open_time_ms // width * width), []).append(item)
    derived: list[CompletedCandle] = []
    for (symbol, start), members in sorted(groups.items()):
        expected = [start + index * FIVE_MINUTE_MS for index in range(count)]
        actual = [item.open_time_ms for item in members]
        # An incomplete, masked, or lifecycle-crossing window is ineligible.
        if actual != expected:
            continue
        slot_states = [eligible_slots.get((symbol, slot)) for slot in expected]
        if any(state is None for state in slot_states):
            raise ValueError("missing lifecycle/mask authority")
        if not all(slot_states):
            continue
        derived.append(CompletedCandle(
            symbol=symbol,
            timeframe=timeframe,
            open_time_ms=start,
            close_time_ms=start + width - 1,
            open=members[0].open,
            high=max(item.high for item in members),
            low=min(item.low for item in members),
            close=members[-1].close,
            volume=sum(item.volume for item in members),
            constituent_count=count,
        ))
    return tuple(derived)


def next_eligible_five_minute_open(
    *,
    completed: CompletedCandle,
    five_minute_rows: Mapping[tuple[str, int], FiveMinuteCandle],
    eligible_slots: Mapping[tuple[str, int], bool],
) -> FiveMinuteCandle:
    next_open = completed.close_time_ms + 1
    identity = (completed.symbol, next_open)
    if eligible_slots.get(identity) is not True:
        raise ValueError("strict next 5m slot is not eligible")
    row = five_minute_rows.get(identity)
    if row is None:
        raise ValueError("strict next 5m open is missing")
    return row
