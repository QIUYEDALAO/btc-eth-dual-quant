# M0 Data Run Report

Generated UTC: 2026-07-09T02:47:45+00:00

## Data Range

- Start: `2017-08-17T00:00:00+00:00`
- End: `2026-07-08T23:59:59+00:00`

## Public Full-history Pull Summary

| Dataset | Interval | Rows | Gaps | ZIP/REST Diff | K-line Anomalies | Funding Interval Anomalies | Archive Status | Commission Status |
|---|---:|---:|---:|---:|---:|---|---|---|
| `spot_klines:BTCUSDT` | `1d` | 3248 | 0 | not_available_in_smoke | 6 | not_applicable | not_applicable | not_applicable |
| `spot_klines:ETHUSDT` | `1d` | 3248 | 0 | not_available_in_smoke | 12 | not_applicable | not_applicable | not_applicable |
| `um_futures_klines:BTCUSDT` | `1d` | 2496 | 0 | not_available_in_smoke | 4 | not_applicable | not_applicable | not_applicable |
| `mark_price_klines:BTCUSDT` | `1d` | 2390 | 0 | not_available_in_smoke | 3 | not_applicable | not_applicable | not_applicable |
| `index_price_klines:BTCUSDT` | `1d` | 2390 | 0 | not_available_in_smoke | 3 | not_applicable | not_applicable | not_applicable |
| `premium_index_klines:BTCUSDT` | `1d` | 2389 | 0 | not_available_in_smoke | 0 | not_applicable | not_applicable | not_applicable |
| `funding_rate_history:BTCUSDT` | `funding_period` | 7481 | 0 | not_applicable | 0 | not_applicable | not_applicable | not_applicable |
| `funding_interval_BTCUSDT` | `inferred` | 7481 | 0 | not_applicable | 0 | 0 | not_applicable | not_applicable |
| `open_interest:BTCUSDT` | `1d` | 30 | 0 | not_applicable | 0 | not_applicable | pass_retention_limited | not_applicable |
| `um_futures_klines:ETHUSDT` | `1d` | 2416 | 0 | not_available_in_smoke | 7 | not_applicable | not_applicable | not_applicable |
| `mark_price_klines:ETHUSDT` | `1d` | 2390 | 0 | not_available_in_smoke | 6 | not_applicable | not_applicable | not_applicable |
| `index_price_klines:ETHUSDT` | `1d` | 2390 | 0 | not_available_in_smoke | 6 | not_applicable | not_applicable | not_applicable |
| `premium_index_klines:ETHUSDT` | `1d` | 2389 | 0 | not_available_in_smoke | 0 | not_applicable | not_applicable | not_applicable |
| `funding_rate_history:ETHUSDT` | `funding_period` | 7247 | 0 | not_applicable | 0 | not_applicable | not_applicable | not_applicable |
| `funding_interval_ETHUSDT` | `inferred` | 7247 | 0 | not_applicable | 0 | 0 | not_applicable | not_applicable |
| `open_interest:ETHUSDT` | `1d` | 30 | 0 | not_applicable | 0 | not_applicable | pass_retention_limited | not_applicable |

## Scheduler Dry-run

- daily 00:10 UTC oi_daily_archive dataset=open_interest command='scripts/m0_backfill_public.py --symbols BTCUSDT,ETHUSDT --interval 1d --limit 30 --include-oi --oi-period 1d'
- daily 00:20 UTC income_daily_archive dataset=funding_income command='scripts/m0_smoke_readonly_private.py --income-limit 100'
- daily 00:30 UTC commission_daily_refresh dataset=commissions command='scripts/m0_smoke_readonly_private.py --symbols BTCUSDT,ETHUSDT'

## Private Smoke

- status=pass

## Archive Notes

- `open_interest:BTCUSDT`: Binance `openInterestHist` only retains a short recent window, so long-range stages archive the latest available OI and mark it `pass_retention_limited`.
- `open_interest:ETHUSDT`: Binance `openInterestHist` only retains a short recent window, so long-range stages archive the latest available OI and mark it `pass_retention_limited`.

## Explained Anomalies

- spot_klines:BTCUSDT: anomaly review classified explained_market_move=6; see `reports/m0/M0_ANOMALY_REVIEW.md`
- spot_klines:ETHUSDT: anomaly review classified explained_market_move=12; see `reports/m0/M0_ANOMALY_REVIEW.md`
- um_futures_klines:BTCUSDT: anomaly review classified explained_market_move=4; see `reports/m0/M0_ANOMALY_REVIEW.md`
- mark_price_klines:BTCUSDT: anomaly review classified explained_market_move=3; see `reports/m0/M0_ANOMALY_REVIEW.md`
- index_price_klines:BTCUSDT: anomaly review classified explained_market_move=3; see `reports/m0/M0_ANOMALY_REVIEW.md`
- um_futures_klines:ETHUSDT: anomaly review classified explained_market_move=7; see `reports/m0/M0_ANOMALY_REVIEW.md`
- mark_price_klines:ETHUSDT: anomaly review classified explained_market_move=6; see `reports/m0/M0_ANOMALY_REVIEW.md`
- index_price_klines:ETHUSDT: anomaly review classified explained_market_move=6; see `reports/m0/M0_ANOMALY_REVIEW.md`

## Unexplained Anomalies

- none

## M1 Gate

- Status: `pass`
- Public full-history: `pass`
- Scheduler dry-run: `pass`
- Private read-only smoke: `pass`
- Required checks: `pass`
- Zero unexplained anomalies: `pass`
- Rule: M1 may proceed only when public full-history, scheduler dry-run, private read-only smoke, all required checks, and zero unexplained anomalies are all pass.
