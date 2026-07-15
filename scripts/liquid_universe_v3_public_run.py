#!/usr/bin/env python3
"""Build V3 liquid-universe evidence from verified public archives only."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Callable
import zipfile
import csv
import io

from btc_eth_dual_quant.data.kline_row_conflicts import RawKlineRow, ResolutionRegistry
from btc_eth_dual_quant.data.liquid_universe import (
    DailyEvidence,
    aggregate_one_hour,
    exclusion_record,
    validate_daily,
    validate_symbol_month_grid,
)
from btc_eth_dual_quant.data.liquid_universe_artifacts import write_manifest
from btc_eth_dual_quant.data.liquid_universe_pipeline import build_membership_rows
from btc_eth_dual_quant.data.liquid_universe_pipeline_v3 import (
    RowResolutionResult,
    build_artifacts_v3,
    resolve_daily_key,
)
from scripts.liquid_universe_public_run import (
    DEFAULT_RAW,
    ROOT,
    _checksum,
    _discover_monthly_daily,
    _download_missing_archive,
    _fetch_checksum_text,
    _minute_rows,
    _prefetch_checksums,
    _source_row,
    canonical_key,
)
from btc_eth_dual_quant.data.public_archive import parse_checksum


DEFAULT_EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_path(raw_root: Path, key: str) -> Path:
    return raw_root / Path(key).relative_to("data/spot")


def current_remote_checksum(key: str) -> str:
    return parse_checksum(_fetch_checksum_text(f"https://data.binance.vision/{key}.CHECKSUM"))


def ensure_registered_archives(raw_root: Path, registry: ResolutionRegistry, *, offline: bool) -> None:
    sources = {
        source.canonical_key
        for entry in registry.entries
        for source in (entry.monthly_archive, entry.daily_archive)
    }
    for key in sorted(sources):
        path = archive_path(raw_root, key)
        if path.exists():
            continue
        if offline:
            raise ValueError(f"registered archive missing: {key}")
        _download_missing_archive(path, key)


def assert_registered_archive_bindings(
    raw_root: Path,
    registry: ResolutionRegistry,
    remote_checksum: Callable[[str], str],
    *,
    file_hasher: Callable[[Path], str] = file_sha256,
) -> None:
    expected = {
        source.canonical_key: source.sha256
        for entry in registry.entries
        for source in (entry.monthly_archive, entry.daily_archive)
    }
    for key, frozen_sha256 in sorted(expected.items()):
        path = archive_path(raw_root, key)
        if not path.exists():
            raise ValueError(f"registered archive missing: {key}")
        if file_hasher(path) != frozen_sha256:
            raise ValueError(f"local registered archive checksum drift: {key}")
        if remote_checksum(key) != frozen_sha256:
            raise ValueError(f"remote checksum drift: {key}")


def raw_rows_from_archive(
    path: Path,
    *,
    symbol: str,
    interval: str,
    archive_key: str,
    archive_sha256: str,
    authority: str,
) -> list[RawKlineRow]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1:
            raise ValueError("archive must contain exactly one CSV")
        reader = csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8"))
        return [
            RawKlineRow.from_fields(
                symbol=symbol,
                interval=interval,
                fields=row,
                line_number=line_number,
                archive_key=archive_key,
                archive_sha256=archive_sha256,
                authority=authority,
            )
            for line_number, row in enumerate(reader, start=1)
            if row and row[0].isdigit()
        ]


def _excluded_result(rows: tuple[RawKlineRow, ...], category: str) -> RowResolutionResult:
    quarantine = tuple({
        "reason": "structurally invalid row excluded by frozen asset contract",
        "exclusion_category": category,
        "symbol": row.symbol,
        "interval": row.interval,
        "open_time_utc": row.open_time_utc,
        "archive_key": row.archive_key,
        "archive_sha256": row.archive_sha256,
        "line_number": row.line_number,
        "raw_row_hash": row.raw_row_hash,
        "raw_fields": list(row.fields),
    } for row in rows)
    return RowResolutionResult("excluded_by_contract", None, quarantine, ())


def _daily_evidence(result: RowResolutionResult) -> DailyEvidence:
    if result.canonical is None:
        raise ValueError("canonical row required")
    row = result.canonical
    timestamp = datetime.fromtimestamp(int(row.fields[0]) / (1_000_000 if int(row.fields[0]) >= 10**15 else 1_000), timezone.utc)
    evidence = DailyEvidence(
        symbol=row.symbol,
        day=timestamp.date(),
        quote_volume=Decimal(row.fields[7]),
        authority=row.source_authority,
        archive_sha256=row.source_archive_sha256,
        open=Decimal(row.fields[1]),
        high=Decimal(row.fields[2]),
        low=Decimal(row.fields[3]),
        close=Decimal(row.fields[4]),
        volume=Decimal(row.fields[5]),
        archive_key=row.source_archive_key,
    )
    validate_daily(evidence, expected_symbol=row.symbol, archive_month=timestamp.strftime("%Y-%m"))
    return evidence


def build_daily_canonical_evidence(
    *,
    monthly_groups: dict[tuple[str, str, int], list[RawKlineRow]],
    daily_groups: dict[tuple[str, str, int], list[RawKlineRow]],
    registry: ResolutionRegistry,
    contract: dict,
    eligibility_registry: dict,
) -> tuple[list[DailyEvidence], list[RowResolutionResult]]:
    daily: list[DailyEvidence] = []
    outcomes: list[RowResolutionResult] = []
    for key in sorted(set(monthly_groups) | set(daily_groups)):
        monthly = tuple(monthly_groups.get(key, ()))
        supplement = tuple(daily_groups.get(key, ()))
        result = resolve_daily_key(monthly, supplement, registry)
        if result.unresolved_row_conflicts:
            rows = monthly + supplement
            event_day = datetime.fromtimestamp(key[2] / 1_000, timezone.utc).date()
            excluded = exclusion_record(key[0], event_day, contract, eligibility_registry)
            if excluded is not None and rows and all(row.errors for row in rows):
                result = _excluded_result(rows, excluded["category"])
        if result.canonical is not None:
            daily.append(_daily_evidence(result))
        if result.status not in {"canonical"}:
            outcomes.append(result)
    return sorted(daily, key=lambda row: (row.symbol, row.day)), outcomes


def _collect_daily_sources(
    *,
    raw_root: Path,
    end_month: str,
    offline: bool,
    workers: int,
) -> tuple[dict, dict, list[dict], list[str]]:
    monthly_archives = _discover_monthly_daily(raw_root, end_month)
    daily_archives = [
        path for path in sorted(raw_root.glob("daily/klines/*/1d/*.zip"))
        if path.parts[-3].endswith("USDT") and path.stem[-10:-3] <= end_month
    ]
    jobs = [(path, canonical_key(symbol, "1d", month)) for symbol, month, path in monthly_archives]
    jobs.extend((path, canonical_key(path.parts[-3], "1d", path.stem[-10:], frequency="daily")) for path in daily_archives)
    _prefetch_checksums(jobs, offline=offline, workers=workers)

    monthly_groups: dict[tuple[str, str, int], list[RawKlineRow]] = defaultdict(list)
    daily_groups: dict[tuple[str, str, int], list[RawKlineRow]] = defaultdict(list)
    sources: list[dict] = []
    processing: list[str] = []
    for symbol, month, path in monthly_archives:
        key = canonical_key(symbol, "1d", month)
        try:
            source = _source_row(path, key, symbol, "1d", month, "official_monthly_zip_primary", offline=offline)
            sources.append(source)
            for row in raw_rows_from_archive(
                path, symbol=symbol, interval="1d", archive_key=key,
                archive_sha256=source["sha256"], authority="official_monthly_zip",
            ):
                if row.open_time_utc[:7] != month:
                    processing.append(f"archive month mismatch:{symbol}:{month}:{row.open_time_utc}")
                monthly_groups[row.canonical_key].append(row)
        except Exception as exc:
            processing.append(f"{symbol}:{month}:1d:{type(exc).__name__}:{exc}")
    for path in daily_archives:
        symbol = path.parts[-3]
        day = path.stem[-10:]
        month = day[:7]
        key = canonical_key(symbol, "1d", day, frequency="daily")
        try:
            source = _source_row(path, key, symbol, "1d", day, "official_daily_zip_fill_only", offline=offline)
            sources.append(source)
            for row in raw_rows_from_archive(
                path, symbol=symbol, interval="1d", archive_key=key,
                archive_sha256=source["sha256"], authority="official_daily_zip",
            ):
                if row.open_time_utc[:10] != day:
                    processing.append(f"archive day mismatch:{symbol}:{day}:{row.open_time_utc}")
                daily_groups[row.canonical_key].append(row)
        except Exception as exc:
            processing.append(f"{symbol}:{day}:daily_1d:{type(exc).__name__}:{exc}")
    return monthly_groups, daily_groups, sources, processing


def render_v3_report(summary: dict, hashes: dict[str, str]) -> str:
    lines = [
        "# Liquid Spot Universe V3 Qualification Report", "",
        f"- Status: {summary['status']}",
        f"- Range: {summary['research_start']} through {summary['end_month']}",
        f"- Expected months: {summary['expected_months']}",
        f"- Processing errors: {summary['processing_errors']}",
        f"- Unresolved row conflicts: {summary['unresolved_row_conflicts']}",
        f"- Unresolved gaps: {summary['unresolved_gaps']}",
        f"- Excluded-category members: {summary['excluded_category_members']}",
        f"- Monthly invalid rows quarantined: {summary['monthly_rows_quarantined']}",
        f"- Daily corrections admitted: {summary['daily_corrections_admitted']}",
        f"- Exact duplicate collapses: {summary['duplicate_collapses']}",
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
    lines.extend(["", "## Monthly Membership", ""])
    lines.extend(
        f"- {row['effective_month']}: {', '.join(row['symbols'])}"
        for row in summary["members_by_month"]
    )
    blockers = summary.get("blockers", [])
    lines.extend(["", "## Blockers", "", *(f"- {item}" for item in blockers or ["none"])])
    return "\n".join(lines).rstrip() + "\n"


def run(
    *,
    raw_root: Path,
    evidence_dir: Path,
    end_month: str,
    report_path: Path,
    offline: bool,
    workers: int = 8,
    verify_remote_registry: bool = True,
) -> dict[str, dict]:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v3.json").read_text())
    eligibility = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text())
    confirmed = json.loads((ROOT / "config/liquid_spot_confirmed_archive_gaps_v2.json").read_text())
    registry = ResolutionRegistry.from_path(ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json")
    if end_month != contract["frozen_end_month"]:
        raise ValueError("end month must match frozen V3 contract")

    ensure_registered_archives(raw_root, registry, offline=offline)
    if verify_remote_registry:
        if offline:
            raise ValueError("remote registered checksum verification required for public V3 run")
        assert_registered_archive_bindings(raw_root, registry, current_remote_checksum)
    monthly_groups, daily_groups, sources, processing = _collect_daily_sources(
        raw_root=raw_root, end_month=end_month, offline=offline, workers=workers,
    )
    daily, outcomes = build_daily_canonical_evidence(
        monthly_groups=monthly_groups,
        daily_groups=daily_groups,
        registry=registry,
        contract=contract,
        eligibility_registry=eligibility,
    )

    membership = build_membership_rows(contract, eligibility, daily)
    needed = sorted({(row.symbol, row.effective_month[:7]) for row in membership})
    if not offline:
        for symbol, month in needed:
            key = canonical_key(symbol, "5m", month)
            path = archive_path(raw_root, key)
            if not path.exists():
                _download_missing_archive(path, key)
    _prefetch_checksums(
        [(archive_path(raw_root, canonical_key(symbol, "5m", month)), canonical_key(symbol, "5m", month))
         for symbol, month in needed if archive_path(raw_root, canonical_key(symbol, "5m", month)).exists()],
        offline=offline,
        workers=workers,
    )
    grid_results = {}
    for symbol, month in needed:
        key = canonical_key(symbol, "5m", month)
        path = archive_path(raw_root, key)
        if not path.exists():
            processing.append(f"missing local archive:{symbol}:{month}:5m")
            continue
        try:
            source = _source_row(path, key, symbol, "5m", month, "official_monthly_zip_detail", offline=offline)
            sources.append(source)
            bars = _minute_rows(path, symbol)
            grid_results[(symbol, month)] = validate_symbol_month_grid(symbol, month, bars)
            grouped = defaultdict(list)
            for bar in bars:
                grouped[bar.open_time.replace(minute=0, second=0, microsecond=0)].append(bar)
            source["derived_1h_count"] = sum(1 for group in grouped.values() if len(group) == 12 and aggregate_one_hour(group))
        except Exception as exc:
            processing.append(f"{symbol}:{month}:5m:{type(exc).__name__}:{exc}")

    artifacts = build_artifacts_v3(
        contract=contract,
        eligibility_registry=eligibility,
        resolution_registry=registry,
        confirmed_gap_registry=confirmed,
        daily=daily,
        bars_by_symbol_month={},
        source_rows=sources,
        resolution_results=outcomes,
        grid_results=grid_results,
        processing_errors=processing,
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in artifacts.items():
        write_manifest(evidence_dir / f"{name}.json", document)
    hashes = {name: document["content_hash"] for name, document in artifacts.items()}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_v3_report(artifacts["qualification_summary"]["content"], hashes), encoding="utf-8")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--report-path", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_QUALIFICATION_REPORT.md")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    artifacts = run(
        raw_root=args.raw_root, evidence_dir=args.evidence_dir, end_month=args.end_month,
        report_path=args.report_path, offline=False, workers=args.workers,
    )
    status = artifacts["qualification_summary"]["content"]["status"]
    print(f"status={status}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
