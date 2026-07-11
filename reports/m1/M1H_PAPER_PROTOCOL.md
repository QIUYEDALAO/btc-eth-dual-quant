# M1H Paper Protocol

- Status: frozen_before_result
- Protocol: M1H-02-FUNDING-EXTREME-SPOT-PAPER-V1
- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN
- Scope: paper research protocol definition only
- Trial status: declared_unopened
- Event scan executed: no
- Candidate outcomes accessed: no
- Formal strategy returns computed: no
- Paper feasibility authorized: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- API or trading authorized: no
- M2 authorized: no

## Economic Hypothesis And Failure Mechanisms

An extreme settled negative funding observation can represent crowded short
positioning and pessimistic derivatives sentiment. Its exhaustion or unwind may
be followed by spot appreciation. Funding is information only: M1H is always
spot long/cash and can never collect funding, short a perpetual, hedge basis or
run two-leg execution.

The mechanism fails if negative funding reflects durable adverse information,
events are too sparse, settlement or interval evidence is incomplete, the
post-settlement spot move cannot cover the frozen research hurdle, BTC and ETH
are one correlated stress episode, or a later lifecycle cannot be represented
conservatively in Freqtrade.

## Frozen Event Identification

A paper event uses a settled public `funding_rate_history` row and must have a
negative funding rate. The rate is annualized with its own M0-inferred interval:

`fundingRate * (365 * 24 / event_interval_hours)`

The annualized value must be at or below the same symbol's lower 5th percentile
over the prior 365 complete UTC days. The reference history excludes the current
event and uses linear percentile interpolation. Every historical settlement in
the window must have valid interval and completeness evidence. There is no
hardcoded default funding interval.

Same-symbol events connected within 24 hours form one cluster and retain only
the first event. BTC and ETH observations remain available for per-symbol
diagnostics, while cross-symbol events connected within 24 hours count as one
independent market episode for projected sample budgets.

The 5% percentile, 365-day window, interpolation and clustering are frozen event
identification rules. They are not strategy entry parameters and may not be
optimized. Comparing 1%, 5% and 10% after observing results is prohibited. Any
change requires a new ADR and a new protocol identity.

## Funding Data Timing Contract

- A funding observation is unavailable before `fundingTime`.
- A decision cannot precede `fundingTime`.
- The observation reference is the first expected canonical 5m open strictly after `fundingTime`.
- A 5m bar at the settlement timestamp is illegal.
- If the expected reference bar is missing, the event is not shifted to a later favorable price.
- Future funding, future spot bars and incomplete bars are prohibited.
- A missing bar, quarantine window or IS-boundary crossing makes the affected observation right-censored.

## Frozen Market-Reaction Windows

The frozen observation windows are 1h, 2h, 4h, 8h, 12h and 24h. They describe
market-reaction paths only. They are not holding periods, exits or strategy
parameters and cannot be removed, added or optimized after results are known.

A future paper-feasibility task must report all of the following together:

- median 24h MFE;
- median 24h close displacement;
- MAE distribution with minimum, P05, median and P95;
- recovery-time distribution with recovered share, recovered median/P90 and unrecovered count.

MFE and MAE use continuous canonical 5m high/low relative to the reference
open. The 24h close displacement uses the completed close at the end of the
24-hour window. Recovery is the first completed 5m close at or above the
reference open; an event not recovered within 24 hours is censored.

These are mechanism-feasibility observations, not fills, positions, PnL,
Sharpe, strategy returns or proof of edge. MFE has no standalone pass Gate and
cannot override a failed close-displacement Gate.

## Frozen Paper Gates

- Projected full independent episodes must be at least 120.
- Projected sealed-OOS episodes must be at least 30, using only IS event rate and calendar length.
- Combined median 24h close displacement must be at least 1.80%.
- Each symbol needs at least 20 complete events and median 24h close displacement of at least 1.80%.
- At least three years need at least ten independent episodes.
- No single year may contain more than 45% of independent episodes.
- Invalid lineage, interval, quarantine or unrewarmed Gate events must be zero.
- MFE, MAE and recovery diagnostics are mandatory disclosures, not standalone Gates.

## Research Leakage Prevention

It is prohibited to adjust the percentile from event counts; alter the event
definition from MFE, MAE, close displacement or recovery; delete years from
their results; create symbol-specific definitions; alter horizons after
feasibility; reselect funding intervals from outcomes; add a spot-price
confirmation after results; or change clustering/right-censor rules. Every protocol change requires a new ADR and cannot overwrite this candidate record.

## Non-Duplication Matrix

| Axis | M1H | M1G | M1B |
| --- | --- | --- | --- |
| Signal family | Settled funding lower-tail observation | Spot panic-price dislocation | Positive funding and payback economics |
| Timing model | Settlement then strictly later canonical 5m observation | Completed panic bar then later spot path | Funding settlement during two-leg holding |
| Return source | Future spot appreciation only | Spot mean reversion | Funding cashflow, basis and two-leg PnL |
| Position family | Spot long/cash only | Spot long/cash | Spot long plus perpetual short |

Spot OHLC cannot trigger M1H. Price decline, close-location, range expansion and
other M1G panic conditions are prohibited. Funding carry, income, basis trades,
hedges, perpetual shorts and M1B two-leg logic are prohibited.

## Execution Representability Design Annex

No entry, exit, stop, position size, cooldown or holding rule is selected.
Before implementation, a future lifecycle must pass a separate Freqtrade
capability review, must not depend on same-bar optimism or favorable gap fills,
and must produce zero timestamp mismatch on deterministic conservative
fixtures. Freqtrade remains the single-leg return authority; Python cannot
become a second strategy engine.

## Next-Task Boundary

This protocol does not authorize funding-data qualification or paper
feasibility. A future M1H-03 task may first validate only lineage, settlement
timestamps, per-event intervals, availability, missing/duplicates, timezone and
completeness. It may not scan or count events, analyze paths or returns, or make
a feasibility decision during that qualification step. If qualification passes,
the same separately authorized task may proceed once to sealed-IS paper
feasibility without another intermediate approval.
