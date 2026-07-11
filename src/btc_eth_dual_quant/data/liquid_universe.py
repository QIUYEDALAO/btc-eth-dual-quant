"""Point-in-time liquid-universe qualification without strategy outcomes."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib, json, statistics

@dataclass(frozen=True)
class DailyEvidence:
    symbol: str; day: date; quote_volume: Decimal; source: str; source_hash: str

@dataclass(frozen=True)
class MinuteBar:
    symbol: str; open_time: datetime; open: Decimal; high: Decimal; low: Decimal; close: Decimal; volume: Decimal

@dataclass(frozen=True)
class MembershipRow:
    effective_month: str; symbol: str; rank: int; median_daily_quote_volume_90d: str
    history_days: int; eligibility_status: str; exclusion_reason: str | None; source_hash: str

def merge_daily(monthly: list[DailyEvidence], daily: list[DailyEvidence]) -> list[DailyEvidence]:
    result = {(x.symbol, x.day): x for x in monthly}
    for row in daily: result.setdefault((row.symbol, row.day), row)
    return sorted(result.values(), key=lambda x: (x.symbol, x.day))

def excluded(symbol: str, contract: dict) -> str | None:
    base = symbol.removesuffix(contract["quote_asset"])
    if base in contract["exclusions"]["exact_base_assets"]: return "excluded_by_contract"
    if any(base.endswith(s) for s in contract["exclusions"]["leveraged_suffixes"]): return "excluded_by_contract"
    return None

def build_month(effective: date, rows: list[DailyEvidence], contract: dict) -> list[MembershipRow]:
    if effective.day != 1: raise ValueError("effective month must start on day one")
    m = contract["membership"]; end = effective; start = end - timedelta(days=m["ranking_window_complete_days"])
    by_symbol: dict[str, list[DailyEvidence]] = {}
    for row in rows:
        if row.day >= effective: continue
        by_symbol.setdefault(row.symbol, []).append(row)
    ranked = []
    for symbol, evidence in by_symbol.items():
        if excluded(symbol, contract): continue
        unique = {x.day: x for x in evidence}
        history_days = len(unique)
        window = [unique.get(start + timedelta(days=i)) for i in range(m["ranking_window_complete_days"])]
        if history_days < m["minimum_complete_history_days"] or any(x is None for x in window): continue
        median = statistics.median(x.quote_volume for x in window if x is not None)
        source_hash = hashlib.sha256("".join(sorted(x.source_hash for x in evidence)).encode()).hexdigest()
        ranked.append((median, symbol, history_days, source_hash))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return [MembershipRow(effective.isoformat(), s, i + 1, str(v), h, "qualified", None, sh)
            for i, (v, s, h, sh) in enumerate(ranked[:m["target_size"]])]

def aggregate_one_hour(bars: list[MinuteBar]) -> MinuteBar:
    if len(bars) != 12: raise ValueError("one hour requires exactly twelve 5m bars")
    ordered = sorted(bars, key=lambda x: x.open_time); start = ordered[0].open_time
    if start.minute != 0 or start.second or start.tzinfo is None: raise ValueError("invalid UTC hour boundary")
    for i, bar in enumerate(ordered):
        if bar.open_time != start + timedelta(minutes=5 * i): raise ValueError("incomplete 5m bucket")
    return MinuteBar(ordered[0].symbol, start, ordered[0].open, max(x.high for x in ordered),
                     min(x.low for x in ordered), ordered[-1].close, sum((x.volume for x in ordered), Decimal(0)))

def membership_hash(rows: list[MembershipRow]) -> str:
    payload = json.dumps([asdict(x) for x in rows], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
