#!/usr/bin/env python3
"""Review M0 K-line anomalies against raw lineage and ZIP source data."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.duckdb_layer import DuckDBLayer
from btc_eth_dual_quant.data.quality import flag_kline_anomalies
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore, RawEnvelope
from m0_report import parse_report


KLINE_DATASETS = {
    "spot_klines": ("spot", "klines"),
    "um_futures_klines": ("futures/um", "klines"),
    "mark_price_klines": ("futures/um", "markPriceKlines"),
    "index_price_klines": ("futures/um", "indexPriceKlines"),
    "premium_index_klines": ("futures/um", "premiumIndexKlines"),
}


@dataclass(frozen=True)
class ReviewedAnomaly:
    dataset: str
    symbol: str
    open_time_utc: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    amplitude: str
    reason: str
    rest_payload_hash: str
    zip_available: bool
    zip_rest_consistent: str
    classification: str
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review M0 K-line anomalies")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--public-report", default="reports/m0/M0_PUBLIC_RUN_REPORT.md")
    parser.add_argument("--output", default="reports/m0/M0_ANOMALY_REVIEW.md")
    parser.add_argument("--timeout-sec", type=int, default=20)
    parser.add_argument("--proxy", default=None, help="Optional proxy URL, e.g. http://127.0.0.1:7897")
    return parser.parse_args()


def utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def utc_day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def normalize_kline_row(row: Any) -> dict[str, Any] | None:
    if isinstance(row, dict):
        try:
            return {
                "open_time": int(row["open_time"]),
                "open": str(row["open"]),
                "high": str(row["high"]),
                "low": str(row["low"]),
                "close": str(row["close"]),
                "volume": str(row.get("volume", "0")),
                "close_time": int(row.get("close_time", row["open_time"])),
                "quote_volume": str(row.get("quote_volume", "0")),
            }
        except (KeyError, TypeError, ValueError):
            return None
    if isinstance(row, list) and len(row) >= 5:
        try:
            return {
                "open_time": int(row[0]),
                "open": str(row[1]),
                "high": str(row[2]),
                "low": str(row[3]),
                "close": str(row[4]),
                "volume": str(row[5]) if len(row) > 5 else "0",
                "close_time": int(row[6]) if len(row) > 6 else int(row[0]),
                "quote_volume": str(row[7]) if len(row) > 7 else "0",
            }
        except (TypeError, ValueError):
            return None
    return None


def anomaly_check_row(dataset: str, row: dict[str, Any]) -> dict[str, Any]:
    if dataset == "premium_index_klines":
        return {**row, "open": row["high"], "low": row["high"], "volume": "1"}
    if dataset in {"mark_price_klines", "index_price_klines"}:
        return {**row, "volume": "1"}
    return row


def amplitude(row: dict[str, Any]) -> Decimal:
    open_price = Decimal(str(row["open"]))
    high = Decimal(str(row["high"]))
    low = Decimal(str(row["low"]))
    return (high - low) / max(abs(open_price), Decimal("1e-18"))


def market_fields_valid(dataset: str, row: dict[str, Any]) -> bool:
    open_price = Decimal(str(row["open"]))
    high = Decimal(str(row["high"]))
    low = Decimal(str(row["low"]))
    close = Decimal(str(row["close"]))
    volume = Decimal(str(row.get("volume", "0")))
    if high < max(open_price, close) or low > min(open_price, close) or high < low:
        return False
    if dataset not in {"mark_price_klines", "index_price_klines", "premium_index_klines"} and volume <= 0:
        return False
    return True


def load_envelopes(dataset: str, raw_root: str, duckdb_path: str) -> list[RawEnvelope]:
    try:
        duckdb = DuckDBLayer(duckdb_path)
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
        if rows:
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
    except Exception:
        pass
    return AppendOnlyRawStore(raw_root).iter_envelopes(dataset)


def zip_url(dataset: str, symbol: str, interval: str, day: str) -> str:
    scope, kind = KLINE_DATASETS[dataset]
    return (
        "https://data.binance.vision/"
        f"data/{scope}/daily/{kind}/{symbol}/{interval}/{symbol}-{interval}-{day}.zip"
    )


def csv_rows_from_zip(url: str, timeout_sec: int) -> list[list[str]]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout_sec) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [name for name in zf.namelist() if name.endswith(".csv")]
        if not names:
            raise ValueError(f"ZIP has no CSV file: {url}")
        with zf.open(names[0]) as fh:
            rows = list(csv.reader(io.TextIOWrapper(fh, encoding="utf-8")))
    if rows and rows[0] and rows[0][0] in {"open_time", "Open time"}:
        rows = rows[1:]
    return rows


def fetch_zip_row(dataset: str, symbol: str, interval: str, open_time_ms: int, timeout_sec: int) -> dict[str, Any] | None:
    url = zip_url(dataset, symbol, interval, utc_day(open_time_ms))
    try:
        rows = csv_rows_from_zip(url, timeout_sec)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    for row in rows:
        normalized = normalize_kline_row(row)
        if normalized and int(normalized["open_time"]) == open_time_ms:
            return normalized
    return None


def rows_consistent(rest_row: dict[str, Any], zip_row: dict[str, Any], dataset: str) -> bool:
    fields = ("open", "high", "low", "close")
    if dataset not in {"mark_price_klines", "index_price_klines", "premium_index_klines"}:
        fields = (*fields, "volume")
    for field in fields:
        if Decimal(str(rest_row[field])) != Decimal(str(zip_row[field])):
            return False
    return True


def review_anomaly(
    dataset: str,
    symbol: str,
    interval: str,
    row: dict[str, Any],
    reason: str,
    rest_payload_hash: str,
    timeout_sec: int,
    zip_fetcher: Callable[[str, str, str, int, int], dict[str, Any] | None] = fetch_zip_row,
) -> ReviewedAnomaly:
    if not market_fields_valid(dataset, row):
        return ReviewedAnomaly(
            dataset=dataset,
            symbol=symbol,
            open_time_utc=utc_iso(int(row["open_time"])),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
            amplitude=f"{amplitude(row):.8f}",
            reason=reason,
            rest_payload_hash=rest_payload_hash,
            zip_available=False,
            zip_rest_consistent="not_checked",
            classification="bad_data",
            note="OHLC ordering or volume sanity check failed before ZIP comparison.",
        )

    zip_row = zip_fetcher(dataset, symbol, interval, int(row["open_time"]), timeout_sec)
    if zip_row is None:
        classification = "unresolved"
        consistent = "not_available"
        note = "ZIP counterpart is unavailable, so the REST anomaly is not cross-source confirmed."
        zip_available = False
    else:
        zip_available = True
        is_consistent = rows_consistent(row, zip_row, dataset)
        consistent = "yes" if is_consistent else "no"
        if is_consistent:
            classification = "explained_market_move"
            note = "ZIP source matches REST; OHLC ordering and volume checks pass; retained as extreme market move."
        else:
            classification = "unresolved"
            note = "ZIP source differs from REST for at least one comparable OHLCV field."

    return ReviewedAnomaly(
        dataset=dataset,
        symbol=symbol,
        open_time_utc=utc_iso(int(row["open_time"])),
        open=row["open"],
        high=row["high"],
        low=row["low"],
        close=row["close"],
        volume=row["volume"],
        amplitude=f"{amplitude(row):.8f}",
        reason=reason,
        rest_payload_hash=rest_payload_hash,
        zip_available=zip_available,
        zip_rest_consistent=consistent,
        classification=classification,
        note=note,
    )


def collect_reviewed_anomalies(
    public_report_path: str | Path,
    raw_root: str,
    duckdb_path: str,
    timeout_sec: int,
    zip_fetcher: Callable[[str, str, str, int, int], dict[str, Any] | None] = fetch_zip_row,
) -> list[ReviewedAnomaly]:
    report = parse_report(public_report_path)
    requested = {
        dataset.name
        for dataset in report.datasets
        if dataset.kline_anomalies > 0 and ":" in dataset.name and dataset.name.split(":", 1)[0] in KLINE_DATASETS
    }
    reviewed: dict[tuple[str, str, int, str], ReviewedAnomaly] = {}
    for full_name in sorted(requested):
        dataset, symbol = full_name.split(":", 1)
        for envelope in load_envelopes(dataset, raw_root, duckdb_path):
            params = envelope.params
            envelope_symbol = str(params.get("symbol") or params.get("pair") or "").upper()
            interval = str(params.get("interval") or "1d")
            if envelope_symbol != symbol:
                continue
            payload = envelope.payload if isinstance(envelope.payload, list) else []
            for raw_row in payload:
                row = normalize_kline_row(raw_row)
                if row is None:
                    continue
                anomalies = flag_kline_anomalies([anomaly_check_row(dataset, row)])
                for anomaly in anomalies:
                    key = (dataset, symbol, anomaly.open_time, anomaly.reason)
                    if key not in reviewed:
                        reviewed[key] = review_anomaly(
                            dataset,
                            symbol,
                            interval,
                            row,
                            anomaly.reason,
                            envelope.content_sha256,
                            timeout_sec,
                            zip_fetcher=zip_fetcher,
                        )
    return [reviewed[key] for key in sorted(reviewed)]


def render_review(items: list[ReviewedAnomaly]) -> str:
    generated = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# M0 Anomaly Review",
        "",
        f"Generated UTC: {generated}",
        "",
        "## Summary",
        "",
    ]
    counts: dict[str, int] = {}
    for item in items:
        counts[item.classification] = counts.get(item.classification, 0) + 1
    if counts:
        lines.extend(f"- {key}: {counts[key]}" for key in sorted(counts))
    else:
        lines.append("- no_kline_anomalies")
    lines.extend(
        [
            "",
            "## Details",
            "",
            "| Dataset | Symbol | Open Time UTC | Open | High | Low | Close | Volume | Amplitude | Reason | REST Payload Hash | ZIP Available | ZIP/REST Consistent | Classification | Note |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|",
        ]
    )
    for item in items:
        lines.append(
            f"| `{item.dataset}` | `{item.symbol}` | `{item.open_time_utc}` | {item.open} | {item.high} | "
            f"{item.low} | {item.close} | {item.volume} | {item.amplitude} | `{item.reason}` | "
            f"`{item.rest_payload_hash}` | {'yes' if item.zip_available else 'no'} | {item.zip_rest_consistent} | "
            f"`{item.classification}` | {item.note} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_review(items: list[ReviewedAnomaly], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_review(items), encoding="utf-8")
    return output


def main() -> int:
    args = parse_args()
    if args.proxy:
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ.setdefault("ALL_PROXY", args.proxy)
    items = collect_reviewed_anomalies(args.public_report, args.raw_root, args.duckdb_path, args.timeout_sec)
    write_review(items, args.output)
    unresolved = sum(1 for item in items if item.classification == "unresolved")
    print(f"Wrote anomaly review: {args.output}")
    print(f"reviewed={len(items)} unresolved={unresolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
