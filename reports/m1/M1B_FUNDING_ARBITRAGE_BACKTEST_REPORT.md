# M1B Funding Arbitrage Backtest Report

- Status: failed_validation
- Scope: funding-rate-arbitrage offline backtest only
- No live trading
- No paper trading with real API
- No execution/live
- No order placement
- No API trading permissions
- Not investment advice

## 1. Data Sources

- spot_klines
- um_futures_klines
- funding_rate_history
- mark_price_klines
- index_price_klines
- premium_index_klines
- Source mode: local M0 public data only

## 2. Data Range

- Portfolio: 2020-01-01 00:00:00 UTC -> 2024-12-31 00:00:00 UTC
- BTCUSDT: 2020-01-01 00:00:00 UTC -> 2024-12-31 00:00:00 UTC
- ETHUSDT: 2020-01-01 00:00:00 UTC -> 2024-12-31 00:00:00 UTC

## 3. IS/OOS Split

- IS start/end: 2020-01-01 00:00:00 UTC -> 2023-07-02 04:48:00 UTC
- OOS start/end: 2023-07-02 04:48:00 UTC -> 2024-12-31 00:00:00 UTC
- OOS was not used for parameter selection.

## 4. Strategy Rules

- Structure: spot long + USDT perpetual short, equal notional hedge.
- Entry: trailing 3-day funding mean annualized >= 8%, current funding positive, and payback threshold satisfied.
- Exit: trailing 3-day funding mean annualized < 2%, or two consecutive negative funding settlements, or forced final close.
- No leverage expansion, martingale, grid, loss adding, symbol rotation, paper trading, or exchange access.

## 5. Payback Threshold Calculation

- expected_hold_days: 14
- roundtrip_cost_base: 0.5000%
- min_payback_ratio: 2.0
- required annualized funding APR: 26.0714%
- 8% annualized funding is rejected by this payback threshold.

## 6. Cost Assumptions

- spot fee per side: 0.1000%
- futures fee per side: 0.0500%
- slippage per leg per fill: 0.0500%
- base full roundtrip baseline: 0.5000%
- cost_x2 doubles all modeled fees and slippage.

## 7. Base Cost Results

- total_return: 119.1019%
- annualized_return: 16.9747%
- annualized_volatility: 135.5083%
- sharpe: 15.0513
- max_drawdown: 1.1040%
- complete_cycles: 15
- win_rate: 100.0000%
- profit_factor: inf
- average_holding_days: 94.76
- funding_income_total: 1.253406
- basis_pnl_total: 0.012613
- fees_total: 0.045000
- slippage_total: 0.030000
- worst_cycle: 0.1062%
- best_cycle: 34.6108%
- longest_sleep_days: 713.00
- percent_time_in_market: 77.8386%

## 8. Cost x2 Results

- total_return: 111.6019%
- annualized_return: 16.1631%
- annualized_volatility: 137.4752%
- sharpe: 14.2041
- max_drawdown: 1.1040%
- complete_cycles: 15
- win_rate: 93.3333%
- profit_factor: 284.3890
- average_holding_days: 94.76
- funding_income_total: 1.253406
- basis_pnl_total: 0.012613
- fees_total: 0.090000
- slippage_total: 0.060000
- worst_cycle: -0.3938%
- best_cycle: 34.1108%
- longest_sleep_days: 713.00
- percent_time_in_market: 77.8386%

## 9. BTCUSDT Results

- total_return: 49.1569%
- annualized_return: 8.3202%
- annualized_volatility: 138.0724%
- sharpe: 14.1515
- max_drawdown: 0.3409%
- complete_cycles: 8
- win_rate: 100.0000%
- profit_factor: inf
- average_holding_days: 71.88
- funding_income_total: 0.520475
- basis_pnl_total: 0.011093
- fees_total: 0.024000
- slippage_total: 0.016000
- worst_cycle: 0.1062%
- best_cycle: 26.1315%
- longest_sleep_days: 713.00
- percent_time_in_market: 31.4896%

## 10. ETHUSDT Results

- total_return: 69.9450%
- annualized_return: 11.1825%
- annualized_volatility: 175.9763%
- sharpe: 17.0713
- max_drawdown: 1.1040%
- complete_cycles: 7
- win_rate: 100.0000%
- profit_factor: inf
- average_holding_days: 120.90
- funding_income_total: 0.732930
- basis_pnl_total: 0.001519
- fees_total: 0.021000
- slippage_total: 0.014000
- worst_cycle: 1.8449%
- best_cycle: 34.6108%
- longest_sleep_days: 670.33
- percent_time_in_market: 46.3490%

## 11. Portfolio Combined Results

- BTC+ETH allocation comparison: equal-weight combined cycles=15
- Base total return: 119.1019%
- Cost x2 total return: 111.6019%

## 12. PnL Decomposition

- Funding income contribution: 1.253406
- Basis PnL contribution: 0.012613
- Fees contribution: -0.045000
- Slippage contribution: -0.030000
- Worst cycle: BTCUSDT 0.1062%
- Best cycle: ETHUSDT 34.6108%

## 13. Cycle Table

| symbol | entry UTC | exit UTC | days | net_return | funding | basis | fees | slippage | reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BTCUSDT | 2020-01-17 16:00:00 UTC | 2020-03-13 00:00:00 UTC | 55.33 | 6.1736% | 0.065419 | 0.001317 | 0.003000 | 0.002000 | negative_funding_streak |
| ETHUSDT | 2020-01-20 08:00:00 UTC | 2020-03-13 08:00:00 UTC | 53.00 | 7.5663% | 0.080312 | 0.000350 | 0.003000 | 0.002000 | low_funding_mean |
| ETHUSDT | 2020-05-02 16:00:00 UTC | 2020-09-21 00:00:00 UTC | 141.33 | 9.1925% | 0.095461 | 0.001464 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2020-05-09 08:00:00 UTC | 2020-05-22 08:00:00 UTC | 13.00 | 0.1062% | 0.004551 | 0.001511 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2020-07-27 08:00:00 UTC | 2020-09-15 08:00:00 UTC | 50.00 | 3.7909% | 0.040577 | 0.002332 | 0.003000 | 0.002000 | negative_funding_streak |
| ETHUSDT | 2020-10-22 00:00:00 UTC | 2021-05-19 16:00:00 UTC | 209.67 | 34.6108% | 0.355077 | -0.003969 | 0.003000 | 0.002000 | low_funding_mean |
| BTCUSDT | 2020-11-19 16:00:00 UTC | 2021-05-22 00:00:00 UTC | 183.33 | 26.1315% | 0.264306 | 0.002009 | 0.003000 | 0.002000 | low_funding_mean |
| ETHUSDT | 2021-08-16 00:00:00 UTC | 2021-09-25 00:00:00 UTC | 40.00 | 1.8781% | 0.023486 | 0.000295 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2021-09-01 16:00:00 UTC | 2021-09-24 08:00:00 UTC | 22.67 | 0.5211% | 0.009382 | 0.000829 | 0.003000 | 0.002000 | negative_funding_streak |
| ETHUSDT | 2021-10-16 00:00:00 UTC | 2022-01-10 08:00:00 UTC | 86.33 | 3.6943% | 0.040884 | 0.001059 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2021-10-16 16:00:00 UTC | 2022-01-13 00:00:00 UTC | 88.33 | 4.3809% | 0.047812 | 0.000997 | 0.003000 | 0.002000 | negative_funding_streak |
| ETHUSDT | 2023-11-11 16:00:00 UTC | 2024-08-05 08:00:00 UTC | 267.67 | 11.1581% | 0.115325 | 0.001256 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2023-12-27 00:00:00 UTC | 2024-04-19 00:00:00 UTC | 114.00 | 6.4791% | 0.068243 | 0.001548 | 0.003000 | 0.002000 | negative_funding_streak |
| BTCUSDT | 2024-11-12 16:00:00 UTC | 2024-12-31 00:00:00 UTC | 48.33 | 1.5735% | 0.020186 | 0.000550 | 0.003000 | 0.002000 | forced_end_exit |
| ETHUSDT | 2024-11-12 16:00:00 UTC | 2024-12-31 00:00:00 UTC | 48.33 | 1.8449% | 0.022385 | 0.001064 | 0.003000 | 0.002000 | forced_end_exit |

## 14. Sleep Periods

| symbol | start UTC | end UTC | days | reason |
| --- | --- | --- | ---: | --- |
| BTCUSDT | 2020-01-01 00:00:00 UTC | 2020-01-17 16:00:00 UTC | 16.67 | below_entry_threshold |
| BTCUSDT | 2020-03-13 00:00:00 UTC | 2020-05-09 08:00:00 UTC | 57.33 | below_entry_threshold |
| BTCUSDT | 2020-05-22 08:00:00 UTC | 2020-07-27 08:00:00 UTC | 66.00 | below_entry_threshold |
| BTCUSDT | 2020-09-15 08:00:00 UTC | 2020-11-19 16:00:00 UTC | 65.33 | below_entry_threshold |
| BTCUSDT | 2021-05-22 00:00:00 UTC | 2021-09-01 16:00:00 UTC | 102.67 | below_entry_threshold |
| BTCUSDT | 2021-09-24 08:00:00 UTC | 2021-10-16 16:00:00 UTC | 22.33 | below_entry_threshold |
| BTCUSDT | 2022-01-13 00:00:00 UTC | 2023-12-27 00:00:00 UTC | 713.00 | below_entry_threshold |
| BTCUSDT | 2024-04-19 00:00:00 UTC | 2024-11-12 16:00:00 UTC | 207.67 | below_entry_threshold |
| ETHUSDT | 2020-01-01 00:00:00 UTC | 2020-01-20 08:00:00 UTC | 19.33 | below_entry_threshold |
| ETHUSDT | 2020-03-13 08:00:00 UTC | 2020-05-02 16:00:00 UTC | 50.33 | below_entry_threshold |
| ETHUSDT | 2020-09-21 00:00:00 UTC | 2020-10-22 00:00:00 UTC | 31.00 | below_entry_threshold |
| ETHUSDT | 2021-05-19 16:00:00 UTC | 2021-08-16 00:00:00 UTC | 88.33 | below_entry_threshold |
| ETHUSDT | 2021-09-25 00:00:00 UTC | 2021-10-16 00:00:00 UTC | 21.00 | below_entry_threshold |
| ETHUSDT | 2022-01-10 08:00:00 UTC | 2023-11-11 16:00:00 UTC | 670.33 | below_entry_threshold |
| ETHUSDT | 2024-08-05 08:00:00 UTC | 2024-11-12 16:00:00 UTC | 99.33 | below_entry_threshold |

## 15. OOS Results

- OOS total_return: 25.4365%
- OOS Sharpe: 26.1582
- OOS complete cycles: 5

## 16. Funding Interval Diagnostics

- Portfolio interval source: component_fundingRate.fundingTime
- Conservative interval hours used: 8.0000
- BTCUSDT interval hours: 8.0000; anomalies: ['none']
- ETHUSDT interval hours: 8.0000; anomalies: ['none']
- Basis data status: basis_data_unavailable

## 17. Failure / Graceful Sleep Analysis

- Funding dries up gracefully gate: pass
- Longest no-trade / sleep period: 713.00 days
- If funding is below threshold, the engine remains flat instead of relaxing entry rules.

## 18. Known Limitations

- Offline validation only; no execution feasibility is implied.
- Private commission and income payloads are not used.
- Funding settlement mechanics are simplified to equal-notional period-rate accounting.
- Mark/index/premium data are diagnostics; spot and perpetual close prices drive modeled hedge PnL.

## 19. M1B Gate Status

| Gate | Status |
| --- | --- |
| Backtest code | pass |
| Funding interval not hardcoded | pass |
| Payback threshold | pass |
| Base cost positive | pass |
| Cost x2 positive | pass |
| Complete cycles >= 20 | fail |
| OOS Sharpe >= 1.0 | pass |
| Max drawdown <= 5% | pass |
| Funding dries up gracefully | pass |
| No lookahead | pass |
| Final M1B status | failed_validation |

## 20. Decision

- Decision: failed_validation; do not promote funding-rate-arbitrage to execution or paper/live stages.
- No result in this report approves live trading.

## Cost x2 Symbol Detail

### BTCUSDT cost_x2
- total_return: 45.1569%
- annualized_return: 7.7333%
- annualized_volatility: 139.5671%
- sharpe: 13.0816
- max_drawdown: 0.3727%
- complete_cycles: 8
- win_rate: 87.5000%
- profit_factor: 115.6662
- average_holding_days: 71.88
- funding_income_total: 0.520475
- basis_pnl_total: 0.011093
- fees_total: 0.048000
- slippage_total: 0.032000
- worst_cycle: -0.3938%
- best_cycle: 25.6315%
- longest_sleep_days: 713.00
- percent_time_in_market: 31.4896%

### ETHUSDT cost_x2
- total_return: 66.4450%
- annualized_return: 10.7210%
- annualized_volatility: 176.7765%
- sharpe: 16.3409
- max_drawdown: 1.1040%
- complete_cycles: 7
- win_rate: 100.0000%
- profit_factor: inf
- average_holding_days: 120.90
- funding_income_total: 0.732930
- basis_pnl_total: 0.001519
- fees_total: 0.042000
- slippage_total: 0.028000
- worst_cycle: 1.3449%
- best_cycle: 34.1108%
- longest_sleep_days: 670.33
- percent_time_in_market: 46.3490%
