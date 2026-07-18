# U-08 Outcome-Blind Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U08-POINT-IN-TIME-LIQUIDITY-RANK-ENTRY-DEMAND-PERSISTENCE`

The event is a prior-only frozen monthly Top-15 membership admission: a current
qualified member absent from the immediately prior membership. The genesis
month is ineligible. If several assets enter together, the sole representative
is the lowest current membership rank, then symbol ascending. Price and outcome
never select the representative.

The decision time is membership effectiveness. The reference is strictly the
next expected 5m open, never a later search. The fixed event-time active peers
exclude the candidate. Complete paths at 24h, 72h, 168h and 336h are required;
missing, quarantine, membership or lifecycle intersections right-censor the
episode.

The primary 336h Gates require 36 complete IS episodes, projected 48 full and
12 sealed-OOS episodes, broad year/symbol/month coverage, median relative and
absolute displacement of at least 1.80%, at least 60% positive relative
persistence, and zero authority/order mismatches.

This protocol creates no fill, position, equity or formal return. It opens no
OOS and authorizes only an exact-head independent review.
