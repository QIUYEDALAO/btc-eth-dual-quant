"""Fail-closed attribution and quarantine for missing public 5m intervals."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import math
from typing import Iterable

from btc_eth_dual_quant.data.liquid_universe import canonical_hash


@dataclass(frozen=True)
class GapRecord:
    symbol: str
    month: str
    timestamp: datetime
    missing_count: int
    duration_minutes: int
    classification: str
    evidence_source: str
    qualification_decision: str


def classify_missing_slots(
    *,
    symbol: str,
    month: str,
    missing: set[datetime],
    missing_by_slot: dict[datetime, set[str]],
    member_count: int,
    evidence_source: str,
    policy: dict,
    verified_symbols: set[str],
    documented_global_slots: set[datetime] | None = None,
    confirmed_symbol_months: set[tuple[str, str]] | None = None,
) -> list[GapRecord]:
    """Classify gaps only when public evidence satisfies a frozen rule."""
    if member_count <= 0:
        raise ValueError("member_count must be positive")
    documented_global_slots = documented_global_slots or set()
    confirmed_symbol_months = confirmed_symbol_months or set()
    threshold = max(
        policy["synchronous_outage_minimum_symbols"],
        math.ceil(member_count * policy["synchronous_outage_minimum_fraction"]),
    )
    all_archives_verified = len(verified_symbols) == member_count
    tagged: list[tuple[datetime, str, str, str]] = []
    for timestamp in sorted(missing):
        peers = len(missing_by_slot.get(timestamp, set()))
        if timestamp in documented_global_slots:
            tagged.append((timestamp, "binance_global_event", f"{evidence_source}; documented_global_event", "quarantine_global_window_all_members"))
        elif peers >= threshold and all_archives_verified:
            tagged.append((timestamp, "binance_global_event", f"{evidence_source}; synchronized_missing={peers}/{member_count}; all_archives_verified=true", "quarantine_global_window_all_members"))
        elif (symbol, month) in confirmed_symbol_months and symbol in verified_symbols:
            tagged.append((timestamp, "symbol_specific_confirmed_archive_gap", f"{evidence_source}; confirmed_symbol_month=true", "quarantine_entire_symbol_month_without_replacement"))
        else:
            tagged.append((timestamp, "unresolved", f"{evidence_source}; synchronized_missing={peers}/{member_count}; confirmation=false", "blocked_unresolved"))

    records: list[GapRecord] = []
    group: list[tuple[datetime, str, str, str]] = []
    for item in tagged:
        if group and (item[0] != group[-1][0] + timedelta(minutes=5) or item[1:] != group[-1][1:]):
            records.append(_record(symbol, month, group))
            group = []
        group.append(item)
    if group:
        records.append(_record(symbol, month, group))
    return records


def _record(symbol: str, month: str, group: list[tuple[datetime, str, str, str]]) -> GapRecord:
    first = group[0]
    return GapRecord(symbol, month, first[0], len(group), len(group) * 5, first[1], first[2], first[3])


def gate(records: list[GapRecord], processing_errors: list[str], *, universe_months: int = 1) -> tuple[str, int]:
    if universe_months <= 0:
        return "blocked_empty_universe", 0
    if processing_errors:
        return "blocked_processing_error", sum(record.qualification_decision == "blocked_unresolved" for record in records)
    unresolved = sum(record.qualification_decision == "blocked_unresolved" for record in records)
    if unresolved:
        return "blocked_unresolved", unresolved
    return "pass_with_quarantine", 0


def quarantine_manifest(
    records: Iterable[GapRecord],
    members_by_month: dict[str, list[str]],
    *,
    contract_hash: str,
    registry_hash: str,
) -> dict:
    """Apply global windows to every member and symbol gaps to full months."""
    records = list(records)
    global_windows: dict[tuple[str, datetime, int], GapRecord] = {}
    symbol_months: dict[tuple[str, str], GapRecord] = {}
    unresolved = []
    for record in records:
        if record.classification == "binance_global_event":
            global_windows[(record.month, record.timestamp, record.missing_count)] = record
        elif record.classification == "symbol_specific_confirmed_archive_gap":
            symbol_months[(record.symbol, record.month)] = record
        else:
            unresolved.append(asdict(record))

    scopes = []
    for (month, start, count), record in sorted(global_windows.items()):
        members = sorted(members_by_month.get(month, []))
        if not members:
            raise ValueError(f"global window references empty month: {month}")
        scopes.append({
            "scope": "global_window",
            "month": month,
            "start": start,
            "end_exclusive": start + timedelta(minutes=5 * count),
            "evidence": record.evidence_source,
            "affected_member_count": len(members),
            "total_member_count": len(members),
            "affected_symbols": members,
            "decision": "quarantine_global_window_all_members",
        })
    for (symbol, month), record in sorted(symbol_months.items()):
        if symbol not in members_by_month.get(month, []):
            raise ValueError(f"symbol-month quarantine is not a member: {symbol}:{month}")
        scopes.append({
            "scope": "symbol_month",
            "symbol": symbol,
            "month": month,
            "reason": record.classification,
            "evidence": record.evidence_source,
            "decision": "quarantine_entire_symbol_month_without_replacement",
        })
    return {
        "schema_version": 2,
        "manifest_type": "liquid_universe_quarantine",
        "contract_hash": contract_hash,
        "registry_hash": registry_hash,
        "attribution_records": [asdict(record) for record in sorted(records, key=lambda item: (item.month, item.symbol, item.timestamp))],
        "scopes": scopes,
        "unresolved": unresolved,
    }
