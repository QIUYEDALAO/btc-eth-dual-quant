# M1B Decision

- Status: suitability_conclusion_b_accepted
- Scope: M1B funding-rate-arbitrage research only
- No live trading
- No paper trading with real API
- No execution/live
- No order placement/cancel
- No API trading permissions

## Decision

Conclusion B is accepted:

Freqtrade is partially suitable for M1B research, but it is not sufficient as a native spot-long + perpetual-short funding-arbitrage backtest or execution engine. M1B requires an external portfolio/accounting/funding backtester or coordinator to model:

- spot long leg
- USDT perpetual short leg
- funding income by settlement period
- basis PnL
- spot leg PnL
- perp short leg PnL
- net exposure <= 5%
- single-leg exposure risk
- reconciliation across legs
- margin stress / liquidation risk diagnostics

## Consequences

- Do not migrate M1B fully to native Freqtrade.
- Keep Freqtrade as a research/UI/futures-leg smoke framework.
- Retain custom offline funding-arbitrage accounting backtester as research candidate.
- Do not merge PR #5 as completed numerical validation unless report status clearly remains under_review or failed/pass based on real numerical data.
- No live trading is allowed.
- No M2 approval is granted.

## Next

The real numerical M1B funding-arbitrage report has now been generated using local M0 public data, still offline only, with no API keys and no trading execution.

## Numerical Report Outcome

- Report: `reports/m1/M1B_FUNDING_ARBITRAGE_BACKTEST_REPORT.md`
- Provenance: `reports/m1/M1B_DATA_RUN_PROVENANCE.md`
- Metrics basis: funding-period time-indexed equity curve
- OOS split basis: time-based last 30%
- Previous cycle-level volatility/Sharpe metrics superseded: yes
- Final M1B status: failed_validation
- Base cost total return: 59.5509%
- Cost x2 total return: 55.8009%
- Complete cycles: 15
- Required complete cycles: 20
- Corrected annualized volatility: 1.3287%
- Corrected Sharpe: 7.0355
- Corrected OOS Sharpe: 11.5406
- OOS equity points: 1645
- Max drawdown: 0.9124%

The funding-arbitrage research result remains not approved for M2, paper/live trading, API keys, execution/live, order placement, cancellation, or real capital deployment.
