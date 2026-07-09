#!/usr/bin/env python3
"""Scheduler dry-run for M0 archival jobs.

Prints the daily OI, income, and commission refresh plan and appends a dry-run
log. It never opens trading permissions or calls order endpoints.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m0_report import M0RunReport, write_report


JOBS = [
    {
        "name": "oi_daily_archive",
        "schedule": "daily 00:10 UTC",
        "dataset": "open_interest",
        "script": "scripts/m0_backfill_public.py --symbols BTCUSDT,ETHUSDT --interval 1d --limit 30 --include-oi --oi-period 1d",
    },
    {
        "name": "income_daily_archive",
        "schedule": "daily 00:20 UTC",
        "dataset": "funding_income",
        "script": "scripts/m0_smoke_readonly_private.py --income-limit 100",
    },
    {
        "name": "commission_daily_refresh",
        "schedule": "daily 00:30 UTC",
        "dataset": "commissions",
        "script": "scripts/m0_smoke_readonly_private.py --symbols BTCUSDT,ETHUSDT",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M0 scheduler dry-run")
    parser.add_argument("--log-path", default="storage/logs/m0_scheduler_dry_run.jsonl")
    parser.add_argument("--report-path", default="reports/m0/M0_SCHEDULER_DRY_RUN_REPORT.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    log_path = Path(args.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for job in JOBS:
        event = {"dry_run_at": now, "trading_permissions": "not_required", **job}
        log_path.open("a", encoding="utf-8").write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        line = f"{job['schedule']} {job['name']} dataset={job['dataset']} command='{job['script']}'"
        lines.append(line)
        print(line)
    write_report(
        M0RunReport(data_start="scheduler_dry_run", data_end=now, scheduler_dry_run=lines),
        args.report_path,
    )
    print(f"Wrote dry-run log: {log_path}")
    print(f"Wrote report: {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
