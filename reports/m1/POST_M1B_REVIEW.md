# Post-M1B Review

## Current Project State

- M0: accepted
- M1A trend: failed_validation
- M1F Freqtrade Lab: accepted_as_feasibility_lab
- M1B funding arbitrage: failed_validation
- No strategy is eligible for M2
- No live trading approval
- No paper trading with real API approval
- No execution/live approval
- No API trading permissions approval

## What Worked

- M0 data engineering completed a full read-only data loop.
- Freqtrade Lab was deployed to the VPS as a research/backtest/WebUI framework candidate.
- The project context system is established through `PROJECT_STATE.yaml`, `PROJECT_LEDGER.md`, `NEXT_ACTION.md`, `reports/INDEX.md`, and validation scripts.
- Both strategy tracks completed real validation instead of relying on guesses.
- M1B funding arbitrage was positive under both base cost and cost x2 assumptions.
- M1B max drawdown was low.
- M1B slept when funding dried up instead of relaxing entry rules.
- M1B did not pass the complete cycle-count threshold.

## What Failed

M1A trend:
- OOS Sharpe did not meet the threshold.
- Trade count did not meet the threshold.
- After deleting the best three trades, the portfolio was below breakeven.
- Parameter rescue is not allowed.

M1B funding arbitrage:
- complete cycles = 15
- required cycles = 20
- final status = failed_validation
- The strategy cannot enter M2.

## Decision Options

### Option A: Stop strategy development for now

Meaning:
- Pause the project at the research stage.
- Keep Freqtrade Lab as a learning and backtest environment.
- Do not continue development investment.

Pros:
- Stops further time spend.
- Avoids forced trading.
- Protects capital.

Cons:
- Does not continue exploring funding-arbitrage potential.

### Option B: M1B diagnostics only

Meaning:
- Do not change rules.
- Do not lower gates.
- Do not enter M2.
- Diagnose why cycles are insufficient.
- Check data coverage, entry threshold, payback threshold, historical phases, and funding regimes.
- Do not tune parameters to rescue the result.

Allowed:
- cycle scarcity analysis
- funding regime analysis
- data coverage analysis
- sensitivity report only as diagnostics, not optimization

Prohibited:
- lowering complete cycle threshold
- lowering payback threshold
- selecting best params
- changing final failed_validation to pass

### Option C: External arbitrage coordinator design review

Meaning:
- No live trading.
- No paper trading.
- No order placement.
- Design external coordinator architecture only.
- Study future management of spot long + perpetual short.
- Study net exposure, reconciliation, margin, single-leg incidents, and exchange anomalies.

Required boundaries:
- design only
- no execution
- no API key
- no M2
- no live trading

## Recommended Next Step

Recommended: a light Option B + Option C combination.

First run M1B diagnostics to determine whether the failed cycle-count gate is mainly sample scarcity. In parallel, perform only an external arbitrage coordinator design review. Do not write execution code and do not enter M2 directly.

## Updated Project Decision

- No strategy is approved for M2.
- M1B failed_validation remains active.
- Next permitted work requires explicit scope:
  - diagnostics only; or
  - design review only.

## Not Investment Advice

Historical backtests do not represent future returns and are not investment advice.
