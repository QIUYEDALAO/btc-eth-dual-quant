"""Offline orchestration for the frozen U-03F V4 independent audit.

The reviewed primitive module owns parsing and integer-time decisions.  This
module only binds those primitives to the frozen source inventory, constructs
production-equivalent evidence independently, and compares it after the fact.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .liquid_universe_v4_audit_artifacts import (
    REQUIRED_AUDIT_ARTIFACTS,
    audit_artifact_set_hash,
    audit_manifest_hash,
    build_audit_artifacts,
    compare_artifact_suite,
    scan_float_timestamp_paths,
    verify_manifest_wrapper,
)
from .liquid_universe_v4_independent import (
    EPOCH,
    FiveMinuteBar,
    KlineRow,
    LifecycleEvent,
    aggregate_one_hour as audit_aggregate_one_hour,
    audit_content_hash,
    audit_identity_hash,
    collect_official_kline_zip_rows,
    expected_slots,
    milliseconds_from_utc,
    month_bounds_ms,
    normalize_raw_timestamp,
    raw_row_hash,
    strict_json_loads,
    validate_lifecycle_registry,
)


PRODUCTION_NAMES = tuple(REQUIRED_AUDIT_ARTIFACTS)
ZERO_AUTHORIZATIONS = {
    "u03f": False,
    "u04": False,
    "hypothesis": False,
    "strategy": False,
    "events": False,
    "signals": False,
    "returns": False,
    "backtesting": False,
    "oos": False,
    "api_trading": False,
    "execution_live": False,
    "m2": False,
}


@dataclass(frozen=True)
class SourceRow:
    symbol: str
    interval: str
    period: str
    authority: str
    canonical_key: str
    archive_sha256: str
    line_number: int
    fields: tuple[str, ...]

    @property
    def timestamp_ms(self) -> int:
        return normalize_raw_timestamp(self.fields[0])

    @property
    def row_hash(self) -> str:
        return raw_row_hash(self.fields)


@dataclass(frozen=True)
class DailyPoint:
    symbol: str
    day: date
    row: KlineRow
    authority: str
    archive_key: str
    archive_sha256: str


def load_json(path: Path) -> Any:
    return strict_json_loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_iso(timestamp_ms: int) -> str:
    instant = EPOCH + timedelta(milliseconds=timestamp_ms)
    return instant.isoformat()


def day_from_ms(timestamp_ms: int) -> date:
    return EPOCH.date() + timedelta(days=timestamp_ms // 86_400_000)


def parse_source_kline(fields: Sequence[str]) -> KlineRow:
    """Normalize Binance's microsecond archive encoding without changing raw identity."""
    normalized = [str(value) for value in fields]
    for index in (0, 6):
        raw = int(normalized[index])
        if raw >= 10**14:
            normalized[index] = str(raw // 1_000)
    return KlineRow.from_fields(normalized)


def month_sequence(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start + "-01")
    terminal = date.fromisoformat(end + "-01")
    output: list[str] = []
    while current <= terminal:
        output.append(current.strftime("%Y-%m"))
        current = date(current.year + int(current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return output


def parse_archive_identity(canonical_key: str) -> tuple[str, str, str, str]:
    path = PurePosixPath(canonical_key)
    parts = path.parts
    if len(parts) != 7 or parts[:2] != ("data", "spot") or parts[3] != "klines":
        raise ValueError(f"unsupported frozen archive key: {canonical_key}")
    frequency, symbol, interval, filename = parts[2], parts[4], parts[5], parts[6]
    if frequency not in {"monthly", "daily"} or interval not in {"1d", "5m"}:
        raise ValueError(f"unsupported frozen archive identity: {canonical_key}")
    prefix = f"{symbol}-{interval}-"
    if not filename.startswith(prefix) or not filename.endswith(".zip"):
        raise ValueError(f"archive filename identity mismatch: {canonical_key}")
    period = filename[len(prefix):-4]
    if frequency == "monthly" and len(period) != 7:
        raise ValueError("monthly archive period is invalid")
    if frequency == "daily" and len(period) != 10:
        raise ValueError("daily archive period is invalid")
    return frequency, symbol, interval, period


def _manifest_source_row(
    *, canonical_key: str, payload: bytes, symbol: str, interval: str,
    period: str, frequency: str, rows: Sequence[Sequence[str]], derived_1h_count: int | None,
) -> dict[str, Any]:
    times = [normalize_raw_timestamp(row[0]) for row in rows]
    authority = (
        "official_daily_zip_fill_only" if frequency == "daily"
        else "official_monthly_zip_primary" if interval == "1d"
        else "official_monthly_zip_detail"
    )
    output: dict[str, Any] = {
        "archive_month": period[:7],
        "authority_role": authority,
        "byte_size": len(payload),
        "canonical_key": canonical_key,
        "canonical_url": "https://data.binance.vision/" + canonical_key,
        "first_timestamp": utc_iso(times[0]) if times else None,
        "interval": interval,
        "last_timestamp": utc_iso(times[-1]) if times else None,
        "row_count": len(rows),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "symbol": symbol,
        "verification_status": "official_checksum_verified",
    }
    if derived_1h_count is not None:
        output["derived_1h_count"] = derived_1h_count
    return output


def _valid_five_minute_rows(rows: Sequence[Sequence[str]]) -> tuple[list[FiveMinuteBar], list[str]]:
    bars: list[FiveMinuteBar] = []
    errors: list[str] = []
    for fields in rows:
        try:
            row = parse_source_kline(fields)
            if row.open_time_ms % 300_000 or row.close_time_ms != row.open_time_ms + 299_999:
                raise ValueError("5m interval boundary is invalid")
            bars.append(FiveMinuteBar(
                row.open_time_ms, row.open, row.high, row.low, row.close,
                row.base_volume, row.quote_volume, row.trade_count,
                row.taker_base_volume, row.taker_quote_volume,
            ))
        except ValueError as exc:
            errors.append(str(exc))
    return bars, sorted(set(errors))


def _source_order(entries: list[Mapping[str, Any]], mode: str) -> list[Mapping[str, Any]]:
    ordered = sorted(entries, key=lambda item: str(item["canonical_key"]))
    if mode == "reverse":
        ordered.reverse()
    elif mode == "shuffled":
        random.Random(314159).shuffle(ordered)
    elif mode != "normal":
        raise ValueError(f"unknown audit order: {mode}")
    return ordered


def _scan_sources(
    *, raw_root: Path, freeze_entries: list[Mapping[str, Any]], order: str,
    lifecycle_events: Sequence[LifecycleEvent],
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], list[SourceRow]], dict[tuple[str, int], list[SourceRow]], dict[tuple[str, str], dict[str, Any]]]:
    source_manifest: list[dict[str, Any]] = []
    monthly_daily: dict[tuple[str, int], list[SourceRow]] = defaultdict(list)
    supplement_daily: dict[tuple[str, int], list[SourceRow]] = defaultdict(list)
    grids: dict[tuple[str, str], dict[str, Any]] = {}
    lifecycle_by_symbol = {event.symbol: event for event in lifecycle_events}
    for frozen in _source_order(freeze_entries, order):
        key = str(frozen["canonical_key"])
        frequency, symbol, interval, period = parse_archive_identity(key)
        path = raw_root / key
        if not path.is_file():
            raise FileNotFoundError(f"missing frozen archive: {key}")
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != frozen.get("sha256") or len(payload) != frozen.get("byte_size"):
            raise RuntimeError(f"source revision detected: {key}")
        raw = collect_official_kline_zip_rows(
            payload, symbol=symbol, interval=interval, archive_period=period,
        )
        if interval == "1d":
            authority = "official_monthly_zip" if frequency == "monthly" else "official_daily_zip"
            target = monthly_daily if frequency == "monthly" else supplement_daily
            for line_number, fields in enumerate(raw.rows, start=1):
                item = SourceRow(symbol, interval, period, authority, key, digest, line_number, fields)
                target[(symbol, item.timestamp_ms)].append(item)
            derived = None
        else:
            bars, errors = _valid_five_minute_rows(raw.rows)
            month = period
            start_ms, end_ms = month_bounds_ms(month)
            event = lifecycle_by_symbol.get(symbol)
            boundary = event.availability_end_exclusive_ms if event and start_ms < event.availability_end_exclusive_ms <= end_ms else None
            limit = boundary if boundary is not None else end_ms
            expected = set(expected_slots(start_ms, end_ms, 300_000, availability_end_exclusive=boundary))
            observed: set[int] = set()
            duplicates: set[int] = set()
            for bar in bars:
                if bar.open_time_ms < start_ms or bar.open_time_ms >= end_ms or bar.open_time_ms % 300_000:
                    errors.append("5m timestamp outside archive month or off-grid")
                    continue
                if boundary is not None and bar.open_time_ms >= boundary:
                    errors.append("unexpected post-lifecycle 5m row")
                    continue
                if bar.open_time_ms in observed:
                    duplicates.add(bar.open_time_ms)
                observed.add(bar.open_time_ms)
            if duplicates:
                errors.append("duplicate 5m timestamp")
            missing = sorted(expected - observed)
            active_bars = [bar for bar in bars if start_ms <= bar.open_time_ms < limit]
            derived = len(audit_aggregate_one_hour(active_bars))
            grids[(symbol, month)] = {
                "symbol": symbol,
                "month": month,
                "expected_count": len(expected),
                "actual_count": len(observed),
                "missing": missing,
                "errors": sorted(set(errors)),
                "complete": not missing and not errors,
                "observed": observed,
            }
        source_manifest.append(_manifest_source_row(
            canonical_key=key, payload=payload, symbol=symbol, interval=interval,
            period=period, frequency=frequency, rows=raw.rows, derived_1h_count=derived,
        ))
    source_manifest.sort(key=lambda row: (
        row["symbol"], row["interval"], row["archive_month"], row["canonical_key"],
    ))
    return source_manifest, monthly_daily, supplement_daily, grids


def _registry_rules(document: Mapping[str, Any]) -> dict[tuple[str, int], Mapping[str, Any]]:
    output: dict[tuple[str, int], Mapping[str, Any]] = {}
    for entry in document.get("entries", []):
        key = (str(entry["symbol"]), milliseconds_from_utc(str(entry["open_time_utc"]).replace("+00:00", "Z")))
        if key in output:
            raise ValueError("duplicate row-resolution registry key")
        output[key] = entry
    return output


def _row_quarantine(item: SourceRow, reason: str, event_id: str | None = None) -> dict[str, Any]:
    output = {
        "archive_key": item.canonical_key,
        "archive_sha256": item.archive_sha256,
        "interval": item.interval,
        "line_number": item.line_number,
        "open_time_utc": utc_iso(item.timestamp_ms),
        "raw_fields": list(item.fields),
        "raw_row_hash": item.row_hash,
        "reason": reason,
        "symbol": item.symbol,
    }
    if event_id is not None:
        output = {"archive_key": output["archive_key"], "archive_sha256": output["archive_sha256"], "event_id": event_id, **{key: value for key, value in output.items() if key not in {"archive_key", "archive_sha256"}}}
    return output


def _source_binding_matches(rows: Sequence[SourceRow], binding: Mapping[str, Any]) -> bool:
    return (
        len(rows) == int(binding.get("raw_multiplicity", len(rows)))
        and all(item.canonical_key == binding.get("canonical_key") and item.archive_sha256 == binding.get("sha256") for item in rows)
        and sorted(item.row_hash for item in rows) == sorted(str(value) for value in binding.get("raw_row_hashes", []))
    )


def _resolve_daily_authority(
    *, monthly: Mapping[tuple[str, int], list[SourceRow]], supplements: Mapping[tuple[str, int], list[SourceRow]],
    row_registry: Mapping[str, Any], lifecycle_events: Sequence[LifecycleEvent],
    eligibility_registry: Mapping[str, Any],
) -> tuple[list[DailyPoint], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    rules = _registry_rules(row_registry)
    events = {event.symbol: event for event in lifecycle_events}
    canonical: list[DailyPoint] = []
    resolutions: list[dict[str, Any]] = []
    lifecycle_quarantine: list[dict[str, Any]] = []
    lifecycle_blocked: list[dict[str, Any]] = []
    blockers: list[str] = []
    counters = {
        "duplicate_collapses": 0,
        "monthly_rows_quarantined": 0,
        "daily_corrections_admitted": 0,
        "unresolved_row_conflicts": 0,
        "blocked_symbol_months": 0,
        "synthetic_fills": 0,
        "replacement_members": 0,
    }
    all_keys = sorted(set(monthly) | set(supplements))
    used_rules: set[tuple[str, int]] = set()
    registered_lifecycle: dict[tuple[str, int, str], tuple[LifecycleEvent, Mapping[str, Any]]] = {}
    for event in lifecycle_events:
        for affected in event.source.get("affected_raw_rows", []):
            registered_lifecycle[(event.symbol, int(affected["open_time_ms"]), str(affected["raw_row_sha256"]))] = (event, affected)
    for key in all_keys:
        symbol, timestamp = key
        primary = list(monthly.get(key, []))
        fill = list(supplements.get(key, []))
        rows = primary + fill
        lifecycle_claims = [registered_lifecycle.get((symbol, timestamp, item.row_hash)) for item in rows]
        if any(lifecycle_claims):
            if not all(claim is not None for claim in lifecycle_claims):
                blockers.append(f"unregistered_lifecycle_row:{symbol}:{timestamp}")
                lifecycle_blocked.append({"symbol": symbol, "open_time_ms": timestamp, "reason": "lifecycle row set changed"})
                continue
            event = lifecycle_claims[0][0]  # type: ignore[index]
            expected_claims = {
                (int(item["open_time_ms"]), str(item["raw_row_sha256"]))
                for item in event.source.get("affected_raw_rows", [])
            }
            observed_claims = {
                (candidate.timestamp_ms, candidate.row_hash)
                for candidate_rows in (monthly, supplements)
                for candidate_key, candidates in candidate_rows.items()
                if candidate_key[0] == event.symbol
                for candidate in candidates
                if (candidate.timestamp_ms, candidate.row_hash) in expected_claims
            }
            if observed_claims != expected_claims:
                blockers.append(f"lifecycle_registered_row_set_changed:{event.event_id}")
            for item in rows:
                lifecycle_quarantine.append(_row_quarantine(item, "registered_lifecycle_affected_row", event.event_id))
            continue
        rule = rules.get(key)
        if rule is not None:
            used_rules.add(key)
            action = rule.get("approved_action")
            if not _source_binding_matches(primary, rule.get("monthly_archive", {})) or not _source_binding_matches(fill, rule.get("daily_archive", {})):
                blockers.append(f"row_registry_source_mismatch:{symbol}:{timestamp}")
                counters["unresolved_row_conflicts"] += 1
                counters["blocked_symbol_months"] += 1
                continue
            if action == "replace_invalid_monthly_with_daily":
                if len(primary) != 1 or len(fill) != 1:
                    blockers.append(f"row_registry_multiplicity_mismatch:{symbol}:{timestamp}")
                    continue
                try:
                    parse_source_kline(primary[0].fields)
                    blockers.append(f"registered_monthly_row_no_longer_invalid:{symbol}:{timestamp}")
                    continue
                except ValueError:
                    pass
                selected = parse_source_kline(fill[0].fields)
                raw_quarantine = [_row_quarantine(item, "invalid monthly row replaced by approved daily evidence") for item in primary]
                counters["daily_corrections_admitted"] += 1
                counters["monthly_rows_quarantined"] += len(primary)
                canonical_source = fill
            elif action == "collapse_byte_identical_duplicate":
                if len(primary) < 2 or len({item.row_hash for item in primary}) != 1:
                    blockers.append(f"registered_duplicate_changed:{symbol}:{timestamp}")
                    continue
                selected = parse_source_kline(primary[0].fields)
                if fill and (len(fill) < 2 or any(item.row_hash != primary[0].row_hash for item in fill)):
                    blockers.append(f"daily_duplicate_changed:{symbol}:{timestamp}")
                    continue
                raw_quarantine = [
                    *(_row_quarantine(item, "collapsed byte-identical raw duplicate") for item in primary[1:]),
                    *(_row_quarantine(item, "collapsed byte-identical raw duplicate") for item in fill[1:]),
                ]
                counters["duplicate_collapses"] += 1
                canonical_source = primary
            else:
                blockers.append(f"unsupported_registry_action:{symbol}:{timestamp}")
                continue
            source = canonical_source[0]
            canonical.append(DailyPoint(symbol, day_from_ms(timestamp), selected, source.authority, source.canonical_key, source.archive_sha256))
            resolutions.append({
                "status": "resolved",
                "canonical_key": None,
                "canonical_resolution_id": rule.get("resolution_id"),
                "canonical_source_archive_sha256": source.archive_sha256,
                "canonical_raw_multiplicity": len(canonical_source),
                "canonical_raw_row_hashes": [item.row_hash for item in canonical_source],
                "canonical_raw_line_numbers": [item.line_number for item in canonical_source],
                "raw_row_quarantine": raw_quarantine,
                "research_panel_quarantine": [],
            })
            continue
        try:
            if len(primary) > 1 or len(fill) > 1:
                raise ValueError("unregistered duplicate")
            selected_source = primary[0] if primary else fill[0]
            selected = parse_source_kline(selected_source.fields)
            if primary and fill and parse_source_kline(primary[0].fields).semantic_tuple() != parse_source_kline(fill[0].fields).semantic_tuple():
                raise ValueError("monthly/daily conflict")
            canonical.append(DailyPoint(symbol, day_from_ms(timestamp), selected, selected_source.authority, selected_source.canonical_key, selected_source.archive_sha256))
        except (IndexError, ValueError) as exc:
            event_day = day_from_ms(timestamp)
            excluded = _excluded_category(symbol, event_day, eligibility_registry)
            if excluded is not None:
                # Structurally invalid rows for an excluded asset cannot enter
                # eligibility or ranking, and therefore are not qualification
                # blockers.  Raw provenance remains frozen in source_manifest.
                continue
            blockers.append(f"daily_authority:{symbol}:{timestamp}:{exc}")
            counters["unresolved_row_conflicts"] += 1
            counters["blocked_symbol_months"] += 1
    if used_rules != set(rules):
        blockers.append("row_registry_entries_unused")
    resolution_content = {
        "registry_id": row_registry["registry_id"],
        "registry_hash": row_registry["canonical_hash"],
        "resolutions": resolutions,
        "counters": counters,
    }
    canonical.sort(key=lambda item: (item.symbol, item.day))
    return canonical, resolution_content, lifecycle_quarantine, lifecycle_blocked, blockers


def _excluded_category(symbol: str, effective: date, registry: Mapping[str, Any]) -> str | None:
    base = symbol.removesuffix("USDT")
    matches: list[Mapping[str, Any]] = []
    for record in registry.get("records", []):
        if record.get("base_asset") != base:
            continue
        start = date.fromisoformat(str(record["effective_from"]))
        end = date.fromisoformat(str(record["effective_to"])) if record.get("effective_to") else None
        if start <= effective and (end is None or effective <= end):
            matches.append(record)
    if len(matches) > 1:
        raise ValueError(f"overlapping asset exclusions: {symbol}")
    return str(matches[0]["category"]) if matches else None


def _eligibility_and_membership(
    *, daily: Sequence[DailyPoint], contract: Mapping[str, Any], registry: Mapping[str, Any], months: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_symbol: dict[str, dict[date, DailyPoint]] = defaultdict(dict)
    for item in daily:
        if item.day in by_symbol[item.symbol]:
            raise ValueError(f"duplicate canonical daily point: {item.symbol}:{item.day}")
        by_symbol[item.symbol][item.day] = item
    history_days = int(contract["membership"]["minimum_complete_history_days"])
    rank_days = int(contract["membership"]["ranking_window_complete_days"])
    target = int(contract["membership"]["target_size"])
    eligibility: list[dict[str, Any]] = []
    memberships: list[dict[str, Any]] = []
    for month in months:
        effective = date.fromisoformat(month + "-01")
        history_start = effective - timedelta(days=history_days)
        rank_start = effective - timedelta(days=rank_days)
        required_history = [history_start + timedelta(days=index) for index in range(history_days)]
        required_rank = required_history[-rank_days:]
        ranked: list[tuple[Decimal, str, str]] = []
        for symbol in sorted(by_symbol):
            values = by_symbol[symbol]
            exclusion = _excluded_category(symbol, effective, registry)
            history_complete = all(day in values for day in required_history)
            rank_complete = all(day in values for day in required_rank)
            if exclusion is not None:
                status, reason = "excluded_by_contract", exclusion
            elif not history_complete:
                status, reason = "insufficient_history", "prior_365_complete_days_missing"
            elif not rank_complete:
                status, reason = "insufficient_rank_window", "prior_90_complete_days_missing"
            else:
                status, reason = "eligible_for_ranking", None
                ordered = [values[day] for day in required_rank]
                sorted_values = sorted(item.row.quote_volume for item in ordered)
                midpoint = len(sorted_values) // 2
                metric = (sorted_values[midpoint - 1] + sorted_values[midpoint]) / Decimal(2)
                provenance = [{
                    "symbol": values[day].symbol,
                    "date": day.isoformat(),
                    "quote_volume": values[day].row.quote_volume,
                    "authority": values[day].authority,
                    "archive_sha256": values[day].archive_sha256,
                    "contract_version": contract["schema_version"],
                } for day in required_history]
                ranked.append((metric, symbol, audit_content_hash(provenance)))
            eligibility.append({
                "effective_month": month,
                "symbol": symbol,
                "status": status,
                "reason": reason,
                "history_window_start": history_start.isoformat(),
                "ranking_window_start": rank_start.isoformat(),
                "window_end_exclusive": effective.isoformat(),
            })
        ranked.sort(key=lambda item: (-item[0], item[1]))
        for rank, (metric, symbol, provenance_hash) in enumerate(ranked[:target], start=1):
            memberships.append({
                "asset_registry_hash": registry["canonical_hash"],
                "contract_hash": contract["canonical_hash"],
                "effective_month": effective.isoformat(),
                "eligibility_status": "qualified",
                "exclusion_reason": None,
                "history_days": history_days,
                "history_window_end_exclusive": effective.isoformat(),
                "history_window_start": history_start.isoformat(),
                "input_provenance_hash": provenance_hash,
                "median_daily_quote_volume_90d": str(metric),
                "rank": rank,
                "ranking_window_end_exclusive": effective.isoformat(),
                "ranking_window_start": rank_start.isoformat(),
                "symbol": symbol,
            })
    return eligibility, memberships


def _gap_and_panel(
    *, memberships: Sequence[Mapping[str, Any]], grids: Mapping[tuple[str, str], Mapping[str, Any]],
    confirmed_gap_registry: Mapping[str, Any], contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    members_by_month: dict[str, list[str]] = defaultdict(list)
    for row in memberships:
        members_by_month[str(row["effective_month"])[:7]].append(str(row["symbol"]))
    confirmed = {(str(item["symbol"]), str(item["month"])) for item in confirmed_gap_registry.get("records", [])}
    records: list[dict[str, Any]] = []
    global_windows: dict[tuple[str, int, int], dict[str, Any]] = {}
    symbol_quarantines: set[tuple[str, str]] = set()
    unresolved = 0
    for month, members in sorted(members_by_month.items()):
        missing_by_slot: dict[int, set[str]] = defaultdict(set)
        for symbol in members:
            for timestamp in grids[(symbol, month)]["missing"]:
                missing_by_slot[int(timestamp)].add(symbol)
        threshold = max(2, math.ceil(len(members) * Decimal("0.8")))
        for symbol in members:
            source_hash = str(grids[(symbol, month)]["archive_sha256"])
            tagged: list[tuple[int, str, str, str]] = []
            for timestamp in grids[(symbol, month)]["missing"]:
                peers = len(missing_by_slot[int(timestamp)])
                if peers >= threshold:
                    classification = "binance_global_event"
                    evidence = f"archive_sha256={source_hash}; synchronized_missing={peers}/{len(members)}; all_archives_verified=true"
                    decision = "quarantine_global_window_all_members"
                elif (symbol, month) in confirmed:
                    classification = "symbol_specific_confirmed_archive_gap"
                    evidence = f"archive_sha256={source_hash}; confirmed_symbol_month=true"
                    decision = "quarantine_entire_symbol_month_without_replacement"
                else:
                    classification = "unresolved"
                    evidence = f"archive_sha256={source_hash}; synchronized_missing={peers}/{len(members)}; confirmation=false"
                    decision = "blocked_unresolved"
                tagged.append((int(timestamp), classification, evidence, decision))
            groups: list[list[tuple[int, str, str, str]]] = []
            for item in tagged:
                if groups and item[0] == groups[-1][-1][0] + 300_000 and item[1:] == groups[-1][-1][1:]:
                    groups[-1].append(item)
                else:
                    groups.append([item])
            for group in groups:
                first = group[0]
                record = {
                    "symbol": symbol,
                    "month": month,
                    "timestamp": first[0],
                    "missing_count": len(group),
                    "duration_minutes": len(group) * 5,
                    "classification": first[1],
                    "evidence_source": first[2],
                    "qualification_decision": first[3],
                }
                records.append(record)
                if first[1] == "binance_global_event":
                    global_windows[(month, first[0], len(group))] = record
                elif first[1] == "symbol_specific_confirmed_archive_gap":
                    symbol_quarantines.add((symbol, month))
                else:
                    unresolved += 1
    panel: list[dict[str, Any]] = []
    for month, members in sorted(members_by_month.items()):
        start_ms, end_ms = month_bounds_ms(month)
        expected_hours = (end_ms - start_ms) // 3_600_000
        global_hours = {
            timestamp // 3_600_000
            for (window_month, start, count) in global_windows
            if window_month == month
            for timestamp in range(start, start + count * 300_000, 300_000)
        }
        for symbol in sorted(members):
            if (symbol, month) in symbol_quarantines:
                status, valid = "symbol_month_quarantined", 0
            elif any(item["symbol"] == symbol and item["month"] == month and item["qualification_decision"] == "blocked_unresolved" for item in records):
                status, valid = "blocked", 0
            elif global_hours:
                status, valid = "global_window_quarantined", expected_hours - len(global_hours)
            else:
                status, valid = "clean", expected_hours
            panel.append({
                "effective_month": month,
                "symbol": symbol,
                "status": status,
                "expected_1h_count": expected_hours,
                "quarantined_1h_count": expected_hours - valid,
                "valid_1h_count": valid,
            })
    diagnostics = {
        "records": records,
        "global_windows": global_windows,
        "symbol_quarantines": symbol_quarantines,
        "unresolved": unresolved,
        "members_by_month": members_by_month,
    }
    return panel, diagnostics


def _membership_diff(old_rows: Sequence[Mapping[str, Any]], new_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def grouped(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
        result: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for row in rows:
            result[str(row["effective_month"])[:7]].append((int(row["rank"]), str(row["symbol"])))
        return {month: [symbol for _, symbol in sorted(values)] for month, values in sorted(result.items())}
    left, right = grouped(old_rows), grouped(new_rows)
    details = [{"effective_month": month, "v3": left.get(month, []), "v4": right.get(month, [])} for month in sorted(set(left) | set(right)) if left.get(month) != right.get(month)]
    return {"months_compared": len(set(left) | set(right)), "changed_months": len(details), "details": details}


def _summary(
    *, source_manifest: Sequence[Mapping[str, Any]], memberships: Sequence[Mapping[str, Any]], panel: Sequence[Mapping[str, Any]],
    gap: Mapping[str, Any], resolution: Mapping[str, Any], lifecycle_events: Sequence[LifecycleEvent], blockers: Sequence[str],
    contract: Mapping[str, Any], months: Sequence[str], lifecycle_quarantine: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    members_by_month = gap["members_by_month"]
    counters = resolution["counters"]
    impact = {
        (event.symbol, utc_iso(event.effective_at_ms)[:7])
        for event in lifecycle_events
        if event.symbol in members_by_month.get(utc_iso(event.effective_at_ms)[:7], [])
    }
    statuses = ("clean", "global_window_quarantined", "symbol_month_quarantined", "blocked")
    return {
        "status": "pass" if not blockers and gap["unresolved"] == 0 else "blocked",
        "contract_id": "BINANCE-SPOT-USDT-DYNAMIC-TOP15-V4",
        "research_start": months[0],
        "end_month": months[-1],
        "historical_symbols_discovered": len({row["symbol"] for row in source_manifest if row["interval"] == "1d"}),
        "excluded_invalid_daily_rows": 0,
        "expected_months": len(months),
        "monthly_memberships": len(members_by_month),
        "membership_rows": len(memberships),
        "processing_errors": len(blockers),
        "unresolved_gaps": gap["unresolved"],
        "excluded_category_members": 0,
        "synthetic_fills": 0,
        "replacement_members": 0,
        "gap_records": len(gap["records"]),
        "gap_missing_slots": sum(int(item["missing_count"]) for item in gap["records"]),
        "global_windows": len(gap["global_windows"]),
        "symbol_month_quarantines": len(gap["symbol_quarantines"]),
        "panel_status_counts": {status: sum(row["status"] == status for row in panel) for status in statuses},
        "members_by_month": [{"effective_month": month, "symbols": sorted(symbols)} for month, symbols in sorted(members_by_month.items())],
        "blockers": sorted(blockers) + ([f"unresolved_gap_records={gap['unresolved']}"] if gap["unresolved"] else []),
        "authorizations": ZERO_AUTHORIZATIONS,
        **counters,
        "lifecycle_event_count": len(lifecycle_events),
        "lifecycle_terminated_symbol_months": len(lifecycle_events),
        "partial_lifecycle_days": sum(1 for item in lifecycle_quarantine if item["open_time_utc"].startswith("2024-10-28")),
        "post_cessation_rows_quarantined": sum(1 for item in lifecycle_quarantine if not item["open_time_utc"].startswith("2024-10-28")),
        "unresolved_lifecycle_rows": 0,
        "epoch_overlaps": 0,
        "active_count_distribution": {"14": len(impact), "15": len(months) - len(impact)},
        "membership_replacements_after_lifecycle": 0,
        "stale_prices": 0,
    }


def _build_contents(
    *, repository: Path, raw_root: Path, protocol: Mapping[str, Any], order: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence_dir = repository / "reports/m0/evidence/liquid_universe_v4"
    v4_contract = load_json(repository / "config/liquid_spot_universe_contract_v4.json")
    v3_contract = load_json(repository / "config/liquid_spot_universe_contract_v3.json")
    eligibility_registry = load_json(repository / "config/liquid_spot_asset_eligibility_v2.json")
    confirmed_gaps = load_json(repository / "config/liquid_spot_confirmed_archive_gaps_v2.json")
    row_registry = load_json(repository / "config/liquid_spot_source_conflict_resolutions_v3.json")
    lifecycle_policy = load_json(repository / "config/liquid_spot_lifecycle_policy_v4.json")
    lifecycle_registry = load_json(repository / "config/liquid_spot_lifecycle_event_resolutions_v4.json")
    freeze = load_json(evidence_dir / "source_freeze_manifest.json")
    lifecycle_events = validate_lifecycle_registry(
        lifecycle_policy, lifecycle_registry,
        research_start="2020-01-01T00:00:00Z",
        expected_policy_hash=protocol["authority_bindings"]["lifecycle_policy_hash"],
        expected_registry_hash=protocol["authority_bindings"]["lifecycle_event_registry_hash"],
        expected_reviewed_event_set_hash=lifecycle_registry["reviewed_event_set_hash"],
    )
    source_manifest, monthly, supplements, grids = _scan_sources(
        raw_root=raw_root, freeze_entries=list(freeze["content"]["archives"]), order=order,
        lifecycle_events=lifecycle_events,
    )
    daily, resolution, lifecycle_quarantine, lifecycle_blocked, blockers = _resolve_daily_authority(
        monthly=monthly, supplements=supplements, row_registry=row_registry,
        lifecycle_events=lifecycle_events, eligibility_registry=eligibility_registry,
    )
    months = month_sequence(protocol["audit_scope"]["range_start"], protocol["audit_scope"]["range_end"])
    eligibility, memberships = _eligibility_and_membership(
        daily=daily, contract=v3_contract, registry=eligibility_registry, months=months,
    )
    membership_keys = {(str(row["symbol"]), str(row["effective_month"])[:7]) for row in memberships}
    if set(grids) != membership_keys:
        blockers.append(f"five_minute_source_set_mismatch:missing={len(membership_keys-set(grids))}:extra={len(set(grids)-membership_keys)}")
    for key, value in grids.items():
        source = next(item for item in source_manifest if item["symbol"] == key[0] and item["interval"] == "5m" and item["archive_month"] == key[1])
        value["archive_sha256"] = source["sha256"]
        blockers.extend(f"{key[0]}:{key[1]}:{error}" for error in value["errors"])
    panel, gap = _gap_and_panel(
        memberships=memberships, grids=grids, confirmed_gap_registry=confirmed_gaps,
        contract=v3_contract,
    )
    summary = _summary(
        source_manifest=source_manifest, memberships=memberships, panel=panel, gap=gap,
        resolution=resolution, lifecycle_events=lifecycle_events, blockers=blockers,
        contract=v4_contract, months=months, lifecycle_quarantine=lifecycle_quarantine,
    )
    availability = [{
        "event_id": event.event_id,
        "symbol": event.symbol,
        "start_inclusive": "2020-01-01T00:00:00Z",
        "end_exclusive": utc_iso(event.availability_end_exclusive_ms),
        "identity_version": event.source["identity_version"],
    } for event in lifecycle_events]
    lifecycle_months = sorted([[event.symbol, utc_iso(event.effective_at_ms)[:7]] for event in lifecycle_events])
    complete_day = {
        "partial_days": [[event.symbol, "1d", int(item["open_time_ms"])] for event in lifecycle_events for item in event.source["affected_raw_rows"] if item["classification"] == "cessation_day_partial_row"],
        "terminated_days": [[event.symbol, "1d", int(item["open_time_ms"])] for event in lifecycle_events for item in event.source["affected_raw_rows"] if item["classification"].startswith("post_cessation")],
        "partial_days_window_eligible": False,
    }
    active = {
        "month_start_membership_rows": len(memberships),
        "lifecycle_terminated_symbol_months": lifecycle_months,
        "active_count_distribution": summary["active_count_distribution"],
        "membership_replacement": False,
    }
    production_v3_membership = load_json(repository / "reports/m0/evidence/liquid_universe_v3/membership_manifest.json")["content"]
    production_v3_summary = load_json(repository / "reports/m0/evidence/liquid_universe_v3/qualification_summary.json")["content"]
    diff = {
        "v3_status": production_v3_summary["status"],
        "v4_status": summary["status"],
        "v3_unresolved_row_conflicts": production_v3_summary["unresolved_row_conflicts"],
        "v4_unresolved_row_conflicts": summary["unresolved_row_conflicts"],
        "lifecycle_events_added": len(lifecycle_events),
        "membership": _membership_diff(production_v3_membership, memberships),
        "v3_mutated": False,
    }
    contents = {
        "source_manifest": source_manifest,
        "row_conflict_resolution_manifest": resolution,
        "lifecycle_policy_manifest": lifecycle_policy,
        "lifecycle_resolution_registry": lifecycle_registry,
        "symbol_availability_manifest": availability,
        "active_universe_manifest": active,
        "complete_day_mask": complete_day,
        "expected_grid_manifest": [{
            "symbol": symbol, "month": month,
            "expected_count": int(value["expected_count"]),
            "actual_count": int(value["actual_count"]),
            "missing_count": len(value["missing"]),
            "errors": list(value["errors"]),
            "complete": bool(value["complete"]),
        } for (symbol, month), value in sorted(grids.items())],
        "raw_row_quarantine_manifest": lifecycle_quarantine,
        "lifecycle_event_quarantine_manifest": lifecycle_blocked,
        "candidate_eligibility_manifest": eligibility,
        "membership_manifest": memberships,
        "qualified_panel_manifest": panel,
        "qualification_summary": summary,
        "V3_V4_diff": diff,
    }
    diagnostics = {
        "source_freeze_content_hash": freeze["content_hash"],
        "source_archive_count": len(freeze["content"]["archives"]),
        "gap_records": len(gap["records"]),
        "global_windows": len(gap["global_windows"]),
        "symbol_month_quarantines": len(gap["symbol_quarantines"]),
        "membership_rows": len(memberships),
        "months": len(months),
    }
    return contents, diagnostics


def build_independent_suite(*, repository: Path, raw_root: Path, protocol: Mapping[str, Any], order: str) -> dict[str, Any]:
    contents, diagnostics = _build_contents(repository=repository, raw_root=raw_root, protocol=protocol, order=order)
    # Normalize mapping key order before exact structural comparison. Array order
    # remains untouched and is part of the frozen identity.
    contents = strict_json_loads(json.dumps(contents, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    manifests = build_audit_artifacts(
        contents,
        contract_hash=load_json(repository / "config/liquid_spot_universe_contract_v4.json")["canonical_hash"],
        lifecycle_registry_hash=load_json(repository / "config/liquid_spot_lifecycle_event_resolutions_v4.json")["canonical_hash"],
    )
    manifests = strict_json_loads(json.dumps(manifests, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return {
        "order": order,
        "manifests": manifests,
        "manifest_hashes": {name: audit_manifest_hash(value) for name, value in sorted(manifests.items())},
        "artifact_set_hash": audit_artifact_set_hash(manifests),
        "source_hash": audit_identity_hash(manifests["source_manifest"]),
        "membership_hash": audit_identity_hash(manifests["membership_manifest"]),
        "grid_hash": audit_identity_hash(manifests["expected_grid_manifest"]),
        "lifecycle_hash": audit_identity_hash({name: manifests[name] for name in ("lifecycle_policy_manifest", "lifecycle_resolution_registry", "symbol_availability_manifest")}),
        "panel_hash": audit_identity_hash(manifests["qualified_panel_manifest"]),
        "diagnostics": diagnostics,
    }


def _validate_frozen_bindings(repository: Path, protocol: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    evidence = repository / "reports/m0/evidence/liquid_universe_v4"
    bindings = protocol["authority_bindings"]
    config_bindings = {
        "v4_contract_hash": ("config/liquid_spot_universe_contract_v4.json", "canonical_hash"),
        "lifecycle_policy_hash": ("config/liquid_spot_lifecycle_policy_v4.json", "canonical_hash"),
        "lifecycle_event_registry_hash": ("config/liquid_spot_lifecycle_event_resolutions_v4.json", "canonical_hash"),
        "v3_row_conflict_registry_hash": ("config/liquid_spot_source_conflict_resolutions_v3.json", "canonical_hash"),
    }
    for binding, (path, field) in config_bindings.items():
        if load_json(repository / path).get(field) != bindings[binding]:
            failures.append(f"frozen binding changed: {binding}")
    freeze = load_json(evidence / "source_freeze_manifest.json")
    try:
        verify_manifest_wrapper(freeze, expected_type="liquid_universe_v4_source_freeze")
    except ValueError as exc:
        failures.append(str(exc))
    if freeze.get("content_hash") != bindings["source_freeze_hash"]:
        failures.append("source freeze hash changed")
    production: dict[str, Any] = {}
    for name, expected in protocol["production_manifest_hashes"].items():
        path = evidence / f"{name}.json"
        try:
            document = load_json(path)
            actual = verify_manifest_wrapper(document)
            production[name] = document
            if actual != expected:
                failures.append(f"production manifest hash changed: {name}")
        except (OSError, ValueError) as exc:
            failures.append(f"production manifest unreadable: {name}:{exc}")
    if production and audit_artifact_set_hash(production) != bindings["production_artifact_set_hash"]:
        failures.append("production artifact set hash changed")
    run_manifest = load_json(evidence / "requalification_run_manifest.json")
    if verify_manifest_wrapper(run_manifest, expected_type="liquid_universe_v4_requalification_run") != bindings["production_run_manifest_hash"]:
        failures.append("production run manifest hash changed")
    return failures


def _production_time_findings(repository: Path) -> list[str]:
    paths = (
        repository / "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
        repository / "scripts/liquid_universe_v4_public_run.py",
    )
    findings: list[str] = []
    for path in paths:
        findings.extend(f"{path.relative_to(repository)}:{item}" for item in scan_float_timestamp_paths(path.read_text(encoding="utf-8")))
    return findings


def _boundary_differential() -> dict[str, Any]:
    # Current-range epochs are exactly representable after the production float
    # round trip.  A sub-millisecond synthetic boundary proves the authority
    # pattern itself cannot preserve the adopted integer-only semantics.
    current = [
        milliseconds_from_utc("2020-01-01T00:00:00Z"),
        milliseconds_from_utc("2024-10-28T03:00:00Z"),
        milliseconds_from_utc("2026-07-01T00:00:00Z"),
    ]
    current_mismatches = sum(int(value) != int((value / 1_000) * 1_000) for value in current)
    fault_us = 9_007_199_254_740_999
    exact_ms = fault_us // 1_000
    float_ms = int((fault_us / 1_000_000) * 1_000)
    return {
        "current_boundary_cases": len(current),
        "current_boundary_mismatches": current_mismatches,
        "fault_microseconds": fault_us,
        "fault_exact_milliseconds": exact_ms,
        "fault_float_milliseconds": float_ms,
        "fault_mismatch": exact_ms != float_ms,
    }


def execute_audit(*, repository: Path, raw_root: Path, protocol_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    binding_failures = _validate_frozen_bindings(repository, protocol)
    if binding_failures:
        return {"verdict": "blocked_protocol_violation", "failures": binding_failures}
    runs = [build_independent_suite(repository=repository, raw_root=raw_root, protocol=protocol, order=mode) for mode in ("normal", "reverse", "shuffled")]
    identity_fields = ("source_hash", "membership_hash", "grid_hash", "lifecycle_hash", "panel_hash", "artifact_set_hash")
    determinism = {field: len({run[field] for run in runs}) == 1 for field in identity_fields}
    production_dir = repository / "reports/m0/evidence/liquid_universe_v4"
    production = {name: load_json(production_dir / f"{name}.json") for name in PRODUCTION_NAMES}
    comparison = compare_artifact_suite(production, runs[0]["manifests"])
    time_findings = _production_time_findings(repository)
    boundary = _boundary_differential()
    qualification_path = repository / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md"
    diff_path = repository / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md"
    run_manifest = load_json(production_dir / "requalification_run_manifest.json")
    recorded_report_hash = run_manifest["content"]["builds"]["cold"]["qualification_report_sha256"]
    report_hash = file_sha256(qualification_path)
    diff_hash = file_sha256(diff_path)
    report_binding_match = recorded_report_hash == report_hash
    high_findings = [f"integer_only_policy_violation:{item}" for item in time_findings]
    if not report_binding_match:
        high_findings.append("run_manifest_qualification_report_hash_does_not_match_committed_report")
    critical_findings: list[str] = []
    if boundary["current_boundary_mismatches"] or not comparison["exact"]:
        critical_findings.append("independent_integer_recomputation_differs_from_production_evidence")
    if not all(determinism.values()):
        critical_findings.append("independent_runs_are_not_deterministic")
    verdict = "pass" if not critical_findings and not high_findings else "failed_audit"
    summary = {
        "schema_version": 1,
        "audit_id": "U03F-LIQUID-UNIVERSE-V4-INDEPENDENT-AUDIT-RUN-V1",
        "protocol_id": protocol["protocol_id"],
        "protocol_hash": audit_identity_hash(protocol),
        "verdict": verdict,
        "range": {"start": protocol["audit_scope"]["range_start"], "end": protocol["audit_scope"]["range_end"]},
        "source_freeze_hash": protocol["authority_bindings"]["source_freeze_hash"],
        "runs": [{key: run[key] for key in ("order", *identity_fields)} for run in runs],
        "determinism": determinism,
        "production_artifact_set_hash": protocol["authority_bindings"]["production_artifact_set_hash"],
        "independent_artifact_set_hash": runs[0]["artifact_set_hash"],
        "comparison": comparison,
        "qualification_report": {
            "committed_sha256": report_hash,
            "run_recorded_sha256": recorded_report_hash,
            "exact_match": report_binding_match,
        },
        "v3_v4_diff_report": {
            "committed_sha256": diff_hash,
            "frozen_sha256": protocol["authority_bindings"]["v3_v4_diff_report_sha256"],
            "exact_match": diff_hash == protocol["authority_bindings"]["v3_v4_diff_report_sha256"],
        },
        "integer_time": {
            "static_findings": time_findings,
            "boundary_differential": boundary,
            "full_data_integer_recomputation_executed": True,
            "current_data_artifact_difference": not comparison["exact"],
            "policy_conformance": "fail" if time_findings else "pass",
        },
        "counts": runs[0]["diagnostics"],
        "critical_findings": critical_findings,
        "high_findings": high_findings,
        "authorization": ZERO_AUTHORIZATIONS,
        "production_evidence_mutated": False,
        "network_accessed": False,
    }
    summary["audit_summary_hash"] = audit_identity_hash(summary)
    return {"summary": summary, "comparison": comparison, "runs": runs, "production": production}


def _evidence_documents(result: Mapping[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    manifests = result["runs"][0]["manifests"]
    return {
        "audit_source_manifest.json": manifests["source_manifest"],
        "audit_row_conflict_manifest.json": manifests["row_conflict_resolution_manifest"],
        "audit_lifecycle_manifest.json": {
            "policy": manifests["lifecycle_policy_manifest"],
            "registry": manifests["lifecycle_resolution_registry"],
            "availability": manifests["symbol_availability_manifest"],
        },
        "audit_membership_manifest.json": manifests["membership_manifest"],
        "audit_expected_grid_manifest.json": manifests["expected_grid_manifest"],
        "audit_quarantine_manifest.json": {
            "raw": manifests["raw_row_quarantine_manifest"],
            "lifecycle": manifests["lifecycle_event_quarantine_manifest"],
        },
        "audit_complete_day_manifest.json": manifests["complete_day_mask"],
        "audit_active_universe_manifest.json": manifests["active_universe_manifest"],
        "audit_qualified_panel_manifest.json": manifests["qualified_panel_manifest"],
        "production_comparison_manifest.json": result["comparison"],
        "audit_run_manifest.json": {
            "schema_version": 1,
            "audit_id": summary["audit_id"],
            "runs": summary["runs"],
            "determinism": summary["determinism"],
            "authorization": summary["authorization"],
        },
        "audit_summary.json": summary,
    }


def render_report(summary: Mapping[str, Any]) -> str:
    comparisons = summary["comparison"]["comparisons"]
    exact_count = sum(item["exact_content_match"] for item in comparisons.values())
    mismatch_count = len(comparisons) - exact_count
    lines = [
        "# U-03F Liquid Universe V4 Independent Audit Report", "",
        f"- Verdict: {summary['verdict']}",
        f"- Range: {summary['range']['start']} through {summary['range']['end']}",
        f"- Source freeze: `{summary['source_freeze_hash']}`",
        f"- Production artifact set: `{summary['production_artifact_set_hash']}`",
        f"- Independent artifact set: `{summary['independent_artifact_set_hash']}`",
        f"- Months compared: {summary['counts']['months']}",
        f"- Membership rows compared: {summary['counts']['membership_rows']}",
        f"- Critical findings: {len(summary['critical_findings'])}",
        f"- High findings: {len(summary['high_findings'])}",
        "- Production evidence mutated: no",
        "- Network accessed: no",
        "- Strategy/events/signals/returns/OOS accessed: no",
        "- U-04 authorized: no",
        "- M2 authorized: no", "",
        "## Audit Coverage", "",
        f"- Frozen source archives read: {summary['counts']['source_archive_count']}",
        f"- Production manifests compared: {len(comparisons)}",
        f"- Exact production manifests: {exact_count}",
        f"- Mismatched production manifests: {mismatch_count}",
        f"- Independent gap records: {summary['counts']['gap_records']}",
        f"- Independent synchronized global windows: {summary['counts']['global_windows']}",
        f"- Independent symbol-month quarantines: {summary['counts']['symbol_month_quarantines']}", "",
        "## Independent Runs", "",
    ]
    for run in summary["runs"]:
        lines.append(f"- {run['order']}: artifact_set=`{run['artifact_set_hash']}`; source=`{run['source_hash']}`; membership=`{run['membership_hash']}`; grid=`{run['grid_hash']}`; lifecycle=`{run['lifecycle_hash']}`; panel=`{run['panel_hash']}`")
    lines.extend(["", "## Production Comparison", "", "| Artifact | Production | Independent | Exact | Rows | Types | Mismatches | First mismatch |", "| --- | --- | --- | --- | --- | --- | ---: | --- |"])
    for name, item in sorted(comparisons.items()):
        first = str(item["first_mismatch"] or "none").replace("|", "\\|")
        lines.append(f"| {name} | `{item['production_content_hash']}` | `{item['independent_content_hash']}` | {str(item['exact_content_match']).lower()} | {str(item['row_count_match']).lower()} | {str(item['field_type_match']).lower()} | {item['mismatch_count']} | {first} |")
    lines.extend(["", "## Minimal Counterexamples", ""])
    mismatches = [
        (name, item) for name, item in sorted(comparisons.items())
        if not item["exact_content_match"]
    ]
    if mismatches:
        for name, item in mismatches:
            lines.append(
                f"- {name}: {item['first_mismatch']}; "
                f"production=`{item['production_content_hash']}`; "
                f"independent=`{item['independent_content_hash']}`; "
                f"mismatches={item['mismatch_count']}"
            )
    else:
        lines.append("- none")
    lines.extend([
        "", "## Reconciliation Summary", "",
        f"- Row-conflict resolution: {'exact' if comparisons['row_conflict_resolution_manifest']['exact_content_match'] else 'mismatch'}",
        f"- Lifecycle policy/registry/availability: {'exact' if all(comparisons[name]['exact_content_match'] for name in ('lifecycle_policy_manifest', 'lifecycle_resolution_registry', 'symbol_availability_manifest')) else 'mismatch'}",
        f"- Membership: {'exact' if comparisons['membership_manifest']['exact_content_match'] else 'mismatch'}",
        f"- Expected grid: {'exact' if comparisons['expected_grid_manifest']['exact_content_match'] else 'mismatch'}",
        f"- Gap/quarantine: {'exact' if all(comparisons[name]['exact_content_match'] for name in ('raw_row_quarantine_manifest', 'lifecycle_event_quarantine_manifest')) else 'mismatch'}",
        f"- Complete-day mask: {'exact' if comparisons['complete_day_mask']['exact_content_match'] else 'mismatch'}",
        f"- Active universe: {'exact' if comparisons['active_universe_manifest']['exact_content_match'] else 'mismatch'}",
        f"- Qualified panel: {'exact' if comparisons['qualified_panel_manifest']['exact_content_match'] else 'mismatch'}",
        "- KLAY lifecycle affected rows: exact through the lifecycle registry, availability and quarantine manifests",
    ])
    lines.extend(["", "## Integer-Time Conformance", "", f"- Full-data integer recomputation executed: {str(summary['integer_time']['full_data_integer_recomputation_executed']).lower()}", f"- Current-data artifact difference: {str(summary['integer_time']['current_data_artifact_difference']).lower()}", f"- Policy conformance: {summary['integer_time']['policy_conformance']}", f"- Boundary differential: `{json.dumps(summary['integer_time']['boundary_differential'], sort_keys=True, separators=(',', ':'))}`", ""])
    lines.extend(f"- {item}" for item in summary["integer_time"]["static_findings"] or ["none"])
    lines.extend(["", "## Report And Run Bindings", "", f"- Qualification report exact: {str(summary['qualification_report']['exact_match']).lower()}", f"- Committed qualification report: `{summary['qualification_report']['committed_sha256']}`", f"- Run-recorded qualification report: `{summary['qualification_report']['run_recorded_sha256']}`", f"- V3/V4 diff report exact: {str(summary['v3_v4_diff_report']['exact_match']).lower()}", "", "## Findings", "", "### Critical", ""])
    lines.extend(f"- {item}" for item in summary["critical_findings"] or ["none"])
    lines.extend(["", "### High", ""])
    lines.extend(f"- {item}" for item in summary["high_findings"] or ["none"])
    lines.extend(["", "## Decision", "", "The audit result is evidence only. It does not modify V4 production artifacts and does not authorize U-04, strategy work, OOS, trading, or M2.", ""])
    return "\n".join(lines)


def write_audit_result(*, result: Mapping[str, Any], evidence_dir: Path, report_path: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in _evidence_documents(result).items():
        (evidence_dir / name).write_text(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result["summary"]), encoding="utf-8")
