#!/usr/bin/env python3
"""Build sanitized T1 evidence from official public Binance spot 1m data."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.minute_archive import (
    MINUTE_MS,
    MinuteArchiveManifest,
    analyze_month,
    compare_rest_sample,
    determine_research_start,
    deterministic_rest_sample_months,
    deterministic_rest_start_ms,
    month_bounds_ms,
    next_month,
    render_minute_archive_report,
)
from m0_dual_source_audit import (
    AppendOnlyRunStore,
    FetchResult,
    PublicFetcher,
    _combined_sha256,
    _daily_zip_url,
    _decode_array_rows,
    _decode_zip_rows,
    _rest_url,
    _sha256,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T1 canonical public spot 1m archive")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--start-month", default="2017-08")
    parser.add_argument("--end-month", default=None, help="Complete UTC month; defaults to previous month")
    parser.add_argument("--zip-base-url", default="https://data.binance.vision")
    parser.add_argument("--spot-base-url", default="https://data-api.binance.vision")
    parser.add_argument("--proxy-url", default=None, help="Approved unauthenticated loopback proxy for REST only")
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--random-rest-months", type=int, default=3)
    parser.add_argument("--raw-root", default="storage/raw/t1_minute_archive")
    parser.add_argument(
        "--reuse-run",
        default=None,
        help="Existing append-only run directory to re-evaluate without redownloading stored responses",
    )
    parser.add_argument("--manifest-out", default="storage/logs/t1_minute_archive_manifest.json")
    parser.add_argument("--report-path", default="reports/m0/T1_CANONICAL_MINUTE_DATA_REPORT.md")
    return parser.parse_args()


def month_range(start: str, end: str | None) -> list[str]:
    if end is None:
        today = datetime.now(timezone.utc).date()
        end = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    result: list[str] = []
    current = start
    while current <= end:
        result.append(current)
        current = next_month(current)
    if not result:
        raise ValueError("T1 range contains no complete month")
    return result


def days_in_month(month: str) -> list[str]:
    start_ms, end_ms = month_bounds_ms(month)
    current = datetime.fromtimestamp(start_ms / 1000, timezone.utc).date()
    end = datetime.fromtimestamp(end_ms / 1000, timezone.utc).date()
    result: list[str] = []
    while current < end:
        result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def missing_days(month: str, rows: list[dict], *, allow_inception_partial: bool = False) -> list[str]:
    start_ms, end_ms = month_bounds_ms(month)
    observed = {int(row["open_time"]) for row in rows if start_ms <= int(row["open_time"]) < end_ms}
    expected_start = min(observed) if allow_inception_partial and observed else start_ms
    days = {
        datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m-%d")
        for timestamp in range(expected_start, end_ms, MINUTE_MS)
        if timestamp not in observed
    }
    return sorted(days)


def fetch_daily_supplements(
    *,
    fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    zip_base_url: str,
    symbol: str,
    month: str,
    days: list[str],
    reuse_run: Path | None = None,
) -> tuple[list[dict], str, list[str]]:
    rows: list[dict] = []
    bodies: list[tuple[str, bytes]] = []
    failures: list[str] = []
    for day in days:
        stored = (
            reuse_run
            / "spot_klines_1m"
            / symbol
            / f"month={month}"
            / f"zip_daily_{day}"
            / "response-0000.zip"
            if reuse_run
            else None
        )
        result = (
            FetchResult(200, stored.read_bytes(), "none")
            if stored is not None and stored.is_file()
            else fetcher.get(_daily_zip_url(zip_base_url, "spot_klines", symbol, "1m", day))
        )
        if not result.ok:
            failures.append(f"{day}:{result.status or 'n/a'}:{result.error_category}")
            continue
        if stored is None or not stored.is_file():
            store.write("spot_klines_1m", symbol, month, f"zip_daily_{day}", 0, result.body)
        try:
            rows.extend(_decode_zip_rows(result.body, "spot_klines"))
        except Exception as exc:
            failures.append(f"{day}:parse:{type(exc).__name__}")
            continue
        bodies.append((day, result.body))
    return rows, _combined_sha256(bodies), failures


def fetch_rest_sample(
    *,
    fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    spot_base_url: str,
    symbol: str,
    month: str,
    reason: str,
    archive_rows: list[dict],
    reuse_run: Path | None = None,
):
    start_ms = deterministic_rest_start_ms(symbol, month)
    if archive_rows:
        first = min(int(row["open_time"]) for row in archive_rows)
        last = max(int(row["open_time"]) for row in archive_rows)
        latest_full_window = max(first, last - (999 * MINUTE_MS))
        start_ms = max(first, min(start_ms, latest_full_window))
    stored = (
        reuse_run / "spot_klines_1m" / symbol / f"month={month}" / "rest_sample" / "response-0000.json"
        if reuse_run
        else None
    )
    result = (
        FetchResult(200, stored.read_bytes(), "none")
        if stored is not None and stored.is_file()
        else fetcher.get(
            _rest_url(
                spot_base_url=spot_base_url,
                futures_base_url="https://fapi.binance.com",
                dataset="spot_klines",
                symbol=symbol,
                interval="1m",
                start_ms=start_ms,
                end_ms=start_ms + (999 * MINUTE_MS),
            )
        )
    )
    if not result.ok:
        return compare_rest_sample(
            month=month,
            reason=reason,
            start_ms=start_ms,
            archive_rows=[],
            rest_rows=[],
        )
    if stored is None or not stored.is_file():
        store.write("spot_klines_1m", symbol, month, "rest_sample", 0, result.body)
    try:
        payload = json.loads(result.body.decode("utf-8"))
        rest_rows = _decode_array_rows(payload, "spot_klines")
    except (UnicodeError, json.JSONDecodeError):
        rest_rows = []
    return compare_rest_sample(
        month=month,
        reason=reason,
        start_ms=start_ms,
        archive_rows=archive_rows,
        rest_rows=rest_rows,
    )


def main() -> int:
    args = parse_args()
    symbols = tuple(item.strip().upper() for item in args.symbols.split(",") if item.strip())
    if symbols != ("BTCUSDT", "ETHUSDT"):
        raise ValueError("T1 scope is fixed to BTCUSDT,ETHUSDT")
    months = month_range(args.start_month, args.end_month)
    reuse_run = Path(args.reuse_run) if args.reuse_run else None
    if reuse_run is not None:
        if not reuse_run.is_dir() or not reuse_run.name.startswith("run="):
            raise ValueError("--reuse-run must identify an existing run=<id> directory")
        run_id = reuse_run.name.removeprefix("run=")
        store = AppendOnlyRunStore(reuse_run.parent, run_id)
    else:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        store = AppendOnlyRunStore(args.raw_root, run_id)
    zip_fetcher = PublicFetcher(args.timeout_sec, args.retries)
    rest_fetcher = PublicFetcher(args.timeout_sec, args.retries, args.proxy_url)
    month_evidence = []
    rest_evidence = []

    for symbol in symbols:
        sample_plan = deterministic_rest_sample_months(months, symbol, args.random_rest_months)
        inception_seen = False
        for month in months:
            prior_inception_seen = inception_seen
            stored_monthly = (
                reuse_run
                / "spot_klines_1m"
                / symbol
                / f"month={month}"
                / "zip_monthly"
                / "response-0000.zip"
                if reuse_run
                else None
            )
            monthly_result = (
                FetchResult(200, stored_monthly.read_bytes(), "none")
                if stored_monthly is not None and stored_monthly.is_file()
                else zip_fetcher.get(
                    f"{args.zip_base_url.rstrip('/')}/data/spot/monthly/klines/{symbol}/1m/"
                    f"{symbol}-1m-{month}.zip"
                )
            )
            monthly_rows: list[dict] = []
            monthly_hash = ""
            if monthly_result.ok:
                if stored_monthly is None or not stored_monthly.is_file():
                    store.write("spot_klines_1m", symbol, month, "zip_monthly", 0, monthly_result.body)
                monthly_hash = _sha256(monthly_result.body)
                try:
                    monthly_rows = _decode_zip_rows(monthly_result.body, "spot_klines")
                except Exception:
                    monthly_rows = []
                inception_seen = inception_seen or bool(monthly_rows)

            is_inception_month = not prior_inception_seen and bool(monthly_rows)
            supplement_days = (
                missing_days(month, monthly_rows, allow_inception_partial=is_inception_month)
                if inception_seen
                else []
            )
            supplemental_rows, daily_hash, daily_failures = fetch_daily_supplements(
                fetcher=zip_fetcher,
                store=store,
                zip_base_url=args.zip_base_url,
                symbol=symbol,
                month=month,
                days=supplement_days,
                reuse_run=reuse_run,
            ) if supplement_days else ([], "", [])
            combined_rows = monthly_rows + supplemental_rows

            sample = None
            if month in sample_plan:
                sample = fetch_rest_sample(
                    fetcher=rest_fetcher,
                    store=store,
                    spot_base_url=args.spot_base_url,
                    symbol=symbol,
                    month=month,
                    reason="+".join(sample_plan[month]),
                    archive_rows=combined_rows,
                    reuse_run=reuse_run,
                )
                rest_evidence.append(sample)

            month_evidence.append(
                analyze_month(
                    symbol=symbol,
                    month=month,
                    monthly_rows=monthly_rows,
                    supplemental_rows=supplemental_rows,
                    monthly_zip_sha256=monthly_hash,
                    daily_bundle_sha256=daily_hash,
                    rest_evidence_complete=True,
                    rest_sampled=sample is not None,
                    rest_sample_passed=sample.passed if sample is not None else True,
                    pending_archive=False,
                    allow_inception_partial=is_inception_month,
                    daily_fetch_failures=len(daily_failures),
                )
            )
            print(
                f"{symbol} {month} rows={len(combined_rows)} daily_failures={len(daily_failures)} "
                f"rest={'pass' if sample and sample.passed else 'n/a' if sample is None else 'blocked'}"
            )

    rest_plan_complete = bool(rest_evidence) and all(item.passed for item in rest_evidence)
    if not rest_plan_complete:
        month_evidence = [
            replace(item, rest_evidence_complete=False, audit_state="blocked", qualifies=False)
            for item in month_evidence
        ]
    research_start = determine_research_start(month_evidence, symbols)
    start_ms, _ = month_bounds_ms(months[0])
    _, end_ms = month_bounds_ms(months[-1])
    manifest = MinuteArchiveManifest(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        requested_start=datetime.fromtimestamp(start_ms / 1000, timezone.utc).isoformat(),
        requested_end=datetime.fromtimestamp((end_ms - 1) / 1000, timezone.utc).isoformat(),
        symbols=symbols,
        months=tuple(month_evidence),
        rest_samples=tuple(rest_evidence),
        research_start=research_start,
    )
    manifest_path = Path(args.manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_minute_archive_report(manifest), encoding="utf-8")
    print(f"manifest={manifest_path}")
    print(f"report={report_path}")
    print(f"research_start={research_start or 'not_qualified'}")
    return 0 if research_start and rest_plan_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
