"""Outcome-free V2 qualification pipeline over verified public evidence."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Any

from btc_eth_dual_quant.data.liquid_universe import (
    DailyEvidence,
    GridResult,
    MembershipRow,
    MinuteBar,
    build_month,
    canonical_hash,
    exclusion_record,
    expected_five_minute_grid,
    month_bounds,
    validate_symbol_month_grid,
)
from btc_eth_dual_quant.data.liquid_universe_artifacts import make_manifest
from btc_eth_dual_quant.data.universe_gap_attribution import (
    GapRecord,
    classify_missing_slots,
    gate,
    quarantine_manifest,
)

CONFIRMED_GAP_REGISTRY_HASH = "0e5d66a3968e0bb6ad89f81db9be8201b97f7e8fe8e257f648db0b5e2ba08f87"


def month_sequence(start: date, end_month: str) -> list[date]:
    end = date.fromisoformat(f"{end_month}-01")
    months = []
    current = start
    while current <= end:
        months.append(current)
        current = date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
    return months


def _eligibility_rows(
    months: list[date],
    daily: list[DailyEvidence],
    contract: dict[str, Any],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    by_symbol: dict[str, set[date]] = defaultdict(set)
    for row in daily:
        by_symbol[row.symbol].add(row.day)
    result = []
    history_days = contract["membership"]["minimum_complete_history_days"]
    rank_days = contract["membership"]["ranking_window_complete_days"]
    for effective in months:
        for symbol in sorted(by_symbol):
            exclusion = exclusion_record(symbol, effective, contract, registry)
            history_start = effective - timedelta(days=history_days)
            rank_start = effective - timedelta(days=rank_days)
            history_complete = all(history_start + timedelta(days=index) in by_symbol[symbol] for index in range(history_days))
            rank_complete = all(rank_start + timedelta(days=index) in by_symbol[symbol] for index in range(rank_days))
            if exclusion:
                status = "excluded_by_contract"
                reason = exclusion["category"]
            elif not history_complete:
                status = "insufficient_history"
                reason = "prior_365_complete_days_missing"
            elif not rank_complete:
                status = "insufficient_rank_window"
                reason = "prior_90_complete_days_missing"
            else:
                status = "eligible_for_ranking"
                reason = None
            result.append({
                "effective_month": effective.strftime("%Y-%m"),
                "symbol": symbol,
                "status": status,
                "reason": reason,
                "history_window_start": history_start.isoformat(),
                "ranking_window_start": rank_start.isoformat(),
                "window_end_exclusive": effective.isoformat(),
            })
    return result


def _confirmed_symbol_months(confirmed_gap_registry: dict[str, Any]) -> set[tuple[str, str]]:
    if confirmed_gap_registry.get("schema_version") != 2:
        raise ValueError("confirmed-gap registry schema mismatch")
    declared_hash = confirmed_gap_registry.get("canonical_hash")
    if declared_hash is not None and (
        declared_hash != CONFIRMED_GAP_REGISTRY_HASH
        or canonical_hash({key: value for key, value in confirmed_gap_registry.items() if key != "canonical_hash"}) != declared_hash
    ):
        raise ValueError("confirmed-gap registry hash mismatch")
    return {(row["symbol"], row["month"]) for row in confirmed_gap_registry.get("records", [])}


def build_membership_rows(contract: dict[str, Any], registry: dict[str, Any], daily: list[DailyEvidence]) -> list[MembershipRow]:
    rows: list[MembershipRow] = []
    for month in month_sequence(date.fromisoformat(contract["research_start"]), contract["frozen_end_month"]):
        rows.extend(build_month(month, daily, contract, registry))
    return rows


def build_artifacts(
    *,
    contract: dict[str, Any],
    registry: dict[str, Any],
    confirmed_gap_registry: dict[str, Any],
    daily: list[DailyEvidence],
    bars_by_symbol_month: dict[tuple[str, str], list[MinuteBar]],
    source_rows: list[dict[str, Any]],
    grid_results: dict[tuple[str, str], GridResult] | None = None,
    processing_errors: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build all V2 artifacts without reading Markdown or outcome data."""
    processing_errors = list(processing_errors or [])
    grid_results = grid_results or {}
    contract_hash = contract["canonical_hash"]
    registry_hash = registry["canonical_hash"]
    months = month_sequence(date.fromisoformat(contract["research_start"]), contract["frozen_end_month"])
    membership_rows = build_membership_rows(contract, registry, daily)
    members_by_month: dict[str, list[str]] = defaultdict(list)
    for row in membership_rows:
        members_by_month[row.effective_month[:7]].append(row.symbol)
    for month, symbols in members_by_month.items():
        if not 1 <= len(symbols) <= contract["membership"]["target_size"]:
            processing_errors.append(f"invalid member count: {month}:{len(symbols)}")

    source_by_key = {(row["symbol"], row["interval"], row["archive_month"]): row for row in source_rows}
    missing_by_key: dict[tuple[str, str], set[datetime]] = {}
    verified_by_month: dict[str, set[str]] = defaultdict(set)
    for month, symbols in members_by_month.items():
        for symbol in symbols:
            key = (symbol, month)
            source = source_by_key.get((symbol, "5m", month))
            if source is None:
                processing_errors.append(f"missing source manifest row: {symbol}:{month}:5m")
                missing_by_key[key] = set(expected_five_minute_grid(month))
                continue
            if source.get("verification_status") not in {
                "official_checksum_verified",
                "official_checksum_unavailable_zip_crc_sha256_verified",
            }:
                processing_errors.append(f"unverified 5m archive: {symbol}:{month}")
            else:
                verified_by_month[month].add(symbol)
            grid = grid_results.get(key) or validate_symbol_month_grid(symbol, month, bars_by_symbol_month.get(key, []))
            missing_by_key[key] = set(grid.missing)
            processing_errors.extend(f"{symbol}:{month}:{error}" for error in grid.errors)

    confirmed = _confirmed_symbol_months(confirmed_gap_registry)
    records: list[GapRecord] = []
    for month, symbols in sorted(members_by_month.items()):
        missing_by_slot: dict[datetime, set[str]] = defaultdict(set)
        for symbol in symbols:
            for timestamp in missing_by_key[(symbol, month)]:
                missing_by_slot[timestamp].add(symbol)
        for symbol in symbols:
            source = source_by_key.get((symbol, "5m", month), {})
            evidence = f"archive_sha256={source.get('sha256', 'missing')}"
            records.extend(classify_missing_slots(
                symbol=symbol,
                month=month,
                missing=missing_by_key[(symbol, month)],
                missing_by_slot=missing_by_slot,
                member_count=len(symbols),
                evidence_source=evidence,
                policy=contract["gap_handling_policy"],
                verified_symbols=verified_by_month[month],
                confirmed_symbol_months=confirmed,
            ))
    gap_status, unresolved_count = gate(records, processing_errors, universe_months=len(members_by_month))
    quarantine = quarantine_manifest(records, members_by_month, contract_hash=contract_hash, registry_hash=registry_hash)

    global_by_month: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    symbol_month_quarantine: set[tuple[str, str]] = set()
    for scope in quarantine["scopes"]:
        if scope["scope"] == "global_window":
            global_by_month[scope["month"]].append((scope["start"], scope["end_exclusive"]))
        else:
            symbol_month_quarantine.add((scope["symbol"], scope["month"]))
    panel = []
    for month, symbols in sorted(members_by_month.items()):
        month_start, month_end = month_bounds(month)
        expected_hours = int((month_end - month_start).total_seconds() // 3600)
        global_hours = {
            timestamp.replace(minute=0, second=0, microsecond=0)
            for start, end in global_by_month.get(month, [])
            for timestamp in _five_minute_range(start, end)
        }
        for symbol in sorted(symbols):
            if (symbol, month) in symbol_month_quarantine:
                status = "symbol_month_quarantined"
                valid_hours = 0
            elif any(record.symbol == symbol and record.month == month and record.qualification_decision == "blocked_unresolved" for record in records):
                status = "blocked"
                valid_hours = 0
            elif global_hours:
                status = "global_window_quarantined"
                valid_hours = expected_hours - len(global_hours)
            else:
                status = "clean"
                valid_hours = expected_hours
            panel.append({
                "effective_month": month,
                "symbol": symbol,
                "status": status,
                "expected_1h_count": expected_hours,
                "quarantined_1h_count": expected_hours - valid_hours,
                "valid_1h_count": valid_hours,
            })

    eligibility = _eligibility_rows(months, daily, contract, registry)
    source_manifest = make_manifest("source_manifest", sorted(source_rows, key=lambda row: (row["symbol"], row["interval"], row["archive_month"])), contract_hash=contract_hash, registry_hash=registry_hash)
    eligibility_manifest = make_manifest("candidate_eligibility_manifest", eligibility, contract_hash=contract_hash, registry_hash=registry_hash)
    membership_manifest = make_manifest("membership_manifest", [asdict(row) for row in membership_rows], contract_hash=contract_hash, registry_hash=registry_hash)
    quarantine_wrapped = make_manifest("quarantine_manifest", quarantine, contract_hash=contract_hash, registry_hash=registry_hash)
    panel_manifest = make_manifest("qualified_panel_manifest", panel, contract_hash=contract_hash, registry_hash=registry_hash)
    excluded_members = sum(
        exclusion_record(row.symbol, date.fromisoformat(row.effective_month), contract, registry) is not None
        for row in membership_rows
    )
    status = "pass" if (
        gap_status == "pass_with_quarantine"
        and len(members_by_month) == len(months)
        and excluded_members == 0
        and not processing_errors
    ) else "blocked"
    summary_content = {
        "status": status,
        "contract_id": contract["universe_id"],
        "research_start": contract["research_start"],
        "end_month": contract["frozen_end_month"],
        "historical_symbols_discovered": len({row.symbol for row in daily}),
        "expected_months": len(months),
        "monthly_memberships": len(members_by_month),
        "membership_rows": len(membership_rows),
        "processing_errors": len(processing_errors),
        "unresolved_gaps": unresolved_count,
        "excluded_category_members": excluded_members,
        "synthetic_fills": 0,
        "replacement_members": 0,
        "gap_records": len(records),
        "gap_missing_slots": sum(record.missing_count for record in records),
        "global_windows": len({(record.month, record.timestamp, record.missing_count) for record in records if record.classification == "binance_global_event"}),
        "symbol_month_quarantines": len(symbol_month_quarantine),
        "panel_status_counts": {status_name: sum(row["status"] == status_name for row in panel) for status_name in ("clean", "global_window_quarantined", "symbol_month_quarantined", "blocked")},
        "members_by_month": [{"effective_month": month, "symbols": sorted(symbols)} for month, symbols in sorted(members_by_month.items())],
        "blockers": sorted(processing_errors) + ([f"unresolved_gap_records={unresolved_count}"] if unresolved_count else []),
        "authorizations": contract["authorizations"],
    }
    summary = make_manifest("qualification_summary", summary_content, contract_hash=contract_hash, registry_hash=registry_hash)
    return {
        "source_manifest": source_manifest,
        "candidate_eligibility_manifest": eligibility_manifest,
        "membership_manifest": membership_manifest,
        "quarantine_manifest": quarantine_wrapped,
        "qualified_panel_manifest": panel_manifest,
        "qualification_summary": summary,
    }


def _five_minute_range(start: datetime, end: datetime):
    current = start
    while current < end:
        yield current
        current += timedelta(minutes=5)


def artifact_set_hash(artifacts: dict[str, dict[str, Any]]) -> str:
    return canonical_hash({name: document["content_hash"] for name, document in sorted(artifacts.items())})
