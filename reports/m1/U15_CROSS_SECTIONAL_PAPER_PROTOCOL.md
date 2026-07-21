# U-15 Cross-Sectional Taker-Buy Absorption Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U15-03-TAKER-BUY-ABSORPTION-PERSISTENCE-PAPER-V1`
- Protocol hash: `3b58d6a23cc78e3b644d935599e625c04267317d42608adf2f0321ec51ab577a`

The completed observation is a UTC 4h auction assembled from exactly 48
qualified 5m rows for every point-in-time active member. Aggressive buy
participation is aggregate taker-buy quote volume divided by aggregate quote
volume. The candidate must have share at least 60%, cross-sectional robust
z-score at least 2.0, relative return in `[-0.40%, 0]`, and absolute completed
log return no greater than `0.60%`. One representative is chosen deterministically
and all events cluster through a 24h connected window.

The observation records only next-open referenced price-path diagnostics at
1/2/4/8/12/24h. It creates no fill, position, exit, equity curve or formal
return. OOS remains sealed.

Before any event scan, an independent exact-head review and a separate
frozen-source qualification must prove exact official taker-buy field identity,
numeric validity, availability, membership/lifecycle/mask handling, three-order
identity, sample ceiling and complexity. Missing or ambiguous fields cannot be
inferred, repaired, filled or substituted.
