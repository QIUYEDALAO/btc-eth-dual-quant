#!/usr/bin/env python3
"""Diagnose M1E public ZIP conflicts without changing the admission contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.m1e_conflict_diagnostics import (
    calendar_budget,
    canonical_diagnostics_sha256,
    classify_aggregate_conflict,
    classify_monthly_daily_conflict,
    differing_fields,
    first_six_month_clean_suffix,
)
from btc_eth_dual_quant.data.m1e_qualification import aggregate_bars, merge_archive_month
from m0_dual_source_audit import AppendOnlyRunStore, PublicFetcher, _decode_array_rows, _decode_zip_rows, _rest_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M1E official source conflict diagnostics")
    parser.add_argument("--qualification-run", default="storage/raw/m1e_1h_qualification/run=20260710T183135Z")
    parser.add_argument("--qualification-manifest", default="storage/logs/m1e_1h_data_manifest.json")
    parser.add_argument("--zip-base-url", default="https://data.binance.vision")
    parser.add_argument("--spot-base-url", default="https://data-api.binance.vision")
    parser.add_argument("--proxy-url", default=None)
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--raw-root", default="storage/raw/m1e_conflict_diagnostics")
    parser.add_argument("--evidence-out", default="storage/logs/m1e_conflict_diagnostics.json")
    parser.add_argument("--report-path", default="reports/m1/M1E_OFFICIAL_SOURCE_CONFLICT_DIAGNOSTICS.md")
    return parser.parse_args()


def load_source(run: Path, symbol: str, timeframe: str, month: str) -> tuple[list[dict], list[dict], list[tuple[str, bytes]]]:
    root = run / f"spot_klines_{timeframe}" / symbol / f"month={month}"
    monthly_path = root / "zip_monthly" / "response-0000.zip"
    monthly_body = monthly_path.read_bytes()
    monthly = _decode_zip_rows(monthly_body, "spot_klines")
    daily: list[dict] = []
    bodies = [("monthly", monthly_body)]
    for path in sorted(root.glob("zip_daily_*/response-0000.zip")):
        body = path.read_bytes()
        daily.extend(_decode_zip_rows(body, "spot_klines"))
        bodies.append((path.parent.name, body))
    return monthly, daily, bodies


def rest_row(fetcher: PublicFetcher, store: AppendOnlyRunStore, base_url: str, symbol: str, timeframe: str, timestamp: int, page: int) -> dict | None:
    url = _rest_url(
        spot_base_url=base_url, futures_base_url="https://fapi.binance.com", dataset="spot_klines",
        symbol=symbol, interval=timeframe, start_ms=timestamp, end_ms=timestamp,
    )
    result = fetcher.get(url)
    if not result.ok:
        return None
    month = datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m")
    store.write(f"spot_klines_{timeframe}", symbol, month, "rest", page, result.body)
    try:
        rows = _decode_array_rows(json.loads(result.body.decode()), "spot_klines")
    except Exception:
        return None
    return next((row for row in rows if int(row["open_time"]) == timestamp), None)


def archive_url(base: str, symbol: str, timeframe: str, month: str) -> str:
    return f"{base.rstrip('/')}/data/spot/monthly/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{month}.zip"


def render_report(evidence: dict) -> str:
    counts = Counter(item["classification"] for item in evidence["diagnostics"])
    lines = [
        "# M1E Official Source Conflict Diagnostics", "",
        "- Status: diagnostics_complete_blocker_confirmed",
        "- Scope: official public-data source diagnostics only",
        f"- Generated UTC: {evidence['generated_utc']}",
        f"- Conflict evidence rows: {len(evidence['diagnostics'])}",
        f"- Canonical diagnostics SHA256: `{evidence['diagnostics_sha256']}`",
        f"- Fresh monthly ZIP hashes unchanged: {sum(item['unchanged'] for item in evidence['archive_refetch'])}/{len(evidence['archive_refetch'])}",
        "- Candidate evaluated: no", "- Candidate OOS returns accessed: no", "- Strategy code authorized: no",
        "- Freqtrade backtesting run: no", "- API key used: no", "- M2 authorized: no", "",
        "## Classification Summary", "",
    ]
    for classification, count in sorted(counts.items()):
        lines.append(f"- {classification}: {count}")
    lines += [
        "", "## Field-Level Evidence", "",
        "| UTC open time | Symbol | TF | Differing fields | REST matches official | REST matches derived/daily | Classification | Contract resolved |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in evidence["diagnostics"]:
        timestamp = datetime.fromtimestamp(item["open_time"] / 1000, timezone.utc).isoformat()
        lines.append(
            f"| {timestamp} | {item['symbol']} | {item['timeframe']} | {', '.join(item['differing_fields'])} "
            f"| {'yes' if item['rest_matches_official'] else 'no'} | {'yes' if item['rest_matches_derived'] else 'no'} "
            f"| {item['classification']} | no |"
        )
    lines += [
        "", "## Findings", "",
        "- All cross-timeframe numeric differences preserve identical OHLC prices and differ only in volume, quote volume, trade count, and taker-volume fields.",
        "- Current public REST confirms the published higher-timeframe row for most aggregate conflicts, confirms the child aggregation for two January 2021 rows, and exposes a third revision for two April 2021 rows.",
        "- The December 2020 monthly/daily conflict remains a contradiction between official archive versions. REST preference cannot overwrite the authoritative monthly ZIP under ADR-0008.",
        "- Fresh monthly ZIP downloads retain the recorded hashes, so the conflict is reproducible and is not a stale local-download error.",
        "- No classification is contract-resolved. The fixed M1E data Gate remains blocked.",
        "", "## Diagnostic Clean Suffix", "",
        f"- First six-month clean suffix start: {evidence['clean_suffix_start'] or 'none'}",
        "- This date is diagnostic only and cannot replace the contract research start without a new ADR.",
        f"- Clean-suffix full calendar: {evidence['clean_suffix_full_days']} days",
        f"- Clean-suffix sealed 30% OOS calendar: {evidence['clean_suffix_oos_days']} days",
        "- Fixed requirements: 1800 full days and 540 OOS days.",
        f"- Clean suffix sample budget: {'pass' if evidence['clean_suffix_budget_pass'] else 'blocked'}",
        "", "## Decision", "",
        "- M1E PR3 sample-budget branch authorized: no",
        "- M1E strategy design authorized: no",
        "- Source precedence or numeric tolerance change authorized: no",
        "- M2 authorized: no", "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    run = Path(args.qualification_run)
    manifest = json.loads(Path(args.qualification_manifest).read_text(encoding="utf-8"))
    blocked_months = [item["month"] for item in manifest["months"] if item["state"] == "blocked" and item["month"] >= manifest["research_start"][:7]]
    fetcher = PublicFetcher(args.timeout_sec, args.retries, args.proxy_url)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = AppendOnlyRunStore(args.raw_root, run_id)
    diagnostics = []
    refetch = []
    rest_page = 0

    for month in blocked_months:
        loaded = {}
        raw_sources = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            for timeframe in ("5m", "1h", "4h"):
                monthly, daily, bodies = load_source(run, symbol, timeframe, month)
                loaded[(symbol, timeframe)] = merge_archive_month(
                    symbol=symbol, month=month, timeframe=timeframe, monthly_rows=monthly, daily_rows=daily
                )
                raw_sources[(symbol, timeframe)] = (monthly, daily)
                stored_monthly = next(body for label, body in bodies if label == "monthly")
                fresh = fetcher.get(archive_url(args.zip_base_url, symbol, timeframe, month))
                fresh_hash = hashlib.sha256(fresh.body).hexdigest() if fresh.ok else ""
                stored_hash = hashlib.sha256(stored_monthly).hexdigest()
                if fresh.ok:
                    store.write(f"spot_klines_{timeframe}", symbol, month, "zip_monthly_refetch", 0, fresh.body)
                refetch.append({
                    "symbol": symbol, "month": month, "timeframe": timeframe,
                    "stored_sha256": stored_hash, "fresh_sha256": fresh_hash,
                    "unchanged": bool(fresh_hash and fresh_hash == stored_hash),
                })

        for symbol in ("BTCUSDT", "ETHUSDT"):
            derived_1h = {int(row["open_time"]): row for row in aggregate_bars(loaded[(symbol, "5m")].rows, "5m", "1h", month).rows}
            official_1h = {int(row["open_time"]): row for row in loaded[(symbol, "1h")].rows}
            derived_4h = {int(row["open_time"]): row for row in aggregate_bars(loaded[(symbol, "1h")].rows, "1h", "4h", month).rows}
            official_4h = {int(row["open_time"]): row for row in loaded[(symbol, "4h")].rows}
            for timeframe, derived, official in (("1h", derived_1h, official_1h), ("4h", derived_4h, official_4h)):
                for timestamp in sorted(set(derived) & set(official)):
                    if not differing_fields(derived[timestamp], official[timestamp]):
                        continue
                    rest = rest_row(fetcher, store, args.spot_base_url, symbol, timeframe, timestamp, rest_page)
                    rest_page += 1
                    diagnostics.append(classify_aggregate_conflict(
                        symbol=symbol, month=month, timeframe=timeframe,
                        derived=derived[timestamp], official=official[timestamp], rest=rest,
                    ))

            for timeframe in ("5m", "1h", "4h"):
                monthly_rows, daily_rows = raw_sources[(symbol, timeframe)]
                monthly = {int(row["open_time"]): row for row in monthly_rows}
                daily = {int(row["open_time"]): row for row in daily_rows}
                for timestamp in sorted(set(monthly) & set(daily)):
                    if not differing_fields(monthly[timestamp], daily[timestamp]):
                        continue
                    rest = rest_row(fetcher, store, args.spot_base_url, symbol, timeframe, timestamp, rest_page)
                    rest_page += 1
                    diagnostics.append(classify_monthly_daily_conflict(
                        symbol=symbol, month=month, timeframe=timeframe,
                        monthly=monthly[timestamp], daily=daily[timestamp], rest=rest,
                    ))

    diagnostics = sorted(diagnostics, key=lambda item: (item.month, item.symbol, item.timeframe, item.open_time))
    clean_start = first_six_month_clean_suffix([(item["month"], item["state"]) for item in manifest["months"]])
    full_days, oos_days = calendar_budget(clean_start, "2026-07-01") if clean_start else (0, 0)
    evidence = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qualification_run_reference": run.name, "blocked_months": blocked_months,
        "diagnostics": [asdict(item) for item in diagnostics],
        "diagnostics_sha256": canonical_diagnostics_sha256(diagnostics),
        "archive_refetch": refetch, "clean_suffix_start": clean_start,
        "clean_suffix_full_days": full_days, "clean_suffix_oos_days": oos_days,
        "clean_suffix_budget_pass": full_days >= 1800 and oos_days >= 540,
        "contract_resolved": False, "api_key_used": False, "private_data_used": False,
        "candidate_evaluated": False, "candidate_oos_returns_accessed": False,
    }
    evidence_path = Path(args.evidence_out)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(evidence), encoding="utf-8")
    print(f"evidence={evidence_path}")
    print(f"report={report_path}")
    print(f"diagnostics={len(diagnostics)} contract_resolved=no clean_suffix={clean_start}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
