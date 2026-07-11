# Strategy Candidate Queue Governance

- Status: queue_frozen_design_only
- Scope: Q-01 candidate order and Q-02 common validation policy
- Historical opened OOS trials: 3
- Opened trials: M1A, M1B, M1C
- Current OOS access authorized: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Queue

| Order | Alias | Registered candidate | Economic family | Current state | Failure transition |
| ---: | --- | --- | --- | --- | --- |
| 1 | M1E | `M1E-1H-TREND-BREAKOUT` | 1h volatility-compression expansion breakout | design review requires separate approval | M1G |
| 2 | M1G | `M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION` | 1h forced-selling mean reversion | declared unopened | M1H |
| 3 | M1H | `FUNDING-EXTREME-SPOT-CONTRARIAN` | funding-extreme spot contrarian | declared unopened | stop BTC/ETH two-asset research |

M1H is an alias for the existing registered hypothesis, not a duplicate trial.

## Common Policy

- Costs per side: Base 0.15%, Cost x2 0.30%, Stress A 0.40%, Stress B 0.55%.
- Paper budget: projected full trades >= 120; projected OOS trades >= 30.
- Paper gross displacement: >= 1.80%, equal to 3x the 0.60% Cost-x2 roundtrip.
- Numerical trades: full >= 80; OOS >= 20.
- OOS daily-MTM Sharpe >= 1.0; PSR >= 0.95; daily-MTM MaxDD <= 15%.
- Base and Cost-x2 full/OOS returns must be strictly positive.
- Return after deleting the best three trades must be >= 0.
- Lookahead and recursive analysis must pass; unexplained data gaps must be zero.
- Strategy must beat the risk-matched benchmark on total return without worse Sharpe or drawdown.
- Stress A/B and DSR are mandatory diagnostics. Candidate-specific hard thresholds must be frozen before implementation.

## Failure And Stop Policy

- No failed candidate may be rescued by tuning, leverage, a smaller timeframe, repeated OOS, or lower Gates.
- Failure moves only to the next preregistered candidate after separate approval.
- Three failures stop BTC/ETH two-asset indicator research.
- A broader liquid-USDT universe requires a separate ADR covering historical constituents, liquidity, survivorship, delisting, and concentration.

This report does not approve a strategy or claim profitability.
