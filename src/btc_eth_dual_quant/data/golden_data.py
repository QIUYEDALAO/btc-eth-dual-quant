"""Deterministic golden OHLCV construction and timeframe derivation."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .minute_archive import KLINE_FIELDS, MINUTE_MS, month_bounds_ms


SUM_FIELDS = (
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)
COMPARE_FIELDS = (*KLINE_FIELDS, "close_time")
FREQTRADE_IMAGE_REF = (
    "freqtradeorg/freqtrade:2026.6@"
    "sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6"
)
FREQTRADE_VERSION = "freqtrade 2026.6"


@dataclass(frozen=True)
class QuarantineRecord:
    symbol: str
    month: str
    open_time: int | None
    reason: str
    primary_source: str
    alternate_source: str
    primary_row_sha256: str
    alternate_row_sha256: str


@dataclass(frozen=True)
class GoldenMonthResult:
    symbol: str
    month: str
    state: str
    rows: tuple[dict[str, Any], ...]
    quarantine: tuple[QuarantineRecord, ...]
    missing_rows: int
    invalid_rows: int
    conflict_rows: int
    format_only_fields: int
    canonical_sha256: str


@dataclass(frozen=True)
class AggregateResult:
    interval: str
    rows: tuple[dict[str, Any], ...]
    incomplete_buckets: tuple[int, ...]
    canonical_sha256: str


@dataclass(frozen=True)
class OfficialComparison:
    symbol: str
    month: str
    overlap_rows: int
    derived_only_rows: int
    official_only_rows: int
    numeric_differences: int
    format_only_fields: int
    invalid_official_rows: int
    derived_sha256: str
    official_sha256: str
    passed: bool


@dataclass(frozen=True)
class FreqtradeDataEntry:
    pair: str
    timeframe: str
    candle_type: str
    start: str
    end: str
    rows: int


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite value")
    return result


def _canonical_row(row: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(row), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def row_sha256(row: Mapping[str, Any] | None) -> str:
    return hashlib.sha256(_canonical_row(row)).hexdigest() if row is not None else ""


def _timestamp(row: Mapping[str, Any]) -> int | None:
    try:
        return int(row.get("open_time"))
    except (TypeError, ValueError):
        return None


def rows_sha256(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: int(item["open_time"])):
        digest.update(_canonical_row(row))
        digest.update(b"\n")
    return digest.hexdigest()


def valid_kline(row: Mapping[str, Any], interval_ms: int = MINUTE_MS) -> bool:
    try:
        timestamp = int(row["open_time"])
        opened = _decimal(row["open"])
        high = _decimal(row["high"])
        low = _decimal(row["low"])
        closed = _decimal(row["close"])
        if timestamp % interval_ms != 0 or min(opened, high, low, closed) <= 0:
            return False
        if high < max(opened, low, closed) or low > min(opened, high, closed):
            return False
        return all(_decimal(row[field]) >= 0 for field in SUM_FIELDS)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def _numeric_equal(left: Any, right: Any) -> bool:
    try:
        return _decimal(left) == _decimal(right)
    except (InvalidOperation, ValueError):
        return str(left) == str(right)


def build_golden_month(
    *,
    symbol: str,
    month: str,
    monthly_rows: Iterable[Mapping[str, Any]],
    daily_rows: Iterable[Mapping[str, Any]] = (),
    enforce_complete_month: bool = True,
) -> GoldenMonthResult:
    start_ms, end_ms = month_bounds_ms(month)
    golden: dict[int, dict[str, Any]] = {}
    quarantine: list[QuarantineRecord] = []
    invalid = 0
    conflicts = 0
    format_only = 0

    def quarantine_row(
        reason: str,
        timestamp: int | None,
        primary_source: str,
        primary: Mapping[str, Any] | None,
        alternate_source: str = "",
        alternate: Mapping[str, Any] | None = None,
    ) -> None:
        quarantine.append(
            QuarantineRecord(
                symbol=symbol,
                month=month,
                open_time=timestamp,
                reason=reason,
                primary_source=primary_source,
                alternate_source=alternate_source,
                primary_row_sha256=row_sha256(primary),
                alternate_row_sha256=row_sha256(alternate),
            )
        )

    for source_row in monthly_rows:
        row = dict(source_row)
        timestamp = _timestamp(row)
        if timestamp is None or not (start_ms <= timestamp < end_ms) or not valid_kline(row):
            invalid += 1
            quarantine_row("invalid_or_off_grid_monthly_row", timestamp, "monthly_zip", row)
            continue
        if timestamp in golden:
            quarantine_row("duplicate_monthly_timestamp", timestamp, "monthly_zip", golden[timestamp], "monthly_zip", row)
            continue
        golden[timestamp] = row

    seen_daily: set[int] = set()
    for source_row in daily_rows:
        row = dict(source_row)
        timestamp = _timestamp(row)
        if timestamp is None or not (start_ms <= timestamp < end_ms) or not valid_kline(row):
            invalid += 1
            quarantine_row("invalid_or_off_grid_daily_row", timestamp, "daily_zip", row)
            continue
        if timestamp in seen_daily:
            quarantine_row("duplicate_daily_timestamp", timestamp, "daily_zip", row)
            continue
        seen_daily.add(timestamp)
        existing = golden.get(timestamp)
        if existing is None:
            golden[timestamp] = row
            continue
        field_difference = False
        for field in COMPARE_FIELDS:
            if not _numeric_equal(existing[field], row[field]):
                field_difference = True
            elif str(existing[field]) != str(row[field]):
                format_only += 1
        if field_difference:
            conflicts += 1
            quarantine_row("monthly_daily_source_conflict", timestamp, "monthly_zip", existing, "daily_zip", row)

    expected = set(range(start_ms, end_ms, MINUTE_MS)) if enforce_complete_month else set(golden)
    missing = sorted(expected - set(golden))
    for timestamp in missing:
        quarantine_row("missing_minute", timestamp, "monthly_and_daily_zip", None)

    if missing or invalid or conflicts:
        state = "blocked"
    elif quarantine:
        state = "audit_complete_with_quarantine"
    else:
        state = "audit_complete"
    rows = tuple(golden[timestamp] for timestamp in sorted(golden) if timestamp in expected)
    return GoldenMonthResult(
        symbol=symbol,
        month=month,
        state=state,
        rows=rows,
        quarantine=tuple(quarantine),
        missing_rows=len(missing),
        invalid_rows=invalid,
        conflict_rows=conflicts,
        format_only_fields=format_only,
        canonical_sha256=rows_sha256(rows),
    )


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


def aggregate_klines(rows: Iterable[Mapping[str, Any]], interval: str) -> AggregateResult:
    sizes = {"5m": 5, "15m": 15}
    if interval not in sizes:
        raise ValueError("golden aggregation supports only 5m and 15m")
    count = sizes[interval]
    interval_ms = count * MINUTE_MS
    buckets: dict[int, dict[int, dict[str, Any]]] = {}
    for source_row in rows:
        row = dict(source_row)
        if not valid_kline(row):
            continue
        timestamp = int(row["open_time"])
        bucket = timestamp - (timestamp % interval_ms)
        buckets.setdefault(bucket, {})[timestamp] = row

    aggregated: list[dict[str, Any]] = []
    incomplete: list[int] = []
    for bucket, indexed in sorted(buckets.items()):
        expected = [bucket + offset * MINUTE_MS for offset in range(count)]
        if sorted(indexed) != expected:
            incomplete.append(bucket)
            continue
        group = [indexed[timestamp] for timestamp in expected]
        result: dict[str, Any] = {
            "open_time": bucket,
            "open": str(group[0]["open"]),
            "high": _decimal_string(max(_decimal(item["high"]) for item in group)),
            "low": _decimal_string(min(_decimal(item["low"]) for item in group)),
            "close": str(group[-1]["close"]),
            "close_time": bucket + interval_ms - 1,
        }
        for field in SUM_FIELDS:
            result[field] = _decimal_string(sum((_decimal(item[field]) for item in group), Decimal(0)))
        aggregated.append(result)
    return AggregateResult(interval, tuple(aggregated), tuple(incomplete), rows_sha256(aggregated))


def compare_official_klines(
    *, symbol: str, month: str, derived_rows: Iterable[Mapping[str, Any]], official_rows: Iterable[Mapping[str, Any]]
) -> OfficialComparison:
    derived_source = [dict(row) for row in derived_rows]
    official_source = [dict(row) for row in official_rows]
    derived = {int(row["open_time"]): row for row in derived_source}
    official = {int(row["open_time"]): row for row in official_source}
    overlap = sorted(set(derived) & set(official))
    numeric = 0
    format_only = 0
    duplicate_official = len(official_source) - len(official)
    invalid = duplicate_official + sum(not valid_kline(row, 15 * MINUTE_MS) for row in official.values())
    for timestamp in overlap:
        for field in COMPARE_FIELDS:
            left, right = derived[timestamp][field], official[timestamp][field]
            if not _numeric_equal(left, right):
                numeric += 1
            elif str(left) != str(right):
                format_only += 1
    derived_only = len(set(derived) - set(official))
    official_only = len(set(official) - set(derived))
    return OfficialComparison(
        symbol=symbol,
        month=month,
        overlap_rows=len(overlap),
        derived_only_rows=derived_only,
        official_only_rows=official_only,
        numeric_differences=numeric,
        format_only_fields=format_only,
        invalid_official_rows=invalid,
        derived_sha256=rows_sha256(derived.values()),
        official_sha256=rows_sha256(official.values()),
        passed=bool(overlap) and not (derived_only or official_only or numeric or invalid),
    )


def write_jsonl_gz(path: Path, rows: Iterable[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            for row in rows:
                line = _canonical_row(row) + b"\n"
                digest.update(line)
                compressed.write(line)
    return digest.hexdigest()


def write_freqtrade_jsongz(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    """Write Freqtrade's six-column OHLCV JSON array with deterministic gzip metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            compressed.write(b"[")
            digest.update(b"[")
            for index, row in enumerate(rows):
                payload = [
                    int(row["open_time"]),
                    float(_decimal(row["open"])),
                    float(_decimal(row["high"])),
                    float(_decimal(row["low"])),
                    float(_decimal(row["close"])),
                    float(_decimal(row["volume"])),
                ]
                chunk = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
                if index:
                    compressed.write(b",")
                    digest.update(b",")
                compressed.write(chunk)
                digest.update(chunk)
            compressed.write(b"]")
            digest.update(b"]")
    return digest.hexdigest()


def quarantine_sha256(records: Iterable[QuarantineRecord]) -> str:
    payload = sorted(
        (asdict(item) for item in records),
        key=lambda item: (
            item["symbol"], item["month"], item["open_time"] if item["open_time"] is not None else -1,
            item["reason"], item["primary_source"], item["alternate_source"],
            item["primary_row_sha256"], item["alternate_row_sha256"],
        ),
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_freqtrade_list_data(output: str) -> tuple[FreqtradeDataEntry, ...]:
    """Parse the stable table fields emitted by ``freqtrade list-data``."""
    ansi = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    entries: list[FreqtradeDataEntry] = []
    for raw_line in ansi.sub("", output).splitlines():
        if "│" not in raw_line:
            continue
        fields = [field.strip() for field in raw_line.split("│")[1:-1]]
        if len(fields) != 6 or fields[2] != "spot" or "/" not in fields[0]:
            continue
        try:
            rows = int(fields[5].replace(",", ""))
        except ValueError:
            continue
        entries.append(FreqtradeDataEntry(*fields[:5], rows))
    return tuple(sorted(entries, key=lambda item: (item.pair, item.timeframe)))


def validate_freqtrade_runtime_evidence(
    evidence: Mapping[str, Any],
    expected: Mapping[tuple[str, str], tuple[str, str, int]] | None = None,
) -> bool:
    if evidence.get("status") != "pass":
        return False
    if evidence.get("image_ref") != FREQTRADE_IMAGE_REF or evidence.get("version") != FREQTRADE_VERSION:
        return False
    if evidence.get("api_key_used") is not False or evidence.get("command") != "list-data":
        return False
    entries = evidence.get("entries")
    if not isinstance(entries, list) or len(entries) != 6:
        return False
    actual = {
        (str(item.get("pair")), str(item.get("timeframe"))): (
            str(item.get("start")), str(item.get("end")), int(item.get("rows", -1))
        )
        for item in entries
        if isinstance(item, Mapping) and item.get("candle_type") == "spot"
    }
    required_keys = {
        (pair, timeframe)
        for pair in ("BTC/USDT", "ETH/USDT")
        for timeframe in ("1m", "5m", "15m")
    }
    if set(actual) != required_keys or any(rows <= 0 for _, _, rows in actual.values()):
        return False
    return expected is None or actual == dict(expected)
