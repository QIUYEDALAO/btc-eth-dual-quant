# U-04 Cross-Sectional Residual-Reversal Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U04-02-CROSS-SECTIONAL-RESIDUAL-REVERSAL-PAPER-V1`
- Scope: outcome-blind protocol definition only
- Public data read or event scan executed: no
- Path or return result accessed: no
- OOS opened: no
- Strategy, backtest, API/trading or M2 authorized: no

## Frozen Event

At each completed UTC 1h close, use the exact point-in-time active membership.
All active members and their prior completed 1h closes must be present, with at
least ten members. Compute member log returns, subtract their cross-sectional
median and divide each residual by `1.4826 × MAD`. A candidate requires both a
standardized residual at most `-3.0` and a relative simple return at most
`-1.80%`. Zero or non-finite scale produces no event and is accounted for.

Only one candidate may represent a timestamp: most-negative standardized
residual, then most-negative raw residual, then symbol order. Candidates across
all symbols connected within 24 hours form one episode; only the first is kept.
Absolute decline alone is never a U-04 event.

## Frozen Observation

The reference is the first expected 5m open strictly after the completed 1h
decision. Missing references are not searched forward. Observe 1, 2, 4, 8, 12
and 24 hours. Relative recovery compares the candidate path with the median
path of the event-time peers; absolute close displacement, MFE, MAE and first
relative recovery time are mandatory diagnostics.

The peer set is frozen at the event time. A missing or quarantined peer,
membership change or lifecycle intersection right-censors the affected path.
No fill, position, exit, equity or formal strategy-return model exists here.

## Frozen Gates

- At least 90 complete IS episodes, with projections of at least 120 full and
  30 sealed-OOS episodes using only the IS daily rate.
- At least three years with ten episodes, at least eight event symbols, no year
  above 45% and no symbol above 25%.
- Combined median 24h relative recovery and absolute close displacement are
  each at least 1.80%.
- Qualification, quarantine, lifecycle and traversal-order mismatches are zero.

Roundtrip references are Base 0.30%, Cost×2 0.60%, Stress A 0.80% and Stress B
1.10%. These are economic references, not returns computed in this task.

## Authorization

Only an exact-head independent review may follow. Data qualification, event
scanning, path observation, signals, formal returns, fixed rules, Freqtrade
code, backtesting, OOS, API/trading, `execution/live` and M2 remain disabled.
