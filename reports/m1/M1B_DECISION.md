# M1B Decision

- Status: paused_for_freqtrade_suitability_review
- Scope: M1B funding-rate-arbitrage research only
- No live trading
- No paper trading with real API
- No execution/live
- No order placement/cancel
- No API trading permissions

## Decision

- Do not proceed with custom M1B numerical backtest until Freqtrade suitability is reviewed.
- If Freqtrade can model funding arbitrage correctly, migrate M1B to Freqtrade.
- If Freqtrade cannot model spot-long + perp-short correctly, retain the custom offline arbitrage backtester only for research/accounting validation.
- No live trading is allowed.

## Current Suitability Finding

Freqtrade can support parts of the workflow: backtesting, Binance spot research, futures mode, and futures short probes. It does not appear to natively model one coordinated portfolio that is simultaneously spot long and USDT perpetual short with cross-leg synchronization, net exposure controls, basis PnL decomposition, and funding-income reconciliation.

Current conclusion: Freqtrade is partially suitable and needs an external portfolio/accounting coordinator for M1B funding-rate-arbitrage validation.

## PR #5 Handling

- Keep PR #5 open.
- Do not merge PR #5 as a completed M1B numerical validation.
- Do not tag M1B.
- Do not enter M2.
