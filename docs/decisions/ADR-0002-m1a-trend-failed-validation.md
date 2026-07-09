# ADR-0002 M1A Trend Failed Validation

- Status: Accepted
- Date: 2026-07-09

## Context

M1A evaluated the fixed BTC/ETH trend leg. The validation report recorded
insufficient OOS Sharpe, insufficient combined trade count, and failure after
deleting the best three trades.

## Decision

M1A trend validation is recorded as failed_validation. The trend leg is not
eligible for M2, paper trading, or live trading.

## Consequences

- Do not tune parameters merely to pass the validation gate.
- Do not lower OOS Sharpe, trade count, or robustness thresholds.
- Do not promote the trend leg to M2 without a new approved validation phase.

## Prohibited Misinterpretations

- A merged failed_validation report is not a strategy approval.
- Passing CI for the report does not mean the strategy passed validation.
- The trend leg must not be rescued by leverage, smaller timeframes, or altcoins
  without a new approved scope.
