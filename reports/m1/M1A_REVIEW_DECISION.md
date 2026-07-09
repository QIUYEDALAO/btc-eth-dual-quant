# M1A Review Decision

generated_utc: 2026-07-09T03:50:00+00:00

## Status

- M1A review status: failed_validation
- Scope: BTC/ETH spot long-only trend following

## Parameters Tested

- SMA 200
- Donchian 55/20
- ATR(20)
- 2x ATR stop
- 1% risk
- 20% vol cap

## Validation Criteria

- OOS Sharpe >= 1.0
- Combined trades >= 80
- Cost x2 remains positive
- Delete best 3 trades remains breakeven or better
- No lookahead

## Actual Results

- OOS portfolio Sharpe = 0.6440
- Combined trade count = 35
- Delete best 3 portfolio return = -40.95%
- Delete best 3 portfolio breakeven_or_better = no

## Decision

- Trend leg is not eligible for M2 paper trading
- Trend leg is not eligible for live trading
- Do not tune parameters to pass
- Do not increase leverage
- Do not add smaller timeframes or altcoins as a rescue
- Record as failed validation

## Allowed Next Steps

- Merge PR only as a truthful validation artifact if checks pass
- Then either perform M1A diagnostics in a new branch, or start M1B funding-rate-arbitrage backtest only after approval

## Prohibited

- live trading
- paper trading
- execution/live
- order placement
- API trading permissions
