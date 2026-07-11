# M1E IS-Only Rule Design

- Status: economic_hypothesis_pass_isolation_only
- Candidate: M1E-1H-TREND-BREAKOUT
- Scope: M1E-04 economic hypothesis only
- Candidate evaluated: no
- Strategy rules selected: no
- Formal strategy returns computed: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Economic Hypothesis

M1E studies a state transition, not a continuously active indicator. A completed
UTC 1h market state first shows unusually compressed realized price movement.
A later completed 1h bar shows directional expansion away from that state. The
hypothesis is that inventory and information imbalance can accumulate while
observed range is compressed, and that the subsequent expansion can activate
stops, forced liquidity and delayed participation. This order imbalance may
persist long enough for a spot long/cash system to cover the frozen stressed
roundtrip cost.

The prospective return is paid by late or forced liquidity takers during the
expansion. It is not assumed to come from leverage, short exposure, constant
market beta, same-bar fills or a lower cost model.

## Failure Regimes

- Range-bound markets can repeatedly produce false expansions.
- News gaps and liquidity shocks can make actual slippage exceed the model.
- A persistent trend without a preceding compression state is outside the
  hypothesis and must not be captured by silently adding a generic trend rule.
- Exchange outages, quarantine and incomplete rewarm windows invalidate signal
  eligibility.
- BTC and ETH can become one correlated exposure, limiting independent evidence
  and portfolio capacity.

## IS Boundary

- IS start: `2020-07-01T00:00:00Z`.
- IS end exclusive: `2024-09-11T00:00:00Z`.
- OOS begins: `2024-09-11T00:00:00Z` and remains sealed.
- Canonical completed 1h data may be admitted only through the future M1E-05
  isolator. Completed 4h data may later be used only as a state filter. The 5m
  series is reserved for later next-open timing validation.

## Deferred Decisions

M1E-04 intentionally does not choose the 4h state filter, compression measure,
expansion threshold, exit, stop, position cap, cooldown or warmup. Those choices
may be frozen only after the IS isolator and paper-feasibility evidence pass in
dependency order. There is no parameter range, candidate list or hyperopt space.

## Gate Decision

The economic hypothesis is coherent and distinct enough to authorize M1E-05 IS
data isolation. It does not authorize paper diagnostics, a fixed strategy
contract, strategy implementation, backtesting, OOS access or trading.
