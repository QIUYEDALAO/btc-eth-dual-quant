# M0 Data Run Report

Generated UTC: 2026-07-08T23:35:57+00:00

## Data Range

- Start: `scheduler_dry_run`
- End: `2026-07-08T23:35:57+00:00`

## Public Full-history Pull Summary

| Dataset | Interval | Rows | Gaps | ZIP/REST Diff | K-line Anomalies | Funding Interval Anomalies | Archive Status | Commission Status |
|---|---:|---:|---:|---:|---:|---|---|---|

## Scheduler Dry-run

- daily 00:10 UTC oi_daily_archive dataset=open_interest command='scripts/m0_backfill_public.py --symbols BTCUSDT,ETHUSDT --interval 1d --limit 30 --include-oi --oi-period 1d'
- daily 00:20 UTC income_daily_archive dataset=funding_income command='scripts/m0_smoke_readonly_private.py --income-limit 100'
- daily 00:30 UTC commission_daily_refresh dataset=commissions command='scripts/m0_smoke_readonly_private.py --symbols BTCUSDT,ETHUSDT'

## Private Smoke

- not_run

## Archive Notes

- none

## Explained Anomalies

- none

## Unexplained Anomalies

- none

## M1 Gate

- Status: `blocked`
- Public full-history: `blocked`
- Scheduler dry-run: `pass`
- Private read-only smoke: `blocked`
- Required checks: `blocked`
- Zero unexplained anomalies: `pass`
- Rule: M1 may proceed only when public full-history, scheduler dry-run, private read-only smoke, all required checks, and zero unexplained anomalies are all pass.
