"""Result-free active-interval isolation for external-strategy original IS.

The module is deliberately independent of Freqtrade and storage.  It turns an
already qualified 5m stream into immutable per-membership segments, derives
completed strategy candles inside each segment, enforces reset/rewarm, and
keeps membership-exit rows in a separate exact-key execution lookup.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping

from btc_eth_dual_quant.audit.completed_candle_derivation import (
    FIVE_MINUTE_MS,
    CompletedCandle,
    FiveMinuteCandle,
    derive_completed_candles,
    next_eligible_five_minute_open,
)


IS_END_MS = 1_726_012_800_000


@dataclass(frozen=True)
class ActiveInterval:
    symbol: str
    start_inclusive_ms: int
    end_exclusive_ms: int


@dataclass(frozen=True)
class CandidateSegment:
    segment_id: str
    symbol: str
    start_inclusive_ms: int
    end_exclusive_ms: int
    timeframe: str
    startup_candle_count: int
    five_minute_rows: tuple[FiveMinuteCandle, ...]
    completed_candles: tuple[CompletedCandle, ...]
    entry_eligible_candles: tuple[CompletedCandle, ...]


@dataclass(frozen=True)
class BoundaryExitRow:
    symbol: str
    open_time_ms: int
    close_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    raw_line_sha256: str


def _valid_ohlcv(row: FiveMinuteCandle | BoundaryExitRow) -> bool:
    values = (row.open, row.high, row.low, row.close, row.volume)
    return (
        all(math.isfinite(float(value)) for value in values)
        and row.low <= min(row.open, row.close)
        and row.high >= max(row.open, row.close)
        and row.volume >= 0
    )


def _segment_id(interval: ActiveInterval) -> str:
    payload = {
        "symbol": interval.symbol,
        "start_inclusive_ms": interval.start_inclusive_ms,
        "end_exclusive_ms": interval.end_exclusive_ms,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _validate_intervals(intervals: Iterable[ActiveInterval], *, is_end_ms: int) -> tuple[ActiveInterval, ...]:
    ordered = tuple(sorted(intervals, key=lambda item: (item.symbol, item.start_inclusive_ms, item.end_exclusive_ms)))
    identities = {(item.symbol, item.start_inclusive_ms, item.end_exclusive_ms) for item in ordered}
    if len(identities) != len(ordered):
        raise ValueError("duplicate active interval")
    previous: dict[str, ActiveInterval] = {}
    for item in ordered:
        if not item.symbol or item.start_inclusive_ms % FIVE_MINUTE_MS or item.end_exclusive_ms % FIVE_MINUTE_MS:
            raise ValueError("invalid active interval identity")
        if item.start_inclusive_ms >= item.end_exclusive_ms or item.end_exclusive_ms > is_end_ms:
            raise ValueError("active interval crosses sealed IS/OOS boundary")
        prior = previous.get(item.symbol)
        if prior is not None and item.start_inclusive_ms < prior.end_exclusive_ms:
            raise ValueError("overlapping active intervals")
        previous[item.symbol] = item
    return ordered


def _completed_five_minute(rows: tuple[FiveMinuteCandle, ...]) -> tuple[CompletedCandle, ...]:
    return tuple(
        CompletedCandle(
            symbol=row.symbol,
            timeframe="5m",
            open_time_ms=row.open_time_ms,
            close_time_ms=row.open_time_ms + FIVE_MINUTE_MS - 1,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            constituent_count=1,
        )
        for row in rows
    )


def build_candidate_segments(
    rows: Iterable[FiveMinuteCandle],
    intervals: Iterable[ActiveInterval],
    *,
    timeframe: str,
    startup_candle_count: int,
    is_end_ms: int = IS_END_MS,
) -> tuple[CandidateSegment, ...]:
    """Derive isolated segments with a fresh indicator age at every admission."""

    if timeframe not in {"5m", "15m", "1h", "4h"}:
        raise ValueError("unsupported strategy timeframe")
    if type(startup_candle_count) is not int or startup_candle_count < 0:
        raise ValueError("invalid startup candle count")
    authority = _validate_intervals(intervals, is_end_ms=is_end_ms)
    ordered_rows = tuple(sorted(rows, key=lambda item: (item.symbol, item.open_time_ms)))
    identities = [(item.symbol, item.open_time_ms) for item in ordered_rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate 5m row")
    for row in ordered_rows:
        if row.open_time_ms % FIVE_MINUTE_MS or row.open_time_ms >= is_end_ms or not _valid_ohlcv(row):
            raise ValueError("invalid or OOS 5m row")

    by_symbol: dict[str, list[ActiveInterval]] = {}
    for interval in authority:
        by_symbol.setdefault(interval.symbol, []).append(interval)
    assigned: dict[str, list[FiveMinuteCandle]] = {_segment_id(interval): [] for interval in authority}
    for row in ordered_rows:
        matches = [
            interval
            for interval in by_symbol.get(row.symbol, [])
            if interval.start_inclusive_ms <= row.open_time_ms < interval.end_exclusive_ms
        ]
        if len(matches) != 1:
            raise ValueError("5m row lacks one exact active-interval authority")
        assigned[_segment_id(matches[0])].append(row)

    result: list[CandidateSegment] = []
    for interval in authority:
        segment_id = _segment_id(interval)
        segment_rows = tuple(sorted(assigned[segment_id], key=lambda item: item.open_time_ms))
        if not segment_rows:
            raise ValueError("active interval has no qualified rows")
        if segment_rows[0].open_time_ms != interval.start_inclusive_ms:
            raise ValueError("active interval first 5m row missing")
        for previous, current in zip(segment_rows, segment_rows[1:]):
            if current.open_time_ms != previous.open_time_ms + FIVE_MINUTE_MS:
                raise ValueError("active interval contains a 5m gap")
        eligible = {(row.symbol, row.open_time_ms): True for row in segment_rows}
        completed = (
            _completed_five_minute(segment_rows)
            if timeframe == "5m"
            else derive_completed_candles(segment_rows, timeframe=timeframe, eligible_slots=eligible)
        )
        # Freqtrade evaluates signals only after startup_candle_count completed
        # candles.  The age starts from zero for every segment; no prior segment
        # is visible to the calculation.
        ready = completed[startup_candle_count:]
        result.append(
            CandidateSegment(
                segment_id=segment_id,
                symbol=interval.symbol,
                start_inclusive_ms=interval.start_inclusive_ms,
                end_exclusive_ms=interval.end_exclusive_ms,
                timeframe=timeframe,
                startup_candle_count=startup_candle_count,
                five_minute_rows=segment_rows,
                completed_candles=completed,
                entry_eligible_candles=ready,
            )
        )
    return tuple(result)


def strict_next_entry_open(segment: CandidateSegment, completed: CompletedCandle) -> FiveMinuteCandle:
    rows = {(row.symbol, row.open_time_ms): row for row in segment.five_minute_rows}
    eligible = {(row.symbol, row.open_time_ms): True for row in segment.five_minute_rows}
    row = next_eligible_five_minute_open(
        completed=completed,
        five_minute_rows=rows,
        eligible_slots=eligible,
    )
    if row.open_time_ms >= segment.end_exclusive_ms:
        raise ValueError("strict next open crosses active interval")
    return row


def boundary_lookup_from_authority(
    records: Iterable[Mapping[str, object]],
    *,
    required_count: int = 92,
    is_end_ms: int = IS_END_MS,
) -> dict[tuple[str, int], BoundaryExitRow]:
    """Build an exact-key forced-exit lookup without returning indicator rows."""

    lookup: dict[tuple[str, int], BoundaryExitRow] = {}
    rows = tuple(records)
    if len(rows) != required_count:
        raise ValueError("boundary authority coverage is incomplete")
    for record in rows:
        try:
            symbol = str(record["symbol"])
            raw = record["row"]
            if not isinstance(raw, Mapping):
                raise ValueError("boundary row object required")
            raw_fields = raw["raw_fields"]
            if not isinstance(raw_fields, list) or len(raw_fields) < 7:
                raise ValueError("boundary raw fields missing")
            row = BoundaryExitRow(
                symbol=symbol,
                open_time_ms=int(raw["open_time_ms"]),
                close_time_ms=int(raw["close_time_ms"]),
                open=float(raw_fields[1]),
                high=float(raw_fields[2]),
                low=float(raw_fields[3]),
                close=float(raw_fields[4]),
                volume=float(raw_fields[5]),
                raw_line_sha256=str(raw["raw_line_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid boundary authority record") from exc
        if raw.get("symbol") != symbol:
            raise ValueError("boundary symbol mismatch")
        if row.open_time_ms % FIVE_MINUTE_MS or row.close_time_ms != row.open_time_ms + FIVE_MINUTE_MS - 1:
            raise ValueError("boundary time mismatch")
        if row.open_time_ms >= is_end_ms or not _valid_ohlcv(row):
            raise ValueError("invalid or OOS boundary row")
        if len(row.raw_line_sha256) != 64:
            raise ValueError("boundary raw-line identity missing")
        identity = (row.symbol, row.open_time_ms)
        if identity in lookup:
            raise ValueError("duplicate boundary identity")
        lookup[identity] = row
    return lookup


def exact_forced_exit(
    lookup: Mapping[tuple[str, int], BoundaryExitRow],
    *,
    symbol: str,
    membership_end_exclusive_ms: int,
) -> BoundaryExitRow:
    """Return only the exact boundary row; no later-row search is possible."""

    row = lookup.get((symbol, membership_end_exclusive_ms))
    if row is None:
        raise ValueError("exact forced-exit boundary row missing")
    return row


def isolation_hash(segments: Iterable[CandidateSegment]) -> str:
    payload = []
    for segment in sorted(segments, key=lambda item: (item.symbol, item.start_inclusive_ms)):
        payload.append(
            {
                "segment": {
                    key: value
                    for key, value in asdict(segment).items()
                    if key not in {"five_minute_rows", "completed_candles", "entry_eligible_candles"}
                },
                "five_minute_rows": [asdict(row) for row in segment.five_minute_rows],
                "completed_candles": [asdict(row) for row in segment.completed_candles],
                "entry_eligible_candles": [asdict(row) for row in segment.entry_eligible_candles],
            }
        )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
