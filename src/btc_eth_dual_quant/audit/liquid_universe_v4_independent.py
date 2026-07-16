"""Independent, fixture-first primitives for the frozen U-03F V4 audit.

This module intentionally shares no production liquid-universe implementation.
It contains only independently specified parsing, integer-time, ranking, grid,
availability and aggregation primitives. Production JSON may be an input
specification or comparison target, never an execution oracle.
"""

from __future__ import annotations

import hashlib
import io
import json
import csv
import zipfile
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
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


def strict_json_loads(text: str) -> Any:
    """Decode JSON while rejecting duplicate object keys."""

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in pairs:
            if key in output:
                raise ValueError(f"duplicate JSON key: {key}")
            output[key] = value
        return output

    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


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


def month_bounds_ms(month: str) -> tuple[int, int]:
    if len(month) != 7 or month[4] != "-":
        raise ValueError("month must be YYYY-MM")
    year, number = (int(item) for item in month.split("-"))
    start = datetime(year, number, 1, tzinfo=timezone.utc)
    next_month = datetime(year + (number == 12), 1 if number == 12 else number + 1, 1, tzinfo=timezone.utc)
    return milliseconds_from_utc(start.isoformat().replace("+00:00", "Z")), milliseconds_from_utc(next_month.isoformat().replace("+00:00", "Z"))


def day_bounds_ms(day: str) -> tuple[int, int]:
    parsed = date.fromisoformat(day)
    start = datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return milliseconds_from_utc(start.isoformat().replace("+00:00", "Z")), milliseconds_from_utc(end.isoformat().replace("+00:00", "Z"))


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


@dataclass(frozen=True)
class ParsedArchive:
    sha256: str
    byte_size: int
    member_name: str
    rows: tuple[KlineRow, ...]
    first_timestamp_ms: int | None
    last_timestamp_ms: int | None


def parse_official_kline_zip(
    payload: bytes,
    *,
    symbol: str,
    interval: str,
    archive_period: str,
) -> ParsedArchive:
    """Parse one official archive without trusting its filename or row order."""

    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC failure")
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) != 1 or not members[0].filename.endswith(".csv"):
                raise ValueError("archive must contain one CSV")
            member = members[0]
            expected_stem = f"{symbol}-{interval}-{archive_period}"
            if member.filename.rsplit("/", 1)[-1] != f"{expected_stem}.csv":
                raise ValueError("archive member identity mismatch")
            text = archive.read(member).decode("utf-8-sig")
    except (zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise ValueError("invalid official ZIP") from exc
    records = list(csv.reader(io.StringIO(text)))
    if records and records[0] and not records[0][0].strip().isdigit():
        records = records[1:]
    rows = tuple(KlineRow.from_fields(record) for record in records if record)
    times = [item.open_time_ms for item in rows]
    if times != sorted(times) or len(times) != len(set(times)):
        raise ValueError("archive rows must be ordered and unique")
    start, end = day_bounds_ms(archive_period) if len(archive_period) == 10 else month_bounds_ms(archive_period)
    if any(timestamp < start or timestamp >= end for timestamp in times):
        raise ValueError("archive row lies outside declared period")
    return ParsedArchive(
        hashlib.sha256(payload).hexdigest(),
        len(payload),
        member.filename,
        rows,
        times[0] if times else None,
        times[-1] if times else None,
    )


def verify_source_freeze(
    entries: Sequence[Mapping[str, Any]], payloads: Mapping[str, bytes]
) -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        key = str(entry["canonical_key"])
        if key in seen:
            raise ValueError("duplicate source-freeze key")
        seen.add(key)
        if key not in payloads:
            raise ValueError(f"missing frozen archive: {key}")
        payload = payloads[key]
        digest = hashlib.sha256(payload).hexdigest()
        if digest != entry.get("sha256") or len(payload) != entry.get("byte_size"):
            raise ValueError(f"source-freeze binding changed: {key}")
        verified.append({"canonical_key": key, "sha256": digest, "byte_size": len(payload)})
    if set(payloads) != seen:
        raise ValueError("unregistered source payload")
    return sorted(verified, key=lambda item: item["canonical_key"])


def raw_row_hash(fields: Sequence[str]) -> str:
    return hashlib.sha256(",".join(str(item) for item in fields).encode("utf-8")).hexdigest()


def apply_resolution_registry(
    *,
    symbol: str,
    monthly_rows: Sequence[Sequence[str]],
    daily_rows: Sequence[Sequence[str]],
    registry_entries: Sequence[Mapping[str, Any]],
    archive_hashes: Mapping[str, str],
) -> tuple[tuple[KlineRow, ...], list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve only exact, hash-bound registry entries; unknown defects fail closed."""

    rules: dict[int, Mapping[str, Any]] = {}
    for entry in registry_entries:
        if entry.get("symbol") != symbol:
            continue
        timestamp = milliseconds_from_utc(str(entry["open_time_utc"]).replace("+00:00", "Z"))
        if timestamp in rules:
            raise ValueError("overlapping row-resolution registry entries")
        rules[timestamp] = entry

    monthly_by_time: dict[int, list[tuple[str, ...]]] = {}
    daily_by_time: dict[int, list[tuple[str, ...]]] = {}
    for raw, destination in ((monthly_rows, monthly_by_time), (daily_rows, daily_by_time)):
        for fields in raw:
            row = tuple(str(item) for item in fields)
            destination.setdefault(normalize_raw_timestamp(row[0]), []).append(row)

    canonical: dict[int, KlineRow] = {}
    quarantine: list[dict[str, Any]] = []
    resolutions: list[dict[str, Any]] = []
    for timestamp in sorted(set(monthly_by_time) | set(daily_by_time)):
        monthly = monthly_by_time.get(timestamp, [])
        daily = daily_by_time.get(timestamp, [])
        rule = rules.get(timestamp)
        needs_rule = len(monthly) != 1
        if not needs_rule and daily:
            try:
                needs_rule = KlineRow.from_fields(monthly[0]).semantic_tuple() != KlineRow.from_fields(daily[0]).semantic_tuple()
            except ValueError:
                needs_rule = True
        if not needs_rule:
            try:
                canonical[timestamp] = KlineRow.from_fields(monthly[0] if monthly else daily[0])
                continue
            except (IndexError, ValueError):
                needs_rule = True
        if not rule:
            raise ValueError(f"unregistered row conflict at {timestamp}")
        action = rule.get("approved_action")
        for source_name, rows, binding_name in (
            ("monthly", monthly, "monthly_archive"),
            ("daily", daily, "daily_archive"),
        ):
            binding = rule.get(binding_name, {})
            key = binding.get("canonical_key")
            if key and archive_hashes.get(str(key)) != binding.get("sha256"):
                raise ValueError("registered source archive hash changed")
            expected_hashes = list(binding.get("raw_row_hashes", []))
            actual_hashes = [raw_row_hash(item) for item in rows]
            if expected_hashes and actual_hashes != expected_hashes:
                raise ValueError(f"registered {source_name} raw multiplicity or hash changed")
        if action == "replace_invalid_monthly_with_daily":
            replacement_rows = rule.get("daily_archive", {}).get("raw_rows", [])
            if len(replacement_rows) != 1:
                raise ValueError("daily correction must bind exactly one row")
            replacement = KlineRow.from_fields(replacement_rows[0])
            if replacement.open_time_ms != timestamp:
                raise ValueError("daily correction timestamp changed")
            canonical[timestamp] = replacement
            quarantine.extend({"source": "monthly", "open_time_ms": timestamp, "raw_row_hash": raw_row_hash(item)} for item in monthly)
        elif action == "collapse_byte_identical_duplicate":
            candidates = monthly or daily
            hashes = [raw_row_hash(item) for item in candidates]
            if len(candidates) < 2 or len(set(hashes)) != 1:
                raise ValueError("duplicate collapse requires byte-identical multiplicity")
            canonical[timestamp] = KlineRow.from_fields(candidates[0])
            quarantine.extend({"source": "duplicate", "open_time_ms": timestamp, "raw_row_hash": value} for value in hashes[1:])
        else:
            raise ValueError(f"unsupported registered action: {action}")
        resolutions.append({"resolution_id": rule.get("resolution_id"), "open_time_ms": timestamp, "action": action})
    unused = set(rules) - set(monthly_by_time) - set(daily_by_time)
    if unused:
        raise ValueError("registry entry has no matching raw row")
    return tuple(canonical[key] for key in sorted(canonical)), quarantine, resolutions


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
    start_inclusive_ms: int = 0

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, start_inclusive: str = "1970-01-01T00:00:00Z") -> "LifecycleEvent":
        if value.get("successor_authority") != "provenance_only":
            raise ValueError("successor cannot inherit history or rank")
        known = milliseconds_from_utc(str(value["known_at"]))
        effective = milliseconds_from_utc(str(value["effective_at"]))
        end = milliseconds_from_utc(str(value["availability_end_exclusive"]))
        last = milliseconds_from_utc(str(value["last_valid_market_time"]))
        if not known < effective or end != effective or last + 1 != end:
            raise ValueError("invalid lifecycle boundary")
        start = milliseconds_from_utc(start_inclusive)
        if start >= end:
            raise ValueError("availability epoch must have positive duration")
        return cls(str(value["event_id"]), str(value["symbol"]), known, effective, end, last, dict(value), start)


def availability_state(event: LifecycleEvent, timestamp_ms: int) -> str:
    if timestamp_ms < event.start_inclusive_ms:
        return "not_yet_available"
    if timestamp_ms >= event.availability_end_exclusive_ms:
        return "lifecycle_terminated"
    day_start = (timestamp_ms // 86_400_000) * 86_400_000
    day_end = day_start + 86_400_000
    return "active_partial" if day_start < event.availability_end_exclusive_ms < day_end else "active_complete"


def validate_lifecycle_registry(
    policy: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    research_start: str,
    expected_policy_hash: str | None = None,
    expected_registry_hash: str | None = None,
    expected_reviewed_event_set_hash: str | None = None,
) -> tuple[LifecycleEvent, ...]:
    if not isinstance(policy.get("schema_version"), int) or not isinstance(registry.get("schema_version"), int):
        raise ValueError("lifecycle schema version is missing")
    if expected_policy_hash is not None and policy.get("canonical_hash") != expected_policy_hash:
        raise ValueError("lifecycle policy hash changed")
    if expected_registry_hash is not None and registry.get("canonical_hash") != expected_registry_hash:
        raise ValueError("lifecycle registry hash changed")
    if expected_reviewed_event_set_hash is not None and registry.get("reviewed_event_set_hash") != expected_reviewed_event_set_hash:
        raise ValueError("reviewed lifecycle event set changed")
    if policy.get("policy_id") != registry.get("policy_id") or policy.get("policy_version") != registry.get("policy_version"):
        raise ValueError("lifecycle policy/registry mismatch")
    semantics = policy.get("semantics", {})
    required_semantics = {
        "availability_bounds": "start_inclusive_end_exclusive",
        "integer_epoch_only": True,
        "availability_mask_before_expected_grid": True,
        "post_boundary_absence_is_gap": False,
        "partial_days_enter_ranking_or_history": False,
        "month_start_membership_rewritten_mid_month": False,
        "successor_inherits_history_or_rank": False,
    }
    if any(semantics.get(key) != value for key, value in required_semantics.items()):
        raise ValueError("lifecycle policy semantics changed")
    events: list[LifecycleEvent] = []
    seen_ids: set[str] = set()
    seen_affected_rows: set[tuple[str, int, str]] = set()
    for source in registry.get("entries", []):
        event = LifecycleEvent.from_mapping(source, start_inclusive=research_start)
        if event.event_id in seen_ids:
            raise ValueError("duplicate lifecycle event ID")
        seen_ids.add(event.event_id)
        if source.get("policy_version") != registry.get("policy_version"):
            raise ValueError("event policy version mismatch")
        required_hash_fields = (
            list(source.get("official_evidence_hashes", []))
            + list(source.get("archive_hashes", []))
            + list(source.get("intraday_evidence_hashes", []))
            + [source.get("similar_scope_scan_hash"), source.get("adjudication_hash")]
        )
        if any(not isinstance(value, str) or len(value) != 64 for value in required_hash_fields):
            raise ValueError("lifecycle evidence hash is missing or malformed")
        for row in source.get("affected_raw_rows", []):
            identity = (event.event_id, int(row["open_time_ms"]), str(row["raw_row_sha256"]))
            if identity in seen_affected_rows:
                raise ValueError("duplicate affected lifecycle row")
            seen_affected_rows.add(identity)
            if not row.get("source_archive_hashes"):
                raise ValueError("affected lifecycle row lacks source binding")
        events.append(event)
    events.sort(key=lambda item: (item.symbol, item.start_inclusive_ms, item.availability_end_exclusive_ms))
    by_symbol: dict[str, list[LifecycleEvent]] = {}
    for event in events:
        by_symbol.setdefault(event.symbol, []).append(event)
    for sequence in by_symbol.values():
        for left, right in zip(sequence, sequence[1:]):
            if right.start_inclusive_ms < left.availability_end_exclusive_ms:
                raise ValueError("overlapping lifecycle epochs")
    return tuple(events)


def classify_lifecycle_rows(
    event: LifecycleEvent,
    raw_rows: Sequence[Sequence[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registered = {
        (str(item["interval"]), int(item["open_time_ms"]), str(item["raw_row_sha256"])): item
        for item in event.source.get("affected_raw_rows", [])
    }
    observed: set[tuple[str, int, str]] = set()
    quarantine: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in raw_rows:
        timestamp = normalize_raw_timestamp(row[0])
        digest = raw_row_hash(row)
        key = ("1d", timestamp, digest)
        if key in registered:
            observed.add(key)
            quarantine.append({"event_id": event.event_id, "open_time_ms": timestamp, "raw_row_hash": digest, "classification": registered[key]["classification"]})
        elif timestamp >= event.availability_end_exclusive_ms:
            blocked.append({"event_id": event.event_id, "open_time_ms": timestamp, "raw_row_hash": digest, "reason": "unregistered_post_event_row"})
    if observed != set(registered):
        raise ValueError("registered lifecycle row set changed")
    return quarantine, blocked


def eligibility_and_membership(
    *,
    effective_month: str,
    daily_quote_volumes: Mapping[str, Mapping[date, Decimal]],
    excluded_symbols: set[str] | None = None,
    lifecycle_events: Sequence[LifecycleEvent] = (),
    target_size: int = 15,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    excluded = excluded_symbols or set()
    start_ms, _ = month_bounds_ms(effective_month)
    start_day = EPOCH.date() + timedelta(days=start_ms // 86_400_000)
    history_days = tuple(start_day - timedelta(days=offset) for offset in range(365, 0, -1))
    ranking_days = history_days[-90:]
    terminated = {event.symbol: event for event in lifecycle_events}
    candidates: list[dict[str, Any]] = []
    metrics: dict[str, Sequence[Decimal]] = {}
    for symbol in sorted(daily_quote_volumes):
        values = daily_quote_volumes[symbol]
        reason: str | None = None
        if symbol in excluded:
            reason = "excluded_by_contract"
        elif symbol in terminated and terminated[symbol].availability_end_exclusive_ms <= start_ms:
            reason = "lifecycle_terminated"
        elif any(day not in values for day in history_days):
            reason = "prior_365_complete_days_missing"
        elif any(day not in values for day in ranking_days):
            reason = "prior_90_complete_days_missing"
        if reason:
            candidates.append({"effective_month": effective_month, "symbol": symbol, "status": "ineligible", "reason": reason})
            continue
        ranking_values = [values[day] for day in ranking_days]
        if any(not item.is_finite() or item < 0 for item in ranking_values):
            raise ValueError("invalid eligibility quote volume")
        metrics[symbol] = ranking_values
        candidates.append({
            "effective_month": effective_month,
            "symbol": symbol,
            "status": "qualified",
            "reason": None,
            "history_days": 365,
            "median_daily_quote_volume_90d": format(median(ranking_values), "f"),
        })
    membership = rank_membership(effective_month, metrics, target_size=target_size)
    return candidates, membership


@dataclass(frozen=True)
class GridAudit:
    symbol: str
    month: str
    expected_slots: tuple[int, ...]
    observed_slots: tuple[int, ...]
    missing_slots: tuple[int, ...]
    off_grid_slots: tuple[int, ...]
    duplicate_slots: tuple[int, ...]


def audit_five_minute_grid(
    *,
    symbol: str,
    month: str,
    bars: Sequence[FiveMinuteBar],
    availability_end_exclusive_ms: int | None = None,
) -> GridAudit:
    start, end = month_bounds_ms(month)
    expected = expected_slots(start, end, 300_000, availability_end_exclusive=availability_end_exclusive_ms)
    counts: dict[int, int] = {}
    off_grid: list[int] = []
    for bar in bars:
        timestamp = bar.open_time_ms
        if timestamp < start or timestamp >= end or timestamp % 300_000:
            off_grid.append(timestamp)
            continue
        if availability_end_exclusive_ms is not None and timestamp >= availability_end_exclusive_ms:
            continue
        counts[timestamp] = counts.get(timestamp, 0) + 1
    duplicates = tuple(sorted(timestamp for timestamp, count in counts.items() if count > 1))
    observed = tuple(sorted(counts))
    missing = tuple(sorted(set(expected) - set(observed)))
    return GridAudit(symbol, month, expected, observed, missing, tuple(sorted(off_grid)), duplicates)


def classify_member_gaps(
    *,
    member_missing_slots: Mapping[str, set[int]],
    confirmed_symbol_months: set[str] | None = None,
) -> dict[str, str]:
    confirmed = confirmed_symbol_months or set()
    members = set(member_missing_slots)
    if not members:
        return {}
    synchronized = set.intersection(*(slots for slots in member_missing_slots.values())) if all(member_missing_slots.values()) else set()
    output: dict[str, str] = {}
    for symbol, missing in member_missing_slots.items():
        residual = missing - synchronized
        if residual and symbol not in confirmed:
            output[symbol] = "unresolved_blocked"
        elif residual:
            output[symbol] = "symbol_month_quarantine"
        elif missing:
            output[symbol] = "global_outage"
        else:
            output[symbol] = "clean"
    return output


def complete_day_mask(
    *,
    day: date,
    observed_slots: set[int],
    availability_end_exclusive_ms: int | None = None,
) -> dict[str, Any]:
    start, end = day_bounds_ms(day.isoformat())
    expected = set(expected_slots(start, end, 300_000, availability_end_exclusive=availability_end_exclusive_ms))
    partial = availability_end_exclusive_ms is not None and start < availability_end_exclusive_ms < end
    return {
        "day": day.isoformat(),
        "expected_count": len(expected),
        "observed_count": len(observed_slots & expected),
        "partial_lifecycle_day": partial,
        "complete": not partial and observed_slots & expected == expected,
    }


def active_universe_at(
    *,
    membership: Sequence[str],
    timestamp_ms: int,
    lifecycle_events: Sequence[LifecycleEvent] = (),
    quarantined_symbols: set[str] | None = None,
    not_yet_available: set[str] | None = None,
) -> list[dict[str, str]]:
    quarantined = quarantined_symbols or set()
    unavailable = not_yet_available or set()
    by_symbol = {event.symbol: event for event in lifecycle_events}
    output: list[dict[str, str]] = []
    for symbol in membership:
        if symbol in quarantined:
            state = "data_quarantined"
        elif symbol in unavailable:
            state = "not_yet_available"
        elif symbol in by_symbol:
            state = availability_state(by_symbol[symbol], timestamp_ms)
        else:
            state = "active_complete"
        output.append({"symbol": symbol, "state": state})
    return output


def attribute_gap(members: set[str], missing_symbols: set[str]) -> str:
    if not missing_symbols:
        return "clean"
    if missing_symbols == members and members:
        return "global_outage"
    if missing_symbols <= members:
        return "symbol_month_quarantine"
    return "unresolved_blocked"
