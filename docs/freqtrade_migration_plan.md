# Freqtrade Migration Plan

The project no longer prioritizes building a full trading bot from scratch.
M0 and M1A remain valuable as data, validation, and risk-control baselines.
Freqtrade is now being evaluated as a candidate framework for backtesting,
dry-run tooling, WebUI hosting, and strategy hosting.

## Current Stage

- Current phase: M1F Freqtrade feasibility.
- This is not M2.
- M1A trend validation is complete and failed validation.
- The trend leg is not eligible for live trading, paper trading, or M2.

## Allowed Next Work

The next permitted evaluation is whether Freqtrade can support the funding-rate
arbitrage concept safely and faithfully enough for a later backtest-validation
stage.

## Hard Boundaries

- No live trading.
- No paper trading with real API credentials.
- No `execution/live`.
- No order placement or cancellation.
- No API trading permissions.
- No API keys in files, reports, logs, or git.
