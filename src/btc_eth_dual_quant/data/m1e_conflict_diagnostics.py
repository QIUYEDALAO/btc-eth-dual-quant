"""Evidence-only classification for M1E public archive conflicts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

from .m1e_qualification import COMPARE_FIELDS
from .minute_archive import next_month


PRICE_FIELDS = ("open", "high", "low", "close")
FLOW_FIELDS = (
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)


@dataclass(frozen=True)
class ConflictDiagnostic:
    symbol: str
    month: str
    timeframe: str
    open_time: int
    differing_fields: tuple[str, ...]
    rest_matches_derived: bool
    rest_matches_official: bool
    classification: str
    resolved_for_contract: bool
    derived_sha256: str
    official_sha256: str
    rest_sha256: str


def _decimal_equal(left: Any, right: Any) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, ValueError):
        return str(left) == str(right)


def row_sha256(row: Mapping[str, Any] | None) -> str:
    if row is None:
        return ""
    payload = json.dumps(dict(row), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def differing_fields(left: Mapping[str, Any], right: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(field for field in COMPARE_FIELDS if not _decimal_equal(left[field], right[field]))


def rows_match(left: Mapping[str, Any] | None, right: Mapping[str, Any] | None) -> bool:
    return left is not None and right is not None and not differing_fields(left, right)


def classify_aggregate_conflict(
    *, symbol: str, month: str, timeframe: str, derived: Mapping[str, Any],
    official: Mapping[str, Any], rest: Mapping[str, Any] | None,
) -> ConflictDiagnostic:
    fields = differing_fields(derived, official)
    price_difference = any(field in PRICE_FIELDS for field in fields)
    rest_derived = rows_match(rest, derived)
    rest_official = rows_match(rest, official)
    if price_difference:
        classification = "unresolved_price_or_timestamp_conflict"
    elif fields and set(fields) <= set(FLOW_FIELDS) and rest_official and not rest_derived:
        classification = "higher_timeframe_flow_revision_confirmed_by_rest"
    elif fields and set(fields) <= set(FLOW_FIELDS) and rest_derived and not rest_official:
        classification = "child_aggregate_flow_confirmed_by_rest"
    elif fields and set(fields) <= set(FLOW_FIELDS):
        classification = "unresolved_flow_revision"
    else:
        classification = "unresolved_source_conflict"
    return ConflictDiagnostic(
        symbol=symbol, month=month, timeframe=timeframe, open_time=int(official["open_time"]),
        differing_fields=fields, rest_matches_derived=rest_derived, rest_matches_official=rest_official,
        classification=classification, resolved_for_contract=False,
        derived_sha256=row_sha256(derived), official_sha256=row_sha256(official), rest_sha256=row_sha256(rest),
    )


def classify_monthly_daily_conflict(
    *, symbol: str, month: str, timeframe: str, monthly: Mapping[str, Any],
    daily: Mapping[str, Any], rest: Mapping[str, Any] | None,
) -> ConflictDiagnostic:
    fields = differing_fields(monthly, daily)
    rest_monthly = rows_match(rest, monthly)
    rest_daily = rows_match(rest, daily)
    if rest_monthly and not rest_daily:
        classification = "monthly_daily_conflict_rest_supports_monthly"
    elif rest_daily and not rest_monthly:
        classification = "monthly_daily_conflict_rest_supports_daily"
    else:
        classification = "monthly_daily_conflict_rest_inconclusive"
    return ConflictDiagnostic(
        symbol=symbol, month=month, timeframe=timeframe, open_time=int(monthly["open_time"]),
        differing_fields=fields, rest_matches_derived=rest_daily, rest_matches_official=rest_monthly,
        classification=classification, resolved_for_contract=False,
        derived_sha256=row_sha256(daily), official_sha256=row_sha256(monthly), rest_sha256=row_sha256(rest),
    )


def first_six_month_clean_suffix(month_states: Sequence[tuple[str, str]]) -> str | None:
    run: list[str] = []
    for month, state in sorted(month_states):
        if state == "blocked":
            run = []
            continue
        if run and next_month(run[-1]) != month:
            run = []
        run.append(month)
    return f"{next_month(run[5])}-01" if len(run) >= 6 else None


def calendar_budget(start: str, end_exclusive: str) -> tuple[int, int]:
    start_day = date.fromisoformat(start)
    end_day = date.fromisoformat(end_exclusive)
    full_days = (end_day - start_day).days
    is_days = int(full_days * 0.70)
    return full_days, full_days - is_days


def canonical_diagnostics_sha256(items: Iterable[ConflictDiagnostic]) -> str:
    payload = [asdict(item) for item in sorted(items, key=lambda item: (item.month, item.symbol, item.timeframe, item.open_time))]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
