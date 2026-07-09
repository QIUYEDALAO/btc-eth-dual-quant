# M1A Trend Backtest Report

Generated UTC: 2026-07-09T03:34:29+00:00

## Status

- Status: under_review
- Scope: trend backtest validation only
- No live trading / no paper trading / no execution/live / no order placement
- This report is not investment advice; historical backtests do not indicate future performance.

## Data

- Data sources used: local M0 public `spot_klines` and `funding_rate_history` only
- Data range: `2017-08-17` to `2026-07-08`
- IS start/end: `2017-08-17` to `2023-11-06`
- OOS start/end: `2023-11-07` to `2026-07-08`
- OOS was not used for parameter selection.

## Baseline Params

- symbol universe: BTCUSDT, ETHUSDT
- instrument: spot long-only
- timeframe: 1d UTC
- trend filter: close > SMA(200)
- entry: close breakout above prior 55-day Donchian high
- exit: close below prior 20-day Donchian low or fixed ATR stop
- ATR: ATR(20)
- initial stop: entry_price - 2.0 * ATR(20)
- risk: equity * 1% per trade
- annualized volatility contribution cap: <= 20% per symbol

## Funding Crowding Filter

- rule: if funding annualized > 40% for >= 3 consecutive days, new entry size is multiplied by 0.5
- crowding_filter_unavailable: none

## Cost Assumptions

- spot_fee: 0.10% per side
- slippage: 0.05% per side
- base_cost one-way: 0.15%
- cost_x2 one-way: 0.30%

## Base Cost Results

| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 82.57% | 0.6705 | -18.18% | 18 | 1012 | 44.44% | 6.4090 |
| `ETHUSDT` | 73.38% | 0.6668 | -21.68% | 17 | 868 | 52.94% | 8.9417 |
| `BTC+ETH equal-weight portfolio` | 77.97% | 0.7367 | -17.12% | 35 | 1175 | 48.57% | 7.3640 |

## Cost x2 Results

| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 80.85% | 0.6607 | -18.27% | 18 | 1012 | 44.44% | 6.0931 |
| `ETHUSDT` | 72.31% | 0.6598 | -21.73% | 17 | 868 | 52.94% | 8.5701 |
| `BTC+ETH equal-weight portfolio` | 76.58% | 0.7271 | -17.36% | 35 | 1175 | 48.57% | 7.0236 |

## OOS Results

| Name | Total Return | Sharpe | Max Drawdown | Trades | Exposure Days | Win Rate | Profit Factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 4.90% | 0.4861 | -4.00% | 4 | 191 | 50.00% | 3.6344 |
| `ETHUSDT` | 5.28% | 0.5698 | -3.41% | 3 | 119 | 66.67% | 5.6068 |
| `BTC+ETH equal-weight portfolio` | 5.09% | 0.6440 | -2.94% | 7 | 245 | 57.14% | 4.3865 |

## Parameter Neighborhood

No best params are selected; this table is a robustness scan around the fixed center.

| Regime MA | Entry | Exit | ATR Stop | Total Return | Sharpe | Max Drawdown | Trade Count |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 160 | 44 | 16 | 1.6 | 118.59% | 0.9310 | -12.38% | 44 |
| 160 | 44 | 16 | 2.0 | 90.10% | 0.9147 | -10.80% | 43 |
| 160 | 44 | 16 | 2.4 | 69.57% | 0.9072 | -8.84% | 41 |
| 160 | 44 | 20 | 1.6 | 114.57% | 0.7903 | -19.12% | 42 |
| 160 | 44 | 20 | 2.0 | 88.76% | 0.7707 | -17.08% | 40 |
| 160 | 44 | 20 | 2.4 | 65.64% | 0.7467 | -13.45% | 38 |
| 160 | 44 | 24 | 1.6 | 101.25% | 0.6939 | -23.35% | 38 |
| 160 | 44 | 24 | 2.0 | 78.43% | 0.6709 | -21.03% | 36 |
| 160 | 44 | 24 | 2.4 | 59.39% | 0.6622 | -16.24% | 34 |
| 160 | 55 | 16 | 1.6 | 103.50% | 0.8894 | -11.65% | 41 |
| 160 | 55 | 16 | 2.0 | 79.15% | 0.8768 | -10.10% | 40 |
| 160 | 55 | 16 | 2.4 | 62.95% | 0.8515 | -8.91% | 40 |
| 160 | 55 | 20 | 1.6 | 103.22% | 0.7635 | -19.30% | 39 |
| 160 | 55 | 20 | 2.0 | 80.38% | 0.7472 | -17.13% | 37 |
| 160 | 55 | 20 | 2.4 | 64.09% | 0.7180 | -15.42% | 37 |
| 160 | 55 | 24 | 1.6 | 91.13% | 0.6607 | -23.95% | 35 |
| 160 | 55 | 24 | 2.0 | 70.95% | 0.6410 | -21.41% | 33 |
| 160 | 55 | 24 | 2.4 | 56.44% | 0.6116 | -19.25% | 33 |
| 160 | 66 | 16 | 1.6 | 86.41% | 0.8478 | -11.25% | 38 |
| 160 | 66 | 16 | 2.0 | 66.38% | 0.8399 | -9.37% | 37 |
| 160 | 66 | 16 | 2.4 | 53.23% | 0.8208 | -8.05% | 37 |
| 160 | 66 | 20 | 1.6 | 77.84% | 0.7034 | -16.96% | 36 |
| 160 | 66 | 20 | 2.0 | 61.02% | 0.6950 | -14.70% | 34 |
| 160 | 66 | 20 | 2.4 | 49.10% | 0.6737 | -12.97% | 34 |
| 160 | 66 | 24 | 1.6 | 72.73% | 0.6409 | -19.54% | 32 |
| 160 | 66 | 24 | 2.0 | 56.86% | 0.6289 | -17.03% | 30 |
| 160 | 66 | 24 | 2.4 | 45.57% | 0.6060 | -15.03% | 30 |
| 200 | 44 | 16 | 1.6 | 119.54% | 0.9452 | -12.37% | 40 |
| 200 | 44 | 16 | 2.0 | 90.60% | 0.9277 | -10.79% | 39 |
| 200 | 44 | 16 | 2.4 | 70.09% | 0.9223 | -8.82% | 37 |
| 200 | 44 | 20 | 1.6 | 115.17% | 0.7989 | -19.15% | 38 |
| 200 | 44 | 20 | 2.0 | 88.09% | 0.7723 | -17.10% | 37 |
| 200 | 44 | 20 | 2.4 | 65.33% | 0.7503 | -13.45% | 35 |
| 200 | 44 | 24 | 1.6 | 102.38% | 0.7043 | -23.42% | 34 |
| 200 | 44 | 24 | 2.0 | 78.27% | 0.6753 | -21.08% | 33 |
| 200 | 44 | 24 | 2.4 | 59.60% | 0.6705 | -16.25% | 31 |
| 200 | 55 | 16 | 1.6 | 102.29% | 0.8904 | -11.66% | 38 |
| 200 | 55 | 16 | 2.0 | 78.13% | 0.8770 | -10.10% | 37 |
| 200 | 55 | 16 | 2.4 | 62.24% | 0.8525 | -8.92% | 37 |
| 200 | 55 | 20 | 1.6 | 101.37% | 0.7599 | -19.29% | 36 |
| 200 | 55 | 20 | 2.0 | 77.97% | 0.7367 | -17.12% | 35 |
| 200 | 55 | 20 | 2.4 | 62.33% | 0.7084 | -15.41% | 35 |
| 200 | 55 | 24 | 1.6 | 90.16% | 0.6615 | -23.94% | 32 |
| 200 | 55 | 24 | 2.0 | 69.27% | 0.6357 | -21.40% | 31 |
| 200 | 55 | 24 | 2.4 | 55.39% | 0.6083 | -19.24% | 31 |
| 200 | 66 | 16 | 1.6 | 85.40% | 0.8488 | -11.25% | 36 |
| 200 | 66 | 16 | 2.0 | 65.47% | 0.8399 | -9.37% | 35 |
| 200 | 66 | 16 | 2.4 | 52.43% | 0.8200 | -8.05% | 35 |
| 200 | 66 | 20 | 1.6 | 76.41% | 0.6996 | -16.96% | 34 |
| 200 | 66 | 20 | 2.0 | 59.05% | 0.6838 | -14.70% | 33 |
| 200 | 66 | 20 | 2.4 | 47.46% | 0.6618 | -12.97% | 33 |
| 200 | 66 | 24 | 1.6 | 71.88% | 0.6418 | -19.54% | 30 |
| 200 | 66 | 24 | 2.0 | 55.37% | 0.6232 | -17.03% | 29 |
| 200 | 66 | 24 | 2.4 | 44.48% | 0.6012 | -15.03% | 29 |
| 240 | 44 | 16 | 1.6 | 100.40% | 0.8800 | -12.30% | 43 |
| 240 | 44 | 16 | 2.0 | 76.49% | 0.8609 | -10.73% | 42 |
| 240 | 44 | 16 | 2.4 | 60.22% | 0.8655 | -8.74% | 39 |
| 240 | 44 | 20 | 1.6 | 97.78% | 0.7377 | -20.48% | 41 |
| 240 | 44 | 20 | 2.0 | 76.03% | 0.7160 | -18.29% | 39 |
| 240 | 44 | 20 | 2.4 | 56.89% | 0.7000 | -13.94% | 36 |
| 240 | 44 | 24 | 1.6 | 85.76% | 0.6409 | -24.90% | 37 |
| 240 | 44 | 24 | 2.0 | 66.61% | 0.6163 | -22.30% | 35 |
| 240 | 44 | 24 | 2.4 | 51.43% | 0.6190 | -16.71% | 32 |
| 240 | 55 | 16 | 1.6 | 86.49% | 0.8309 | -11.62% | 40 |
| 240 | 55 | 16 | 2.0 | 66.80% | 0.8205 | -10.07% | 39 |
| 240 | 55 | 16 | 2.4 | 54.32% | 0.8049 | -8.89% | 38 |
| 240 | 55 | 20 | 1.6 | 86.76% | 0.7033 | -20.60% | 38 |
| 240 | 55 | 20 | 2.0 | 68.31% | 0.6888 | -18.29% | 36 |
| 240 | 55 | 20 | 2.4 | 55.57% | 0.6674 | -16.02% | 35 |
| 240 | 55 | 24 | 1.6 | 76.13% | 0.6031 | -25.36% | 34 |
| 240 | 55 | 24 | 2.0 | 59.90% | 0.5855 | -22.55% | 32 |
| 240 | 55 | 24 | 2.4 | 48.87% | 0.5659 | -19.82% | 31 |
| 240 | 66 | 16 | 1.6 | 72.96% | 0.8016 | -10.04% | 38 |
| 240 | 66 | 16 | 2.0 | 56.46% | 0.7958 | -8.58% | 37 |
| 240 | 66 | 16 | 2.4 | 46.22% | 0.7861 | -7.38% | 36 |
| 240 | 66 | 20 | 1.6 | 65.16% | 0.6504 | -17.16% | 36 |
| 240 | 66 | 20 | 2.0 | 51.52% | 0.6434 | -14.87% | 34 |
| 240 | 66 | 20 | 2.4 | 42.30% | 0.6298 | -12.66% | 33 |
| 240 | 66 | 24 | 1.6 | 60.61% | 0.5887 | -19.85% | 32 |
| 240 | 66 | 24 | 2.0 | 47.78% | 0.5784 | -17.27% | 30 |
| 240 | 66 | 24 | 2.4 | 39.29% | 0.5656 | -14.79% | 29 |

## Delete Best 3 Trades

| Name | Total Return | Sharpe | Max Drawdown | Breakeven Or Better |
|---|---:|---:|---:|---|
| `BTCUSDT` | 0.98% | 0.3528 | -81.58% | yes |
| `ETHUSDT` | 3.09% | 0.2631 | -72.56% | yes |
| `BTC+ETH equal-weight portfolio` | -40.95% | 0.4778 | -100.00% | no |

## Bull/Bear Segment Results

| Symbol | Segment | Return | Max Drawdown | Trade Count | Exposure Days | Note |
|---|---|---:|---:|---:|---:|---|
| `BTCUSDT` | 2017 bull | 0.00% | 0.00% | 0 | 0 | early crypto bull regime |
| `BTCUSDT` | 2018 bear | 0.00% | 0.00% | 0 | 0 | crypto bear market |
| `BTCUSDT` | 2020-2021 bull | 37.05% | -18.18% | 7 | 389 | pandemic liquidity bull regime |
| `BTCUSDT` | 2022 bear | 0.00% | 0.00% | 0 | 0 | crypto deleveraging bear market |
| `BTCUSDT` | 2023-2025 | 11.28% | -5.21% | 10 | 518 | post-2022 recovery regime |
| `BTCUSDT` | 2026-to-end | 0.00% | 0.00% | 0 | 0 | current partial period |
| `ETHUSDT` | 2017 bull | 0.00% | 0.00% | 0 | 0 | early crypto bull regime |
| `ETHUSDT` | 2018 bear | -1.03% | -1.42% | 1 | 8 | crypto bear market |
| `ETHUSDT` | 2020-2021 bull | 53.10% | -21.68% | 5 | 406 | pandemic liquidity bull regime |
| `ETHUSDT` | 2022 bear | 0.00% | 0.00% | 0 | 0 | crypto deleveraging bear market |
| `ETHUSDT` | 2023-2025 | 14.65% | -7.17% | 8 | 398 | post-2022 recovery regime |
| `ETHUSDT` | 2026-to-end | 0.00% | 0.00% | 0 | 0 | current partial period |

## Trade Statistics

- total trades: 35
- win rate: 48.57%
- average win: 62.28%
- average loss: -7.85%
- payoff ratio: 7.9328
- profit factor: 7.3640
- longest losing streak: 4
- best trade: 433.35%
- worst trade: -13.36%

## Known Limitations

- Offline validation only; no paper/live trading semantics are implemented.
- Funding crowding filter depends on availability of local M0 funding history.
- Spot liquidity, taxes, and exchange operational constraints are not modeled.

## M1A Gate Status

- Backtest code: `pass`
- Lookahead tests: `pass`
- Cost x2: `pass`
- Parameter neighborhood: `pass`
- Delete best 3 trades: `pass`
- OOS Sharpe >= 1: `fail`
- Trade count >= 80 combined: `fail`
- Final M1A status: under_review
