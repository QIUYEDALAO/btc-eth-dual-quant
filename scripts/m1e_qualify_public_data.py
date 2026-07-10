#!/usr/bin/env python3
"""Qualify official public BTC/ETH 5m, 1h, and 4h data for M1E."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.golden_data import FREQTRADE_IMAGE_REF, FREQTRADE_VERSION, parse_freqtrade_list_data, write_freqtrade_jsongz, write_jsonl_gz
from btc_eth_dual_quant.data.m1e_qualification import (
    INTERVAL_MS,
    LIQUIDITY_P95_MAXIMUM,
    aggregate_bars,
    compare_parity,
    determine_research_start,
    merge_archive_month,
    month_from_timestamp,
    qualify_pair_month,
)
from btc_eth_dual_quant.data.minute_archive import KLINE_FIELDS, month_bounds_ms, next_month
from m0_dual_source_audit import AppendOnlyRunStore, FetchResult, PublicFetcher, _decode_array_rows, _decode_zip_rows, _rest_url


SYMBOLS = ("BTCUSDT", "ETHUSDT")
TIMEFRAMES = ("5m", "1h", "4h")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M1E official public data qualification")
    parser.add_argument("--start-month", default="2020-01")
    parser.add_argument("--end-month", default=None)
    parser.add_argument("--zip-base-url", default="https://data.binance.vision")
    parser.add_argument("--spot-base-url", default="https://data-api.binance.vision")
    parser.add_argument("--proxy-url", default=None, help="Optional approved unauthenticated loopback proxy for REST evidence")
    parser.add_argument("--timeout-sec", type=int, default=45)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--raw-root", default="storage/raw/m1e_1h_qualification")
    parser.add_argument("--reuse-run", default=None)
    parser.add_argument("--derived-root", default="storage/duckdb/m1e_1h_qualification")
    parser.add_argument("--manifest-out", default="storage/logs/m1e_1h_data_manifest.json")
    parser.add_argument("--freqtrade-dir", default="freqtrade_lab/user_data/data/binance")
    parser.add_argument("--report-path", default="reports/m1/M1E_1H_DATA_QUALIFICATION_REPORT.md")
    parser.add_argument("--skip-runtime", action="store_true")
    parser.add_argument("--runtime-output", default=None, help="Ignored pinned-container list-data output from this cache")
    return parser.parse_args()


def month_range(start: str, end: str | None) -> list[str]:
    if end is None:
        previous = datetime.now(timezone.utc).date().replace(day=1) - timedelta(days=1)
        end = previous.strftime("%Y-%m")
    result: list[str] = []
    current = start
    while current <= end:
        result.append(current)
        current = next_month(current)
    if not result:
        raise ValueError("qualification contains no complete month")
    return result


def archive_url(base: str, symbol: str, timeframe: str, scope: str) -> str:
    cadence = "monthly" if len(scope) == 7 else "daily"
    return f"{base.rstrip('/')}/data/spot/{cadence}/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{scope}.zip"


def stored_path(run: Path, symbol: str, timeframe: str, month: str, source: str) -> Path:
    return run / f"spot_klines_{timeframe}" / symbol / f"month={month}" / source / "response-0000.zip"


def missing_days(month: str, timeframe: str, rows: list[dict]) -> list[str]:
    start_ms, end_ms = month_bounds_ms(month)
    observed = {int(row["open_time"]) for row in rows if start_ms <= int(row["open_time"]) < end_ms}
    days = {
        datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m-%d")
        for timestamp in range(start_ms, end_ms, INTERVAL_MS[timeframe])
        if timestamp not in observed
    }
    return sorted(days)


def fetch_or_reuse(
    *, fetcher: PublicFetcher, store: AppendOnlyRunStore, reuse: Path | None,
    symbol: str, timeframe: str, month: str, source: str, url: str,
) -> FetchResult:
    stored = stored_path(reuse, symbol, timeframe, month, source) if reuse else None
    if stored is not None and stored.is_file():
        return FetchResult(200, stored.read_bytes(), "none")
    result = fetcher.get(url)
    if result.ok:
        store.write(f"spot_klines_{timeframe}", symbol, month, source, 0, result.body)
    return result


def runtime_check(data_dir: Path, expected: dict[tuple[str, str], tuple[str, str, int]], skip: bool, runtime_output: str | None) -> dict:
    if skip:
        return {"status": "not_run", "note": "explicitly skipped", "entries": []}
    command = [
        "docker", "run", "--rm", "-v", f"{data_dir.resolve()}:/freqtrade/user_data/data/binance:ro",
        FREQTRADE_IMAGE_REF, "list-data", "--datadir", "/freqtrade/user_data/data/binance",
        "--data-format-ohlcv", "jsongz", "--show-timerange", "--no-color",
    ]
    try:
        if runtime_output:
            output = Path(runtime_output).read_text(encoding="utf-8")
            returncode = 0
        else:
            completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300, check=False)
            output = completed.stdout
            returncode = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "fail", "note": type(exc).__name__, "entries": []}
    entries = [asdict(item) for item in parse_freqtrade_list_data(output)]
    actual = {(item["pair"], item["timeframe"]): (item["start"], item["end"], item["rows"]) for item in entries}
    passed = returncode == 0 and FREQTRADE_VERSION in output and actual == expected
    return {
        "status": "pass" if passed else "fail", "note": "pinned list-data exact range and rows" if passed else "runtime output mismatch",
        "image_ref": FREQTRADE_IMAGE_REF, "version": FREQTRADE_VERSION, "command": "list-data",
        "execution_location": "external_public_runtime" if runtime_output else "local",
        "entries": entries, "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def rest_sample_months(months: list[str]) -> list[str]:
    selected = {months[0], months[len(months) // 2], months[-1]}
    selected.update(month for month in ("2020-03", "2021-05", "2022-11") if month in months)
    return sorted(selected)


def compare_rest_sample(fetcher: PublicFetcher, base_url: str, symbol: str, month: str, official: list[dict]) -> dict:
    by_time = {int(row["open_time"]): row for row in official}
    available = sorted(by_time)
    if not available:
        return {"symbol": symbol, "month": month, "status": "blocked", "overlap": 0, "differences": 0}
    sample_start = available[len(available) // 2]
    url = _rest_url(
        spot_base_url=base_url, futures_base_url="https://fapi.binance.com",
        dataset="spot_klines", symbol=symbol, interval="1h", start_ms=sample_start,
        end_ms=sample_start + 499 * INTERVAL_MS["1h"],
    )
    result = fetcher.get(url)
    if not result.ok:
        return {"symbol": symbol, "month": month, "status": "blocked", "overlap": 0, "differences": 0, "error": result.error_category}
    try:
        rest_rows = _decode_array_rows(json.loads(result.body.decode()), "spot_klines")
    except Exception:
        rest_rows = []
    rest = {int(row["open_time"]): row for row in rest_rows}
    overlap = sorted(set(rest) & set(by_time))
    differences = sum(
        Decimal(str(rest[timestamp][field])) != Decimal(str(by_time[timestamp][field]))
        for timestamp in overlap for field in KLINE_FIELDS
    )
    return {
        "symbol": symbol, "month": month, "status": "pass" if overlap and not differences else "blocked",
        "overlap": len(overlap), "differences": differences,
        "archive_sha256": hashlib.sha256(json.dumps([by_time[t] for t in overlap], sort_keys=True, default=str).encode()).hexdigest() if overlap else "",
        "rest_sha256": hashlib.sha256(json.dumps([rest[t] for t in overlap], sort_keys=True, default=str).encode()).hexdigest() if overlap else "",
    }


def render_report(manifest: dict) -> str:
    statuses = {state: sum(item["state"] == state for item in manifest["months"]) for state in ("audit_complete", "audit_complete_with_confirmed_outage", "blocked")}
    lines = [
        "# M1E 1H Data Qualification Report", "",
        f"- Status: {manifest['status']}",
        "- Scope: public-data qualification only",
        f"- Qualification range: {manifest['range_start']} through {manifest['range_end']}",
        f"- Research start: {manifest['research_start'] or 'not_qualified'}",
        f"- Manifest SHA256: `{manifest['manifest_sha256']}`",
        "- Candidate evaluated: no", "- OOS prices/returns accessed: no", "- Strategy code authorized: no",
        "- Freqtrade backtesting run: no", "- API key used: no", "- Private data used: no",
        "- Runtime artifacts committed: no", "- M2 authorized: no", "",
        "## Data Summary", "",
        "| Symbol | Timeframe | Rows | Canonical SHA256 |", "| --- | --- | ---: | --- |",
    ]
    for item in manifest["datasets"]:
        lines.append(f"| {item['symbol']} | {item['timeframe']} | {item['rows']} | `{item['sha256']}` |")
    lines += [
        "", "## Month Qualification", "",
        f"- audit_complete: {statuses['audit_complete']}",
        f"- audit_complete_with_confirmed_outage: {statuses['audit_complete_with_confirmed_outage']}",
        f"- blocked: {statuses['blocked']}",
        f"- Confirmed outage 5m rows: {sum(item['confirmed_outage_rows'] for item in manifest['months'])}",
        f"- Isolated 1h buckets: {sum(item['isolated_1h_buckets'] for item in manifest['months'])}",
        f"- Isolated 4h buckets: {sum(item['isolated_4h_buckets'] for item in manifest['months'])}",
        f"- Quarantine SHA256: `{manifest['quarantine_sha256']}`",
        f"- Official monthly ZIP payload hashes: {len(manifest['source_hashes'])}",
        f"- Public fetch failures: {len(manifest['fetch_failures'])}",
        "- Confirmed outages are not filled or tradable; future rolling windows must fully rewarm.",
        "", "### Blocking Months In The Contract Research Range", "",
        "| Month | Reasons |", "| --- | --- |",
        "", "## Aggregate Parity", "",
        "| Timeframe | Overlap | Numeric differences | Format-only fields | Unexplained timestamps | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for timeframe in ("1h", "4h"):
        rows = [item for item in manifest["parity"] if item["timeframe"] == timeframe]
        unexplained = sum(item["unexplained_timestamps"] for item in rows)
        numeric = sum(item["numeric_differences"] for item in rows)
        lines.append(f"| {timeframe} | {sum(item['overlap_rows'] for item in rows)} | {numeric} | {sum(item['format_only_fields'] for item in rows)} | {unexplained} | {'pass' if not numeric and not unexplained else 'blocked'} |")
    rest = manifest["rest_evidence"]
    blocked_range = [item for item in manifest["months"] if manifest["research_start"] and item["month"] >= manifest["research_start"][:7] and item["state"] == "blocked"]
    if blocked_range:
        lines.extend(f"| {item['month']} | {', '.join(item['blockers'])} |" for item in blocked_range)
    else:
        lines.append("| none | none |")
    lines += [
        "", "## REST Evidence", "",
        f"- Samples: {len(rest)}", f"- Overlap rows: {sum(item['overlap'] for item in rest)}",
        f"- Field differences: {sum(item['differences'] for item in rest)}",
        f"- Status: {'pass' if rest and all(item['status'] == 'pass' for item in rest) else 'blocked'}",
        "- REST is compare-only and never overwrites ZIP data.",
        "", "## Liquidity And Runtime", "",
        f"- Fixed monthly 1m p95 spread-proxy maximum: {manifest['liquidity_threshold']}",
        f"- Qualified common six-month window: {manifest['qualified_window'] or 'none'}",
        f"- Freqtrade image: `{FREQTRADE_IMAGE_REF}`",
        f"- Freqtrade list-data: {manifest['freqtrade_runtime']['status']}",
        f"- Runtime evidence location: {manifest['freqtrade_runtime'].get('execution_location', 'not_run')}",
        "- Freqtrade operation: list-data only; no strategy or backtesting command was run.",
        "", "## Gate", "",
        f"- Public ZIP qualification: {'pass' if manifest['status'] == 'pass' else 'blocked'}",
        f"- Official 1h/4h numeric differences zero outside isolated outages: {'pass' if manifest['parity_pass'] else 'blocked'}",
        f"- Freqtrade cache readable: {manifest['freqtrade_runtime']['status']}",
        f"- Sample-budget stage authorized: {'yes' if manifest['status'] == 'pass' else 'no'}",
        "- Strategy code authorized: no", "- Candidate OOS returns authorized: no", "- M2 authorized: no", "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.start_month != "2020-01":
        raise ValueError("M1E start month is fixed to 2020-01")
    months = month_range(args.start_month, args.end_month)
    reuse = Path(args.reuse_run) if args.reuse_run else None
    if reuse and (not reuse.is_dir() or not reuse.name.startswith("run=")):
        raise ValueError("--reuse-run must be an append-only run directory")
    run_id = reuse.name.removeprefix("run=") if reuse else datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = AppendOnlyRunStore(reuse.parent if reuse else args.raw_root, run_id)
    fetcher = PublicFetcher(args.timeout_sec, args.retries)
    archive_bodies: dict[tuple[str, str, str], bytes] = {}
    fetch_failures: list[str] = []

    def fetch_month(key: tuple[str, str, str]) -> tuple[tuple[str, str, str], FetchResult]:
        symbol, timeframe, month = key
        return key, fetch_or_reuse(fetcher=fetcher, store=store, reuse=reuse, symbol=symbol, timeframe=timeframe, month=month, source="zip_monthly", url=archive_url(args.zip_base_url, symbol, timeframe, month))

    keys = [(symbol, timeframe, month) for symbol in SYMBOLS for timeframe in TIMEFRAMES for month in months]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(fetch_month, key) for key in keys]
        for future in as_completed(futures):
            key, result = future.result()
            if result.ok:
                archive_bodies[key] = result.body
            else:
                fetch_failures.append(":".join(key) + ":monthly:" + result.error_category)

    archives = {}
    source_hashes = []
    for symbol, timeframe, month in keys:
        body = archive_bodies.get((symbol, timeframe, month), b"")
        try:
            monthly_rows = _decode_zip_rows(body, "spot_klines") if body else []
        except Exception:
            monthly_rows = []
            fetch_failures.append(f"{symbol}:{timeframe}:{month}:monthly_parse")
        daily_rows: list[dict] = []
        daily_hashes: list[str] = []
        for day in missing_days(month, timeframe, monthly_rows):
            source = f"zip_daily_{day}"
            result = fetch_or_reuse(fetcher=fetcher, store=store, reuse=reuse, symbol=symbol, timeframe=timeframe, month=month, source=source, url=archive_url(args.zip_base_url, symbol, timeframe, day))
            if not result.ok:
                fetch_failures.append(f"{symbol}:{timeframe}:{day}:daily:{result.error_category}")
                continue
            try:
                daily_rows.extend(_decode_zip_rows(result.body, "spot_klines"))
                daily_hashes.append(hashlib.sha256(result.body).hexdigest())
            except Exception:
                fetch_failures.append(f"{symbol}:{timeframe}:{day}:daily_parse")
        archive = merge_archive_month(symbol=symbol, month=month, timeframe=timeframe, monthly_rows=monthly_rows, daily_rows=daily_rows)
        archives[(symbol, timeframe, month)] = archive
        source_hashes.append({
            "symbol": symbol, "timeframe": timeframe, "month": month,
            "monthly_sha256": hashlib.sha256(body).hexdigest() if body else "",
            "daily_bundle_sha256": hashlib.sha256("\n".join(sorted(daily_hashes)).encode()).hexdigest() if daily_hashes else "",
        })

    qualifications = []
    parity_items = []
    isolated = {symbol: {timeframe: set() for timeframe in TIMEFRAMES} for symbol in SYMBOLS}
    for month in months:
        month_archives = {(symbol, timeframe): archives[(symbol, timeframe, month)] for symbol in SYMBOLS for timeframe in TIMEFRAMES}
        p1 = {}
        p4 = {}
        for symbol in SYMBOLS:
            derived1 = aggregate_bars(month_archives[(symbol, "5m")].rows, "5m", "1h", month)
            derived4 = aggregate_bars(derived1.rows, "1h", "4h", month)
            p1[symbol] = compare_parity(symbol=symbol, month=month, timeframe="1h", derived=derived1.rows, official=month_archives[(symbol, "1h")].rows)
            p4[symbol] = compare_parity(symbol=symbol, month=month, timeframe="4h", derived=derived4.rows, official=month_archives[(symbol, "4h")].rows)
        qualification = qualify_pair_month(month=month, archives=month_archives, one_hour_parity=p1, four_hour_parity=p4)
        qualifications.append(qualification)
        for symbol in SYMBOLS:
            isolated[symbol]["5m"].update(qualification.confirmed_outage_5m)
            isolated[symbol]["1h"].update(qualification.isolated_1h_buckets)
            isolated[symbol]["4h"].update(qualification.isolated_4h_buckets)
            for evidence, buckets in ((p1[symbol], set(qualification.isolated_1h_buckets)), (p4[symbol], set(qualification.isolated_4h_buckets))):
                item = asdict(evidence)
                item["unexplained_timestamps"] = len((set(evidence.derived_only) | set(evidence.official_only)) - buckets)
                parity_items.append(item)

    t1_manifest = json.loads((ROOT / "storage/logs/t1_minute_archive_manifest.json").read_text(encoding="utf-8"))
    liquidity = {(item["symbol"], item["month"]): Decimal(item["p95_spread_proxy"]) for item in t1_manifest["months"]}
    research_start = determine_research_start(qualifications, liquidity)
    research_month = research_start[:7] if research_start else None
    research_qualifications = [item for item in qualifications if research_month and item.month >= research_month]

    derived_root = Path(args.derived_root)
    cache_root = Path(args.freqtrade_dir)
    datasets = []
    expected_runtime = {}
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            rows = [
                row for month in months if research_month and month >= research_month
                for row in archives[(symbol, timeframe, month)].rows
                if int(row["open_time"]) not in isolated[symbol][timeframe]
            ]
            sha = write_jsonl_gz(derived_root / f"{symbol}-{timeframe}.jsonl.gz", rows)
            write_freqtrade_jsongz(cache_root / f"{symbol.replace('USDT', '_USDT')}-{timeframe}.json.gz", rows)
            datasets.append({"symbol": symbol, "timeframe": timeframe, "rows": len(rows), "sha256": sha})
            if rows:
                expected_runtime[(symbol.replace("USDT", "/USDT"), timeframe)] = (
                    datetime.fromtimestamp(int(rows[0]["open_time"]) / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.fromtimestamp(int(rows[-1]["open_time"]) / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), len(rows),
                )

    runtime = runtime_check(cache_root, expected_runtime, args.skip_runtime, args.runtime_output)
    rest_fetcher = PublicFetcher(args.timeout_sec, args.retries, args.proxy_url)
    rest_evidence = []
    for symbol in SYMBOLS:
        for month in rest_sample_months([item.month for item in research_qualifications]):
            rest_evidence.append(compare_rest_sample(rest_fetcher, args.spot_base_url, symbol, month, list(archives[(symbol, "1h", month)].rows)))

    parity_pass = all(not item["numeric_differences"] and not item["unexplained_timestamps"] for item in parity_items)
    no_blocked_month = bool(research_qualifications) and all(item.state != "blocked" for item in research_qualifications)
    rest_pass = bool(rest_evidence) and all(item["status"] == "pass" for item in rest_evidence)
    passed = bool(research_start) and no_blocked_month and parity_pass and rest_pass and runtime["status"] == "pass" and not fetch_failures
    qualified_window = None
    if research_start:
        research_index = months.index(research_month)
        window = months[research_index - 6:research_index]
        qualified_window = f"{window[0]} through {window[-1]}" if len(window) == 6 else None
    manifest = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "pass" if passed else "blocked",
        "range_start": f"{months[0]}-01", "range_end": datetime.fromtimestamp(month_bounds_ms(months[-1])[1] / 1000 - 0.001, timezone.utc).isoformat(),
        "research_start": research_start, "qualified_window": qualified_window, "liquidity_threshold": str(LIQUIDITY_P95_MAXIMUM),
        "months": [{"month": item.month, "state": item.state, "confirmed_outage_rows": len(item.confirmed_outage_5m), "isolated_1h_buckets": len(item.isolated_1h_buckets), "isolated_4h_buckets": len(item.isolated_4h_buckets), "blockers": list(item.blockers)} for item in qualifications],
        "datasets": datasets, "parity": parity_items, "parity_pass": parity_pass, "rest_evidence": rest_evidence,
        "source_hashes": source_hashes, "fetch_failures": sorted(fetch_failures), "freqtrade_runtime": runtime,
        "api_key_used": False, "private_data_used": False, "candidate_evaluated": False, "oos_accessed": False,
        "strategy_returns_computed": False, "runtime_artifacts_committed": False,
    }
    quarantine_rows = [
        {
            "month": item.month, "state": item.state, "confirmed_outage_5m": list(item.confirmed_outage_5m),
            "isolated_1h": list(item.isolated_1h_buckets), "isolated_4h": list(item.isolated_4h_buckets),
            "blockers": list(item.blockers),
        }
        for item in qualifications if item.state != "audit_complete"
    ]
    manifest["quarantine_sha256"] = write_jsonl_gz(Path(args.derived_root) / "quarantine.jsonl.gz", quarantine_rows)
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    manifest_path = Path(args.manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    report = Path(args.report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(manifest), encoding="utf-8")
    print(f"run={store.root}")
    print(f"manifest={manifest_path}")
    print(f"report={report}")
    print(f"status={manifest['status']} research_start={research_start or 'none'} blockers={len(fetch_failures) + sum(item.state == 'blocked' for item in research_qualifications)}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
