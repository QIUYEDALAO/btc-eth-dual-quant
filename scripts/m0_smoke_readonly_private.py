#!/usr/bin/env python3
"""M0 private read-only smoke test.

Requires a Binance API key with no trading permission. The script only calls
read-only commission and funding-income endpoints.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.binance import BinanceReadOnlyCollector, BinanceReadOnlyRestClient
from btc_eth_dual_quant.data.costs import parse_futures_commission, parse_spot_commission
from btc_eth_dual_quant.data.duckdb_layer import DuckDBLayer
from btc_eth_dual_quant.data.registry import load_registry
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore
from m0_report import DatasetRun, M0RunReport, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M0 private read-only smoke test")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT", help="Comma-separated symbols")
    parser.add_argument("--income-limit", type=int, default=100)
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--duckdb-path", default="storage/duckdb/m0.duckdb")
    parser.add_argument("--report-path", default="reports/m0/M0_DATA_RUN_REPORT.md")
    parser.add_argument("--proxy", default=None, help="Optional proxy URL, e.g. http://127.0.0.1:7897")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without signed calls")
    return parser.parse_args()


def _require_read_only_ack() -> None:
    if os.environ.get("BINANCE_M0_READ_ONLY_ACK") != "1":
        raise SystemExit(
            "Refusing private smoke without BINANCE_M0_READ_ONLY_ACK=1. "
            "Use an API key with read-only access and no spot/futures trading permission."
        )


def _missing_fields(payload: Any, fields: list[str]) -> list[str]:
    if not isinstance(payload, dict):
        return fields
    missing: list[str] = []
    for field in fields:
        if field in {"maker", "taker", "discount", "commissionAsset"}:
            continue
        if field not in payload:
            missing.append(field)
    return missing


def main() -> int:
    args = parse_args()
    if args.proxy:
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ.setdefault("ALL_PROXY", args.proxy)
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    if args.dry_run:
        print("M0 private smoke dry-run")
        print("requires=BINANCE_API_KEY,BINANCE_API_SECRET,BINANCE_M0_READ_ONLY_ACK=1")
        print("endpoints=GET /api/v3/account/commission, GET /fapi/v1/commissionRate, GET /fapi/v1/income")
        return 0

    _require_read_only_ack()
    registry = load_registry(ROOT / "data_registry.yaml")
    commission_record = registry.by_name("commissions")
    income_record = registry.by_name("funding_income")
    store = AppendOnlyRawStore(args.raw_root)
    collector = BinanceReadOnlyCollector(BinanceReadOnlyRestClient(), store)
    runs: list[DatasetRun] = []
    private_lines: list[str] = []

    for symbol in symbols:
        spot_env = collector.spot_account_commission(commission_record, symbol)
        futures_env = collector.futures_commission_rate(commission_record, symbol)
        spot_rate = parse_spot_commission(spot_env.payload)
        futures_rate = parse_futures_commission(futures_env.payload)
        private_lines.append(f"{symbol} spot commission taker={spot_rate.taker} maker={spot_rate.maker}")
        private_lines.append(f"{symbol} futures commission taker={futures_rate.taker} maker={futures_rate.maker}")

    income_env = collector.funding_income(income_record, limit=args.income_limit)
    income_payload = income_env.payload if isinstance(income_env.payload, list) else []
    income_missing = []
    for row in income_payload:
        income_missing.extend(_missing_fields(row, income_record.fields))
    income_status = "pass" if not income_missing else f"missing_fields={sorted(set(income_missing))}"
    runs.append(
        DatasetRun(
            name="funding_income",
            interval="income_event",
            rows=len(income_payload),
            archive_status=income_status,
            commission_status="not_applicable",
            unexplained=[] if not income_missing else [income_status],
        )
    )
    runs.append(
        DatasetRun(
            name="commissions",
            interval="symbol_snapshot",
            rows=len(symbols) * 2,
            commission_status="pass",
        )
    )

    duckdb = DuckDBLayer(args.duckdb_path)
    duckdb.index_from_store(store, "funding_income")
    duckdb.index_from_store(store, "commissions")
    write_report(
        M0RunReport(
            data_start="private_smoke",
            data_end="private_smoke",
            datasets=runs,
            private_smoke=private_lines,
        ),
        args.report_path,
    )
    print(f"Wrote report: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
