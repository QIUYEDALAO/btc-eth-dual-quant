#!/usr/bin/env python3
"""M0 public read-only backfill.

Downloads BTC/ETH public Binance market data through REST, appends raw response
envelopes, builds the DuckDB raw-envelope index, and emits a data-run report.
No strategy signals are computed here.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.binance import BinanceReadOnlyCollector, BinanceReadOnlyRestClient
from btc_eth_dual_quant.data.duckdb_layer import DuckDBLayer
from btc_eth_dual_quant.data.funding import infer_funding_interval_hours
from btc_eth_dual_quant.data.quality import (
    ZipRestAudit,
    audit_zip_rest_klines,
    detect_kline_gaps,
    flag_kline_anomalies,
)
from btc_eth_dual_quant.data.registry import RegistryRecord, load_registry
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore, RawEnvelope
from m0_report import DatasetRun, M0RunReport, write_report


KLINE_DATASETS = {
    "spot_klines",
    "um_futures_klines",
    "mark_price_klines",
    "index_price_klines",
    "premium_index_klines",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M0 public read-only Binance backfill")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT", help="Comma-separated symbols")
    parser.add_argument("--interval", default="1d", help="K-line interval")
    parser.add_argument("--limit", type=int, default=30, help="REST page limit per dataset")
    parser.add_argument("--max-pages", type=int, default=100, help="Safety cap for paginated REST pulls per dataset")
    parser.add_argument("--days", type=int, default=None, help="UTC lookback window in days; sets start/end timestamps")
    parser.add_argument("--start-date", default=None, help="UTC start date YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="UTC end date YYYY-MM-DD; defaults to now when omitted")
    parser.add_argument("--start-ms", type=int, default=None)
    parser.add_argument("--end-ms", type=int, default=None)
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--report-path", default="reports/m0/M0_PUBLIC_RUN_REPORT.md")
    parser.add_argument("--spot-base-url", default="https://api.binance.com")
    parser.add_argument("--futures-base-url", default="https://fapi.binance.com")
    parser.add_argument("--timeout-sec", type=int, default=20)
    parser.add_argument("--proxy", default=None, help="Optional proxy URL, e.g. http://127.0.0.1:7897")
    parser.add_argument("--zip-fallback", action="store_true", help="Use data.binance.vision ZIP fallback for public kline datasets when REST fails")
    parser.add_argument(
        "--skip-zip-compare",
        action="store_true",
        help="Skip ZIP/REST audit; resulting report is intentionally blocked for acceptance",
    )
    parser.add_argument("--zip-lookback-days", type=int, default=90)
    parser.add_argument("--include-oi", action="store_true", help="Also archive openInterestHist")
    parser.add_argument("--spot-only", action="store_true", help="Only collect spot klines")
    parser.add_argument("--oi-period", default="1d", help="openInterestHist period")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without network calls or writes")
    return parser.parse_args()


def _epoch_ms(value: Any) -> int:
    timestamp = int(value)
    if abs(timestamp) >= 100_000_000_000_000:
        timestamp //= 1000
    return timestamp


def _rows_from_kline_payload(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload if isinstance(payload, list) else []:
        if isinstance(row, list) and len(row) >= 7:
            rows.append(
                {
                    "open_time": _epoch_ms(row[0]),
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5] if len(row) > 5 else "0",
                    "close_time": _epoch_ms(row[6]),
                    "quote_volume": row[7] if len(row) > 7 else "0",
                }
            )
    return rows


def _utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def _date_start_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000)


def _date_end_ms(value: str) -> int:
    return int((datetime.fromisoformat(value).replace(tzinfo=timezone.utc) + timedelta(days=1)).timestamp() * 1000) - 1


def _row_time_bounds(rows: list[dict[str, Any]], start_field: str, end_field: str | None = None) -> tuple[int | None, int | None]:
    if not rows:
        return None, None
    starts = [int(row[start_field]) for row in rows if row.get(start_field) is not None]
    if not starts:
        return None, None
    if end_field:
        ends = [int(row[end_field]) for row in rows if row.get(end_field) is not None]
    else:
        ends = starts
    return min(starts), max(ends or starts)


def _csv_rows_from_zip(url: str, timeout_sec: int) -> list[list[str]]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout_sec) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [name for name in zf.namelist() if name.endswith(".csv")]
        if not names:
            raise ValueError(f"ZIP has no CSV file: {url}")
        with zf.open(names[0]) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8")
            rows = list(csv.reader(text))
    if rows and rows[0] and rows[0][0] in {"open_time", "Open time"}:
        rows = rows[1:]
    return rows


def _month_starts(start_ms: int | None, end_ms: int | None, lookback_days: int) -> list[date]:
    if start_ms is None or end_ms is None:
        end_day = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
        start_day = end_day - timedelta(days=max(1, lookback_days) - 1)
    else:
        start_day = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).date().replace(day=1)
        end_day = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).date().replace(day=1)
    months: list[date] = []
    current = start_day
    while current <= end_day:
        months.append(current)
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        current = date(year, month, 1)
    return months


def _kline_zip_url(dataset_name: str, symbol: str, interval: str, month: date) -> str:
    kind_by_dataset = {
        "spot_klines": "klines",
        "um_futures_klines": "klines",
        "mark_price_klines": "markPriceKlines",
        "index_price_klines": "indexPriceKlines",
        "premium_index_klines": "premiumIndexKlines",
    }
    kind = kind_by_dataset[dataset_name]
    scope = "spot" if dataset_name == "spot_klines" else "futures/um"
    return (
        "https://data.binance.vision/"
        f"data/{scope}/monthly/{kind}/{symbol}/{interval}/{symbol}-{interval}-{month:%Y-%m}.zip"
    )


def _funding_zip_url(symbol: str, month: date) -> str:
    return (
        "https://data.binance.vision/"
        f"data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month:%Y-%m}.zip"
    )


def _row_ms(row: list[str], idx: int = 0) -> int | None:
    try:
        return _epoch_ms(row[idx])
    except (IndexError, TypeError, ValueError):
        return None


def _within_ms(value: int | None, start_ms: int | None, end_ms: int | None) -> bool:
    if value is None:
        return False
    if start_ms is not None and value < start_ms:
        return False
    if end_ms is not None and value > end_ms:
        return False
    return True


def _zip_kline_payload(
    dataset_name: str,
    symbol: str,
    interval: str,
    limit: int,
    timeout_sec: int,
    lookback_days: int,
    start_ms: int | None,
    end_ms: int | None,
) -> tuple[list[list[str]], list[str]]:
    collected: list[list[str]] = []
    sources: list[str] = []
    for month in _month_starts(start_ms, end_ms, lookback_days):
        url = _kline_zip_url(dataset_name, symbol, interval, month)
        try:
            rows = _csv_rows_from_zip(url, timeout_sec)
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        filtered = [row for row in rows if _within_ms(_row_ms(row, 0), start_ms, end_ms)]
        if filtered:
            collected.extend(filtered)
            sources.append(url)
    if not collected:
        raise ValueError(f"no ZIP fallback rows found for {dataset_name}:{symbol}")
    collected = sorted(collected, key=lambda row: _row_ms(row, 0) or 0)
    if start_ms is None and end_ms is None:
        collected = collected[-limit:]
    return collected, sources


def _zip_funding_payload(
    symbol: str,
    limit: int,
    timeout_sec: int,
    lookback_days: int,
    start_ms: int | None,
    end_ms: int | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    collected: list[dict[str, Any]] = []
    sources: list[str] = []
    for month in _month_starts(start_ms, end_ms, lookback_days):
        url = _funding_zip_url(symbol, month)
        try:
            rows = _csv_rows_from_zip(url, timeout_sec)
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        month_records: list[dict[str, Any]] = []
        for row in rows:
            ts = _row_ms(row, 0)
            if not _within_ms(ts, start_ms, end_ms):
                continue
            try:
                interval_hours = row[1]
                funding_rate = row[2]
            except IndexError:
                continue
            month_records.append(
                {
                    "symbol": symbol,
                    "fundingTime": ts,
                    "fundingRate": funding_rate,
                    "fundingIntervalHours": interval_hours,
                }
            )
        if month_records:
            collected.extend(month_records)
            sources.append(url)
    if not collected:
        raise ValueError(f"no ZIP fallback rows found for funding_rate_history:{symbol}")
    collected = sorted(collected, key=lambda row: int(row["fundingTime"]))
    if start_ms is None and end_ms is None:
        collected = collected[-limit:]
    return collected, sources


def _recent_zip_payload(
    dataset_name: str,
    symbol: str,
    interval: str,
    limit: int,
    timeout_sec: int,
    lookback_days: int,
) -> tuple[list[list[str]], list[str]]:
    kind_by_dataset = {
        "um_futures_klines": "klines",
        "mark_price_klines": "markPriceKlines",
        "index_price_klines": "indexPriceKlines",
        "premium_index_klines": "premiumIndexKlines",
    }
    kind = kind_by_dataset[dataset_name]
    collected: list[list[str]] = []
    sources: list[str] = []
    day = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
    for offset in range(lookback_days):
        current = day - timedelta(days=offset)
        url = (
            "https://data.binance.vision/"
            f"data/futures/um/daily/{kind}/{symbol}/{interval}/{symbol}-{interval}-{current.isoformat()}.zip"
        )
        try:
            rows = _csv_rows_from_zip(url, timeout_sec)
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        collected.extend(rows)
        sources.append(url)
        if len(collected) >= limit:
            break
    if not collected:
        raise ValueError(f"no ZIP fallback rows found for {dataset_name}:{symbol}")
    return collected[-limit:], sources


def _append_zip_fallback(
    collector: BinanceReadOnlyCollector,
    record: RegistryRecord,
    dataset_name: str,
    symbol: str,
    interval: str,
    limit: int,
    timeout_sec: int,
    lookback_days: int,
    start_ms: int | None = None,
    end_ms: int | None = None,
) -> RawEnvelope:
    if start_ms is not None or end_ms is not None or dataset_name == "spot_klines":
        payload, sources = _zip_kline_payload(
            dataset_name, symbol, interval, limit, timeout_sec, lookback_days, start_ms, end_ms
        )
    else:
        payload, sources = _recent_zip_payload(dataset_name, symbol, interval, limit, timeout_sec, lookback_days)
    return collector.store.append(
        dataset=record.name,
        source=f"{record.source} ZIP fallback",
        endpoint="ZIP " + ",".join(sources),
        params={"symbol": symbol, "interval": interval, "limit": limit, "fallback": "data.binance.vision"},
        payload=payload,
    )


def _append_funding_zip_fallback(
    collector: BinanceReadOnlyCollector,
    record: RegistryRecord,
    symbol: str,
    limit: int,
    timeout_sec: int,
    lookback_days: int,
    start_ms: int | None,
    end_ms: int | None,
) -> RawEnvelope:
    payload, sources = _zip_funding_payload(symbol, limit, timeout_sec, lookback_days, start_ms, end_ms)
    return collector.store.append(
        dataset=record.name,
        source=f"{record.source} ZIP fallback",
        endpoint="ZIP " + ",".join(sources),
        params={"symbol": symbol, "limit": limit, "fallback": "data.binance.vision"},
        payload=payload,
    )


def _combined_envelope(envelopes: list[RawEnvelope]) -> RawEnvelope:
    if not envelopes:
        raise ValueError("cannot combine zero envelopes")
    first = envelopes[0]
    payload: list[Any] = []
    for envelope in envelopes:
        if isinstance(envelope.payload, list):
            payload.extend(envelope.payload)
    return RawEnvelope(
        dataset=first.dataset,
        source=first.source,
        endpoint=first.endpoint,
        params=first.params,
        payload=payload,
        ingested_at_ms=first.ingested_at_ms,
        content_sha256=first.content_sha256,
    )


def _anomaly_input_rows(dataset: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if dataset == "premium_index_klines":
        return [{**row, "open": row["high"], "low": row["high"], "volume": "1"} for row in rows]
    if dataset in {"mark_price_klines", "index_price_klines"}:
        return [{**row, "volume": "1"} for row in rows]
    return rows


def _month_for_ms(timestamp_ms: int) -> date:
    value = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date()
    return value.replace(day=1)


def _audit_months(dataset: str, rows: list[dict[str, Any]]) -> tuple[list[date], str]:
    months = sorted({_month_for_ms(int(row["open_time"])) for row in rows})
    if not months:
        return [], "not_available"
    now_month = datetime.now(tz=timezone.utc).date().replace(day=1)
    completed = [month for month in months if month < now_month]
    eligible = completed or months
    first = eligible[0]
    middle = eligible[len(eligible) // 2]
    latest = eligible[-1]
    selected = {first, middle, latest}
    anomalies = flag_kline_anomalies(_anomaly_input_rows(dataset, rows))
    anomaly_months = sorted({_month_for_ms(item.open_time) for item in anomalies})
    selected.update(anomaly_months)
    anomaly_scope = ",".join(month.isoformat()[:7] for month in anomaly_months) or "none"
    scope = (
        f"first={first.isoformat()[:7]};middle={middle.isoformat()[:7]};"
        f"latest_complete={latest.isoformat()[:7]};anomaly={anomaly_scope}"
    )
    return sorted(selected), scope


def _zip_rest_audit(
    dataset: str,
    symbol: str,
    interval: str,
    rest_rows: list[dict[str, Any]],
    timeout_sec: int,
) -> ZipRestAudit:
    zip_payload: list[list[str]] = []
    months, scope = _audit_months(dataset, rest_rows)
    missing_months: list[str] = []
    for month in months:
        url = _kline_zip_url(dataset, symbol, interval, month)
        try:
            zip_payload.extend(_csv_rows_from_zip(url, timeout_sec))
        except HTTPError as exc:
            if exc.code == 404:
                missing_months.append(month.isoformat()[:7])
                continue
            raise
    if missing_months:
        raise ValueError(
            f"ZIP/REST audit missing selected ZIP month(s) for {dataset}:{symbol}: {','.join(missing_months)}"
        )
    zip_rows = _rows_from_kline_payload(zip_payload)
    audit = audit_zip_rest_klines(zip_rows, rest_rows, scope=scope)
    if audit.overlap_rows <= 0:
        raise ValueError(f"ZIP/REST audit found no overlapping rows for {dataset}:{symbol}")
    return audit


def _payload_last_ms(payload: Any, kind: str) -> int | None:
    if not isinstance(payload, list) or not payload:
        return None
    last = payload[-1]
    if kind == "kline" and isinstance(last, list) and len(last) > 6:
        return int(last[6])
    if kind == "funding" and isinstance(last, dict) and last.get("fundingTime") is not None:
        return int(last["fundingTime"])
    if kind == "oi" and isinstance(last, dict) and last.get("timestamp") is not None:
        return int(last["timestamp"])
    return None


def _collect_paginated(
    fn: Callable[..., RawEnvelope],
    record: RegistryRecord,
    kwargs: dict[str, Any],
    start_ms: int | None,
    end_ms: int | None,
    limit: int,
    max_pages: int,
    kind: str,
) -> RawEnvelope:
    envelopes: list[RawEnvelope] = []
    current_start = start_ms
    for _ in range(max_pages):
        page_kwargs = {**kwargs, "limit": limit, "startTime": current_start, "endTime": end_ms}
        envelope = fn(record, **page_kwargs)
        envelopes.append(envelope)
        payload = envelope.payload if isinstance(envelope.payload, list) else []
        if not payload:
            break
        last_ms = _payload_last_ms(payload, kind)
        if last_ms is None:
            break
        if end_ms is not None and last_ms >= end_ms - 1:
            break
        if len(payload) < limit:
            break
        next_start = last_ms + 1
        if current_start is not None and next_start <= current_start:
            break
        current_start = next_start
    return _combined_envelope(envelopes)


def _summarize_kline(
    dataset: str,
    interval: str,
    envelope: RawEnvelope,
    audit: ZipRestAudit | None = None,
    audit_error: str | None = None,
) -> DatasetRun:
    rows = _rows_from_kline_payload(envelope.payload)
    start_ms, end_ms = _row_time_bounds(rows, "open_time", "close_time")
    gaps = detect_kline_gaps(rows, interval).gaps if rows else []
    base_dataset = dataset.split(":", 1)[0]
    anomaly_rows = _anomaly_input_rows(base_dataset, rows)
    anomalies = flag_kline_anomalies(anomaly_rows) if rows else []
    unexplained = []
    if anomalies:
        reason_counts: dict[str, int] = {}
        for anomaly in anomalies:
            reason_counts[anomaly.reason] = reason_counts.get(anomaly.reason, 0) + 1
        unexplained.append(f"kline anomalies pending review: {reason_counts}")
    if audit_error:
        unexplained.append(f"ZIP/REST comparison incomplete: {audit_error}")
    if audit and audit.differences:
        unexplained.append(f"ZIP/REST comparison differences={len(audit.differences)}")
    return DatasetRun(
        name=dataset,
        interval=interval,
        rows=len(rows),
        start_ms=start_ms,
        end_ms=end_ms,
        gaps=len(gaps),
        zip_rest_differences=len(audit.differences) if audit else "not_run",
        zip_rest_overlap=audit.overlap_rows if audit else "not_run",
        rest_payload_sha256=audit.rest_payload_sha256 if audit else "not_run",
        zip_payload_sha256=audit.zip_payload_sha256 if audit else "not_run",
        zip_rest_scope=audit.scope if audit else "not_run",
        kline_anomalies=len(anomalies),
        funding_interval_warnings="not_applicable",
        archive_status="not_applicable",
        commission_status="not_applicable",
        unexplained=unexplained,
    )


def _summarize_funding(envelope: RawEnvelope, symbol: str) -> DatasetRun:
    payload = envelope.payload if isinstance(envelope.payload, list) else []
    rows = [row for row in payload if isinstance(row, dict)]
    start_ms, end_ms = _row_time_bounds(rows, "fundingTime")
    return DatasetRun(
        name=f"funding_rate_history:{symbol}",
        interval="funding_period",
        rows=len(payload),
        start_ms=start_ms,
        end_ms=end_ms,
        gaps=0,
        zip_rest_differences="not_applicable",
        kline_anomalies=0,
        funding_interval_warnings="not_applicable",
        archive_status="not_applicable",
        commission_status="not_applicable",
    )


def _failed_run(name: str, interval: str, error: Exception) -> DatasetRun:
    return DatasetRun(
        name=name,
        interval=interval,
        rows=0,
        gaps=0,
        zip_rest_differences="not_run",
        kline_anomalies=0,
        funding_interval_warnings="not_run",
        archive_status="failed",
        commission_status="not_applicable",
        unexplained=[f"{type(error).__name__}: {error}"],
    )


def _summarize_open_interest(envelope: RawEnvelope, symbol: str, period: str, retention_limited: bool) -> DatasetRun:
    payload = envelope.payload if isinstance(envelope.payload, list) else []
    rows = [row for row in payload if isinstance(row, dict)]
    start_ms, end_ms = _row_time_bounds(rows, "timestamp")
    archive_status = "pass_retention_limited" if payload and retention_limited else ("pass" if payload else "empty_response")
    return DatasetRun(
        name=f"open_interest:{symbol}",
        interval=period,
        rows=len(payload),
        start_ms=start_ms,
        end_ms=end_ms,
        zip_rest_differences="not_applicable",
        kline_anomalies=0,
        funding_interval_warnings="not_applicable",
        archive_status=archive_status,
        commission_status="not_applicable",
        unexplained=[] if payload else ["openInterestHist returned no rows"],
    )


def _summarize_funding_interval(symbol: str, funding_history_payload: list[dict[str, Any]]) -> DatasetRun:
    try:
        result = infer_funding_interval_hours(symbol, funding_rate_history=funding_history_payload)
        warnings = len(result.warnings)
        unexplained = result.warnings
    except ValueError as exc:
        warnings = 1
        unexplained = [str(exc)]
    rows = [row for row in funding_history_payload if isinstance(row, dict)]
    start_ms, end_ms = _row_time_bounds(rows, "fundingTime")
    return DatasetRun(
        name=f"funding_interval_{symbol}",
        interval="inferred",
        rows=len(funding_history_payload),
        start_ms=start_ms,
        end_ms=end_ms,
        zip_rest_differences="not_applicable",
        kline_anomalies=0,
        funding_interval_warnings=warnings,
        archive_status="not_applicable",
        commission_status="not_applicable",
        unexplained=unexplained,
    )


def _collect_for_symbol(
    collector: BinanceReadOnlyCollector,
    records: dict[str, RegistryRecord],
    symbol: str,
    interval: str,
    limit: int,
    start_ms: int | None,
    end_ms: int | None,
    include_oi: bool,
    oi_period: str,
    zip_fallback: bool,
    timeout_sec: int,
    zip_lookback_days: int,
    oi_retention_limited: bool,
    max_pages: int,
    spot_only: bool,
    zip_compare: bool,
) -> list[DatasetRun]:
    params = {"limit": limit, "startTime": start_ms, "endTime": end_ms}
    runs: list[DatasetRun] = []

    kline_calls: list[tuple[str, Callable[..., RawEnvelope], dict[str, Any]]] = [
        ("spot_klines", collector.spot_klines, {"symbol": symbol, "interval": interval}),
        ("um_futures_klines", collector.um_futures_klines, {"symbol": symbol, "interval": interval}),
        ("mark_price_klines", collector.mark_price_klines, {"symbol": symbol, "interval": interval}),
        ("index_price_klines", collector.index_price_klines, {"pair": symbol, "interval": interval}),
        ("premium_index_klines", collector.premium_index_klines, {"symbol": symbol, "interval": interval}),
    ]
    if spot_only:
        kline_calls = [call for call in kline_calls if call[0] == "spot_klines"]
    for name, fn, kwargs in kline_calls:
        run_name = f"{name}:{symbol}"
        try:
            envelope = _collect_paginated(
                fn, records[name], kwargs, start_ms, end_ms, limit, max_pages, "kline"
            )
            audit = None
            audit_error = None
            if zip_compare:
                try:
                    audit = _zip_rest_audit(
                        name,
                        symbol,
                        interval,
                        _rows_from_kline_payload(envelope.payload),
                        timeout_sec,
                    )
                except Exception as exc:
                    audit_error = f"{type(exc).__name__}: {exc}"
            else:
                audit_error = "skipped by --skip-zip-compare"
            runs.append(_summarize_kline(run_name, interval, envelope, audit, audit_error))
        except Exception as exc:
            if zip_fallback:
                try:
                    envelope = _append_zip_fallback(
                        collector,
                        records[name],
                        name,
                        symbol,
                        interval,
                        limit,
                        timeout_sec,
                        zip_lookback_days,
                        start_ms,
                        end_ms,
                    )
                    run = _summarize_kline(run_name, interval, envelope)
                    run.zip_rest_differences = "not_available_rest_failed"
                    run.zip_rest_overlap = "not_available_rest_failed"
                    run.rest_payload_sha256 = "not_available_rest_failed"
                    run.zip_payload_sha256 = envelope.content_sha256
                    run.unexplained.append(f"REST failed; used ZIP fallback: {type(exc).__name__}: {exc}")
                    runs.append(run)
                except Exception as fallback_exc:
                    failed = _failed_run(run_name, interval, fallback_exc)
                    failed.unexplained.insert(0, f"REST failed before ZIP fallback: {type(exc).__name__}: {exc}")
                    runs.append(failed)
            else:
                runs.append(_failed_run(run_name, interval, exc))

    if spot_only:
        return runs

    funding_payload: list[dict[str, Any]] = []
    try:
        funding_limit = max(limit, 1000) if start_ms is not None or end_ms is not None else limit
        funding_envelope = _collect_paginated(
            collector.funding_rate_history,
            records["funding_rate_history"],
            {"symbol": symbol},
            start_ms,
            end_ms,
            funding_limit,
            max_pages,
            "funding",
        )
        runs.append(_summarize_funding(funding_envelope, symbol))
        funding_payload = funding_envelope.payload if isinstance(funding_envelope.payload, list) else []
        runs.append(_summarize_funding_interval(symbol, funding_payload))
    except Exception as exc:
        if zip_fallback:
            try:
                funding_envelope = _append_funding_zip_fallback(
                    collector,
                    records["funding_rate_history"],
                    symbol,
                    max(limit, 1000),
                    timeout_sec,
                    zip_lookback_days,
                    start_ms,
                    end_ms,
                )
                run = _summarize_funding(funding_envelope, symbol)
                run.unexplained.append(f"REST failed; used ZIP fallback: {type(exc).__name__}: {exc}")
                runs.append(run)
                funding_payload = funding_envelope.payload if isinstance(funding_envelope.payload, list) else []
                interval_run = _summarize_funding_interval(symbol, funding_payload)
                if interval_run.funding_interval_warnings != 0:
                    interval_run.unexplained.append("fundingIntervalHours column present in ZIP source; verify against inferred cadence")
                runs.append(interval_run)
            except Exception as fallback_exc:
                failed = _failed_run(f"funding_rate_history:{symbol}", "funding_period", fallback_exc)
                failed.unexplained.insert(0, f"REST failed before ZIP fallback: {type(exc).__name__}: {exc}")
                runs.append(failed)
                runs.append(
                    DatasetRun(
                        name=f"funding_interval_{symbol}",
                        interval="inferred",
                        rows=0,
                        funding_interval_warnings=1,
                        archive_status="not_applicable",
                        unexplained=[
                            f"funding interval unavailable because fundingRate failed: {type(fallback_exc).__name__}: {fallback_exc}"
                        ],
                    )
                )
        else:
            runs.append(_failed_run(f"funding_rate_history:{symbol}", "funding_period", exc))
            runs.append(
                DatasetRun(
                    name=f"funding_interval_{symbol}",
                    interval="inferred",
                    rows=0,
                    funding_interval_warnings=1,
                    archive_status="not_applicable",
                    unexplained=[f"funding interval unavailable because fundingRate failed: {type(exc).__name__}: {exc}"],
                )
            )
    if include_oi:
        try:
            oi_start_ms = None if oi_retention_limited else start_ms
            oi_end_ms = None if oi_retention_limited else end_ms
            oi_envelope = _collect_paginated(
                collector.open_interest_hist,
                records["open_interest"],
                {"symbol": symbol, "period": oi_period},
                oi_start_ms,
                oi_end_ms,
                min(limit, 500),
                max_pages,
                "oi",
            )
            runs.append(_summarize_open_interest(oi_envelope, symbol, oi_period, oi_retention_limited))
        except Exception as exc:
            runs.append(_failed_run(f"open_interest:{symbol}", oi_period, exc))
    return runs


def main() -> int:
    args = parse_args()
    if args.proxy:
        import os

        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ.setdefault("ALL_PROXY", args.proxy)
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    if args.days is not None:
        end_dt = datetime.now(tz=timezone.utc)
        start_dt = end_dt - timedelta(days=args.days)
        if args.start_ms is None:
            args.start_ms = int(start_dt.timestamp() * 1000)
        if args.end_ms is None:
            args.end_ms = int(end_dt.timestamp() * 1000)
    if args.start_date and args.start_ms is None:
        args.start_ms = _date_start_ms(args.start_date)
    if args.end_date and args.end_ms is None:
        args.end_ms = _date_end_ms(args.end_date)
    if args.start_date and args.end_date is None and args.end_ms is None:
        args.end_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    registry = load_registry(ROOT / "data_registry.yaml")
    records = {record.name: record for record in registry.enabled_records()}
    required = {"spot_klines"} if args.spot_only else (KLINE_DATASETS | {"funding_rate_history"})
    if args.include_oi and not args.spot_only:
        required.add("open_interest")
    missing = sorted(required - records.keys())
    if missing:
        raise SystemExit(f"Missing enabled registry records: {missing}")

    if args.dry_run:
        print("M0 public backfill dry-run")
        print(f"symbols={symbols} interval={args.interval} limit={args.limit}")
        print("datasets=" + ",".join(sorted(required)))
        if args.include_oi:
            print(f"oi_period={args.oi_period}")
        return 0

    store = AppendOnlyRawStore(args.raw_root)
    collector = BinanceReadOnlyCollector(
        BinanceReadOnlyRestClient(
            spot_base_url=args.spot_base_url,
            futures_base_url=args.futures_base_url,
            timeout_sec=args.timeout_sec,
        ),
        store,
    )
    runs: list[DatasetRun] = []
    for symbol in symbols:
        oi_retention_limited = bool(
            args.include_oi
            and args.start_ms is not None
            and args.start_ms < int((datetime.now(tz=timezone.utc) - timedelta(days=35)).timestamp() * 1000)
        )
        runs.extend(
            _collect_for_symbol(
                collector,
                records,
                symbol,
                args.interval,
                args.limit,
                args.start_ms,
                args.end_ms,
                args.include_oi and not args.spot_only,
                args.oi_period,
                args.zip_fallback,
                args.timeout_sec,
                args.zip_lookback_days,
                oi_retention_limited,
                args.max_pages,
                args.spot_only,
                not args.skip_zip_compare,
            )
        )

    try:
        duckdb = DuckDBLayer(args.duckdb_path)
        for dataset in required:
            duckdb.index_from_store(store, dataset)
    except Exception as exc:
        runs.append(_failed_run("duckdb_index", "raw_envelopes", exc))

    starts = [run.start_ms for run in runs if run.start_ms is not None and run.rows > 0]
    ends = [run.end_ms for run in runs if run.end_ms is not None and run.rows > 0]
    data_start = _utc_iso(min(starts)) if starts else "not_available"
    data_end = _utc_iso(max(ends)) if ends else "not_available"
    write_report(M0RunReport(data_start=data_start, data_end=data_end, datasets=runs), args.report_path)
    print(f"Wrote report: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
