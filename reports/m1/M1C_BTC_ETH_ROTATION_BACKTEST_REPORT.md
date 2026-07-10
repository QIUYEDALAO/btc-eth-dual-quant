# M1C BTC/ETH Rotation Backtest Report

- Status: failed_validation
- Generated UTC: 2026-07-10T00:45:15+00:00
- Evidence workflow: https://github.com/QIUYEDALAO/btc-eth-dual-quant/actions/runs/29060604088
- Scope: Freqtrade historical backtest validation only
- Strategy: BTCETHRelativeStrengthRotation
- No live trading / no dry-run / no execution/live / no order placement
- Freqtrade is the sole strategy-return authority
- Not investment advice

## Data and Split

- Full data range: 2017-08-17 through 2026-07-09 UTC
- Effective full backtest range after startup: 2018-03-05 00:00:00 through 2026-07-09 00:00:00 UTC
- IS range: 2017-08-17 through 2023-11-07 UTC
- OOS range: 2023-11-08 through 2026-07-09 UTC
- Effective OOS backtest range: 2023-11-08 00:00:00 through 2026-07-09 00:00:00 UTC
- OOS policy: sealed final 30% by calendar time
- Data source: Freqtrade Binance public spot JSON cache

| Symbol | Rows | Start UTC | End UTC | Missing daily bars | File SHA256 |
|---|---:|---|---|---:|---|
| `BTC/USDT` | 3249 | `2017-08-17T00:00:00+00:00` | `2026-07-09T00:00:00+00:00` | 0 | `be5f8a37c8fea931ac91eb8c604056a6a5d6b6ff7b6dc51c0b8c9555f58d83cc` |
| `ETH/USDT` | 3249 | `2017-08-17T00:00:00+00:00` | `2026-07-09T00:00:00+00:00` | 0 | `fb9dd183f9026c6a0646cb03b48061d5f6626e2690ceb0db4826932a063616f2` |

## Fixed Rules and Costs

- Weekly Sunday-close decision, next daily open execution
- close > SMA200 and positive 90-day return
- stronger eligible asset wins; BTC wins exact ties; otherwise cash
- one position, 50% maximum tradable equity, no short or leverage
- emergency stoploss: -20%
- Base cost: 0.15% per side (0.10% fee + 0.05% slippage equivalent)
- Cost x2: 0.30% per side

## Core Results

| Run | Complete trades | Total return | Sharpe | Max drawdown | Final balance |
|---|---:|---:|---:|---:|---:|
| `base-full` | 31 | 409.6494% | 0.0750 | 15.7711% | 509649.4047 USDT |
| `x2-full` | 31 | 386.4426% | 0.0725 | 16.6528% | 486442.6448 USDT |
| `base-oos` | 15 | 53.5309% | 0.1146 | 15.7710% | 153530.9308 USDT |
| `x2-oos` | 15 | 50.1075% | 0.1091 | 16.6527% | 150107.5001 USDT |

## IS Segment Robustness

| Segment | Range | Complete trades | Net return |
|---|---|---:|---:|
| `segment-1` | `2018-03-05 00:00:00 -> 2019-03-08 00:00:00` | 2 | -19.2422% |
| `segment-2` | `2019-03-08 00:00:00 -> 2020-09-27 00:00:00` | 5 | 65.2818% |
| `segment-3` | `2020-09-27 00:00:00 -> 2022-04-18 00:00:00` | 6 | 115.8483% |
| `segment-4` | `2022-04-18 00:00:00 -> 2023-11-08 00:00:00` | 3 | 9.4271% |

## Annual Breakdown (Base)

| Year | Trades | Profit |
|---|---:|---:|
| 31/12/2018 | 2 | -19.2422% |
| 31/12/2019 | 2 | 35.5223% |
| 31/12/2020 | 4 | 26.9360% |
| 31/12/2021 | 4 | 146.3865% |
| 31/12/2022 | 1 | 3.9423% |
| 31/12/2023 | 3 | 1.5567% |
| 31/12/2024 | 12 | 57.8500% |
| 31/12/2025 | 3 | 156.6978% |

## Concentration and Extremes

- Return after deleting best 3 trades: 143.5612%
- Best complete trade: `BTC/USDT` 2020-11-02 00:00:00+00:00 -> 2021-01-18 00:00:00+00:00, 159.5480%
- Worst complete trade: `ETH/USDT` 2018-05-07 00:00:00+00:00 -> 2018-05-12 00:00:00+00:00, -20.2396%
- lookahead-analysis: pass; signals=20, biased_entries=0, biased_exits=0
- recursive-analysis: pass

## Gate Matrix

| Gate | Status |
|---|---|
| Backtest code | pass |
| Complete trades >= 80 | fail |
| OOS complete trades >= 20 | fail |
| OOS Sharpe >= 1.0 | fail |
| Base total return > 0 | pass |
| Cost x2 total return > 0 | pass |
| Base OOS return > 0 | pass |
| Cost x2 OOS return > 0 | pass |
| Maximum drawdown <= 15% | fail |
| Delete best 3 return >= 0 | pass |
| At least 3/4 IS segments positive | pass |
| lookahead-analysis | pass |
| recursive-analysis | pass |
| Unexplained data gaps = 0 | pass |

## Complete Trade Detail (Base)

| # | Pair | Open UTC | Close UTC | Days | Exit | Profit |
|---:|---|---|---|---:|---|---:|
| 1 | `ETH/USDT` | `2018-03-12 00:00:00+00:00` | `2018-03-15 00:00:00+00:00` | 3.00 | `stop_loss` | -20.2383% |
| 2 | `ETH/USDT` | `2018-05-07 00:00:00+00:00` | `2018-05-12 00:00:00+00:00` | 5.00 | `stop_loss` | -20.2396% |
| 3 | `BTC/USDT` | `2019-04-08 00:00:00+00:00` | `2019-09-23 00:00:00+00:00` | 168.00 | `weekly_rotation` | 93.3750% |
| 4 | `BTC/USDT` | `2019-10-28 00:00:00+00:00` | `2019-11-04 00:00:00+00:00` | 7.00 | `weekly_rotation` | -3.7711% |
| 5 | `ETH/USDT` | `2020-02-03 00:00:00+00:00` | `2020-03-12 00:00:00+00:00` | 38.00 | `stop_loss` | -20.2365% |
| 6 | `ETH/USDT` | `2020-04-20 00:00:00+00:00` | `2020-05-11 00:00:00+00:00` | 21.00 | `weekly_rotation` | 3.9096% |
| 7 | `BTC/USDT` | `2020-06-01 00:00:00+00:00` | `2020-06-15 00:00:00+00:00` | 14.00 | `weekly_rotation` | -1.4199% |
| 8 | `ETH/USDT` | `2020-06-15 00:00:00+00:00` | `2020-11-02 00:00:00+00:00` | 140.00 | `weekly_rotation` | 70.6618% |
| 9 | `BTC/USDT` | `2020-11-02 00:00:00+00:00` | `2021-01-18 00:00:00+00:00` | 77.00 | `weekly_rotation` | 159.5480% |
| 10 | `ETH/USDT` | `2021-01-18 00:00:00+00:00` | `2021-07-19 00:00:00+00:00` | 182.00 | `weekly_rotation` | 53.0210% |
| 11 | `BTC/USDT` | `2021-08-16 00:00:00+00:00` | `2021-09-13 00:00:00+00:00` | 28.00 | `weekly_rotation` | -2.3129% |
| 12 | `ETH/USDT` | `2021-09-13 00:00:00+00:00` | `2021-09-21 00:00:00+00:00` | 8.00 | `stop_loss` | -20.2393% |
| 13 | `ETH/USDT` | `2021-09-27 00:00:00+00:00` | `2022-01-10 00:00:00+00:00` | 105.00 | `weekly_rotation` | 2.7185% |
| 14 | `ETH/USDT` | `2023-01-16 00:00:00+00:00` | `2023-01-30 00:00:00+00:00` | 14.00 | `weekly_rotation` | 5.6220% |
| 15 | `BTC/USDT` | `2023-01-30 00:00:00+00:00` | `2023-06-19 00:00:00+00:00` | 140.00 | `weekly_rotation` | 10.6038% |
| 16 | `BTC/USDT` | `2023-06-26 00:00:00+00:00` | `2023-08-21 00:00:00+00:00` | 56.00 | `weekly_rotation` | -14.2835% |
| 17 | `BTC/USDT` | `2023-10-23 00:00:00+00:00` | `2024-01-15 00:00:00+00:00` | 84.00 | `weekly_rotation` | 38.7260% |
| 18 | `ETH/USDT` | `2024-01-15 00:00:00+00:00` | `2024-02-05 00:00:00+00:00` | 21.00 | `weekly_rotation` | -7.6809% |
| 19 | `BTC/USDT` | `2024-02-05 00:00:00+00:00` | `2024-02-19 00:00:00+00:00` | 14.00 | `weekly_rotation` | 22.0714% |
| 20 | `ETH/USDT` | `2024-02-19 00:00:00+00:00` | `2024-03-25 00:00:00+00:00` | 35.00 | `weekly_rotation` | 19.5558% |
| 21 | `BTC/USDT` | `2024-03-25 00:00:00+00:00` | `2024-04-08 00:00:00+00:00` | 14.00 | `weekly_rotation` | 2.8904% |
| 22 | `ETH/USDT` | `2024-04-08 00:00:00+00:00` | `2024-04-15 00:00:00+00:00` | 7.00 | `weekly_rotation` | -8.9323% |
| 23 | `BTC/USDT` | `2024-04-15 00:00:00+00:00` | `2024-06-03 00:00:00+00:00` | 49.00 | `weekly_rotation` | 2.8948% |
| 24 | `ETH/USDT` | `2024-06-03 00:00:00+00:00` | `2024-06-10 00:00:00+00:00` | 7.00 | `weekly_rotation` | -2.2646% |
| 25 | `ETH/USDT` | `2024-06-17 00:00:00+00:00` | `2024-06-24 00:00:00+00:00` | 7.00 | `weekly_rotation` | -5.8974% |
| 26 | `ETH/USDT` | `2024-07-15 00:00:00+00:00` | `2024-07-29 00:00:00+00:00` | 14.00 | `weekly_rotation` | 0.4673% |
| 27 | `BTC/USDT` | `2024-07-29 00:00:00+00:00` | `2024-08-05 00:00:00+00:00` | 7.00 | `weekly_rotation` | -15.0375% |
| 28 | `BTC/USDT` | `2024-09-30 00:00:00+00:00` | `2024-10-07 00:00:00+00:00` | 7.00 | `weekly_rotation` | -4.5277% |
| 29 | `BTC/USDT` | `2024-10-21 00:00:00+00:00` | `2025-03-03 00:00:00+00:00` | 133.00 | `weekly_rotation` | 36.1508% |
| 30 | `BTC/USDT` | `2025-05-12 00:00:00+00:00` | `2025-07-07 00:00:00+00:00` | 56.00 | `weekly_rotation` | 4.5705% |
| 31 | `ETH/USDT` | `2025-07-07 00:00:00+00:00` | `2025-11-10 00:00:00+00:00` | 126.00 | `weekly_rotation` | 38.9976% |

## Known Limitations

- Freqtrade assumes backtest orders fill according to its candle model.
- Slippage is represented conservatively through the per-side fee override, not an order-book replay.
- M0 dual-source audit remains blocked independently; a numerical pass could not authorize M2 until P4 and M0 pass.
- No parameters were selected from OOS or segment results.

## Decision

At least one fixed gate failed. M1C is `failed_validation`; parameter rescue and progression to P4 or M2 are prohibited.
