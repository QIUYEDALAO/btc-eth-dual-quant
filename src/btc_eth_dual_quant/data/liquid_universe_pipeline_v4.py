"""V4 lifecycle dispatch layered over the existing V3 row-conflict engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from btc_eth_dual_quant.data.kline_row_conflicts import RawKlineRow, ResolutionRegistry
from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES, make_v4_manifest
from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry
from btc_eth_dual_quant.data.liquid_universe import GridResult, MinuteBar, month_bounds, validate_minute_bar
from btc_eth_dual_quant.data.liquid_universe_pipeline_v3 import resolve_daily_key


@dataclass(frozen=True)
class V4DispatchResult:
    status: str
    canonical: Any | None
    raw_row_quarantine: tuple[dict[str, Any], ...]
    count_as_gap: bool
    close_time_rewritten: bool = False


def validate_lifecycle_symbol_month_grid(
    symbol: str,
    month: str,
    bars: Iterable[MinuteBar],
    *,
    availability_end_exclusive_ms: int,
) -> GridResult:
    """Validate only the physically available part of a lifecycle-ending month."""
    start, month_end = month_bounds(month)
    end = datetime.fromtimestamp(availability_end_exclusive_ms / 1_000, timezone.utc)
    if not start < end <= month_end or availability_end_exclusive_ms % 300_000:
        raise ValueError("lifecycle boundary must be an aligned instant inside the month")
    expected_count = int((end - start).total_seconds() // 300)
    expected = {start.timestamp() * 1_000 + index * 300_000 for index in range(expected_count)}
    seen: set[float] = set()
    errors: list[str] = []
    for bar in bars:
        try:
            validate_minute_bar(bar, expected_symbol=symbol, expected_month=month)
        except ValueError as exc:
            errors.append(str(exc))
        timestamp_ms = bar.open_time.timestamp() * 1_000
        if timestamp_ms >= availability_end_exclusive_ms:
            errors.append(f"unexpected post-lifecycle 5m row: {bar.open_time.isoformat()}")
            continue
        if timestamp_ms in seen:
            errors.append(f"duplicate 5m timestamp: {bar.open_time.isoformat()}")
        seen.add(timestamp_ms)
    missing_ms = sorted(expected - seen)
    missing = tuple(datetime.fromtimestamp(value / 1_000, timezone.utc) for value in missing_ms)
    return GridResult(symbol, month, expected_count, len(seen), missing, tuple(sorted(set(errors))))


def _quarantine(row: RawKlineRow, reason: str, event_id: str | None) -> dict[str, Any]:
    return {
        "reason": reason,
        "event_id": event_id,
        "symbol": row.symbol,
        "interval": row.interval,
        "open_time_utc": row.open_time_utc,
        "archive_key": row.archive_key,
        "archive_sha256": row.archive_sha256,
        "line_number": row.line_number,
        "raw_row_hash": row.raw_row_hash,
        "raw_fields": list(row.fields),
    }


def dispatch_daily_rows(
    monthly_rows: Iterable[RawKlineRow],
    daily_rows: Iterable[RawKlineRow],
    row_registry: ResolutionRegistry,
    lifecycle_registry: LifecycleEventRegistry,
) -> V4DispatchResult:
    monthly = tuple(monthly_rows)
    daily = tuple(daily_rows)
    rows = monthly + daily
    if not rows:
        raise ValueError("at least one source row is required")
    keys = {row.canonical_key for row in rows}
    if len(keys) != 1:
        raise ValueError("source rows contain multiple canonical keys")
    key = rows[0].canonical_key
    claims = tuple(
        claim for row in rows
        if (claim := lifecycle_registry.claim_row(row.symbol, row.interval, key[2], row.raw_row_hash)) is not None
    )
    row_claim = row_registry.get(key)
    if row_claim is not None and claims:
        return V4DispatchResult(
            "blocked_policy_overlap",
            None,
            tuple(_quarantine(row, "row and lifecycle policies overlap", claims[0].event_id) for row in rows),
            True,
        )
    if claims:
        if any(claim.status == "unresolved_blocked" for claim in claims):
            claim = next(claim for claim in claims if claim.status == "unresolved_blocked")
            return V4DispatchResult(
                claim.status,
                None,
                tuple(_quarantine(row, claim.reason, claim.event_id) for row in rows),
                True,
            )
        if len({(claim.event_id, claim.row_classification) for claim in claims}) != 1:
            return V4DispatchResult(
                "blocked_policy_overlap",
                None,
                tuple(_quarantine(row, "conflicting lifecycle claims", claims[0].event_id) for row in rows),
                True,
            )
        claim = claims[0]
        return V4DispatchResult(
            claim.status,
            None,
            tuple(_quarantine(row, claim.reason, claim.event_id) for row in rows),
            False,
        )
    resolved = resolve_daily_key(monthly, daily, row_registry)
    return V4DispatchResult(
        resolved.status,
        resolved.canonical,
        resolved.raw_row_quarantine,
        resolved.unresolved_row_conflicts > 0,
    )


def build_fixture_artifacts_v4(
    contract: dict[str, Any],
    lifecycle_registry: LifecycleEventRegistry,
    *,
    reverse_inputs: bool = False,
) -> dict[str, dict[str, Any]]:
    events = [
        {
            "event_id": event.event_id,
            "symbol": event.symbol,
            "identity_version": event.identity_version,
            "effective_at": event.effective_at.isoformat(),
            "availability_end_exclusive": event.availability_end_exclusive.isoformat(),
            "affected_raw_row_hashes": sorted(event.affected_raw_row_hashes),
            "adjudication_hash": event.adjudication_hash,
        }
        for event in lifecycle_registry.events
    ]
    if reverse_inputs:
        events.reverse()
    events.sort(key=lambda item: item["event_id"])
    authorizations = {
        "u03f": False,
        "u04": False,
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
    contents: dict[str, Any] = {
        "source_manifest": {"fixture_only": True, "sources": []},
        "row_conflict_resolution_manifest": {"fixture_only": True, "resolutions": []},
        "lifecycle_policy_manifest": {"policy_id": contract["lifecycle_policy"]["policy_id"]},
        "lifecycle_resolution_registry": events,
        "symbol_availability_manifest": [
            {"symbol": item["symbol"], "end_exclusive": item["availability_end_exclusive"]}
            for item in events
        ],
        "active_universe_manifest": {"membership_replacement": False, "states": ["active_complete", "lifecycle_terminated"]},
        "complete_day_mask": {"partial_days_window_eligible": False},
        "expected_grid_manifest": {"availability_mask_precedes_grid": True},
        "raw_row_quarantine_manifest": [
            {"event_id": item["event_id"], "raw_row_hashes": item["affected_raw_row_hashes"]}
            for item in events
        ],
        "lifecycle_event_quarantine_manifest": [],
        "candidate_eligibility_manifest": {"fixture_only": True},
        "membership_manifest": {"month_start_membership_immutable": True},
        "qualified_panel_manifest": {"fixture_only": True, "real_rows": 0},
        "qualification_summary": {
            "status": "implementation_fixture_pass",
            "real_public_requalification_run": False,
            "authorizations": authorizations,
        },
        "V3_V4_diff": {
            "v3_contract_hash": contract["bindings"]["v3_contract_hash"],
            "v4_contract_hash": contract["canonical_hash"],
            "lifecycle_layer_added": True,
            "v3_mutated": False,
        },
    }
    return {
        name: make_v4_manifest(
            name,
            contents[name],
            contract_hash=contract["canonical_hash"],
            lifecycle_registry_hash=lifecycle_registry.canonical_hash,
        )
        for name in sorted(V4_MANIFEST_TYPES)
    }
