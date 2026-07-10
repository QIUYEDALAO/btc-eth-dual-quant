# M1E Binance Source-Owner Escalation Package

- Status: submitted_awaiting_response
- Target repository: `binance/binance-public-data`
- Existing issue: https://github.com/binance/binance-public-data/issues/475
- Existing issue overlap rows: 16
- New supplemental rows: 14
- Supplemental evidence SHA256: `1148b87ffa6b9089210b90996c63c136ac1e32d56571617e7beb661bb3c4f805`
- Monthly ZIP refetch hashes unchanged: 36/36
- External submission performed: yes
- Submission URL: https://github.com/binance/binance-public-data/issues/475#issuecomment-4939090508
- Submitted UTC: 2026-07-10T20:04:37Z
- API key used: no
- Raw payload included: no
- M1E contract resolved: no
- M2 authorized: no

## Routing Decision

Binance issue #475 already documents the December 2020 monthly/daily/API disagreement. This package should be added as a comment to that issue instead of opening a duplicate. It contributes 14 non-December cross-timeframe cases from January 2021 through April 2022.

## Supplemental Evidence

| UTC open time | Symbol | TF | Fields | REST relationship | Classification | Monthly ZIP |
| --- | --- | --- | --- | --- | --- | --- |
| 2021-01-21T08:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches derived | child_aggregate_flow_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-2021-01.zip) |
| 2021-01-21T08:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches derived | child_aggregate_flow_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/4h/ETHUSDT-4h-2021-01.zip) |
| 2021-04-22T02:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2021-04.zip) |
| 2021-04-23T01:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches third version | unresolved_flow_revision | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2021-04.zip) |
| 2021-04-23T02:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2021-04.zip) |
| 2021-04-23T00:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-2021-04.zip) |
| 2021-04-22T02:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-2021-04.zip) |
| 2021-04-23T01:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches third version | unresolved_flow_revision | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-2021-04.zip) |
| 2021-04-23T02:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-2021-04.zip) |
| 2021-04-23T00:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/4h/ETHUSDT-4h-2021-04.zip) |
| 2021-09-23T01:00:00+00:00 | BTCUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2021-09.zip) |
| 2021-11-01T03:00:00+00:00 | ETHUSDT | 1h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1h/ETHUSDT-1h-2021-11.zip) |
| 2022-04-13T04:00:00+00:00 | BTCUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h/BTCUSDT-4h-2022-04.zip) |
| 2022-04-13T04:00:00+00:00 | ETHUSDT | 4h | volume, quote_volume, trade_count, taker_buy_base_volume, taker_buy_quote_volume | REST matches official | higher_timeframe_flow_revision_confirmed_by_rest | [ZIP](https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/4h/ETHUSDT-4h-2022-04.zip) |

## Suggested Issue Comment

```markdown
I independently reproduced the monthly/daily/API inconsistency described here and found an additional cross-timeframe archive problem outside the December 2020 scope.

Using BTCUSDT and ETHUSDT spot monthly kline ZIPs, I compared deterministic 12x5m -> 1h and 4x1h -> 4h aggregates with the published higher-timeframe ZIP rows, then checked the exact timestamps against current `GET /api/v3/klines`.

Additional affected UTC timestamps:
- 2021-01-21T08:00:00+00:00 BTCUSDT 4h: child_aggregate_flow_confirmed_by_rest
- 2021-01-21T08:00:00+00:00 ETHUSDT 4h: child_aggregate_flow_confirmed_by_rest
- 2021-04-22T02:00:00+00:00 BTCUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-04-23T01:00:00+00:00 BTCUSDT 1h: unresolved_flow_revision
- 2021-04-23T02:00:00+00:00 BTCUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-04-23T00:00:00+00:00 BTCUSDT 4h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-04-22T02:00:00+00:00 ETHUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-04-23T01:00:00+00:00 ETHUSDT 1h: unresolved_flow_revision
- 2021-04-23T02:00:00+00:00 ETHUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-04-23T00:00:00+00:00 ETHUSDT 4h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-09-23T01:00:00+00:00 BTCUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2021-11-01T03:00:00+00:00 ETHUSDT 1h: higher_timeframe_flow_revision_confirmed_by_rest
- 2022-04-13T04:00:00+00:00 BTCUSDT 4h: higher_timeframe_flow_revision_confirmed_by_rest
- 2022-04-13T04:00:00+00:00 ETHUSDT 4h: higher_timeframe_flow_revision_confirmed_by_rest

All 36 affected monthly ZIPs were downloaded again and retained the same SHA-256 hashes. The supplemental evidence contains 14 conflict rows with SHA-256 `1148b87ffa6b9089210b90996c63c136ac1e32d56571617e7beb661bb3c4f805`.

The differences are in volume, quote volume, trade count, and taker-volume fields; OHLC prices are equal for these supplemental cross-timeframe cases. REST supports the published higher timeframe in 10 rows, the child aggregation in 2 rows, and a third value in 2 rows.

Could Binance clarify whether kline archives at different intervals are expected to be arithmetically consistent, and which source is canonical when the child aggregate, higher-timeframe monthly ZIP, and current API disagree?
```

## Submission Boundary

The prepared package was posted only after explicit user approval. Submission does not resolve the contract: M1E remains blocked until Binance corrects or documents the conflicting sources and the project reruns its fixed Gate.
