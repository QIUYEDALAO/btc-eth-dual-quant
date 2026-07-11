# M1G Freqtrade Capability Review

- Status: capability_pass_with_mandatory_execution_audit
- Runtime: Freqtrade 2026.6 pinned image and digest
- Fixed contract changed: no
- Strategy implemented: no
- Performance backtest executed: no
- OOS opened: no
- M2 authorized: no

## Native Support

Freqtrade 2026.6 can represent the signal and lifecycle core:

- Completed 1h signals enter on the next main-candle open.
- `--timeframe-detail 5m` evaluates active trades and callbacks every 5m.
- Native backtesting evaluates stoploss before ROI in the same detail candle.
- `minimal_roi` can express +1.80% from minute zero and a forced open-price
  timeout at 1,440 minutes.
- `max_open_trades=1` and `tradable_balance_ratio=0.25` express the slot and
  capital cap.
- Informative BTC/ETH data can compute one deterministic same-time winner.
- `confirm_trade_entry()` runs in backtesting, and `Trade.get_trades_proxy()`
  exposes all closed backtest trades without a pair filter. The strategy can
  reject entries for 72 hours after the latest exit across either pair.

The built-in `CooldownPeriod` is not used for this requirement because its
2026.6 `global_stop()` is not implemented and its regular path is pair-specific.

## Material Execution Difference

Freqtrade's native ROI and stoploss prices are close to, but not identical to,
the fixed conservative gap rules:

- ROI normally exits at the target, but when a whole detail candle is above the
  target it may use that candle's low.
- Native stoploss can use the stop threshold after an open below the stop when
  the same detail candle recovers through the threshold. The contract requires
  the worse opening price.

These differences can improve reported results and therefore cannot be ignored.
They were identified before strategy implementation and before any performance
backtest, so this is not a result-driven rule change.

## Decision

Freqtrade remains the only signal, position-state and trade-lifecycle authority.
Python may not detect a second set of events or run a second strategy. It must
only reprice Freqtrade-exported trades against canonical 5m OHLC using the
already frozen target-gap, stop-gap, ambiguity and timeout rules.

Every future IS/OOS Gate must pass both:

1. the native Freqtrade result; and
2. the more conservative contract-execution audit.

This makes the capability conclusion `pass_with_mandatory_execution_audit`, not
an unconditional framework pass. After review and merge, exact strategy
implementation and non-performance fixtures may follow. Performance backtesting,
OOS, dry-run, live, API permissions and M2 remain unauthorized.

## Source Evidence

- [Freqtrade 2026.6 backtesting assumptions](https://github.com/freqtrade/freqtrade/blob/2026.6/docs/backtesting.md)
- [Freqtrade 2026.6 backtesting implementation](https://github.com/freqtrade/freqtrade/blob/2026.6/freqtrade/optimize/backtesting.py)
- [Freqtrade 2026.6 CooldownPeriod implementation](https://github.com/freqtrade/freqtrade/blob/2026.6/freqtrade/plugins/protections/cooldown_period.py)
- [Freqtrade 2026.6 trade proxy implementation](https://github.com/freqtrade/freqtrade/blob/2026.6/freqtrade/persistence/trade_model.py)
