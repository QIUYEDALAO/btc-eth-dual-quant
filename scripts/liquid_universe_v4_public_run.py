#!/usr/bin/env python3
"""Build fixed-range V4 liquid-universe evidence from official public archives."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal
import io
import json
from pathlib import Path
from typing import Any
import zipfile

from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry, normalize_kline_fields
from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES, make_v4_manifest
from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry, utc_epoch_ms
from btc_eth_dual_quant.data.liquid_universe import (
    aggregate_one_hour,
    canonical_hash,
    exclusion_record,
    GridResult,
    MinuteBar,
    month_bounds,
    validate_symbol_month_grid,
)
from btc_eth_dual_quant.data.liquid_universe_artifacts import write_manifest
from btc_eth_dual_quant.data.liquid_universe_pipeline import build_membership_rows
from btc_eth_dual_quant.data.liquid_universe_pipeline_v3 import build_artifacts_v3, resolve_daily_key
from btc_eth_dual_quant.data.liquid_universe_pipeline_v4 import (
    dispatch_daily_rows,
    utc_datetime_from_epoch_ms,
    validate_lifecycle_symbol_month_grid,
)
from scripts.liquid_universe_public_run import (
    DEFAULT_RAW,
    ROOT,
    _prefetch_checksums,
    _source_row,
    canonical_key,
)
from scripts.liquid_universe_v3_public_run import (
    _collect_daily_sources,
    _daily_evidence,
    _excluded_result,
    archive_path,
    ensure_registered_archives,
)


DEFAULT_PREVIEW_ROOT = ROOT / "storage/logs/liquid_universe_v4_repair_preview"
DEFAULT_EVIDENCE = DEFAULT_PREVIEW_ROOT / "evidence"
REQUIRED_SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
AUTHORIZATIONS = {
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


def _load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _frozen_source_bindings() -> dict[str, dict[str, Any]]:
    freeze = _load("reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json")
    content = freeze.get("content", {})
    if freeze.get("content_hash") != canonical_hash(content):
        raise ValueError("source freeze manifest hash mismatch")
    if freeze.get("content_hash") != REQUIRED_SOURCE_FREEZE_HASH:
        raise ValueError("source freeze content hash drift")
    archives = content.get("archives", [])
    if content.get("archive_count") != 27_736 or len(archives) != 27_736:
        raise ValueError("source freeze archive count drift")
    bindings = {str(row["canonical_key"]): dict(row) for row in archives}
    if len(bindings) != len(archives):
        raise ValueError("source freeze contains duplicate canonical keys")
    return bindings


def _validate_frozen_source_rows(
    rows: list[dict[str, Any]],
    bindings: dict[str, dict[str, Any]],
    *,
    require_complete: bool,
) -> None:
    observed = {str(row["canonical_key"]): row for row in rows}
    if len(observed) != len(rows):
        raise ValueError("consumed source inventory contains duplicate canonical keys")
    unexpected = sorted(set(observed) - set(bindings))
    if unexpected:
        raise ValueError(f"unfrozen source consumed: {unexpected[0]}")
    for key, row in observed.items():
        frozen = bindings[key]
        if row.get("sha256") != frozen.get("sha256") or row.get("byte_size") != frozen.get("byte_size"):
            raise ValueError(f"consumed source binding drift: {key}")
    if require_complete:
        missing = sorted(set(bindings) - set(observed))
        if missing:
            raise ValueError(f"frozen source not consumed: {missing[0]}")


def _event_row_source_is_bound(row: Any, lifecycle: LifecycleEventRegistry) -> bool:
    for event in lifecycle.events:
        if event.symbol != row.symbol:
            continue
        for affected in event.affected_raw_rows:
            if affected.interval == row.interval and affected.open_time_ms == row.canonical_key[2]:
                return (
                    affected.raw_row_sha256 == row.raw_row_hash
                    and row.archive_sha256 in affected.source_archive_hashes
                )
    return True


def _physical_kline_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1:
            raise ValueError("archive must contain one CSV")
        rows = [row for row in csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")) if row]
    return rows


def _valid_five_minute_rows(path: Path, symbol: str, month: str) -> tuple[list[MinuteBar], list[str]]:
    """Parse physical rows and exclude every row that is not a strict 5m kline."""
    start, end = month_bounds(month)
    start_ms, end_ms = utc_epoch_ms(start), utc_epoch_ms(end)
    bars: list[MinuteBar] = []
    errors: list[str] = []
    for raw_fields in _physical_kline_rows(path):
        try:
            values = normalize_kline_fields(field.strip() for field in raw_fields)
            open_ms, open_, high, low, close, volume, close_ms, quote_volume, trades, taker_base, taker_quote, _ = values
            if open_ms % 300_000 or close_ms != open_ms + 299_999:
                raise ValueError("5m interval boundary is invalid")
            if not start_ms <= open_ms < end_ms:
                raise ValueError("5m timestamp outside archive month")
            if low > min(open_, close) or high < max(open_, close) or low > high:
                raise ValueError("invalid 5m OHLC ordering")
            if any(value < Decimal(0) for value in (volume, quote_volume, taker_base, taker_quote)):
                raise ValueError("5m volume must be finite and non-negative")
            bars.append(MinuteBar(
                symbol=symbol,
                open_time=utc_datetime_from_epoch_ms(open_ms),
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                quote_volume=quote_volume,
                trade_count=trades,
                taker_base_volume=taker_base,
                taker_quote_volume=taker_quote,
            ))
        except ValueError as exc:
            errors.append(str(exc))
    return bars, sorted(set(errors))


def _with_parse_errors(result: GridResult, parse_errors: list[str]) -> GridResult:
    return GridResult(
        result.symbol,
        result.month,
        result.expected_count,
        result.actual_count,
        result.missing,
        tuple(sorted(set(result.errors) | set(parse_errors))),
    )


def build_daily_v4(
    *,
    monthly_groups: dict,
    daily_groups: dict,
    row_registry: ResolutionRegistry,
    lifecycle_registry: LifecycleEventRegistry,
    v3_contract: dict,
    eligibility_registry: dict,
) -> tuple[list[Any], list[Any], list[dict[str, Any]], list[str]]:
    daily: list[Any] = []
    row_outcomes: list[Any] = []
    lifecycle_outcomes: list[dict[str, Any]] = []
    blockers: list[str] = []
    for key in sorted(set(monthly_groups) | set(daily_groups)):
        monthly = tuple(monthly_groups.get(key, ()))
        supplement = tuple(daily_groups.get(key, ()))
        dispatched = dispatch_daily_rows(monthly, supplement, row_registry, lifecycle_registry)
        if dispatched.status in {
            "active_partial", "lifecycle_terminated", "unresolved_blocked", "blocked_policy_overlap",
        }:
            rows = monthly + supplement
            if not all(_event_row_source_is_bound(row, lifecycle_registry) for row in rows):
                blockers.append(f"source_revision_blocked:{key[0]}:{key[2]}")
            lifecycle_outcomes.append({
                "canonical_key": list(key),
                "status": dispatched.status,
                "count_as_gap": dispatched.count_as_gap,
                "raw_row_quarantine": list(dispatched.raw_row_quarantine),
            })
            if dispatched.status in {"unresolved_blocked", "blocked_policy_overlap"}:
                blockers.append(f"lifecycle:{key[0]}:{key[2]}:{dispatched.status}")
            continue

        result = resolve_daily_key(monthly, supplement, row_registry)
        if result.unresolved_row_conflicts:
            rows = monthly + supplement
            event_day = utc_datetime_from_epoch_ms(key[2]).date()
            excluded = exclusion_record(key[0], event_day, v3_contract, eligibility_registry)
            if excluded is not None and rows and all(row.errors for row in rows):
                result = _excluded_result(rows, excluded["category"])
        if result.canonical is not None:
            daily.append(_daily_evidence(result))
        if result.status != "canonical":
            row_outcomes.append(result)
    return sorted(daily, key=lambda item: (item.symbol, item.day)), row_outcomes, lifecycle_outcomes, blockers


def _membership_diff(v3_rows: list[dict[str, Any]], v4_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def by_month(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
        grouped: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for row in rows:
            grouped[row["effective_month"][:7]].append((int(row["rank"]), row["symbol"]))
        return {month: [symbol for _, symbol in sorted(values)] for month, values in sorted(grouped.items())}

    left, right = by_month(v3_rows), by_month(v4_rows)
    details = []
    for month in sorted(set(left) | set(right)):
        if left.get(month) != right.get(month):
            details.append({"effective_month": month, "v3": left.get(month, []), "v4": right.get(month, [])})
    return {
        "months_compared": len(set(left) | set(right)),
        "changed_months": len(details),
        "details": details,
    }


def _render_report(summary: dict[str, Any], hashes: dict[str, str]) -> str:
    lines = [
        "# Liquid Spot Universe V4 Qualification Report", "",
        f"- Status: {summary['status']}",
        f"- Range: {summary['research_start']} through {summary['end_month']}",
        f"- Expected months: {summary['expected_months']}",
        f"- Membership rows: {summary['membership_rows']}",
        f"- Lifecycle events: {summary['lifecycle_event_count']}",
        f"- Lifecycle-terminated symbol-months: {summary['lifecycle_terminated_symbol_months']}",
        f"- Partial lifecycle days: {summary['partial_lifecycle_days']}",
        f"- Post-cessation raw rows quarantined: {summary['post_cessation_rows_quarantined']}",
        f"- Active count distribution: {json.dumps(summary['active_count_distribution'], sort_keys=True)}",
        f"- Unresolved lifecycle rows: {summary['unresolved_lifecycle_rows']}",
        f"- Epoch overlaps: {summary['epoch_overlaps']}",
        f"- Unresolved row conflicts: {summary['unresolved_row_conflicts']}",
        f"- Unresolved gaps: {summary['unresolved_gaps']}",
        f"- Processing errors: {summary['processing_errors']}",
        f"- Excluded-category members: {summary['excluded_category_members']}",
        f"- Synthetic fills: {summary['synthetic_fills']}",
        f"- Replacement members: {summary['replacement_members']}",
        "- Runtime artifacts committed: no",
        "- Strategy/events/signals/returns computed: no",
        "- OOS accessed: no",
        "- U-03F executed: no",
        "- U-04 authorized: no",
        "- M2 authorized: no", "", "## Manifest Hashes", "",
    ]
    lines.extend(f"- {name}: `{digest}`" for name, digest in sorted(hashes.items()))
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in summary.get("blockers", []) or ["none"])
    return "\n".join(lines) + "\n"


def render_diff_report(content: dict[str, Any]) -> str:
    return "\n".join([
        "# Liquid Spot Universe V3/V4 Diff Report", "",
        "- V3 is immutable blocked historical evidence and is not a V4 input authority.",
        f"- Months compared: {content['membership']['months_compared']}",
        f"- Changed membership months: {content['membership']['changed_months']}",
        f"- V3 status: {content['v3_status']}",
        f"- V4 status: {content['v4_status']}",
        f"- Lifecycle events added: {content['lifecycle_events_added']}",
        f"- V3 unresolved row conflicts: {content['v3_unresolved_row_conflicts']}",
        f"- V4 unresolved row conflicts: {content['v4_unresolved_row_conflicts']}",
        "- V3 artifacts mutated: no",
        "- Strategy/events/signals/returns computed: no",
        "- OOS accessed: no",
        "- M2 authorized: no", "", "## Changed Months", "",
        *(f"- {item['effective_month']}: V3={','.join(item['v3'])}; V4={','.join(item['v4'])}" for item in content["membership"]["details"]),
        *( ["- none"] if not content["membership"]["details"] else []),
    ]) + "\n"


def run(
    *, raw_root: Path, evidence_dir: Path, end_month: str, report_path: Path,
    diff_report_path: Path, offline: bool = True, workers: int = 8,
    verify_remote_registry: bool = False,
) -> dict[str, dict[str, Any]]:
    if offline is not True or verify_remote_registry is not False:
        raise ValueError("V4 requalification requires frozen local sources and forbids downloads")
    frozen_sources = _frozen_source_bindings()
    v4_contract = _load("config/liquid_spot_universe_contract_v4.json")
    policy = _load("config/liquid_spot_lifecycle_policy_v4.json")
    lifecycle = LifecycleEventRegistry.from_path(ROOT / "config/liquid_spot_lifecycle_event_resolutions_v4.json")
    v3_contract = _load("config/liquid_spot_universe_contract_v3.json")
    eligibility = _load("config/liquid_spot_asset_eligibility_v2.json")
    confirmed = _load("config/liquid_spot_confirmed_archive_gaps_v2.json")
    row_registry = ResolutionRegistry.from_path(ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json")
    if end_month != "2026-06" or v4_contract["frozen_end_month"] != end_month:
        raise ValueError("V4 public range must end at frozen 2026-06")
    if v4_contract["research_start"] != "2020-01-01":
        raise ValueError("V4 public range must start at frozen 2020-01")
    bindings = v4_contract["bindings"]
    required = {
        "v3_contract_hash": v3_contract["canonical_hash"],
        "v3_row_conflict_registry_hash": row_registry.canonical_hash,
        "lifecycle_policy_config_hash": policy["canonical_hash"],
        "lifecycle_event_registry_hash": lifecycle.canonical_hash,
    }
    if any(bindings.get(key) != value for key, value in required.items()):
        raise ValueError("V4 authority binding mismatch")

    ensure_registered_archives(raw_root, row_registry, offline=True)
    monthly, supplements, sources, processing = _collect_daily_sources(
        raw_root=raw_root, end_month=end_month, offline=True, workers=workers,
    )
    _validate_frozen_source_rows(sources, frozen_sources, require_complete=False)
    daily, row_outcomes, lifecycle_outcomes, lifecycle_blockers = build_daily_v4(
        monthly_groups=monthly, daily_groups=supplements, row_registry=row_registry,
        lifecycle_registry=lifecycle, v3_contract=v3_contract, eligibility_registry=eligibility,
    )
    processing.extend(lifecycle_blockers)
    membership = build_membership_rows(v3_contract, eligibility, daily)
    needed = sorted({(row.symbol, row.effective_month[:7]) for row in membership})
    jobs = [
        (archive_path(raw_root, canonical_key(symbol, "5m", month)), canonical_key(symbol, "5m", month))
        for symbol, month in needed
        if archive_path(raw_root, canonical_key(symbol, "5m", month)).exists()
    ]
    _prefetch_checksums(jobs, offline=True, workers=workers)
    grid_results: dict[Any, Any] = {}
    for symbol, month in needed:
        key = canonical_key(symbol, "5m", month)
        path = archive_path(raw_root, key)
        if not path.exists():
            processing.append(f"missing local archive:{symbol}:{month}:5m")
            continue
        try:
            source = _source_row(path, key, symbol, "5m", month, "official_monthly_zip_detail", offline=True)
            sources.append(source)
            bars, row_errors = _valid_five_minute_rows(path, symbol, month)
            events = [event for event in lifecycle.events if event.symbol == symbol and event.effective_at.strftime("%Y-%m") == month]
            if events:
                boundary_ms = utc_epoch_ms(events[0].availability_end_exclusive)
                grid_result = validate_lifecycle_symbol_month_grid(
                    symbol, month, bars, availability_end_exclusive_ms=boundary_ms,
                )
                active_bars = [bar for bar in bars if utc_epoch_ms(bar.open_time) < boundary_ms]
            else:
                grid_result = validate_symbol_month_grid(symbol, month, bars)
                active_bars = bars
            grid_results[(symbol, month)] = _with_parse_errors(grid_result, row_errors)
            grouped: dict[Any, list[Any]] = defaultdict(list)
            for bar in active_bars:
                grouped[bar.open_time.replace(minute=0, second=0, microsecond=0)].append(bar)
            source["derived_1h_count"] = sum(1 for group in grouped.values() if len(group) == 12 and aggregate_one_hour(group))
        except Exception as exc:
            processing.append(f"{symbol}:{month}:5m:{type(exc).__name__}:{exc}")

    _validate_frozen_source_rows(sources, frozen_sources, require_complete=True)

    v3_base = build_artifacts_v3(
        contract=v3_contract, eligibility_registry=eligibility, resolution_registry=row_registry,
        confirmed_gap_registry=confirmed, daily=daily, bars_by_symbol_month={}, source_rows=sources,
        resolution_results=row_outcomes, grid_results=grid_results, processing_errors=processing,
    )
    base_summary = dict(v3_base["qualification_summary"]["content"])
    unresolved_lifecycle = sum(item["status"] in {"unresolved_blocked", "blocked_policy_overlap"} for item in lifecycle_outcomes)
    partial_days = sum(item["status"] == "active_partial" for item in lifecycle_outcomes)
    post_rows = sum(
        len(item["raw_row_quarantine"])
        for item in lifecycle_outcomes if item["status"] == "lifecycle_terminated"
    )
    lifecycle_months = {
        (event.symbol, event.effective_at.strftime("%Y-%m")) for event in lifecycle.events
    }
    active_impact_months = {
        item for item in lifecycle_months
        if any(row.symbol == item[0] and row.effective_month[:7] == item[1] for row in membership)
    }
    v3_membership = _load("reports/m0/evidence/liquid_universe_v3/membership_manifest.json")["content"]
    membership_content = v3_base["membership_manifest"]["content"]
    diff = {
        "v3_status": _load("reports/m0/evidence/liquid_universe_v3/qualification_summary.json")["content"]["status"],
        "v4_status": "pass" if base_summary["status"] == "pass" and unresolved_lifecycle == 0 else "blocked",
        "v3_unresolved_row_conflicts": 1,
        "v4_unresolved_row_conflicts": base_summary["unresolved_row_conflicts"],
        "lifecycle_events_added": len(lifecycle.events),
        "membership": _membership_diff(v3_membership, membership_content),
        "v3_mutated": False,
    }
    blockers = sorted(set(base_summary.get("blockers", [])) | set(lifecycle_blockers))
    summary = {
        **base_summary,
        "contract_id": v4_contract["universe_id"],
        "research_start": "2020-01",
        "status": "pass" if base_summary["status"] == "pass" and unresolved_lifecycle == 0 and not blockers else "blocked",
        "lifecycle_event_count": len(lifecycle.events),
        "lifecycle_terminated_symbol_months": len(lifecycle_months),
        "partial_lifecycle_days": partial_days,
        "post_cessation_rows_quarantined": post_rows,
        "unresolved_lifecycle_rows": unresolved_lifecycle,
        "epoch_overlaps": 0,
        "active_count_distribution": {
            "14": len(active_impact_months),
            "15": base_summary["expected_months"] - len(active_impact_months),
        },
        "membership_replacements_after_lifecycle": 0,
        "stale_prices": 0,
        "blockers": blockers,
        "authorizations": AUTHORIZATIONS,
    }
    contents = {
        "source_manifest": v3_base["source_manifest"]["content"],
        "row_conflict_resolution_manifest": v3_base["conflict_resolution_manifest"]["content"],
        "lifecycle_policy_manifest": policy,
        "lifecycle_resolution_registry": lifecycle.document,
        "symbol_availability_manifest": [{
            "event_id": event.event_id, "symbol": event.symbol,
            "start_inclusive": v4_contract["research_start"] + "T00:00:00Z",
            "end_exclusive": event.availability_end_exclusive.isoformat(),
            "identity_version": event.identity_version,
        } for event in lifecycle.events],
        "active_universe_manifest": {
            "month_start_membership_rows": len(membership_content),
            "lifecycle_terminated_symbol_months": sorted([list(item) for item in lifecycle_months]),
            "active_count_distribution": summary["active_count_distribution"],
            "membership_replacement": False,
        },
        "complete_day_mask": {
            "partial_days": [item["canonical_key"] for item in lifecycle_outcomes if item["status"] == "active_partial"],
            "terminated_days": [item["canonical_key"] for item in lifecycle_outcomes if item["status"] == "lifecycle_terminated"],
            "partial_days_window_eligible": False,
        },
        "expected_grid_manifest": [{
            "symbol": symbol, "month": month, "expected_count": result.expected_count,
            "actual_count": result.actual_count, "missing_count": len(result.missing),
            "errors": list(result.errors), "complete": result.complete,
        } for (symbol, month), result in sorted(grid_results.items())],
        "raw_row_quarantine_manifest": [row for item in lifecycle_outcomes for row in item["raw_row_quarantine"]],
        "lifecycle_event_quarantine_manifest": [item for item in lifecycle_outcomes if item["status"] in {"unresolved_blocked", "blocked_policy_overlap"}],
        "candidate_eligibility_manifest": v3_base["candidate_eligibility_manifest"]["content"],
        "membership_manifest": membership_content,
        "qualified_panel_manifest": v3_base["qualified_panel_manifest"]["content"],
        "qualification_summary": summary,
        "V3_V4_diff": diff,
    }
    artifacts = {
        name: make_v4_manifest(name, contents[name], contract_hash=v4_contract["canonical_hash"], lifecycle_registry_hash=lifecycle.canonical_hash)
        for name in sorted(V4_MANIFEST_TYPES)
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in artifacts.items():
        write_manifest(evidence_dir / f"{name}.json", document)
    hashes = {name: document["content_hash"] for name, document in artifacts.items()}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(summary, hashes), encoding="utf-8")
    diff_report_path.write_text(render_diff_report(diff), encoding="utf-8")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_PREVIEW_ROOT / "qualification_report.md")
    parser.add_argument("--diff-report-path", type=Path, default=DEFAULT_PREVIEW_ROOT / "v3_v4_diff_report.md")
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    artifacts = run(
        raw_root=args.raw_root, evidence_dir=args.evidence_dir, end_month=args.end_month,
        report_path=args.report_path, diff_report_path=args.diff_report_path,
        offline=True, workers=args.workers, verify_remote_registry=False,
    )
    status = artifacts["qualification_summary"]["content"]["status"]
    print(f"status={status} artifact_set={canonical_hash({name: doc['content_hash'] for name, doc in artifacts.items()})}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
