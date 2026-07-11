# M1G IS-Only Rule Design

- Status: economic_hypothesis_pass_paper_protocol_only
- Candidate: M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION
- Scope: economic hypothesis and failure regimes only
- Candidate events evaluated: no
- Strategy rules selected: no
- Formal strategy returns computed: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Economic Hypothesis

M1G studies temporary forced-selling dislocations. A completed UTC 1h candle may
represent urgent liquidity demand, liquidation and one-sided inventory transfer.
If the move is not a permanent information repricing, exhaustion of urgent
sellers can allow passive liquidity and delayed buyers to restore part of the
displacement. The prospective edge is that short-horizon rebound, not market
beta, leverage, averaging down or an optimistic fill model.

The hypothesis is intentionally directional: a completed downward dislocation
may later permit a spot-long observation. It does not assume every large decline
reverts. The next stage must first freeze a price-only event protocol and prove
that typical favorable movement can cover the existing 1.80% paper hurdle.

## Failure Regimes

- A permanent information shock can continue repricing rather than revert.
- Liquidation cascades can arrive in correlated clusters and deepen left-tail loss.
- Event-time spread and slippage can exceed the frozen cost scenarios.
- A statistically visible rebound can still be too small to cover costs.
- Exchange outages, quarantine and incomplete rewarm windows invalidate events.
- BTC and ETH events can be one correlated risk exposure rather than independent evidence.

## Data And Isolation

- IS: `2020-07-01T00:00:00Z` through `2024-09-11T00:00:00Z` exclusive.
- OOS begins `2024-09-11T00:00:00Z` and remains sealed.
- Canonical completed 1h OHLC and completed 4h price-only context may be read.
- 5m is reserved for later next-open timing evidence.
- Existing sealed IS snapshots and their gap/rewarm metadata are reused; a
  duplicate data pipeline is not created.
- Volume and flow fields are not authorized under the current canonical contract.

## Deferred Decisions

This review does not choose a panic threshold, confirmation, 4h filter, target,
holding horizon, stop, position cap, cooldown, cluster rule or warmup. There is
no parameter range, candidate list, grid or hyperopt space.

## Decision

The economic mechanism is coherent enough to authorize only a separate commit
that freezes the M1G IS paper-diagnostic protocol before outcomes are read. It
does not authorize running that diagnostic, selecting strategy rules, writing a
Freqtrade strategy, backtesting, opening OOS or entering M2.
