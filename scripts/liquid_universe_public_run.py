#!/usr/bin/env python3
"""Build V2 liquid-universe qualification from verified public archives only."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from btc_eth_dual_quant.data.liquid_universe import (
    DailyEvidence,
    MinuteBar,
    aggregate_one_hour,
    exclusion_record,
    merge_daily,
    validate_daily,
    validate_symbol_month_grid,
)
from btc_eth_dual_quant.data.liquid_universe_artifacts import render_qualification_report, write_manifest
from btc_eth_dual_quant.data.liquid_universe_pipeline import build_artifacts, build_membership_rows
from btc_eth_dual_quant.data.public_archive import ensure_archive, parse_checksum, verify_zip

BUCKET = "https://data.binance.vision"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "storage/raw/liquid_universe/data/spot"
DEFAULT_EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v2"


def archive_timestamp(value: str) -> datetime:
    raw = int(value)
    return datetime.fromtimestamp(raw / (1_000_000 if raw >= 10**15 else 1_000), timezone.utc)


def canonical_key(symbol: str, interval: str, month: str, *, frequency: str = "monthly") -> str:
    return f"data/spot/{frequency}/klines/{symbol}/{interval}/{symbol}-{interval}-{month}.zip"


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            mode="w",
            encoding="utf-8",
            delete=False,
        ) as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _fetch_checksum_text(
    url: str,
    *,
    retries: int = 3,
    opener: Callable[..., object] = urllib.request.urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    if retries < 1:
        raise ValueError("retries must be positive")
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return opener(url, timeout=30).read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            last_error = exc
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        if attempt + 1 < retries:
            sleep(float(2**attempt))
    raise OSError(f"checksum download failed after {retries} attempts: {url}") from last_error


def _checksum(path: Path, key: str, *, offline: bool) -> tuple[str | None, str]:
    checksum_path = path.with_suffix(path.suffix + ".CHECKSUM")
    if checksum_path.exists():
        return parse_checksum(checksum_path.read_text(encoding="utf-8")), "official_checksum_verified"
    if offline:
        return None, "official_checksum_unavailable_zip_crc_sha256_verified"
    url = f"{BUCKET}/{urllib.parse.quote(key)}.CHECKSUM"
    try:
        text = _fetch_checksum_text(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "official_checksum_unavailable_zip_crc_sha256_verified"
        raise
    _atomic_write_text(checksum_path, text)
    return parse_checksum(text), "official_checksum_verified"


def _prefetch_checksums(jobs: list[tuple[Path, str]], *, offline: bool, workers: int) -> None:
    if workers < 1:
        raise ValueError("workers must be positive")
    if offline:
        return
    ordered = sorted(jobs, key=lambda item: item[1])
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_checksum, path, key, offline=False) for path, key in ordered]
        for future in futures:
            future.result()


def _download_missing_archive(path: Path, key: str) -> None:
    checksum_url = f"{BUCKET}/{urllib.parse.quote(key)}.CHECKSUM"
    try:
        checksum_text = _fetch_checksum_text(checksum_url)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        checksum_text = None
    ensure_archive(
        url=f"{BUCKET}/{urllib.parse.quote(key)}",
        destination=path,
        checksum_text=checksum_text,
    )
    if checksum_text is not None:
        _atomic_write_text(path.with_suffix(path.suffix + ".CHECKSUM"), checksum_text)


def _archive_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1:
            raise ValueError("archive must contain one CSV")
        return [row for row in csv.reader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8")) if row and row[0].isdigit()]


def _source_row(path: Path, key: str, symbol: str, interval: str, month: str, role: str, *, offline: bool) -> dict:
    expected, status = _checksum(path, key, offline=offline)
    digest, count, first, last = verify_zip(path, expected_sha256=expected)
    return {
        "canonical_key": key,
        "canonical_url": f"{BUCKET}/{key}",
        "symbol": symbol,
        "interval": interval,
        "archive_month": month,
        "byte_size": path.stat().st_size,
        "sha256": digest,
        "verification_status": status,
        "row_count": count,
        "first_timestamp": first,
        "last_timestamp": last,
        "authority_role": role,
    }


def _daily_rows(
    path: Path,
    symbol: str,
    month: str,
    source: dict,
    authority: str,
    contract: dict,
    registry: dict,
) -> list[DailyEvidence]:
    result = []
    for row in _archive_rows(path):
        timestamp = archive_timestamp(row[0])
        if timestamp.time() != datetime.min.time().replace(tzinfo=None) or timestamp.strftime("%Y-%m") != month:
            raise ValueError(f"invalid daily UTC boundary: {symbol}:{timestamp.isoformat()}")
        evidence = DailyEvidence(
            symbol=symbol,
            day=timestamp.date(),
            quote_volume=Decimal(row[7]),
            authority=authority,
            archive_sha256=source["sha256"],
            open=Decimal(row[1]),
            high=Decimal(row[2]),
            low=Decimal(row[3]),
            close=Decimal(row[4]),
            volume=Decimal(row[5]),
            archive_key=source["canonical_key"],
        )
        try:
            validate_daily(evidence, expected_symbol=symbol, archive_month=month)
        except ValueError as exc:
            excluded = exclusion_record(symbol, evidence.day, contract, registry)
            if excluded is None:
                raise
            source.setdefault("excluded_invalid_daily_rows", []).append({
                "timestamp": timestamp.isoformat(),
                "reason": str(exc),
                "exclusion_category": excluded["category"],
            })
            continue
        result.append(evidence)
    return result


def _minute_rows(path: Path, symbol: str) -> list[MinuteBar]:
    return [
        MinuteBar(
            symbol=symbol,
            open_time=archive_timestamp(row[0]),
            open=Decimal(row[1]),
            high=Decimal(row[2]),
            low=Decimal(row[3]),
            close=Decimal(row[4]),
            volume=Decimal(row[5]),
            quote_volume=Decimal(row[7]),
            trade_count=int(row[8]),
            taker_base_volume=Decimal(row[9]),
            taker_quote_volume=Decimal(row[10]),
        )
        for row in _archive_rows(path)
    ]


def _discover_monthly_daily(raw_root: Path, end_month: str) -> list[tuple[str, str, Path]]:
    discovered = []
    for path in raw_root.glob("monthly/klines/*/1d/*.zip"):
        symbol = path.parts[-3]
        month = path.stem[-7:]
        if symbol.endswith("USDT") and "2019-01" <= month <= end_month:
            discovered.append((symbol, month, path))
    return sorted(discovered)


def _diagnostic_deduplicate(rows: list[DailyEvidence]) -> list[DailyEvidence]:
    """Keep deterministic first evidence only after merge has already blocked."""
    result: dict[tuple[str, date], DailyEvidence] = {}
    for row in sorted(rows, key=lambda item: (item.symbol, item.day, item.archive_key)):
        result.setdefault((row.symbol, row.day), row)
    return list(result.values())


def run(
    *,
    raw_root: Path,
    evidence_dir: Path,
    end_month: str,
    report_path: Path,
    offline: bool,
    workers: int = 8,
) -> dict[str, dict]:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
    confirmed = json.loads((ROOT / "config/liquid_spot_confirmed_archive_gaps_v2.json").read_text(encoding="utf-8"))
    if end_month != contract["frozen_end_month"]:
        raise ValueError("end month must match frozen V2 contract")

    monthly: list[DailyEvidence] = []
    supplements: list[DailyEvidence] = []
    sources: list[dict] = []
    processing: list[str] = []
    monthly_archives = _discover_monthly_daily(raw_root, end_month)
    daily_archives = [
        path
        for path in sorted(raw_root.glob("daily/klines/*/1d/*.zip"))
        if path.parts[-3].endswith("USDT") and path.stem[-10:-3] <= end_month
    ]
    _prefetch_checksums(
        [(path, canonical_key(symbol, "1d", month)) for symbol, month, path in monthly_archives]
        + [
            (path, canonical_key(path.parts[-3], "1d", path.stem[-10:], frequency="daily"))
            for path in daily_archives
        ],
        offline=offline,
        workers=workers,
    )
    for symbol, month, path in monthly_archives:
        key = canonical_key(symbol, "1d", month)
        try:
            source = _source_row(path, key, symbol, "1d", month, "official_monthly_zip_primary", offline=offline)
            sources.append(source)
            monthly.extend(_daily_rows(path, symbol, month, source, "official_monthly_zip", contract, registry))
        except Exception as exc:
            processing.append(f"{symbol}:{month}:1d:{type(exc).__name__}:{exc}")
    for path in daily_archives:
        symbol = path.parts[-3]
        day = path.stem[-10:]
        month = day[:7]
        if not symbol.endswith("USDT") or month > end_month:
            continue
        key = canonical_key(symbol, "1d", day, frequency="daily")
        try:
            source = _source_row(path, key, symbol, "1d", day, "official_daily_zip_fill_only", offline=offline)
            sources.append(source)
            supplements.extend(_daily_rows(path, symbol, month, source, "official_daily_zip", contract, registry))
        except Exception as exc:
            processing.append(f"{symbol}:{day}:daily_1d:{type(exc).__name__}:{exc}")
    try:
        daily = merge_daily(monthly, supplements)
    except ValueError as exc:
        processing.append(f"daily_merge:{exc}")
        daily = _diagnostic_deduplicate(monthly + supplements)

    membership = build_membership_rows(contract, registry, daily)
    needed = sorted({(row.symbol, row.effective_month[:7]) for row in membership})
    if not offline:
        for symbol, month in needed:
            key = canonical_key(symbol, "5m", month)
            path = raw_root / Path(key).relative_to("data/spot")
            if not path.exists():
                _download_missing_archive(path, key)
    _prefetch_checksums(
        [
            (
                raw_root / Path(canonical_key(symbol, "5m", month)).relative_to("data/spot"),
                canonical_key(symbol, "5m", month),
            )
            for symbol, month in needed
            if (raw_root / Path(canonical_key(symbol, "5m", month)).relative_to("data/spot")).exists()
        ],
        offline=offline,
        workers=workers,
    )
    grid_results = {}
    final_processing = list(processing)
    for symbol, month in needed:
        key = canonical_key(symbol, "5m", month)
        path = raw_root / Path(key).relative_to("data/spot")
        if not path.exists():
            final_processing.append(f"missing local archive:{symbol}:{month}:5m")
            continue
        try:
            source = _source_row(path, key, symbol, "5m", month, "official_monthly_zip_detail", offline=offline)
            sources.append(source)
            bars = _minute_rows(path, symbol)
            grid_results[(symbol, month)] = validate_symbol_month_grid(symbol, month, bars)
            grouped = defaultdict(list)
            for bar in bars:
                grouped[bar.open_time.replace(minute=0, second=0, microsecond=0)].append(bar)
            derived = 0
            for group in grouped.values():
                if len(group) == 12:
                    aggregate_one_hour(group)
                    derived += 1
            source["derived_1h_count"] = derived
        except Exception as exc:
            final_processing.append(f"{symbol}:{month}:5m:{type(exc).__name__}:{exc}")

    artifacts = build_artifacts(
        contract=contract,
        registry=registry,
        confirmed_gap_registry=confirmed,
        daily=daily,
        bars_by_symbol_month={},
        grid_results=grid_results,
        source_rows=sources,
        processing_errors=final_processing,
    )
    for name, document in artifacts.items():
        write_manifest(evidence_dir / f"{name}.json", document)
    hashes = {name: document["content_hash"] for name, document in artifacts.items()}
    report = render_qualification_report(artifacts["qualification_summary"]["content"], hashes)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--report-path", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_QUALIFICATION_REPORT.md")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    artifacts = run(
        raw_root=args.raw_root,
        evidence_dir=args.evidence_dir,
        end_month=args.end_month,
        report_path=args.report_path,
        offline=args.offline,
        workers=args.workers,
    )
    status = artifacts["qualification_summary"]["content"]["status"]
    print(f"status={status} artifact_set={json.dumps({name: doc['content_hash'] for name, doc in artifacts.items()}, sort_keys=True)}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
