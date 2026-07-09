# M1C BTC/ETH/Cash Rotation Design

Design status: design_pass

## Scope

M1C is a Binance spot, long-only, UTC-daily research candidate implemented only
in Freqtrade. It may hold BTC/USDT, ETH/USDT, or cash. This design does not
authorize M2, dry-run, live trading, API credentials, or an execution module.
Python may validate timestamps and exported evidence, but it must not calculate
a second single-leg strategy return series.

## Immutable Strategy Contract

- Pairs: `BTC/USDT`, `ETH/USDT`.
- Timeframe: UTC `1d` candles.
- Decision candle: the completed Sunday UTC candle (`weekday == 6`).
- Fill: the next daily candle open; a Sunday signal may first act at Monday
  `00:00:00Z`.
- Absolute trend: `close > SMA(200)` using the signal pair's completed closes.
- Relative strength: `close / close.shift(90) - 1`.
- Eligible: absolute trend is true and relative strength is strictly positive.
- Both eligible: choose the higher relative strength.
- Exact tie: choose BTC/USDT.
- One eligible: choose it.
- None eligible: hold cash.
- Re-evaluate only on completed Sunday candles.
- Maximum open trades: one.
- Maximum capital available to the strategy: 50% of account equity; at least
  50% remains outside the strategy's tradable balance.
- Emergency stoploss: 20% from the Freqtrade trade entry price.
- Shorting, leverage, position adjustment, ROI exits, trailing stop, martingale,
  grid logic, hyperopt, and parameter-neighborhood selection are disabled.

The machine-readable copy is
`freqtrade_lab/m1c-btc-eth-rotation-contract.json`. A change to any immutable
field requires a new P1 design review; it is not a P2 implementation detail.

## Freqtrade Representation

The strategy whitelist contains exactly the two pairs. Both 1d dataframes are
registered as informative pairs and aligned by their UTC `date`. Each pair's
indicator dataframe receives the same BTC and ETH score columns. An entry is
emitted only for the selected winner, and an exit is emitted for a held pair
when the selected target is the other pair or cash.

`max_open_trades = 1`, `stake_amount = "unlimited"`, and
`tradable_balance_ratio = 0.5` express one 50%-of-equity position. The strategy
uses `minimal_roi = {"0": 100.0}` only as an effectively unreachable ROI
threshold; exit signals and the emergency stoploss are the permitted exits.

The strategy must not read the process wall clock to decide whether a candle is
Sunday. It must derive the decision weekday from each dataframe row's UTC
timestamp. Missing either pair at a timestamp makes the target cash for that
timestamp and records a data-alignment diagnostic.

## Framework Capability Evidence

Pinned Freqtrade release `2026.6` resolves to source commit
`b604e2fd70539f7f73d3c62c16ce0b155bbab319`. Static review of
`freqtrade/optimize/backtesting.py` at that commit established:

1. `_get_ohlcv_as_lists()` shifts entry and exit signals by one candle before
   the backtest loop. A completed Sunday signal therefore acts no earlier than
   Monday open.
2. `_time_pair_generator_det()` puts pairs with open trades first.
3. `backtest_loop()` processes the old pair's exit and
   `LocalTrade.close_bt_trade()` decrements the open-trade count immediately.
4. The later winner pair can then pass `trade_slot_available()` at the same
   Monday timestamp.

This proves that a different-pair rotation can be represented deterministically
without a second backtester. P2 must still run a pinned-image fixture that
asserts old-pair close time equals new-pair open time. If the runtime fixture
disagrees, P2 becomes `blocked_framework_capability` and no workaround engine is
allowed.

Official behavior references:

- https://www.freqtrade.io/en/stable/backtesting/
- https://www.freqtrade.io/en/stable/strategy-customization/
- https://www.freqtrade.io/en/stable/configuration/
- https://www.freqtrade.io/en/stable/lookahead-analysis/
- https://docs.freqtrade.io/en/stable/recursive-analysis/
- https://github.com/freqtrade/freqtrade/tree/2026.6

## Data and Time Semantics

- `date` is the candle open timestamp; `close_time` is `date + 1 day`.
- Indicator values at row `t` may use only rows at or before `t`.
- The row's signal becomes executable only at row `t + 1` open.
- BTC and ETH scores must share exactly the same UTC timestamp.
- Incomplete current-day candles are excluded before analysis.
- A missing or non-finite SMA, return, BTC row, or ETH row cannot create an
  entry.

## P2 Acceptance Tests

P2 must prove all of the following with deterministic fixtures and the pinned
Freqtrade runtime:

- SMA200 and 90-day return do not use future rows.
- Sunday close signals first act at Monday open.
- BTC and ETH ranking rows use identical UTC timestamps.
- BTC wins exact ties.
- no eligible pair produces cash.
- no timestamp has more than one open trade.
- the emergency stoploss is exactly `-0.20`.
- tradable capital is capped at 50%.
- a rotation closes the old pair before opening the new pair at the same open.
- lookahead-analysis and recursive-analysis complete without a reported bias.
- no live, dry-run, credential, order, or execution entry point exists.

## P3 Gates

The numerical gates are fixed before implementation: at least 80 complete
trades, at least 20 OOS trades, OOS Sharpe at least 1.0, positive base and
cost-x2 full/OOS returns, maximum drawdown no more than 15%, non-negative return
after deleting the best three trades, at least three positive IS subperiods,
lookahead and recursive checks passing, and no unexplained data gaps.

Any failed gate makes M1C `failed_validation`. Parameters may not be changed to
rescue the result. Even a numerical pass cannot enter M2 until P4 and the
relevant M0 dual-source audit pass.

## Decision

P1 is `design_pass`: the rules are fixed and the pinned Freqtrade source can
represent the required cross-pair ranking and same-open rotation. This is
permission to implement P2 only. It is not strategy approval and does not
authorize P3 conclusions, M2, dry-run, live trading, or API access.
