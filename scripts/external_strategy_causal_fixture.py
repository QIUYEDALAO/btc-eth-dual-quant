#!/usr/bin/env python3
"""Generate deterministic synthetic OHLCV used only by causal validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


def rows(
    count: int = 18000,
    price_scale: float = 1.0,
    trend_per_bar: float = 0.0,
) -> list[list[float | int]]:
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    result = []
    previous = 100.0
    for index in range(count):
        center = 100.0 + (trend_per_bar * index) + price_scale * (
            2.0 * math.sin(index / 37.0) + 0.8 * math.sin(index / 5.0)
        )
        open_price = previous
        close = center + price_scale * 0.2 * math.sin(index / 2.0)
        high = max(open_price, close) + price_scale * (
            0.15 + 0.2 * abs(math.sin(index / 11.0))
        )
        low = min(open_price, close) - price_scale * (
            0.15 + 0.2 * abs(math.cos(index / 13.0))
        )
        volume = 100.0 + 18.0 * math.sin(index / 17.0) + 8.0 * math.sin(index / 3.0)
        timestamp = int((start + timedelta(minutes=5 * index)).timestamp() * 1000)
        result.append([
            timestamp,
            round(open_price, 8),
            round(high, 8),
            round(low, 8),
            round(close, 8),
            round(volume, 8),
        ])
        previous = close
    return result


def aggregate(source: list[list[float | int]], width: int) -> list[list[float | int]]:
    if len(source) % width:
        source = source[: len(source) - (len(source) % width)]
    return [
        [
            block[0][0], block[0][1], max(row[2] for row in block),
            min(row[3] for row in block), block[-1][4],
            round(sum(float(row[5]) for row in block), 8),
        ]
        for offset in range(0, len(source), width)
        for block in [source[offset : offset + width]]
    ]


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = {
        "schema_version": "external-strategy-causal-fixture-v1",
        "market_data": False,
        "oos_data": False,
        "formula": "deterministic_multi_frequency_synthetic_ohlcv",
        "start_utc": "2023-01-01T00:00:00Z",
        "profiles": {},
    }
    profiles = {
        "default": (1.0, 0.0),
        "Supertrend": (1.0, 0.004),
        "UniversalMACD": (3.0, 0.0),
        "Heracles": (0.70, 0.0),
    }
    for profile, (price_scale, trend_per_bar) in profiles.items():
        destination = args.output / profile / "binance"
        destination.mkdir(parents=True, exist_ok=True)
        datasets = {"5m": rows(price_scale=price_scale, trend_per_bar=trend_per_bar)}
        datasets["15m"] = aggregate(datasets["5m"], 3)
        datasets["1h"] = aggregate(datasets["5m"], 12)
        datasets["4h"] = aggregate(datasets["5m"], 48)
        manifest["profiles"][profile] = {
            "price_scale": price_scale,
            "trend_per_bar": trend_per_bar,
            "timeframes": {},
        }
        for timeframe, values in datasets.items():
            payload = json.dumps(values, separators=(",", ":")) + "\n"
            path = destination / f"BTC_USDT-{timeframe}.json"
            path.write_text(payload, encoding="utf-8")
            manifest["profiles"][profile]["timeframes"][timeframe] = {
                "rows": len(values),
                "sha256": hashlib.sha256(payload.encode()).hexdigest(),
            }
    manifest["content_hash"] = digest(manifest)
    (args.output / "fixture_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    config = {
        "$schema": "https://schema.freqtrade.io/schema.json",
        "max_open_trades": 5,
        "stake_currency": "USDT",
        "stake_amount": 10000,
        "tradable_balance_ratio": 1.0,
        "dry_run_wallet": 100000,
        "dry_run": False,
        "trading_mode": "spot",
        "margin_mode": "",
        "exchange": {
            "name": "binance",
            "key": "",
            "secret": "",
            "ccxt_config": {"enableRateLimit": False},
            "ccxt_async_config": {"enableRateLimit": False},
            "pair_whitelist": ["BTC/USDT"],
            "pair_blacklist": [],
        },
        "pairlists": [{"method": "StaticPairList"}],
        "entry_pricing": {"price_side": "other", "use_order_book": False},
        "exit_pricing": {"price_side": "other", "use_order_book": False},
        "dataformat_ohlcv": "json",
        "dataformat_trades": "json",
    }
    (args.output / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(manifest["content_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
