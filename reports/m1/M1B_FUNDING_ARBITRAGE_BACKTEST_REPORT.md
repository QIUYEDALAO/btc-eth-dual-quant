# M1B Funding Arbitrage Backtest Report

- Status: under_review
- Scope: funding-rate-arbitrage offline backtest only
- No live trading
- No paper trading with real API
- No execution/live
- No order placement
- No API trading permissions
- Not investment advice

## 1. Data Sources

- Required local M0 public datasets: spot_klines, um_futures_klines, funding_rate_history, mark_price_klines, index_price_klines, premium_index_klines.
- This committed report is an under_review placeholder because local M0 public raw/DuckDB data was not present in this worktree when `scripts/m1b_run_funding_arbitrage_backtest.py` was executed.
- The report generation script does not access the network, does not read API keys, does not run private smoke, and does not use Freqtrade as an execution engine.

## 2. Data Range

- BTCUSDT: not generated; local M0 public data unavailable.
- ETHUSDT: not generated; local M0 public data unavailable.
- Portfolio: not generated; local M0 public data unavailable.

## 3. IS/OOS Split

- IS start/end: not generated.
- OOS start/end: not generated.
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

- not generated; local M0 public data unavailable.

## 8. Cost x2 Results

- not generated; local M0 public data unavailable.

## 9. BTCUSDT Results

- not generated; local M0 public data unavailable.

## 10. ETHUSDT Results

- not generated; local M0 public data unavailable.

## 11. Portfolio Combined Results

- not generated; local M0 public data unavailable.

## 12. PnL Decomposition

- Funding income contribution: not generated.
- Basis PnL contribution: not generated.
- Fees/slippage contribution: not generated.
- Worst cycle: not generated.
- Best cycle: not generated.

## 13. Cycle Table

- not generated; local M0 public data unavailable.

## 14. Sleep Periods

- not generated; local M0 public data unavailable.

## 15. OOS Results

- not generated; local M0 public data unavailable.

## 16. Funding Interval Diagnostics

- Funding interval is inferred from local fundingRate.fundingTime history by the M1B engine.
- No hardcoded funding interval is used.
- Funding interval anomalies are reported by the generation script when local data is available.

## 17. Failure / Graceful Sleep Analysis

- not generated; local M0 public data unavailable.
- When funding is below threshold, the engine remains flat instead of relaxing entry rules.

## 18. Known Limitations

- Offline validation only; no execution feasibility is implied.
- Private commission and income payloads are not used.
- Local M0 public raw/DuckDB data is required to produce final numerical results.
- Mark/index/premium data are diagnostics; spot and perpetual close prices drive modeled hedge PnL.

## 19. M1B Gate Status

| Gate | Status |
| --- | --- |
| Backtest code | pass |
| Funding interval not hardcoded | pass |
| Payback threshold | pass |
| Base cost positive | under_review |
| Cost x2 positive | under_review |
| Complete cycles >= 20 | under_review |
| OOS Sharpe >= 1.0 | under_review |
| Max drawdown <= 5% | under_review |
| Funding dries up gracefully | under_review |
| No lookahead | pass |
| Final M1B status | under_review |

## 20. Decision

- Decision: under_review; numerical validation is pending local M0 public data.
- No result in this report approves live trading.
