#!/usr/bin/env python3
"""Build T2 golden 1m data, deterministic derivatives, and sanitized evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.golden_data import (
    FREQTRADE_IMAGE_REF,
    aggregate_klines,
    build_golden_month,
    compare_official_klines,
    quarantine_sha256,
    write_freqtrade_jsongz,
    write_jsonl_gz,
    validate_freqtrade_runtime_evidence,
)
from btc_eth_dual_quant.data.minute_archive import next_month
from m0_dual_source_audit import AppendOnlyRunStore, PublicFetcher, _decode_zip_rows


IMAGE_REF = FREQTRADE_IMAGE_REF


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T2 golden public data builder")
    parser.add_argument("--t1-run", required=True)
    parser.add_argument("--t1-manifest", default="storage/logs/t1_minute_archive_manifest.json")
    parser.add_argument("--research-start", default="2023-10-01")
    parser.add_argument("--zip-base-url", default="https://data.binance.vision")
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--derived-root", default="storage/duckdb/t2_golden")
    parser.add_argument("--raw-root", default="storage/raw/t2_official_15m")
    parser.add_argument("--freqtrade-dir", default="freqtrade_lab/user_data/data/binance")
    parser.add_argument("--manifest-out", default="storage/logs/t2_golden_manifest.json")
    parser.add_argument("--runtime-evidence", default=None)
    parser.add_argument("--report-path", default="reports/m0/T2_GOLDEN_DATA_AND_QUARANTINE_REPORT.md")
    return parser.parse_args()


def month_range(start: str, end: str) -> list[str]:
    result: list[str] = []
    current = start
    while current <= end:
        result.append(current)
        current = next_month(current)
    return result


def load_t1_month(run: Path, symbol: str, month: str) -> tuple[list[dict], list[dict]]:
    root = run / "spot_klines_1m" / symbol / f"month={month}"
    monthly_path = root / "zip_monthly" / "response-0000.zip"
    monthly = _decode_zip_rows(monthly_path.read_bytes(), "spot_klines") if monthly_path.is_file() else []
    daily: list[dict] = []
    for path in sorted(root.glob("zip_daily_*/response-0000.zip")):
        daily.extend(_decode_zip_rows(path.read_bytes(), "spot_klines"))
    return monthly, daily


def render_report(manifest: dict) -> str:
    comparisons = manifest["official_15m_comparisons"]
    runtime = manifest["freqtrade_runtime"]
    research_blockers = manifest["research_blockers"]
    passed = not research_blockers and comparisons and all(item["passed"] for item in comparisons) and runtime["status"] == "pass"
    lines = [
        "# T2 Golden Data and Quarantine Report",
        "",
        f"- Status: {'pass' if passed else 'blocked'}",
        "- Scope: golden 1m, deterministic 5m/15m, official 15m parity, and Freqtrade cache validation only",
        "- API key used: no",
        "- Private data used: no",
        "- Strategy returns computed: no",
        "- Runtime artifacts committed: no",
        f"- Research range: {manifest['research_start']} through {manifest['research_end']}",
        f"- Manifest SHA256: `{manifest['manifest_sha256']}`",
        "",
        "## Golden and Derived Data",
        "",
        "| Symbol | 1m rows | 1m hash | 5m rows | 5m hash | 15m rows | 15m hash | Incomplete 5m | Incomplete 15m |",
        "| --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: |",
    ]
    for item in manifest["symbols"]:
        lines.append(
            f"| {item['symbol']} | {item['rows_1m']} | `{item['hash_1m']}` | {item['rows_5m']} | `{item['hash_5m']}` "
            f"| {item['rows_15m']} | `{item['hash_15m']}` | {item['incomplete_5m']} | {item['incomplete_15m']} |"
        )
    lines.extend(
        [
            "",
            "## Quarantine",
            "",
            f"- Pre-start quarantined symbol-months: {manifest['pre_start_quarantined_months']}",
            f"- Quarantine records: {manifest['quarantine_records']}",
            f"- Quarantine SHA256: `{manifest['quarantine_sha256']}`",
            "- Monthly ZIP rows are never overwritten; daily ZIP rows only fill absent valid minute timestamps.",
            "",
            "## Official 15m Parity",
            "",
            "| Symbol | Months | Overlap | Numeric differences | Derived-only | Official-only | Invalid official | Format-only | Official ZIP bundle hash | Status |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for symbol in ("BTCUSDT", "ETHUSDT"):
        selected = [item for item in comparisons if item["symbol"] == symbol]
        bundle_payload = "\n".join(
            f"{item['month']}:{item['official_payload_sha256']}" for item in sorted(selected, key=lambda row: row["month"])
        )
        bundle_hash = hashlib.sha256(bundle_payload.encode("ascii")).hexdigest() if selected else ""
        lines.append(
            f"| {symbol} | {len(selected)} | {sum(item['overlap_rows'] for item in selected)} "
            f"| {sum(item['numeric_differences'] for item in selected)} | {sum(item['derived_only_rows'] for item in selected)} "
            f"| {sum(item['official_only_rows'] for item in selected)} | {sum(item['invalid_official_rows'] for item in selected)} "
            f"| {sum(item['format_only_fields'] for item in selected)} | `{bundle_hash}` | "
            f"{'pass' if selected and all(item['passed'] for item in selected) else 'blocked'} |"
        )
    lines.extend(
        [
            "",
            "## Freqtrade Cache",
            "",
            f"- Image: `{runtime['image_ref']}`",
            "- Data format: jsongz",
            "- Command: `freqtrade list-data --show-timerange --data-format-ohlcv jsongz`",
            f"- Runtime status: {runtime['status']}",
            f"- Runtime note: {runtime['note']}",
            "",
            "## Gate",
            "",
            f"- Research-range golden 1m complete: {'pass' if not research_blockers else 'blocked'}",
            f"- Deterministic 5m/15m complete: {'pass' if all(not item['incomplete_5m'] and not item['incomplete_15m'] for item in manifest['symbols']) else 'blocked'}",
            f"- Official 15m numeric differences zero: {'pass' if comparisons and all(item['passed'] for item in comparisons) else 'blocked'}",
            f"- Quarantine traceable by hash: {'pass' if manifest['quarantine_sha256'] else 'blocked'}",
            f"- Freqtrade list-data: {runtime['status']}",
            f"- T3 authorized: {'yes' if passed else 'no'}",
            "- M1D strategy code authorized: no",
            "- M2 authorized: no",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    t1_run = Path(args.t1_run)
    if not t1_run.is_dir() or not t1_run.name.startswith("run="):
        raise ValueError("--t1-run must identify the append-only T1 run directory")
    t1_manifest = json.loads(Path(args.t1_manifest).read_text(encoding="utf-8"))
    if t1_manifest.get("research_start") != args.research_start:
        raise ValueError("research start does not match frozen T1 evidence")
    end_month = t1_manifest["requested_end"][:7]
    research_month = args.research_start[:7]
    months = month_range(research_month, end_month)
    symbols = ("BTCUSDT", "ETHUSDT")
    derived_root = Path(args.derived_root)
    freqtrade_dir = Path(args.freqtrade_dir)
    quarantine_records = []
    research_blockers: list[str] = []
    symbol_summaries = []
    all_derived_15m: dict[str, list[dict]] = {}

    # Preserve detailed evidence for every pre-start month already quarantined by T1.
    blocked_pre_start = [
        item for item in t1_manifest["months"]
        if item["month"] < research_month and item["audit_state"] != "audit_complete"
    ]
    for item in blocked_pre_start:
        monthly, daily = load_t1_month(t1_run, item["symbol"], item["month"])
        result = build_golden_month(
            symbol=item["symbol"], month=item["month"], monthly_rows=monthly, daily_rows=daily
        )
        quarantine_records.extend(result.quarantine)

    for symbol in symbols:
        golden_rows: list[dict] = []
        for month in months:
            monthly, daily = load_t1_month(t1_run, symbol, month)
            result = build_golden_month(symbol=symbol, month=month, monthly_rows=monthly, daily_rows=daily)
            if result.state != "audit_complete":
                research_blockers.append(f"{symbol}:{month}:{result.state}")
            quarantine_records.extend(result.quarantine)
            golden_rows.extend(result.rows)
        derived_5m = aggregate_klines(golden_rows, "5m")
        derived_15m = aggregate_klines(golden_rows, "15m")
        all_derived_15m[symbol] = list(derived_15m.rows)
        golden_hash = write_jsonl_gz(derived_root / f"{symbol}-1m.jsonl.gz", golden_rows)
        write_jsonl_gz(derived_root / f"{symbol}-5m.jsonl.gz", derived_5m.rows)
        write_jsonl_gz(derived_root / f"{symbol}-15m.jsonl.gz", derived_15m.rows)
        cache_hashes = {
            interval: write_freqtrade_jsongz(
                freqtrade_dir / f"{symbol.replace('USDT', '_USDT')}-{interval}.json.gz",
                rows,
            )
            for interval, rows in (
                ("1m", golden_rows), ("5m", derived_5m.rows), ("15m", derived_15m.rows)
            )
        }
        symbol_summaries.append(
            {
                "symbol": symbol,
                "rows_1m": len(golden_rows),
                "hash_1m": golden_hash,
                "rows_5m": len(derived_5m.rows),
                "hash_5m": derived_5m.canonical_sha256,
                "rows_15m": len(derived_15m.rows),
                "hash_15m": derived_15m.canonical_sha256,
                "incomplete_5m": len(derived_5m.incomplete_buckets),
                "incomplete_15m": len(derived_15m.incomplete_buckets),
                "freqtrade_cache_hashes": cache_hashes,
            }
        )

    quarantine_path = derived_root / "quarantine.jsonl.gz"
    write_jsonl_gz(
        quarantine_path,
        (asdict(item) | {"open_time": item.open_time if item.open_time is not None else -1} for item in quarantine_records),
    )

    fetcher = PublicFetcher(args.timeout_sec, args.retries)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = AppendOnlyRunStore(args.raw_root, run_id)
    comparisons = []
    for symbol in symbols:
        by_month: dict[str, list[dict]] = {month: [] for month in months}
        for row in all_derived_15m[symbol]:
            month = datetime.fromtimestamp(int(row["open_time"]) / 1000, timezone.utc).strftime("%Y-%m")
            if month in by_month:
                by_month[month].append(row)
        for month in months:
            url = (
                f"{args.zip_base_url.rstrip('/')}/data/spot/monthly/klines/{symbol}/15m/"
                f"{symbol}-15m-{month}.zip"
            )
            response = fetcher.get(url)
            if not response.ok:
                research_blockers.append(f"{symbol}:{month}:official_15m_{response.error_category}")
                continue
            store.write("spot_klines_15m", symbol, month, "zip_monthly", 0, response.body)
            official = _decode_zip_rows(response.body, "spot_klines")
            comparison = asdict(
                compare_official_klines(
                    symbol=symbol, month=month, derived_rows=by_month[month], official_rows=official
                )
            )
            comparison["official_payload_sha256"] = hashlib.sha256(response.body).hexdigest()
            comparisons.append(comparison)

    runtime = {"status": "not_run", "note": "pinned Freqtrade list-data evidence not supplied", "image_ref": IMAGE_REF}
    if args.runtime_evidence:
        supplied = json.loads(Path(args.runtime_evidence).read_text(encoding="utf-8"))
        expected_runtime = {}
        start_label = datetime.fromisoformat(f"{args.research_start}T00:00:00+00:00").strftime("%Y-%m-%d %H:%M:%S")
        end_ms = int(datetime.fromisoformat(t1_manifest["requested_end"]).timestamp() * 1000)
        for summary in symbol_summaries:
            pair = summary["symbol"].replace("USDT", "/USDT")
            for timeframe, minutes, rows_key in (("1m", 1, "rows_1m"), ("5m", 5, "rows_5m"), ("15m", 15, "rows_15m")):
                interval_ms = minutes * 60_000
                final_open_ms = end_ms - (end_ms % interval_ms)
                end_label = datetime.fromtimestamp(final_open_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                expected_runtime[(pair, timeframe)] = (start_label, end_label, int(summary[rows_key]))
        if not validate_freqtrade_runtime_evidence(supplied, expected_runtime):
            raise ValueError("invalid or unsafe Freqtrade runtime evidence")
        runtime = {
            "status": str(supplied.get("status", "fail")),
            "note": str(supplied.get("note", "Pinned container validated all six cache entries.")),
            "image_ref": IMAGE_REF,
        }

    manifest = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "research_start": args.research_start,
        "research_end": t1_manifest["requested_end"],
        "symbols": symbol_summaries,
        "pre_start_quarantined_months": len(blocked_pre_start),
        "quarantine_records": len(quarantine_records),
        "quarantine_sha256": quarantine_sha256(quarantine_records),
        "research_blockers": research_blockers,
        "official_15m_comparisons": comparisons,
        "freqtrade_runtime": runtime,
        "api_key_used": False,
        "private_data_used": False,
        "runtime_artifacts_committed": False,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    manifest_path = Path(args.manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(manifest), encoding="utf-8")
    print(f"manifest={manifest_path}")
    print(f"report={report_path}")
    print(f"research_blockers={len(research_blockers)}")
    print(f"runtime_status={runtime['status']}")
    return 0 if not research_blockers and comparisons and all(item["passed"] for item in comparisons) and runtime["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
