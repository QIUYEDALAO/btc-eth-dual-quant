"""Metadata-only calendar budget gate for M1D feasibility research."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping

from btc_eth_dual_quant.audit.feasibility import CandidateIdentity


FIXED_OOS_FRACTION = Decimal("0.30")
FIXED_REQUIRED_OOS_DAYS = 540


@dataclass(frozen=True)
class SampleBudgetPolicy:
    oos_fraction: Decimal = FIXED_OOS_FRACTION
    required_oos_days: int = FIXED_REQUIRED_OOS_DAYS

    def __post_init__(self) -> None:
        if self.oos_fraction != FIXED_OOS_FRACTION:
            raise ValueError("OOS fraction is frozen at 30%")
        if self.required_oos_days != FIXED_REQUIRED_OOS_DAYS:
            raise ValueError("OOS calendar minimum is frozen at 540 days")


@dataclass(frozen=True)
class ResearchCalendarMetadata:
    research_start: date
    latest_complete_day: date
    t1_schema_version: int
    t2_schema_version: int
    t2_research_blockers: int


@dataclass(frozen=True)
class CalendarBudgetResult:
    research_start: date
    latest_complete_day: date
    full_days: int
    is_days: int
    oos_days: int
    required_oos_days: int
    shortage_days: int
    required_full_days: int
    earliest_eligible_end_day: date
    calendar_gate_passed: bool
    status: str
    canonical_sha256: str


def _parse_end_day(value: str) -> date:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("research end must include a timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("research end must use UTC")
    if (parsed.hour, parsed.minute, parsed.second, parsed.microsecond) != (23, 59, 59, 999000):
        raise ValueError("research end must be the final millisecond of a complete UTC day")
    if (parsed + timedelta(milliseconds=1)).month == parsed.month:
        raise ValueError("research end must be a complete UTC month")
    return parsed.date()


def extract_research_calendar_metadata(
    t1_manifest: Mapping[str, Any],
    t2_manifest: Mapping[str, Any],
) -> ResearchCalendarMetadata:
    allowed_t1 = {
        "schema_version": int(t1_manifest.get("schema_version", 0)),
        "research_start": str(t1_manifest.get("research_start", "")),
        "requested_end": str(t1_manifest.get("requested_end", "")),
        "api_key_used": t1_manifest.get("api_key_used"),
        "private_data_used": t1_manifest.get("private_data_used"),
    }
    allowed_t2 = {
        "schema_version": int(t2_manifest.get("schema_version", 0)),
        "research_start": str(t2_manifest.get("research_start", "")),
        "research_end": str(t2_manifest.get("research_end", "")),
        "api_key_used": t2_manifest.get("api_key_used"),
        "private_data_used": t2_manifest.get("private_data_used"),
        "research_blockers": t2_manifest.get("research_blockers"),
    }
    if allowed_t1["schema_version"] != 1 or allowed_t2["schema_version"] != 1:
        raise ValueError("T1/T2 manifest schema version must be 1")
    if allowed_t1["api_key_used"] is not False or allowed_t2["api_key_used"] is not False:
        raise ValueError("sample-budget precheck accepts public metadata only")
    if allowed_t1["private_data_used"] is not False or allowed_t2["private_data_used"] is not False:
        raise ValueError("sample-budget precheck rejects private-data metadata")
    if allowed_t1["research_start"] != allowed_t2["research_start"]:
        raise ValueError("T1 and T2 research starts differ")
    if allowed_t1["requested_end"] != allowed_t2["research_end"]:
        raise ValueError("T1 and T2 latest complete timestamps differ")
    blockers = allowed_t2["research_blockers"]
    if not isinstance(blockers, list):
        raise ValueError("T2 research_blockers must be a list")
    try:
        start = date.fromisoformat(allowed_t1["research_start"])
        end = _parse_end_day(allowed_t1["requested_end"])
    except ValueError as exc:
        raise ValueError(f"invalid T1/T2 research calendar metadata: {exc}") from exc
    if end < start:
        raise ValueError("research end precedes research start")
    if start.day != 1:
        raise ValueError("research start must be the first day of a UTC month")
    return ResearchCalendarMetadata(start, end, 1, 1, len(blockers))


def evaluate_calendar_budget(
    metadata: ResearchCalendarMetadata,
    candidate: CandidateIdentity,
) -> CalendarBudgetResult:
    policy = SampleBudgetPolicy()
    if candidate.oos_opened:
        raise ValueError("sample-budget precheck requires sealed OOS")
    if candidate.status != "declared_unopened":
        raise ValueError("sample-budget precheck requires declared_unopened status")
    if metadata.t2_research_blockers:
        raise ValueError("T2 metadata contains research blockers")
    full_days = (metadata.latest_complete_day - metadata.research_start).days + 1
    oos_days = math.ceil(full_days * float(policy.oos_fraction))
    is_days = full_days - oos_days
    required_full_days = math.ceil(policy.required_oos_days / float(policy.oos_fraction))
    earliest_end = metadata.research_start + timedelta(days=required_full_days - 1)
    passed = oos_days >= policy.required_oos_days
    payload = {
        "candidate_id": candidate.candidate_id,
        "candidate_sha256": candidate.sha256,
        "research_start": metadata.research_start.isoformat(),
        "latest_complete_day": metadata.latest_complete_day.isoformat(),
        "full_days": full_days,
        "is_days": is_days,
        "oos_days": oos_days,
        "required_oos_days": policy.required_oos_days,
        "required_full_days": required_full_days,
        "earliest_eligible_end_day": earliest_end.isoformat(),
        "calendar_gate_passed": passed,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return CalendarBudgetResult(
        research_start=metadata.research_start,
        latest_complete_day=metadata.latest_complete_day,
        full_days=full_days,
        is_days=is_days,
        oos_days=oos_days,
        required_oos_days=policy.required_oos_days,
        shortage_days=max(0, policy.required_oos_days - oos_days),
        required_full_days=required_full_days,
        earliest_eligible_end_day=earliest_end,
        calendar_gate_passed=passed,
        status="calendar_pass" if passed else "blocked_insufficient_oos_calendar",
        canonical_sha256=hashlib.sha256(encoded).hexdigest(),
    )
