# ADR-0010: Candidate Queue And Common Validation Gates

- Status: accepted for governance only
- Date: 2026-07-11

## Decision

The BTC/ETH two-asset research queue is frozen before any new rule design:

1. M1E: one-hour volatility-compression expansion breakout.
2. M1G: one-hour panic-dislocation mean reversion.
3. M1H: the already registered `FUNDING-EXTREME-SPOT-CONTRARIAN` hypothesis.

Only M1E may become eligible for a separately approved design review. M1G and M1H remain unopened. A failed candidate moves to the next queue item without parameter rescue. If all three fail, BTC/ETH two-asset indicator research stops; any 10-20 asset expansion requires a new ADR.

M1A, M1B, and M1C are retrospectively recorded as three opened OOS trials. M1D, M1E, M1G, the daily panic candidate, and M1H remain unopened. DSR uses the count of candidates whose OOS was actually opened. A parameter or rule change after an OOS opening creates a new candidate and cannot erase the prior trial.

## Common Gates

Freqtrade is the sole single-leg return authority. Python may validate timestamps, daily-MTM equity, metrics, and exported trades. All candidates share the four fixed costs, sealed final-30% OOS, 1800/540-day calendar minimum, 80/20 completed-trade minimum, OOS daily-MTM Sharpe at least 1.0, PSR at least 0.95, maximum daily-MTM drawdown 15%, positive Base and Cost-x2 full/OOS returns, nonnegative return after deleting the best three trades, bias checks, zero unexplained gaps, and the risk-matched benchmark gates.

IS paper feasibility must project at least 120 full and 30 OOS trades, and typical gross displacement must be at least three times the 0.60% Cost-x2 roundtrip, or 1.80%. This stage may not report formal strategy returns.

Stress A/B and DSR are mandatory diagnostics. This ADR does not invent an unapproved DSR threshold or a generic stress hard threshold. Each candidate must freeze any stress hard Gate before implementation; it may not choose it after seeing OOS.

## Safety

This decision authorizes no rule design, strategy code, backtest, OOS access, API key, private endpoint, paper/live mode, order operation, execution module, or M2 progression.
