"""Pure M1E public-data qualification and deterministic aggregation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

from .minute_archive import KLINE_FIELDS, MINUTE_MS, month_bounds_ms, next_month


INTERVAL_MS = {"5m": 5 * MINUTE_MS, "1h": 60 * MINUTE_MS, "4h": 240 * MINUTE_MS}
SUM_FIELDS = ("volume", "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume")
COMPARE_FIELDS = (*KLINE_FIELDS, "close_time")
LIQUIDITY_P95_MAXIMUM = Decimal("0.0030")
COMMON_QUALIFIED_MONTHS = 6


@dataclass(frozen=True)
class ArchiveMonth:
    symbol: str
    month: str
    timeframe: str
    rows: tuple[dict[str, Any], ...]
    missing_timestamps: tuple[int, ...]
    outage_candidate_timestamps: tuple[int, ...]
    invalid_rows: int
    conflict_rows: int
    daily_fill_rows: int
    format_only_fields: int
    canonical_sha256: str


@dataclass(frozen=True)
class DerivedBars:
    timeframe: str
    rows: tuple[dict[str, Any], ...]
    incomplete_buckets: tuple[int, ...]
    canonical_sha256: str


@dataclass(frozen=True)
class ParityEvidence:
    symbol: str
    month: str
    timeframe: str
    overlap_rows: int
    numeric_differences: int
    format_only_fields: int
    derived_only: tuple[int, ...]
    official_only: tuple[int, ...]
    derived_sha256: str
    official_sha256: str


@dataclass(frozen=True)
class PairMonthQualification:
    month: str
    state: str
    confirmed_outage_5m: tuple[int, ...]
    isolated_1h_buckets: tuple[int, ...]
    isolated_4h_buckets: tuple[int, ...]
    blockers: tuple[str, ...]


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite value")
    return result


def _canonical_rows(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: int(item["open_time"])):
        digest.update(json.dumps(dict(row), sort_keys=True, separators=(",", ":"), default=str).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def valid_kline(row: Mapping[str, Any], timeframe: str) -> bool:
    try:
        interval_ms = INTERVAL_MS[timeframe]
        timestamp = int(row["open_time"])
        opened, high, low, closed = (_decimal(row[field]) for field in ("open", "high", "low", "close"))
        if timestamp % interval_ms or min(opened, high, low, closed) <= 0:
            return False
        if high < max(opened, closed, low) or low > min(opened, closed, high):
            return False
        if int(row["close_time"]) != timestamp + interval_ms - 1:
            return False
        return all(_decimal(row[field]) >= 0 for field in SUM_FIELDS)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def outage_candidate_kline(row: Mapping[str, Any], timeframe: str) -> bool:
    """Accept a structurally valid, aligned bar that closed early during an outage."""
    try:
        interval_ms = INTERVAL_MS[timeframe]
        timestamp = int(row["open_time"])
        close_time = int(row["close_time"])
        opened, high, low, closed = (_decimal(row[field]) for field in ("open", "high", "low", "close"))
        return (
            timestamp % interval_ms == 0
            and min(opened, high, low, closed) > 0
            and high >= max(opened, low, closed)
            and low <= min(opened, high, closed)
            and timestamp <= close_time < timestamp + interval_ms - 1
            and all(_decimal(row[field]) >= 0 for field in SUM_FIELDS)
        )
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def merge_archive_month(
    *,
    symbol: str,
    month: str,
    timeframe: str,
    monthly_rows: Iterable[Mapping[str, Any]],
    daily_rows: Iterable[Mapping[str, Any]] = (),
) -> ArchiveMonth:
    interval_ms = INTERVAL_MS[timeframe]
    start_ms, end_ms = month_bounds_ms(month)
    rows: dict[int, dict[str, Any]] = {}
    outage_candidates: set[int] = set()
    invalid = conflicts = fills = format_only = 0
    for source in monthly_rows:
        row = dict(source)
        try:
            timestamp = int(row["open_time"])
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        if start_ms <= timestamp < end_ms and outage_candidate_kline(row, timeframe):
            outage_candidates.add(timestamp)
            continue
        if not (start_ms <= timestamp < end_ms) or not valid_kline(row, timeframe) or timestamp in rows:
            invalid += 1
            continue
        rows[timestamp] = row

    seen_daily: set[int] = set()
    for source in daily_rows:
        row = dict(source)
        try:
            timestamp = int(row["open_time"])
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        if start_ms <= timestamp < end_ms and outage_candidate_kline(row, timeframe):
            outage_candidates.add(timestamp)
            continue
        if not (start_ms <= timestamp < end_ms) or not valid_kline(row, timeframe) or timestamp in seen_daily:
            invalid += 1
            continue
        seen_daily.add(timestamp)
        current = rows.get(timestamp)
        if current is None:
            rows[timestamp] = row
            fills += 1
            continue
        for field in COMPARE_FIELDS:
            if _decimal(current[field]) != _decimal(row[field]):
                conflicts += 1
                break
            if str(current[field]) != str(row[field]):
                format_only += 1

    expected = set(range(start_ms, end_ms, interval_ms))
    ordered = tuple(rows[timestamp] for timestamp in sorted(rows) if timestamp in expected)
    return ArchiveMonth(
        symbol=symbol,
        month=month,
        timeframe=timeframe,
        rows=ordered,
        missing_timestamps=tuple(sorted(expected - set(rows))),
        outage_candidate_timestamps=tuple(sorted(outage_candidates)),
        invalid_rows=invalid,
        conflict_rows=conflicts,
        daily_fill_rows=fills,
        format_only_fields=format_only,
        canonical_sha256=_canonical_rows(ordered),
    )


def aggregate_bars(rows: Iterable[Mapping[str, Any]], child: str, target: str, month: str) -> DerivedBars:
    supported = {("5m", "1h"): 12, ("1h", "4h"): 4}
    count = supported.get((child, target))
    if count is None:
        raise ValueError("M1E supports only 12x5m->1h and 4x1h->4h")
    child_ms, target_ms = INTERVAL_MS[child], INTERVAL_MS[target]
    indexed = {int(row["open_time"]): dict(row) for row in rows if valid_kline(row, child)}
    start_ms, end_ms = month_bounds_ms(month)
    results: list[dict[str, Any]] = []
    incomplete: list[int] = []
    for bucket in range(start_ms, end_ms, target_ms):
        expected = [bucket + index * child_ms for index in range(count)]
        if any(timestamp not in indexed for timestamp in expected):
            incomplete.append(bucket)
            continue
        group = [indexed[timestamp] for timestamp in expected]
        result: dict[str, Any] = {
            "open_time": bucket,
            "open": str(group[0]["open"]),
            "high": format(max(_decimal(item["high"]) for item in group), "f"),
            "low": format(min(_decimal(item["low"]) for item in group), "f"),
            "close": str(group[-1]["close"]),
            "close_time": bucket + target_ms - 1,
        }
        for field in SUM_FIELDS:
            result[field] = format(sum((_decimal(item[field]) for item in group), Decimal(0)), "f")
        results.append(result)
    return DerivedBars(target, tuple(results), tuple(incomplete), _canonical_rows(results))


def compare_parity(
    *, symbol: str, month: str, timeframe: str, derived: Iterable[Mapping[str, Any]], official: Iterable[Mapping[str, Any]]
) -> ParityEvidence:
    left = {int(row["open_time"]): dict(row) for row in derived}
    right = {int(row["open_time"]): dict(row) for row in official}
    overlap = sorted(set(left) & set(right))
    numeric = format_only = 0
    for timestamp in overlap:
        for field in COMPARE_FIELDS:
            if _decimal(left[timestamp][field]) != _decimal(right[timestamp][field]):
                numeric += 1
            elif str(left[timestamp][field]) != str(right[timestamp][field]):
                format_only += 1
    return ParityEvidence(
        symbol, month, timeframe, len(overlap), numeric, format_only,
        tuple(sorted(set(left) - set(right))), tuple(sorted(set(right) - set(left))),
        _canonical_rows(left.values()), _canonical_rows(right.values()),
    )


def qualify_pair_month(
    *,
    month: str,
    archives: Mapping[tuple[str, str], ArchiveMonth],
    one_hour_parity: Mapping[str, ParityEvidence],
    four_hour_parity: Mapping[str, ParityEvidence],
) -> PairMonthQualification:
    symbols = ("BTCUSDT", "ETHUSDT")
    blockers: list[str] = []
    for key, archive in archives.items():
        if archive.invalid_rows or archive.conflict_rows:
            blockers.append(f"{key[0]}:{key[1]}:invalid_or_conflict")

    missing_5 = {symbol: set(archives[(symbol, "5m")].missing_timestamps) for symbol in symbols}
    if missing_5["BTCUSDT"] != missing_5["ETHUSDT"]:
        blockers.append("single_symbol_5m_gap")
    confirmed_5 = missing_5["BTCUSDT"] & missing_5["ETHUSDT"]
    outage_candidates_5 = {
        symbol: set(archives[(symbol, "5m")].outage_candidate_timestamps) for symbol in symbols
    }
    if outage_candidates_5["BTCUSDT"] != outage_candidates_5["ETHUSDT"]:
        blockers.append("single_symbol_5m_early_close")
    if not (outage_candidates_5["BTCUSDT"] <= confirmed_5):
        blockers.append("untracked_5m_early_close")
    isolated_1h = {timestamp - timestamp % INTERVAL_MS["1h"] for timestamp in confirmed_5}
    isolated_4h = {timestamp - timestamp % INTERVAL_MS["4h"] for timestamp in confirmed_5}

    for timeframe in ("1h", "4h"):
        left_missing = set(archives[("BTCUSDT", timeframe)].missing_timestamps)
        right_missing = set(archives[("ETHUSDT", timeframe)].missing_timestamps)
        if left_missing != right_missing:
            blockers.append(f"single_symbol_{timeframe}_gap")

    for symbol in symbols:
        for parity, isolated, label in (
            (one_hour_parity[symbol], isolated_1h, "1h"),
            (four_hour_parity[symbol], isolated_4h, "4h"),
        ):
            if parity.numeric_differences:
                blockers.append(f"{symbol}:{label}:numeric_difference")
            if set(parity.derived_only) - isolated or set(parity.official_only) - isolated:
                blockers.append(f"{symbol}:{label}:unexplained_timestamp_difference")

    blockers = sorted(set(blockers))
    state = "blocked" if blockers else "audit_complete_with_confirmed_outage" if confirmed_5 else "audit_complete"
    return PairMonthQualification(
        month, state, tuple(sorted(confirmed_5)), tuple(sorted(isolated_1h)), tuple(sorted(isolated_4h)), tuple(blockers)
    )


def determine_research_start(
    qualifications: Sequence[PairMonthQualification],
    liquidity: Mapping[tuple[str, str], Decimal],
) -> str | None:
    qualified: list[str] = []
    for item in sorted(qualifications, key=lambda value: value.month):
        liquid = all(liquidity.get((symbol, item.month), Decimal("Infinity")) <= LIQUIDITY_P95_MAXIMUM for symbol in ("BTCUSDT", "ETHUSDT"))
        if item.state != "blocked" and liquid:
            qualified.append(item.month)
        else:
            qualified = []
        if len(qualified) >= COMMON_QUALIFIED_MONTHS:
            return f"{next_month(qualified[-1])}-01"
    return None


def month_from_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m")
