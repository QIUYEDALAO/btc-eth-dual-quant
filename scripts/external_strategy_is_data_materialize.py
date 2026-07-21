#!/usr/bin/env python3
"""Materialize hash-bound, OOS-sealed Freqtrade IS data from frozen V4 ZIPs."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
START_MS = 1577836800000  # 2020-01-01
IS_END_MS = 1726012800000  # 2024-09-11, exclusive
WIDTHS = {"5m": 1, "15m": 3, "1h": 12, "4h": 48}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: dict[str, Any]) -> str:
    clone = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    raw = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def month_start(value: str) -> datetime:
    return datetime.strptime(value[:7], "%Y-%m").replace(tzinfo=timezone.utc)


def next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1)
    return value.replace(month=value.month + 1)


def merge_months(months: list[str]) -> list[dict[str, str]]:
    ordered = sorted({month[:7] for month in months})
    if not ordered:
        return []
    intervals = []
    start = previous = month_start(ordered[0])
    for text in ordered[1:]:
        current = month_start(text)
        if current != next_month(previous):
            intervals.append((start, next_month(previous)))
            start = current
        previous = current
    intervals.append((start, next_month(previous)))
    return [
        {
            "start_inclusive": max(start_value, datetime.fromtimestamp(START_MS / 1000, timezone.utc)).isoformat().replace("+00:00", "Z"),
            "end_exclusive": min(end_value, datetime.fromtimestamp(IS_END_MS / 1000, timezone.utc)).isoformat().replace("+00:00", "Z"),
        }
        for start_value, end_value in intervals
        if start_value.timestamp() * 1000 < IS_END_MS and end_value.timestamp() * 1000 > START_MS
    ]


def read_archive(path: Path, masked: set[int]) -> list[list[float | int]]:
    values: list[list[float | int]] = []
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"archive member count invalid: {path}")
        with archive.open(members[0]) as raw:
            for binary in raw:
                first = binary.partition(b",")[0]
                try:
                    open_ms = int(first)
                except ValueError:
                    if first.lower().startswith(b"open_time"):
                        continue
                    raise ValueError(f"invalid timestamp field: {path}")
                if open_ms >= IS_END_MS:
                    break
                if open_ms < START_MS or open_ms in masked:
                    continue
                row = next(csv.reader(io.StringIO(binary.decode("utf-8-sig"))))
                if len(row) < 7:
                    raise ValueError(f"short kline row: {path}")
                close_ms = int(row[6])
                if open_ms % 300000 or close_ms != open_ms + 299999:
                    raise ValueError(f"unmasked invalid 5m boundary: {path}:{open_ms}")
                open_price, high, low, close, volume = map(float, row[1:6])
                if low > min(open_price, close) or high < max(open_price, close) or volume < 0:
                    raise ValueError(f"invalid OHLCV: {path}:{open_ms}")
                values.append([open_ms, open_price, high, low, close, volume])
    return values


def aggregate(rows: list[list[float | int]], width: int) -> list[list[float | int]]:
    if width == 1:
        return rows
    step = width * 300000
    buckets: dict[int, list[list[float | int]]] = defaultdict(list)
    for row in rows:
        buckets[int(row[0]) // step * step].append(row)
    result = []
    for key in sorted(buckets):
        block = sorted(buckets[key], key=lambda row: int(row[0]))
        expected = [key + offset * 300000 for offset in range(width)]
        if [int(row[0]) for row in block] != expected:
            continue
        result.append([
            key, block[0][1], max(float(row[2]) for row in block),
            min(float(row[3]) for row in block), block[-1][4],
            sum(float(row[5]) for row in block),
        ])
    return result


def write_gzip_json(path: Path, rows: list[list[float | int]]) -> None:
    payload = (json.dumps(rows, separators=(",", ":")) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(payload)


def market(symbol: str) -> dict[str, Any]:
    pair = f"{symbol[:-4]}/USDT"
    return {
        "id": symbol, "symbol": pair, "base": symbol[:-4], "quote": "USDT", "settle": None,
        "type": "spot", "spot": True, "margin": False, "swap": False, "future": False,
        "option": False, "active": True, "contract": False, "linear": None, "info": {},
        "precision": {"amount": 0.00000001, "price": 0.00000001, "base": None, "quote": None},
        "limits": {
            "amount": {"min": 0.00000001, "max": None},
            "price": {"min": 0.00000001, "max": None},
            "cost": {"min": 0.01, "max": None},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_freeze_path = ROOT / "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json"
    membership_path = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/membership_manifest.json"
    mask_path = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/invalid_interval_slot_mask_manifest.json"
    source = json.loads(source_freeze_path.read_text())
    membership = json.loads(membership_path.read_text())
    masks = json.loads(mask_path.read_text())
    frozen = {row["canonical_key"]: row for row in source["content"]["archives"]}
    membership_rows = [
        row for row in membership["content"]
        if "2020-01" <= row["effective_month"][:7] <= "2024-09"
        and row.get("eligibility_status") == "qualified"
    ]
    symbols = sorted({row["symbol"] for row in membership_rows})
    active_months: dict[str, list[str]] = defaultdict(list)
    for row in membership_rows:
        active_months[row["symbol"]].append(row["effective_month"][:7])
    masked_by_symbol: dict[str, set[int]] = defaultdict(set)
    for row in masks["content"]:
        if int(row["open_time_ms"]) < IS_END_MS:
            masked_by_symbol[row["symbol"]].add(int(row["open_time_ms"]))

    output_data = args.output / "data/binance"
    file_rows = []
    archive_rows = []
    for symbol in symbols:
        combined: dict[int, list[float | int]] = {}
        for month in sorted(set(active_months[symbol])):
            relative = f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip"
            expected = frozen.get(relative)
            path = args.raw_root / relative
            if expected is None or not path.is_file():
                raise SystemExit(f"active frozen archive missing: {relative}")
            if path.stat().st_size != expected["byte_size"] or sha256_file(path) != expected["sha256"]:
                raise SystemExit(f"active archive identity drift: {relative}")
            rows = read_archive(path, masked_by_symbol[symbol])
            for row in rows:
                timestamp = int(row[0])
                if timestamp in combined and combined[timestamp] != row:
                    raise SystemExit(f"conflicting active row: {symbol}:{timestamp}")
                combined[timestamp] = row
            archive_rows.append({"path": relative, "sha256": expected["sha256"], "size": expected["byte_size"]})
        ordered = [combined[key] for key in sorted(combined)]
        pair_file = symbol[:-4] + "_USDT"
        for timeframe, width in WIDTHS.items():
            derived = aggregate(ordered, width)
            path = output_data / f"{pair_file}-{timeframe}.json.gz"
            write_gzip_json(path, derived)
            file_rows.append({
                "symbol": symbol, "timeframe": timeframe, "rows": len(derived),
                "path": str(path.relative_to(args.output)), "sha256": sha256_file(path),
            })

    authority = {
        "schema_version": "external-strategy-is-membership-authority-v1",
        "is_start": "2020-01-01T00:00:00Z",
        "evaluated_is_start": "2020-07-01T00:00:00Z",
        "is_end_exclusive": "2024-09-11T00:00:00Z",
        "oos_rows_decoded": 0,
        "membership_manifest_byte_sha256": sha256_file(membership_path),
        "membership_manifest_hash": membership["content_hash"],
        "invalid_interval_mask_byte_sha256": sha256_file(mask_path),
        "invalid_interval_mask_hash": masks["content_hash"],
        "pairs": {
            f"{symbol[:-4]}/USDT": {"active_intervals": merge_months(active_months[symbol])}
            for symbol in symbols
        },
    }
    authority["content_hash"] = canonical_hash(authority)
    authority_path = args.output / "authority/membership_authority.json"
    authority_path.parent.mkdir(parents=True, exist_ok=True)
    authority_path.write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n")
    markets = {f"{symbol[:-4]}/USDT": market(symbol) for symbol in symbols}
    markets_path = args.output / "authority/offline_markets_is.json"
    markets_path.write_text(json.dumps(markets, indent=2, sort_keys=True) + "\n")
    config = {
        "$schema": "https://schema.freqtrade.io/schema.json",
        "max_open_trades": 5, "stake_currency": "USDT", "stake_amount": 10000,
        "tradable_balance_ratio": 1.0, "dry_run_wallet": 100000, "dry_run": False,
        "trading_mode": "spot", "margin_mode": "",
        "exchange": {
            "name": "binance", "key": "", "secret": "",
            "ccxt_config": {"enableRateLimit": False},
            "ccxt_async_config": {"enableRateLimit": False},
            "pair_whitelist": sorted(markets), "pair_blacklist": [],
        },
        "pairlists": [{"method": "StaticPairList"}],
        "entry_pricing": {"price_side": "other", "use_order_book": False},
        "exit_pricing": {"price_side": "other", "use_order_book": False},
        "dataformat_ohlcv": "jsongz", "dataformat_trades": "json",
    }
    (args.output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    manifest = {
        "schema_version": "external-strategy-is-data-materialization-v1",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "pass",
        "data_authority_hash": "a6e613140b4daf60ac3f8da51ccbcbc9db8118f80bc575f6e10dcf124d5faa4a",
        "source_freeze_hash": source["content_hash"],
        "membership_authority_hash": authority["content_hash"],
        "offline_markets_sha256": sha256_file(markets_path),
        "symbol_count": len(symbols),
        "archives": sorted(archive_rows, key=lambda item: item["path"]),
        "files": sorted(file_rows, key=lambda item: (item["symbol"], item["timeframe"])),
        "market_rows_decoded": sum(row["rows"] for row in file_rows if row["timeframe"] == "5m"),
        "oos_rows_decoded": 0,
    }
    manifest["content_hash"] = canonical_hash(manifest)
    (args.output / "data_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"IS data PASS: symbols={len(symbols)} archives={len(archive_rows)} hash={manifest['content_hash']} oos=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
