"""Outcome-free V3 row resolution used before universe membership is built."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from btc_eth_dual_quant.data.kline_row_conflicts import (
    CompleteGroup,
    RawKlineRow,
    ResolutionEntry,
    ResolutionRegistry,
    classify_complete_group,
    normalize_kline_fields,
)
from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_pipeline import build_artifacts as build_v2_artifacts

V3_MANIFEST_TYPES = {
    "source_manifest",
    "conflict_resolution_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "quarantine_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
}


@dataclass(frozen=True)
class CanonicalKlineRow:
    symbol: str
    interval: str
    fields: tuple[str, ...]
    source_authority: str
    source_archive_key: str
    source_archive_sha256: str
    raw_multiplicity: int
    raw_row_hashes: tuple[str, ...]
    raw_line_numbers: tuple[int, ...]
    resolution_id: str | None


@dataclass(frozen=True)
class RowResolutionResult:
    status: str
    canonical: CanonicalKlineRow | None
    raw_row_quarantine: tuple[dict[str, Any], ...]
    research_panel_quarantine: tuple[dict[str, Any], ...]
    duplicate_collapses: int = 0
    monthly_rows_quarantined: int = 0
    daily_corrections_admitted: int = 0
    unresolved_row_conflicts: int = 0
    blocked_symbol_months: int = 0
    synthetic_fills: int = 0
    replacement_members: int = 0


def _blocked(rows: tuple[RawKlineRow, ...], reason: str) -> RowResolutionResult:
    return RowResolutionResult(
        status="blocked_pending_adjudication",
        canonical=None,
        raw_row_quarantine=tuple(_quarantine(row, reason) for row in rows),
        research_panel_quarantine=({"reason": reason, "canonical_key": list(rows[0].canonical_key)},) if rows else (),
        unresolved_row_conflicts=1,
        blocked_symbol_months=1,
    )


def _quarantine(row: RawKlineRow, reason: str) -> dict[str, Any]:
    return {
        "reason": reason,
        "symbol": row.symbol,
        "interval": row.interval,
        "open_time_utc": row.open_time_utc,
        "archive_key": row.archive_key,
        "archive_sha256": row.archive_sha256,
        "line_number": row.line_number,
        "raw_row_hash": row.raw_row_hash,
        "raw_fields": list(row.fields),
    }


def _source_matches(rows: tuple[RawKlineRow, ...], evidence: Any) -> bool:
    if len(rows) != evidence.raw_multiplicity:
        return False
    if any(row.archive_key != evidence.canonical_key or row.archive_sha256 != evidence.sha256 for row in rows):
        return False
    return sorted(row.raw_row_hash for row in rows) == sorted(evidence.raw_row_hashes)


def _canonical(row: RawKlineRow, group: CompleteGroup, resolution_id: str | None) -> CanonicalKlineRow:
    return CanonicalKlineRow(
        symbol=row.symbol,
        interval=row.interval,
        fields=row.fields,
        source_authority=row.authority,
        source_archive_key=row.archive_key,
        source_archive_sha256=row.archive_sha256,
        raw_multiplicity=group.raw_multiplicity,
        raw_row_hashes=group.raw_row_hashes,
        raw_line_numbers=group.line_numbers,
        resolution_id=resolution_id,
    )


def _comparators_match(entry: ResolutionEntry, daily: RawKlineRow) -> bool:
    if len(entry.rest_comparators) != 2:
        return False
    expected = daily.normalized
    return all(
        len(item.normalized_rows) == 1
        and normalize_kline_fields(item.normalized_rows[0]) == expected
        and len(item.payload_sha256) == 64
        for item in entry.rest_comparators
    )


def _only_allowed_fields_differ(monthly: RawKlineRow, daily: RawKlineRow, allowed: tuple[str, ...]) -> bool:
    left = monthly.normalized
    right = daily.normalized
    fields = (
        "open_time", "open", "high", "low", "close", "base_volume", "close_time",
        "quote_volume", "trade_count", "taker_buy_base_volume", "taker_buy_quote_volume", "ignore",
    )
    differing = {field for field, old, new in zip(fields, left, right, strict=True) if old != new}
    return differing == set(allowed)


def resolve_daily_key(
    monthly_rows: Iterable[RawKlineRow],
    daily_rows: Iterable[RawKlineRow],
    registry: ResolutionRegistry,
) -> RowResolutionResult:
    """Resolve one complete canonical key without network or membership logic."""
    monthly = tuple(monthly_rows)
    daily = tuple(daily_rows)
    combined = monthly + daily
    if not combined:
        raise ValueError("at least one source row is required")
    keys = {row.canonical_key for row in combined}
    if len(keys) != 1:
        raise ValueError("source rows contain multiple canonical keys")
    key = combined[0].canonical_key
    entry = registry.get(key)
    monthly_group = classify_complete_group(monthly) if monthly else None
    daily_group = classify_complete_group(daily) if daily else None

    needs_resolution = (
        (monthly_group is not None and (monthly_group.classification != "single" or bool(monthly[0].errors)))
        or (daily_group is not None and daily_group.classification not in {"single"})
    )
    if needs_resolution and entry is None:
        return _blocked(combined, "unregistered row conflict")

    if entry is not None and entry.approved_action == "collapse_byte_identical_duplicate":
        if monthly_group is None or monthly_group.classification != "byte_identical_duplicate":
            return _blocked(combined, "registered exact duplicate classification mismatch")
        if not _source_matches(monthly, entry.monthly_archive):
            return _blocked(combined, "registered monthly source binding mismatch")
        if daily and (daily_group is None or daily_group.classification != "byte_identical_duplicate"):
            return _blocked(combined, "daily duplicate group is not byte-identical")
        if daily and not _source_matches(daily, entry.daily_archive):
            return _blocked(combined, "registered daily source binding mismatch")
        if monthly[0].errors or (daily and daily[0].errors):
            return _blocked(combined, "duplicate canonical candidate is structurally invalid")
        if daily and monthly[0].normalized != daily[0].normalized:
            return _blocked(combined, "monthly and daily duplicate candidates conflict")
        if not _comparators_match(entry, monthly[0]):
            return _blocked(combined, "frozen comparator mismatch")
        return RowResolutionResult(
            status="resolved",
            canonical=_canonical(monthly[0], monthly_group, entry.resolution_id),
            raw_row_quarantine=tuple(
                _quarantine(row, "collapsed byte-identical raw duplicate")
                for row in monthly[1:] + daily[1:]
            ),
            research_panel_quarantine=(),
            duplicate_collapses=1,
        )

    if entry is not None and entry.approved_action == "replace_invalid_monthly_with_daily":
        if monthly_group is None or monthly_group.classification != "single" or not monthly[0].errors:
            return _blocked(combined, "registered monthly invalid-row classification mismatch")
        if daily_group is None or not daily_group.collapsible or daily[0].errors:
            return _blocked(combined, "daily correction candidate is not uniquely valid")
        if not _source_matches(monthly, entry.monthly_archive) or not _source_matches(daily, entry.daily_archive):
            return _blocked(combined, "registered source binding mismatch")
        if not _comparators_match(entry, daily[0]):
            return _blocked(combined, "frozen comparator mismatch")
        if not _only_allowed_fields_differ(monthly[0], daily[0], entry.invalid_fields):
            return _blocked(combined, "daily correction differs outside approved invalid fields")
        return RowResolutionResult(
            status="resolved",
            canonical=_canonical(daily[0], daily_group, entry.resolution_id),
            raw_row_quarantine=tuple(_quarantine(row, "invalid monthly row replaced by approved daily evidence") for row in monthly),
            research_panel_quarantine=(),
            duplicate_collapses=int(daily_group.classification == "byte_identical_duplicate"),
            monthly_rows_quarantined=len(monthly),
            daily_corrections_admitted=1,
        )

    if entry is not None:
        return _blocked(combined, "registered action does not match observed conflict")

    if monthly_group is not None:
        if monthly_group.classification != "single" or monthly[0].errors:
            return _blocked(combined, "unresolved monthly row")
        if daily_group is not None:
            if daily_group.classification != "single" or daily[0].errors:
                return _blocked(combined, "unresolved daily row")
            if monthly[0].normalized != daily[0].normalized:
                return _blocked(combined, "monthly/daily conflict")
        return RowResolutionResult("canonical", _canonical(monthly[0], monthly_group, None), (), ())

    if daily_group is None or daily_group.classification != "single" or daily[0].errors:
        return _blocked(combined, "unresolved daily fill")
    return RowResolutionResult("canonical", _canonical(daily[0], daily_group, None), (), ())


def make_v3_manifest(
    manifest_type: str,
    content: Any,
    *,
    contract: dict[str, Any],
    eligibility_registry_hash: str,
    resolution_registry: ResolutionRegistry,
) -> dict[str, Any]:
    if manifest_type not in V3_MANIFEST_TYPES:
        raise ValueError(f"unknown V3 manifest type: {manifest_type}")
    document = {
        "schema_version": 3,
        "manifest_type": manifest_type,
        "contract_hash": contract["canonical_hash"],
        "eligibility_registry_hash": eligibility_registry_hash,
        "resolution_registry_hash": resolution_registry.canonical_hash,
        "adjudication_evidence_hash": resolution_registry.adjudication_evidence_hash,
        "content": content,
    }
    return {**document, "content_hash": canonical_hash(document)}


def build_artifacts_v3(
    *,
    contract: dict[str, Any],
    eligibility_registry: dict[str, Any],
    resolution_registry: ResolutionRegistry,
    confirmed_gap_registry: dict[str, Any],
    daily: list[Any],
    bars_by_symbol_month: dict[Any, Any],
    source_rows: list[dict[str, Any]],
    resolution_results: Iterable[RowResolutionResult],
    grid_results: dict[Any, Any] | None = None,
    processing_errors: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build V3 machine evidence while preserving the frozen V2 membership logic."""
    if contract.get("universe_id") != "LIQUID-SPOT-USDT-TOP15-V3":
        raise ValueError("V3 artifact builder requires the V3 contract")
    bindings = contract.get("conflict_resolution_policy", {})
    if bindings.get("resolution_registry_hash") != resolution_registry.canonical_hash:
        raise ValueError("contract/resolution registry hash mismatch")
    if bindings.get("adjudication_evidence_hash") != resolution_registry.adjudication_evidence_hash:
        raise ValueError("contract/adjudication evidence hash mismatch")

    outcomes = tuple(resolution_results)
    unresolved = sum(item.unresolved_row_conflicts for item in outcomes)
    base = build_v2_artifacts(
        contract=contract,
        registry=eligibility_registry,
        confirmed_gap_registry=confirmed_gap_registry,
        daily=daily,
        bars_by_symbol_month=bars_by_symbol_month,
        source_rows=source_rows,
        grid_results=grid_results,
        processing_errors=list(processing_errors or []),
    )
    eligibility_hash = eligibility_registry["canonical_hash"]
    resolution_content = {
        "registry_id": resolution_registry.document["registry_id"],
        "registry_hash": resolution_registry.canonical_hash,
        "resolutions": [
            {
                "status": item.status,
                "canonical_key": (
                    item.research_panel_quarantine[0].get("canonical_key")
                    if item.research_panel_quarantine else None
                ),
                "canonical_resolution_id": item.canonical.resolution_id if item.canonical else None,
                "canonical_source_archive_sha256": item.canonical.source_archive_sha256 if item.canonical else None,
                "canonical_raw_multiplicity": item.canonical.raw_multiplicity if item.canonical else None,
                "canonical_raw_row_hashes": list(item.canonical.raw_row_hashes) if item.canonical else [],
                "canonical_raw_line_numbers": list(item.canonical.raw_line_numbers) if item.canonical else [],
                "raw_row_quarantine": list(item.raw_row_quarantine),
                "research_panel_quarantine": list(item.research_panel_quarantine),
            }
            for item in outcomes
            if item.canonical and item.canonical.resolution_id or item.unresolved_row_conflicts
        ],
        "counters": _resolution_counters(outcomes),
    }
    quarantine_content = {
        "gap_quarantine": base["quarantine_manifest"]["content"],
        "raw_row_quarantine": [row for item in outcomes for row in item.raw_row_quarantine],
        "research_panel_quarantine": [row for item in outcomes for row in item.research_panel_quarantine],
    }
    summary_content = dict(base["qualification_summary"]["content"])
    summary_content.update(_resolution_counters(outcomes))
    summary_content["unresolved_row_conflicts"] = unresolved
    if unresolved:
        row_conflict_blockers = sorted({
            "row_conflict:"
            + ":".join(str(value) for value in item.research_panel_quarantine[0]["canonical_key"])
            + ":"
            + str(item.research_panel_quarantine[0]["reason"])
            for item in outcomes
            if item.unresolved_row_conflicts and item.research_panel_quarantine
        })
        summary_content["blockers"] = sorted(set(summary_content.get("blockers", [])) | set(row_conflict_blockers))
    summary_content["status"] = "pass" if summary_content["status"] == "pass" and unresolved == 0 else "blocked"
    summary_content["authorizations"] = contract["authorizations"]

    content_by_name = {
        "source_manifest": base["source_manifest"]["content"],
        "conflict_resolution_manifest": resolution_content,
        "candidate_eligibility_manifest": base["candidate_eligibility_manifest"]["content"],
        "membership_manifest": base["membership_manifest"]["content"],
        "quarantine_manifest": quarantine_content,
        "qualified_panel_manifest": base["qualified_panel_manifest"]["content"],
        "qualification_summary": summary_content,
    }
    return {
        name: make_v3_manifest(
            name,
            content,
            contract=contract,
            eligibility_registry_hash=eligibility_hash,
            resolution_registry=resolution_registry,
        )
        for name, content in content_by_name.items()
    }


def _resolution_counters(outcomes: Iterable[RowResolutionResult]) -> dict[str, int]:
    rows = tuple(outcomes)
    return {
        "duplicate_collapses": sum(item.duplicate_collapses for item in rows),
        "monthly_rows_quarantined": sum(item.monthly_rows_quarantined for item in rows),
        "daily_corrections_admitted": sum(item.daily_corrections_admitted for item in rows),
        "unresolved_row_conflicts": sum(item.unresolved_row_conflicts for item in rows),
        "blocked_symbol_months": sum(item.blocked_symbol_months for item in rows),
        "synthetic_fills": sum(item.synthetic_fills for item in rows),
        "replacement_members": sum(item.replacement_members for item in rows),
    }
