"""Deterministic attribution of missing 5m archive intervals."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

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

def classify_missing_slots(*, symbol: str, month: str, missing: set[datetime],
                           missing_by_slot: dict[datetime, set[str]], member_count: int,
                           evidence_source: str, policy: dict) -> list[GapRecord]:
    """Split consecutive missing slots whenever attribution class changes."""
    threshold = max(policy["synchronous_outage_minimum_symbols"],
                    math.ceil(member_count * policy["synchronous_outage_minimum_fraction"]))
    tagged = []
    for ts in sorted(missing):
        peers = len(missing_by_slot.get(ts, set()))
        if peers >= threshold:
            tagged.append((ts, "binance_global_event", f"{evidence_source}; synchronized_missing={peers}/{member_count}", "quarantine_isolate"))
        else:
            tagged.append((ts, "symbol_specific_archive_gap", f"{evidence_source}; peer_symbols_present={member_count-peers}", "quarantine_isolate_symbol_month_without_replacement"))
    records=[]; group=[]
    for item in tagged:
        if group and (item[0] != group[-1][0] + timedelta(minutes=5) or item[1] != group[-1][1]):
            records.append(_record(symbol, month, group))
            group=[]
        group.append(item)
    if group: records.append(_record(symbol, month, group))
    return records

def _record(symbol, month, group):
    first=group[0]
    return GapRecord(symbol, month, first[0], len(group), len(group)*5,
                     first[1], first[2], first[3])

def gate(records: list[GapRecord], processing_errors: list[str]) -> tuple[str, int]:
    unresolved=sum(r.qualification_decision == "blocked_unresolved" for r in records)
    if processing_errors: return "blocked_processing_error", unresolved
    if unresolved: return "blocked_unresolved", unresolved
    return "pass_with_quarantine", 0
