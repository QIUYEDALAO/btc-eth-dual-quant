"""Local M0 public-data loader for M1A offline backtests.

This module reads existing M0 raw envelopes or the local DuckDB raw index. It
does not call exchange APIs and does not mutate raw storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from btc_eth_dual_quant.data.duckdb_layer import DuckDBLayer
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore, RawEnvelope

from .trend_strategy import FundingRecord, TrendBar, validate_bars


class M0DataUnavailableError(RuntimeError):
    pass


def _normalize_kline(row: Any, symbol: str) -> TrendBar | None:
    try:
        if isinstance(row, dict):
            return TrendBar(
                symbol=symbol,
                open_time_ms=int(row["open_time"]),
                close_time_ms=int(row.get("close_time", int(row["open_time"]) + 86_400_000 - 1)),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
            )
        if isinstance(row, list) and len(row) >= 6:
            return TrendBar(
                symbol=symbol,
                open_time_ms=int(row[0]),
                close_time_ms=int(row[6]) if len(row) > 6 else int(row[0]) + 86_400_000 - 1,
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
    except (KeyError, TypeError, ValueError):
        return None
    return None


def _funding_interval_hours(records: list[dict[str, Any]]) -> float | None:
    times = sorted({int(row["fundingTime"]) for row in records if "fundingTime" in row})
    if len(times) < 2:
        return None
    diffs = [right - left for left, right in zip(times, times[1:]) if right > left]
    if not diffs:
        return None
    return min(diffs) / 3_600_000


def _normalize_funding(row: Any, symbol: str, interval_hours: float | None) -> FundingRecord | None:
    if not isinstance(row, dict):
        return None
    try:
        rate = float(row["fundingRate"])
        time_ms = int(row["fundingTime"])
    except (KeyError, TypeError, ValueError):
        return None
    annualized = 0.0 if not interval_hours else rate * (24.0 / interval_hours) * 365.0
    return FundingRecord(symbol=symbol, funding_time_ms=time_ms, funding_rate=rate, annualized_rate=annualized)


def _envelopes_from_duckdb(dataset: str, duckdb_path: str | Path) -> list[RawEnvelope]:
    db_path = Path(duckdb_path)
    if not db_path.exists():
        return []
    try:
        duckdb = DuckDBLayer(db_path)
        with duckdb.connect() as con:
            rows = con.execute(
                """
                SELECT source, endpoint, params_json, payload_json, ingested_at_ms, content_sha256
                FROM raw_envelopes
                WHERE dataset = ?
                ORDER BY ingested_at_ms, content_sha256
                """,
                [dataset],
            ).fetchall()
    except Exception:
        return []
    return [
        RawEnvelope(
            dataset=dataset,
            source=source,
            endpoint=endpoint,
            params=json.loads(params_json),
            payload=json.loads(payload_json),
            ingested_at_ms=int(ingested_at_ms),
            content_sha256=content_sha256,
        )
        for source, endpoint, params_json, payload_json, ingested_at_ms, content_sha256 in rows
    ]


def _load_envelopes(dataset: str, raw_root: str | Path, duckdb_path: str | Path) -> list[RawEnvelope]:
    envelopes = _envelopes_from_duckdb(dataset, duckdb_path)
    if envelopes:
        return envelopes
    root = Path(raw_root)
    if not (root / dataset).exists():
        return []
    return AppendOnlyRawStore(root).iter_envelopes(dataset)


def load_kline_bars(
    dataset: str,
    symbol: str,
    raw_root: str | Path = "storage/raw",
    duckdb_path: str | Path = "storage/duckdb/m0.duckdb",
    interval: str = "1d",
) -> list[TrendBar]:
    """Load a public M0 kline dataset without calling exchange APIs."""

    envelopes = _load_envelopes(dataset, raw_root, duckdb_path)
    bars_by_time: dict[int, TrendBar] = {}
    for envelope in envelopes:
        params = envelope.params
        envelope_symbol = str(params.get("symbol") or "").upper()
        envelope_interval = str(params.get("interval") or interval)
        if envelope_symbol != symbol.upper() or envelope_interval != interval:
            continue
        payload = envelope.payload if isinstance(envelope.payload, list) else []
        for raw_row in payload:
            bar = _normalize_kline(raw_row, symbol.upper())
            if bar is not None:
                bars_by_time.setdefault(bar.open_time_ms, bar)
    bars = [bars_by_time[key] for key in sorted(bars_by_time)]
    if not bars:
        raise M0DataUnavailableError(f"missing M0 {dataset} data for {symbol}; run M0 public backfill first")
    validate_bars(bars)
    return bars


def load_spot_bars(symbol: str, raw_root: str | Path = "storage/raw", duckdb_path: str | Path = "storage/duckdb/m0.duckdb") -> list[TrendBar]:
    return load_kline_bars("spot_klines", symbol, raw_root, duckdb_path)


def load_funding_history_dicts(
    symbol: str,
    raw_root: str | Path = "storage/raw",
    duckdb_path: str | Path = "storage/duckdb/m0.duckdb",
) -> list[dict[str, Any]]:
    """Load raw public funding-rate records as dicts for interval inference."""

    envelopes = _load_envelopes("funding_rate_history", raw_root, duckdb_path)
    raw_records: list[dict[str, Any]] = []
    for envelope in envelopes:
        params = envelope.params
        envelope_symbol = str(params.get("symbol") or "").upper()
        if envelope_symbol != symbol.upper():
            continue
        payload = envelope.payload if isinstance(envelope.payload, list) else []
        for row in payload:
            if isinstance(row, dict):
                raw_records.append(row)
    if not raw_records:
        raise M0DataUnavailableError(f"missing M0 funding_rate_history data for {symbol}; run M0 public backfill first")
    return sorted(raw_records, key=lambda row: int(row.get("fundingTime", 0)))


def load_funding_records(
    symbol: str,
    raw_root: str | Path = "storage/raw",
    duckdb_path: str | Path = "storage/duckdb/m0.duckdb",
) -> list[FundingRecord]:
    raw_records = load_funding_history_dicts(symbol, raw_root, duckdb_path)
    interval_hours = _funding_interval_hours(raw_records)
    records = [
        item
        for row in raw_records
        if (item := _normalize_funding(row, symbol.upper(), interval_hours)) is not None
    ]
    return sorted(records, key=lambda item: item.funding_time_ms)


def load_m1a_inputs(
    symbols: list[str],
    raw_root: str | Path = "storage/raw",
    duckdb_path: str | Path = "storage/duckdb/m0.duckdb",
) -> tuple[dict[str, list[TrendBar]], dict[str, list[FundingRecord]]]:
    bars = {symbol: load_spot_bars(symbol, raw_root, duckdb_path) for symbol in symbols}
    funding = {symbol: load_funding_records(symbol, raw_root, duckdb_path) for symbol in symbols}
    return bars, funding
