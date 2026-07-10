# M1E Official Source Conflict Diagnostics

- Status: diagnostics_complete_blocker_confirmed
- Scope: official public-data source diagnostics only
- Generated UTC: 2026-07-10T19:23:00.203926+00:00
- Conflict evidence rows: 30
- Canonical diagnostics SHA256: `7994646f4d5883d4b58f6d2360724633b8c9009e3fe404d5f6b9acb9a1211869`
- Fresh monthly ZIP hashes unchanged: 36/36
- Candidate evaluated: no
- Candidate OOS returns accessed: no
- Strategy code authorized: no
- Freqtrade backtesting run: no
- API key used: no
- M2 authorized: no

## Classification Summary

- child_aggregate_flow_confirmed_by_rest: 2
- higher_timeframe_flow_revision_confirmed_by_rest: 10
- monthly_daily_conflict_rest_supports_daily: 16
- unresolved_flow_revision: 2

## Field-Level Evidence

| UTC open time | Symbol | TF | Differing fields | REST matches official | REST matches derived/daily | Classification | Contract resolved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-12-21T13:00:00+00:00 | BTCUSDT | 1h | high, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume, close_time | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:15:00+00:00 | BTCUSDT | 5m | high, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:20:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:25:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:30:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:35:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:40:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:45:00+00:00 | BTCUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume, close_time | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:00:00+00:00 | ETHUSDT | 1h | high, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume, close_time | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:15:00+00:00 | ETHUSDT | 5m | high, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:20:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:25:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:30:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:35:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:40:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2020-12-21T13:45:00+00:00 | ETHUSDT | 5m | open, high, low, close, volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume, close_time | no | yes | monthly_daily_conflict_rest_supports_daily | no |
| 2021-01-21T08:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | child_aggregate_flow_confirmed_by_rest | no |
| 2021-01-21T08:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | yes | child_aggregate_flow_confirmed_by_rest | no |
| 2021-04-22T02:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-04-23T01:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | no | unresolved_flow_revision | no |
| 2021-04-23T02:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-04-23T00:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-04-22T02:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-04-23T01:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | no | no | unresolved_flow_revision | no |
| 2021-04-23T02:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-04-23T00:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-09-23T01:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2021-11-01T03:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2022-04-13T04:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |
| 2022-04-13T04:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | yes | no | higher_timeframe_flow_revision_confirmed_by_rest | no |

## Findings

- All cross-timeframe numeric differences preserve identical OHLC prices and differ only in volume, quote volume, trade count, and taker-volume fields.
- Current public REST confirms the published higher-timeframe row for most aggregate conflicts, confirms the child aggregation for two January 2021 rows, and exposes a third revision for two April 2021 rows.
- The December 2020 monthly/daily conflict remains a contradiction between official archive versions. REST preference cannot overwrite the authoritative monthly ZIP under ADR-0008.
- Fresh monthly ZIP downloads retain the recorded hashes, so the conflict is reproducible and is not a stale local-download error.
- No classification is contract-resolved. The fixed M1E data Gate remains blocked.

## Diagnostic Clean Suffix

- First six-month clean suffix start: 2022-11-01
- This date is diagnostic only and cannot replace the contract research start without a new ADR.
- Clean-suffix full calendar: 1338 days
- Clean-suffix sealed 30% OOS calendar: 402 days
- Fixed requirements: 1800 full days and 540 OOS days.
- Clean suffix sample budget: blocked

## Decision

- M1E PR3 sample-budget branch authorized: no
- M1E strategy design authorized: no
- Source precedence or numeric tolerance change authorized: no
- M2 authorized: no
