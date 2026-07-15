"""Deterministic point-in-time liquid-universe qualification.

V2 keeps qualification logic outcome-free.  It validates public evidence,
builds monthly membership, and derives complete 1h bars from canonical 5m
rows.  It does not contain signals, returns, or trading behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import math
import re
import statistics
from typing import Any, Iterable

UTC = timezone.utc
SYMBOL_RE = re.compile(r"^[A-Z0-9]+USDT$")
REGISTRY_CATEGORIES = {
    "stable_value",
    "fiat_pegged",
    "commodity_backed_or_external_reference_asset",
    "leveraged_token",
    "wrapped_asset",
    "staked_or_receipt_token",
    "migrated_or_duplicate_representation",
}


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def canonical_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def content_hash(document: dict[str, Any]) -> str:
    return canonical_hash({key: value for key, value in document.items() if key not in {"canonical_hash", "content_hash"}})


@dataclass(frozen=True)
class DailyEvidence:
    symbol: str
    day: date
    quote_volume: Decimal
    authority: str
    archive_sha256: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    archive_key: str = ""

    @property
    def source(self) -> str:  # V1 compatibility for historical callers.
        return self.authority

    @property
    def source_hash(self) -> str:
        return self.archive_sha256


@dataclass(frozen=True)
class MinuteBar:
    symbol: str
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal = Decimal(0)
    trade_count: int = 0
    taker_base_volume: Decimal = Decimal(0)
    taker_quote_volume: Decimal = Decimal(0)


@dataclass(frozen=True)
class MembershipRow:
    effective_month: str
    symbol: str
    rank: int
    median_daily_quote_volume_90d: str
    history_days: int
    eligibility_status: str
    exclusion_reason: str | None
    ranking_window_start: str
    ranking_window_end_exclusive: str
    history_window_start: str
    history_window_end_exclusive: str
    contract_hash: str
    asset_registry_hash: str
    input_provenance_hash: str

    @property
    def source_hash(self) -> str:  # V1 report compatibility.
        return self.input_provenance_hash


@dataclass(frozen=True)
class GridResult:
    symbol: str
    month: str
    expected_count: int
    actual_count: int
    missing: tuple[datetime, ...]
    errors: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not self.missing and not self.errors


def _finite_non_negative(value: Decimal) -> bool:
    return value.is_finite() and value >= 0


def validate_daily(row: DailyEvidence, *, expected_symbol: str | None = None, archive_month: str | None = None) -> None:
    if not SYMBOL_RE.fullmatch(row.symbol):
        raise ValueError(f"invalid daily symbol: {row.symbol}")
    if expected_symbol is not None and row.symbol != expected_symbol:
        raise ValueError("daily symbol does not match archive symbol")
    if archive_month is not None and row.day.strftime("%Y-%m") != archive_month:
        raise ValueError("daily timestamp is outside archive month")
    if row.authority not in {"official_monthly_zip", "official_daily_zip"}:
        raise ValueError("invalid daily authority")
    if len(row.archive_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in row.archive_sha256.lower()):
        raise ValueError("invalid archive SHA256")
    if not all(value.is_finite() for value in (row.open, row.high, row.low, row.close)):
        raise ValueError("non-finite daily OHLC")
    if row.low > min(row.open, row.close) or row.high < max(row.open, row.close) or row.low > row.high:
        raise ValueError("invalid daily OHLC ordering")
    if not _finite_non_negative(row.volume) or not _finite_non_negative(row.quote_volume):
        raise ValueError("daily volume must be finite and non-negative")


def _unique_daily(rows: Iterable[DailyEvidence], authority: str) -> dict[tuple[str, date], DailyEvidence]:
    result: dict[tuple[str, date], DailyEvidence] = {}
    for row in rows:
        validate_daily(row)
        if row.authority != authority:
            raise ValueError(f"expected {authority} evidence")
        key = (row.symbol, row.day)
        if key in result:
            raise ValueError(f"duplicate {authority} daily evidence: {row.symbol}:{row.day}")
        result[key] = row
    return result


def merge_daily(monthly: list[DailyEvidence], daily: list[DailyEvidence]) -> list[DailyEvidence]:
    """Apply monthly-primary, daily-fill-only precedence with conflict blocking."""
    result = _unique_daily(monthly, "official_monthly_zip")
    supplement = _unique_daily(daily, "official_daily_zip")
    for key, row in supplement.items():
        primary = result.get(key)
        if primary is None:
            result[key] = row
        elif (primary.open, primary.high, primary.low, primary.close, primary.volume, primary.quote_volume) != (
            row.open, row.high, row.low, row.close, row.volume, row.quote_volume
        ):
            raise ValueError(f"monthly/daily conflict: {row.symbol}:{row.day}")
    return sorted(result.values(), key=lambda item: (item.symbol, item.day))


def validate_registry(registry: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if registry.get("schema_version") != 2 or registry.get("registry_id") != "LIQUID-SPOT-ASSET-ELIGIBILITY-V2":
        failures.append("registry identity mismatch")
    if set(registry.get("allowed_categories", [])) != REGISTRY_CATEGORIES:
        failures.append("registry categories mismatch")
    version = registry.get("registry_version")
    by_asset: dict[str, list[tuple[date, date | None]]] = {}
    required = {"base_asset", "category", "effective_from", "effective_to", "reason", "public_evidence_reference", "registry_version"}
    for index, record in enumerate(registry.get("records", [])):
        if set(record) != required:
            failures.append(f"registry record {index} fields mismatch")
            continue
        if record["category"] not in REGISTRY_CATEGORIES:
            failures.append(f"registry record {index} unknown category")
        if record["registry_version"] != version:
            failures.append(f"registry record {index} version mismatch")
        try:
            start = date.fromisoformat(record["effective_from"])
            end = date.fromisoformat(record["effective_to"]) if record["effective_to"] else None
        except (TypeError, ValueError):
            failures.append(f"registry record {index} invalid effective date")
            continue
        if end is not None and end < start:
            failures.append(f"registry record {index} inverted effective range")
        ranges = by_asset.setdefault(record["base_asset"], [])
        for old_start, old_end in ranges:
            if (old_end is None or start <= old_end) and (end is None or old_start <= end):
                failures.append(f"registry overlap for {record['base_asset']}")
        ranges.append((start, end))
    if registry.get("canonical_hash") != content_hash(registry):
        failures.append("registry canonical hash mismatch")
    return failures


def exclusion_record(symbol: str, effective: date, contract: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any] | None:
    if not symbol.endswith(contract["quote_asset"]):
        raise ValueError("symbol quote asset mismatch")
    if validate_registry(registry):
        raise ValueError("asset registry is invalid")
    base = symbol.removesuffix(contract["quote_asset"])
    matches = []
    for record in registry["records"]:
        if record["base_asset"] != base:
            continue
        start = date.fromisoformat(record["effective_from"])
        end = date.fromisoformat(record["effective_to"]) if record["effective_to"] else None
        if start <= effective and (end is None or effective <= end):
            matches.append(record)
    if len(matches) > 1:
        raise ValueError(f"conflicting eligibility records for {base}")
    return matches[0] if matches else None


def excluded(symbol: str, contract: dict[str, Any], registry: dict[str, Any], effective: date) -> str | None:
    record = exclusion_record(symbol, effective, contract, registry)
    return record["category"] if record else None


def build_month(effective: date, rows: list[DailyEvidence], contract: dict[str, Any], registry: dict[str, Any]) -> list[MembershipRow]:
    if effective.day != 1:
        raise ValueError("effective month must start on day one")
    if contract.get("universe_id") not in {
        "LIQUID-SPOT-USDT-TOP15-V2",
        "LIQUID-SPOT-USDT-TOP15-V3",
    }:
        raise ValueError("qualification requires an active V2 or V3 contract")
    if contract["exclusion_registry"]["registry_hash"] != registry.get("canonical_hash"):
        raise ValueError("contract/registry hash mismatch")
    membership = contract["membership"]
    rank_days = membership["ranking_window_complete_days"]
    history_days = membership["minimum_complete_history_days"]
    rank_start = effective - timedelta(days=rank_days)
    history_start = effective - timedelta(days=history_days)
    by_symbol: dict[str, dict[date, DailyEvidence]] = {}
    for row in rows:
        validate_daily(row)
        if row.day >= effective:
            continue
        symbol_days = by_symbol.setdefault(row.symbol, {})
        if row.day in symbol_days:
            raise ValueError(f"duplicate merged daily evidence: {row.symbol}:{row.day}")
        symbol_days[row.day] = row

    ranked: list[tuple[Decimal, str, str]] = []
    for symbol, evidence in by_symbol.items():
        if exclusion_record(symbol, effective, contract, registry):
            continue
        required_history = [history_start + timedelta(days=index) for index in range(history_days)]
        if any(day not in evidence for day in required_history):
            continue
        required_rank = [rank_start + timedelta(days=index) for index in range(rank_days)]
        rank_rows = [evidence[day] for day in required_rank]
        median = statistics.median(row.quote_volume for row in rank_rows)
        provenance = [
            {
                "symbol": row.symbol,
                "date": row.day,
                "quote_volume": row.quote_volume,
                "authority": row.authority,
                "archive_sha256": row.archive_sha256,
                "contract_version": contract["schema_version"],
            }
            for row in (evidence[day] for day in required_history)
        ]
        ranked.append((median, symbol, canonical_hash(provenance)))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        MembershipRow(
            effective_month=effective.isoformat(),
            symbol=symbol,
            rank=index + 1,
            median_daily_quote_volume_90d=str(median),
            history_days=history_days,
            eligibility_status="qualified",
            exclusion_reason=None,
            ranking_window_start=rank_start.isoformat(),
            ranking_window_end_exclusive=effective.isoformat(),
            history_window_start=history_start.isoformat(),
            history_window_end_exclusive=effective.isoformat(),
            contract_hash=contract["canonical_hash"],
            asset_registry_hash=registry["canonical_hash"],
            input_provenance_hash=provenance_hash,
        )
        for index, (median, symbol, provenance_hash) in enumerate(ranked[: membership["target_size"]])
    ]


def validate_minute_bar(bar: MinuteBar, *, expected_symbol: str | None = None, expected_month: str | None = None) -> None:
    if not SYMBOL_RE.fullmatch(bar.symbol):
        raise ValueError("invalid 5m symbol")
    if expected_symbol is not None and bar.symbol != expected_symbol:
        raise ValueError("5m symbol does not match archive symbol")
    if bar.open_time.tzinfo is not UTC:
        raise ValueError("5m timestamp must use timezone.utc")
    if bar.open_time.second or bar.open_time.microsecond or bar.open_time.minute % 5:
        raise ValueError("off-grid 5m timestamp")
    if expected_month is not None and bar.open_time.strftime("%Y-%m") != expected_month:
        raise ValueError("5m timestamp outside archive month")
    if not all(value.is_finite() for value in (bar.open, bar.high, bar.low, bar.close)):
        raise ValueError("non-finite 5m OHLC")
    if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close) or bar.low > bar.high:
        raise ValueError("invalid 5m OHLC ordering")
    if not all(_finite_non_negative(value) for value in (bar.volume, bar.quote_volume, bar.taker_base_volume, bar.taker_quote_volume)):
        raise ValueError("5m volume must be finite and non-negative")
    if not isinstance(bar.trade_count, int) or bar.trade_count < 0:
        raise ValueError("5m trade count must be a non-negative integer")


def month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
    end = datetime(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1, tzinfo=UTC)
    return start, end


def expected_five_minute_grid(month: str) -> tuple[datetime, ...]:
    start, end = month_bounds(month)
    count = int((end - start).total_seconds() // 300)
    return tuple(start + timedelta(minutes=5 * index) for index in range(count))


def validate_symbol_month_grid(symbol: str, month: str, bars: list[MinuteBar]) -> GridResult:
    errors: list[str] = []
    seen: set[datetime] = set()
    for bar in bars:
        try:
            validate_minute_bar(bar, expected_symbol=symbol, expected_month=month)
        except ValueError as exc:
            errors.append(str(exc))
        if bar.open_time in seen:
            errors.append(f"duplicate 5m timestamp: {bar.open_time.isoformat()}")
        seen.add(bar.open_time)
    expected = expected_five_minute_grid(month)
    missing = tuple(timestamp for timestamp in expected if timestamp not in seen)
    return GridResult(symbol, month, len(expected), len(seen), missing, tuple(sorted(set(errors))))


def aggregate_one_hour(bars: list[MinuteBar]) -> MinuteBar:
    if len(bars) != 12:
        raise ValueError("one hour requires exactly twelve 5m bars")
    if any(bar.open_time.tzinfo is not UTC for bar in bars):
        raise ValueError("5m timestamp must use timezone.utc")
    ordered = sorted(bars, key=lambda item: item.open_time)
    symbols = {bar.symbol for bar in ordered}
    if len(symbols) != 1:
        raise ValueError("one hour cannot mix symbols")
    start = ordered[0].open_time
    if start.tzinfo is not UTC or start.minute != 0 or start.second or start.microsecond:
        raise ValueError("invalid UTC hour boundary")
    seen: set[datetime] = set()
    for index, bar in enumerate(ordered):
        validate_minute_bar(bar, expected_symbol=ordered[0].symbol, expected_month=start.strftime("%Y-%m"))
        if bar.open_time in seen:
            raise ValueError("duplicate 5m timestamp")
        seen.add(bar.open_time)
        if bar.open_time != start + timedelta(minutes=5 * index):
            raise ValueError("incomplete 5m bucket")
    return MinuteBar(
        symbol=ordered[0].symbol,
        open_time=start,
        open=ordered[0].open,
        high=max(bar.high for bar in ordered),
        low=min(bar.low for bar in ordered),
        close=ordered[-1].close,
        volume=sum((bar.volume for bar in ordered), Decimal(0)),
        quote_volume=sum((bar.quote_volume for bar in ordered), Decimal(0)),
        trade_count=sum(bar.trade_count for bar in ordered),
        taker_base_volume=sum((bar.taker_base_volume for bar in ordered), Decimal(0)),
        taker_quote_volume=sum((bar.taker_quote_volume for bar in ordered), Decimal(0)),
    )


def membership_hash(rows: list[MembershipRow]) -> str:
    return canonical_hash(sorted(rows, key=lambda row: (row.effective_month, row.rank, row.symbol)))
