# M1B Final Decision

- M1B final status: failed_validation
- M1B PR: #5
- merged commit: 105fd0dc39607100f70210c79f4bfe5f7413e479
- tag: m1b-funding-failed-validation-v0.5.0
- metrics basis: funding-period time-indexed equity curve
- OOS split basis: time-based last 30%
- Freqtrade suitability conclusion: B accepted
- Freqtrade role: research/UI/futures-leg smoke only
- External portfolio/accounting/funding backtester: still required

## Key Results

- Base cost total return: 59.5509%
- Cost x2 total return: 55.8009%
- Corrected annualized volatility: 1.3287%
- Corrected Sharpe: 7.0355
- Corrected OOS Sharpe: 11.5406
- OOS equity points: 1645
- Complete cycles: 15
- Required complete cycles: 20
- Max drawdown: 0.9124%

## Gate Result

- Backtest code: pass
- Funding interval not hardcoded: pass
- Payback threshold: pass
- Base cost positive: pass
- Cost x2 positive: pass
- Complete cycles >= 20: fail
- OOS Sharpe >= 1.0: pass
- Max drawdown <= 5%: pass
- Funding dries up gracefully: pass
- No lookahead: pass
- Final M1B status: failed_validation

## Decision

M1B funding-rate-arbitrage is not eligible for M2 because the complete cycle-count gate failed.

This result does not approve:
- live trading
- paper trading with real API
- execution/live
- order placement
- API trading permissions
- funding arbitrage execution
- real capital deployment

## Allowed Future Work

Only after explicit approval:
- M1B diagnostics / postmortem
- external arbitrage coordinator design review
- additional data coverage review
