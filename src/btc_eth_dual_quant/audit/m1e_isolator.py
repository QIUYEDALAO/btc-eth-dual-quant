"""M1E in-sample isolation with a physically sealed OOS boundary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping


IS_START_MS = int(datetime(2020, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
IS_END_EXCLUSIVE_MS = int(datetime(2024, 9, 11, tzinfo=timezone.utc).timestamp() * 1000)
INTERVAL_MS = {"1h": 60 * 60 * 1000, "4h": 4 * 60 * 60 * 1000}
SYMBOLS = ("BTCUSDT", "ETHUSDT")
FIELDS = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume",
)


@dataclass(frozen=True)
class IsolatedBar:
    symbol: str
    timeframe: str
    open_time: int
    close_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    quote_volume: str
    trade_count: str
    taker_buy_base_volume: str
    taker_buy_quote_volume: str
    segment_id: int
    bars_since_segment_start: int


@dataclass(frozen=True)
class IsolationResult:
    symbol: str
    timeframe: str
    rows: tuple[IsolatedBar, ...]
    gap_count: int
    segment_count: int
    canonical_sha256: str


def _decimal(value: object) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite value")
    return result


def _validate_row(row: Mapping[str, object], timeframe: str) -> None:
    missing = [field for field in FIELDS if field not in row]
    if missing:
        raise ValueError(f"missing fields: {','.join(missing)}")
    interval = INTERVAL_MS[timeframe]
    opened_at = int(row["open_time"])
    closed_at = int(row["close_time"])
    if opened_at < IS_START_MS or opened_at >= IS_END_EXCLUSIVE_MS:
        raise ValueError("bar outside sealed IS window")
    if opened_at % interval or closed_at != opened_at + interval - 1:
        raise ValueError("unaligned or incomplete bar")
    opened, high, low, closed = (_decimal(row[field]) for field in ("open", "high", "low", "close"))
    if min(opened, high, low, closed) <= 0:
        raise ValueError("non-positive OHLC")
    if high < max(opened, low, closed) or low > min(opened, high, closed):
        raise ValueError("illegal OHLC ordering")
    for field in ("volume", "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume"):
        if _decimal(row[field]) < 0:
            raise ValueError(f"negative {field}")


def isolate_bars(*, symbol: str, timeframe: str, rows: Iterable[Mapping[str, object]]) -> IsolationResult:
    if symbol not in SYMBOLS:
        raise ValueError("M1E supports only BTCUSDT and ETHUSDT")
    if timeframe not in INTERVAL_MS:
        raise ValueError("M1E signal isolation supports only 1h and 4h")

    interval = INTERVAL_MS[timeframe]
    isolated: list[IsolatedBar] = []
    prior: int | None = None
    segment = 0
    age = 0
    gaps = 0
    for source in rows:
        row = dict(source)
        _validate_row(row, timeframe)
        timestamp = int(row["open_time"])
        if prior is not None and timestamp <= prior:
            raise ValueError("bars must be strictly increasing and unique")
        if prior is None or timestamp != prior + interval:
            if prior is not None:
                gaps += 1
            segment += 1
            age = 1
        else:
            age += 1
        isolated.append(IsolatedBar(
            symbol=symbol,
            timeframe=timeframe,
            open_time=timestamp,
            close_time=int(row["close_time"]),
            open=str(row["open"]),
            high=str(row["high"]),
            low=str(row["low"]),
            close=str(row["close"]),
            volume=str(row["volume"]),
            quote_volume=str(row["quote_volume"]),
            trade_count=str(row["trade_count"]),
            taker_buy_base_volume=str(row["taker_buy_base_volume"]),
            taker_buy_quote_volume=str(row["taker_buy_quote_volume"]),
            segment_id=segment,
            bars_since_segment_start=age,
        ))
        prior = timestamp

    digest = hashlib.sha256()
    for row in isolated:
        digest.update(json.dumps(asdict(row), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return IsolationResult(symbol, timeframe, tuple(isolated), gaps, segment, digest.hexdigest())


def eligible_after_rewarm(row: IsolatedBar, required_bars: int) -> bool:
    """Apply a later frozen warmup without changing the isolated snapshot."""
    if not isinstance(required_bars, int) or required_bars <= 0:
        raise ValueError("required_bars must be a positive frozen integer")
    return row.bars_since_segment_start >= required_bars
