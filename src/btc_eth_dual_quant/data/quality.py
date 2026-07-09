"""M0 data-quality checks."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any, Iterable


INTERVAL_MS = {
    "1m": 60_000,
    "3m": 3 * 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "2h": 2 * 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
    "1d": 24 * 60 * 60_000,
    "3d": 3 * 24 * 60 * 60_000,
    "1w": 7 * 24 * 60 * 60_000,
}


@dataclass(frozen=True)
class Gap:
    missing_start_ms: int
    missing_end_ms: int
    missing_count: int


@dataclass(frozen=True)
class GapReport:
    gaps: list[Gap]
    blocks_backtest: bool


@dataclass(frozen=True)
class SourceDifference:
    open_time: int
    field: str
    left: Decimal
    right: Decimal
    relative_diff: Decimal


@dataclass(frozen=True)
class KlineAnomaly:
    open_time: int
    reason: str


@dataclass(frozen=True)
class ZipRestAudit:
    overlap_rows: int
    differences: list[SourceDifference]
    zip_only_rows: int
    rest_only_rows: int
    rest_payload_sha256: str
    zip_payload_sha256: str
    scope: str = "unspecified"


def interval_to_ms(interval: str) -> int:
    try:
        return INTERVAL_MS[interval]
    except KeyError as exc:
        raise ValueError(f"unsupported interval: {interval}") from exc


def _value(row: Any, key: str, index: int | None = None) -> Any:
    if isinstance(row, dict):
        return row[key]
    if index is None:
        raise KeyError(key)
    return row[index]


def detect_kline_gaps(rows: Iterable[Any], interval: str, max_consecutive_missing: int = 3) -> GapReport:
    """Check UTC millisecond open-time continuity for K-line rows."""

    step = interval_to_ms(interval)
    times = sorted(int(_value(row, "open_time", 0)) for row in rows)
    gaps: list[Gap] = []
    for prev, cur in zip(times, times[1:]):
        diff = cur - prev
        if diff > step:
            missing_count = diff // step - 1
            gaps.append(Gap(prev + step, cur - step, missing_count))
    return GapReport(gaps=gaps, blocks_backtest=any(gap.missing_count > max_consecutive_missing for gap in gaps))


def compare_zip_rest_klines(
    zip_rows: Iterable[dict[str, Any]],
    rest_rows: Iterable[dict[str, Any]],
    tolerance: Decimal = Decimal("0.001"),
) -> list[SourceDifference]:
    """Compare overlapping OHLCV fields; default tolerance is 0.1%."""

    rest_by_time = {int(row["open_time"]): row for row in rest_rows}
    differences: list[SourceDifference] = []
    for left in zip_rows:
        open_time = int(left["open_time"])
        right = rest_by_time.get(open_time)
        if not right:
            continue
        for field in ("open", "high", "low", "close", "volume", "quote_volume"):
            left_value = Decimal(str(left[field]))
            right_value = Decimal(str(right[field]))
            denominator = max(abs(left_value), abs(right_value), Decimal("1e-18"))
            relative = abs(left_value - right_value) / denominator
            if relative > tolerance:
                differences.append(SourceDifference(open_time, field, left_value, right_value, relative))
    return differences


def audit_zip_rest_klines(
    zip_rows: Iterable[dict[str, Any]],
    rest_rows: Iterable[dict[str, Any]],
    tolerance: Decimal = Decimal("0.001"),
    scope: str = "unspecified",
) -> ZipRestAudit:
    """Hash and compare the exact overlapping rows from two public sources."""

    zip_by_time = {int(row["open_time"]): row for row in zip_rows}
    rest_by_time = {int(row["open_time"]): row for row in rest_rows}
    overlap_times = sorted(set(zip_by_time) & set(rest_by_time))
    zip_overlap = [zip_by_time[time_ms] for time_ms in overlap_times]
    rest_overlap = [rest_by_time[time_ms] for time_ms in overlap_times]

    def digest(rows: list[dict[str, Any]]) -> str:
        payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return ZipRestAudit(
        overlap_rows=len(overlap_times),
        differences=compare_zip_rest_klines(zip_overlap, rest_overlap, tolerance),
        zip_only_rows=len(set(zip_by_time) - set(rest_by_time)),
        rest_only_rows=len(set(rest_by_time) - set(zip_by_time)),
        rest_payload_sha256=digest(rest_overlap),
        zip_payload_sha256=digest(zip_overlap),
        scope=scope,
    )


def flag_kline_anomalies(rows: Iterable[dict[str, Any]]) -> list[KlineAnomaly]:
    """Flag suspicious K-lines without modifying raw values."""

    anomalies: list[KlineAnomaly] = []
    for row in rows:
        open_time = int(row["open_time"])
        open_price = Decimal(str(row["open"]))
        high = Decimal(str(row["high"]))
        low = Decimal(str(row["low"]))
        volume = Decimal(str(row.get("volume", "0")))
        denominator = max(abs(open_price), Decimal("1e-18"))
        if (high - low) / denominator > Decimal("0.30"):
            anomalies.append(KlineAnomaly(open_time, "amplitude_gt_30pct"))
        if volume == 0:
            anomalies.append(KlineAnomaly(open_time, "zero_volume"))
    return anomalies


def archive_completeness_by_day(records: Iterable[dict[str, Any]], timestamp_field: str) -> dict[str, int]:
    """Count archived records by UTC date for OI/income continuity reports."""

    from datetime import datetime, timezone

    counts: dict[str, int] = defaultdict(int)
    for record in records:
        ts_ms = int(record[timestamp_field])
        day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        counts[day] += 1
    return dict(sorted(counts.items()))


def missing_archive_days(records: Iterable[dict[str, Any]], timestamp_field: str, start_day: str, end_day: str) -> list[str]:
    """Return UTC days with no archived records in the inclusive date range."""

    from datetime import date, timedelta

    observed = set(archive_completeness_by_day(records, timestamp_field))
    current = date.fromisoformat(start_day)
    end = date.fromisoformat(end_day)
    missing: list[str] = []
    while current <= end:
        day = current.isoformat()
        if day not in observed:
            missing.append(day)
        current += timedelta(days=1)
    return missing
