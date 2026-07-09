# ADR-0004 M1B Freqtrade Suitability Before Custom Backtest

- Status: Accepted
- Date: 2026-07-09

## Context

PR #5 introduced custom M1B funding-arbitrage offline backtest work, but the
custom numerical report remains under review. The user raised a valid concern:
Freqtrade has backtesting capability, so the project should confirm whether
Freqtrade can accurately model spot-long plus perpetual-short funding-rate
arbitrage before continuing custom numerical validation.

## Decision

Do not continue custom M1B numerical validation until Freqtrade suitability is
reviewed.

If Freqtrade can model funding arbitrage correctly, migrate M1B to Freqtrade.

If Freqtrade cannot model spot-long plus perp-short correctly, retain the custom
offline arbitrage backtester only as research.

## Consequences

- PR #5 remains open and must not be merged as completed numerical validation.
- The next M1B output should be a suitability decision A/B/C and updated M1B
  decision report.
- M2 remains not allowed.

## Prohibited Misinterpretations

- A Freqtrade futures short smoke test does not prove full spot-long plus
  perpetual-short arbitrage support.
- A two-bot setup does not remove leg synchronization or reconciliation risk.
- A custom offline backtester must not become execution/live or paper trading.
