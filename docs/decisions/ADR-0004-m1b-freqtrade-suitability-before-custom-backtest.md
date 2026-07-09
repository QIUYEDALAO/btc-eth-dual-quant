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

## Current PR #5 Finding

- PR #5 currently contains a suitability report with conclusion B.
- B means Freqtrade is partially suitable but requires an external
  portfolio/accounting/funding backtester for spot-long plus perpetual-short
  funding-rate arbitrage.
- This finding has been accepted on PR #5 but is not yet merged into main.
- PR #5 must remain open and must not be treated as completed M1B numerical
  validation until a real numerical report exists.

## PR #5 Review Outcome

- Conclusion B is accepted on PR #5.
- Freqtrade is partially suitable for research and futures-leg smoke tests.
- Freqtrade is not sufficient as native spot-long + perpetual-short
  funding-arbitrage backtest or execution engine.
- External portfolio/accounting/funding backtester remains required.
- This outcome does not approve M2, live trading, paper trading, API keys, or
  order placement.

## Prohibited Misinterpretations

- A Freqtrade futures short smoke test does not prove full spot-long plus
  perpetual-short arbitrage support.
- A two-bot setup does not remove leg synchronization or reconciliation risk.
- A custom offline backtester must not become execution/live or paper trading.
