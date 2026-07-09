#!/usr/bin/env python3
"""Revalidate M0 public-data audit evidence without private API access."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btc_eth_dual_quant.data.funding import infer_funding_interval_hours
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore
from m0_report import DatasetRun, M0RunReport
from m0_report_merge import _combine_public_reports


SYMBOLS = ("BTCUSDT", "ETHUSDT")
KLINE_DATASETS = (
    "spot_klines",
    "um_futures_klines",
    "mark_price_klines",
    "index_price_klines",
    "premium_index_klines",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate M0 1h public audit evidence")
    parser.add_argument("--public", action="append", required=True, help="M0 public report path")
    parser.add_argument("--raw-root", default="storage/raw")
    parser.add_argument("--out", default="reports/m0/M0_AUDIT_REVALIDATION_REPORT.md")
    return parser.parse_args()


def _valid_hash(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def _dataset_checks(dataset: DatasetRun) -> list[tuple[str, bool, str]]:
    checks = [
        ("1h interval", dataset.interval == "1h", dataset.interval),
        ("rows present", dataset.rows > 0, str(dataset.rows)),
        ("no gaps", dataset.gaps == 0, str(dataset.gaps)),
        ("ZIP/REST fields equal", dataset.zip_rest_differences == 0, str(dataset.zip_rest_differences)),
        (
            "ZIP/REST overlap present",
            isinstance(dataset.zip_rest_overlap, int) and dataset.zip_rest_overlap > 0,
            str(dataset.zip_rest_overlap),
        ),
        ("REST payload hash", _valid_hash(dataset.rest_payload_sha256), dataset.rest_payload_sha256),
        ("ZIP payload hash", _valid_hash(dataset.zip_payload_sha256), dataset.zip_payload_sha256),
    ]
    for marker in ("first=", "middle=", "latest_complete="):
        checks.append((f"scope {marker[:-1]}", marker in dataset.zip_rest_scope, dataset.zip_rest_scope))
    if dataset.kline_anomalies:
        checks.append(("anomaly months audited", "anomaly=" in dataset.zip_rest_scope, dataset.zip_rest_scope))
    return checks


def _funding_events(raw_root: str | Path, symbol: str) -> list[dict[str, object]]:
    store = AppendOnlyRawStore(raw_root)
    by_time: dict[int, dict[str, object]] = {}
    for envelope in store.iter_envelopes("funding_rate_history"):
        if not isinstance(envelope.payload, list):
            continue
        for row in envelope.payload:
            if not isinstance(row, dict) or row.get("fundingTime") is None:
                continue
            if row.get("symbol", symbol) != symbol:
                continue
            by_time[int(row["fundingTime"])] = row
    return [by_time[key] for key in sorted(by_time)]


def _interval_distribution(events: list[dict[str, object]], symbol: str) -> tuple[str, int, list[str]]:
    result = infer_funding_interval_hours(symbol, funding_rate_history=events)
    distribution = Counter(result.event_intervals.values())
    formatted = ", ".join(
        f"{hours.normalize()}h={count}" for hours, count in sorted(distribution.items(), key=lambda item: item[0])
    )
    return formatted, len(result.event_intervals), result.warnings


def render_audit_report(public_report: M0RunReport, raw_root: str | Path) -> tuple[str, bool]:
    by_name = {dataset.name: dataset for dataset in public_report.datasets}
    check_rows: list[tuple[str, str, str]] = []
    zip_rows: list[DatasetRun] = []
    interval_rows: list[tuple[str, int, str, str]] = []

    for symbol in SYMBOLS:
        for name in KLINE_DATASETS:
            full_name = f"{name}:{symbol}"
            dataset = by_name.get(full_name)
            if dataset is None:
                check_rows.append((full_name, "blocked", "dataset missing"))
                continue
            zip_rows.append(dataset)
            for label, passed, detail in _dataset_checks(dataset):
                check_rows.append((f"{full_name} / {label}", "pass" if passed else "blocked", detail))

        funding_name = f"funding_rate_history:{symbol}"
        funding = by_name.get(funding_name)
        funding_ok = funding is not None and funding.rows > 1 and funding.interval == "funding_period"
        check_rows.append(
            (
                funding_name,
                "pass" if funding_ok else "blocked",
                f"rows={funding.rows if funding else 0}; interval={funding.interval if funding else 'missing'}",
            )
        )
        events = _funding_events(raw_root, symbol)
        try:
            distribution, event_count, warnings = _interval_distribution(events, symbol)
            interval_ok = event_count > 0 and not warnings
            interval_rows.append((symbol, event_count, distribution, "; ".join(warnings) or "none"))
        except ValueError as exc:
            interval_ok = False
            interval_rows.append((symbol, 0, "not_available", str(exc)))
        check_rows.append(
            (
                f"funding interval events:{symbol}",
                "pass" if interval_ok else "blocked",
                interval_rows[-1][2],
            )
        )

    passed = bool(check_rows) and all(status == "pass" for _, status, _ in check_rows)
    generated = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# M0 Audit Revalidation Report",
        "",
        f"- Status: {'pass' if passed else 'blocked'}",
        f"- Generated UTC: {generated}",
        "- Scope: public-data audit revalidation only",
        "- Private smoke rerun: no",
        "- API key used: no",
        "- Raw data committed: no",
        "- DuckDB committed: no",
        f"- Data start: {public_report.data_start}",
        f"- Data end: {public_report.data_end}",
        "- Profile: BTCUSDT and ETHUSDT 1h spot/UM futures/mark/index/premium plus funding history",
        "",
        "## ZIP/REST Evidence",
        "",
        "| Dataset | Rows | Gaps | Overlap | Field differences | Scope | REST SHA256 | ZIP SHA256 |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for dataset in zip_rows:
        lines.append(
            f"| `{dataset.name}` | {dataset.rows} | {dataset.gaps} | {dataset.zip_rest_overlap} | "
            f"{dataset.zip_rest_differences} | `{dataset.zip_rest_scope}` | "
            f"`{dataset.rest_payload_sha256}` | `{dataset.zip_payload_sha256}` |"
        )

    lines.extend(
        [
            "",
            "## Funding Interval Evidence",
            "",
            "Each historical settlement retains its inferred interval; no fixed global cadence is substituted.",
            "",
            "| Symbol | Funding events with interval | Interval distribution | Warnings |",
            "|---|---:|---|---|",
        ]
    )
    for symbol, count, distribution, warnings in interval_rows:
        lines.append(f"| `{symbol}` | {count} | `{distribution}` | {warnings} |")

    lines.extend(["", "## Required Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for name, status, detail in check_rows:
        lines.append(f"| `{name}` | {status} | `{detail}` |")

    blocked = [name for name, status, _ in check_rows if status != "pass"]
    lines.extend(["", "## Blockers", ""])
    lines.extend([f"- {name}" for name in blocked] or ["- none"])
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- M0 audit status: {'pass' if passed else 'audit_revalidation_required'}",
            "- This report does not approve M2, paper trading, live trading, order placement, or API trading permissions.",
            "",
        ]
    )
    return "\n".join(lines), passed


def main() -> int:
    args = parse_args()
    public_report = _combine_public_reports(args.public)
    text, passed = render_audit_report(public_report, args.raw_root)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"Wrote M0 audit revalidation report: {output}")
    print(f"status={'pass' if passed else 'blocked'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
