# U-04 Cross-Sectional Residual-Reversal Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL`
- Scope: one outcome-blind economic hypothesis only
- Public data read: no
- Candidate events evaluated: no
- Strategy rules selected: no
- Formal returns computed: no
- OOS opened: no
- Freqtrade strategy or backtest authorized: no
- Trading or M2 authorized: no

## Economic Hypothesis

At a completed UTC observation time, every candidate asset must belong to the
exact point-in-time active liquid-spot member set. Its prior-only price move is
compared with the contemporaneous common move of that same active cross-section.
An asset-specific negative residual can reflect local inventory imbalance,
forced selling or urgent liquidity demand rather than a permanent information
change. After that local pressure exhausts, part of the residual may reverse.

The prospective source of edge is the partial repair of an asset-specific
relative dislocation. It is not an absolute-drop rule, a current-universe
backfill, a post-outcome loser selection or a claim that every laggard rebounds.
Any future decision must use completed information, and any future entry may be
no earlier than the next eligible open after that decision.

## Point-In-Time And Causal Boundary

- The cross-section is the exact active membership at the observation time;
  current exchange membership cannot rewrite history.
- Every active member row required by the future protocol must be complete and
  governed by the frozen source, lifecycle and invalid-interval authorities.
- Missing members cannot be replaced and quarantined slots cannot be filled.
- Only prior-available, completed observations may define the common component
  or residual.
- A lifecycle event cannot be assumed to provide an exit, conversion or return.

## Failure Regimes

- The weakness is a permanent asset-specific information repricing.
- The asset terminates or enters an unresolved lifecycle boundary.
- A few members dominate the common-component estimate.
- Correlated members make the apparent cross-sectional sample non-independent.
- Relative weakness persists instead of reversing.
- A partial repair is too small to cover stressed costs.
- Membership, source, lifecycle or invalid-interval authority drifts.
- A broad market decline leaves material absolute long exposure despite the
  relative nature of the observation.

## Deferred Protocol Decisions

This design selects no timeframe, IS/OOS split, common-component estimator,
residual formula, threshold, clustering rule, observation window, sample Gate,
cost Gate, entry detail, exit family, stop, position cap or lifecycle treatment.
A separate outcome-blind protocol must freeze those decisions before any event
scan. Lifecycle-intersecting fixed-rule work additionally requires a separately
reviewed delisting/execution policy.

## Decision

The mechanism is sufficiently distinct and causal to authorize only a separate
U-04 paper-protocol design. This document does not establish profitability and
does not authorize event scanning, signals, returns, fixed rules, Freqtrade
code, backtesting, OOS, API/trading, `execution/live` or M2.
