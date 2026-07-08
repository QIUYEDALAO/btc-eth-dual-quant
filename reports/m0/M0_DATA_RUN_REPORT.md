# M0 Data Run Report

Generated UTC: 2026-07-08T22:44:00+00:00

## Data Range

- Start: `2017-08-17T00:00:00+00:00`
- End: `2026-07-08T23:59:59+00:00`

## Pull Summary

| Dataset | Interval | Rows | Gaps | ZIP/REST Diff | K-line Anomalies | Funding Interval Anomalies | Archive Status | Commission Status |
|---|---:|---:|---:|---:|---:|---|---|---|
| `spot_klines:BTCUSDT` | `1d` | 3248 | 0 | not_available_in_smoke | 6 | not_applicable | not_applicable | not_applicable |
| `spot_klines:ETHUSDT` | `1d` | 3248 | 0 | not_available_in_smoke | 12 | not_applicable | not_applicable | not_applicable |

## Scheduler Dry-run

- not_run

## Private Smoke

- not_run

## Archive Notes

- none

## Unexplained Anomalies

- spot_klines:BTCUSDT: kline anomalies detected: {'amplitude_gt_30pct': 6}
- spot_klines:ETHUSDT: kline anomalies detected: {'amplitude_gt_30pct': 12}

## M1 Gate

- Status: `blocked`
- Rule: M1 may proceed only when this report has actual M0 data runs, private smoke completed, all required checks complete, and zero unexplained anomalies.
