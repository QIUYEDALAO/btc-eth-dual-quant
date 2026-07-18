# U-09 Outcome-Blind Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U09-CROSS-SECTIONAL-IDIOSYNCRATIC-VOLATILITY-QUALITY-PERSISTENCE`

Every 336h from the fixed first anchor, the protocol uses the preceding 168
completed 1h returns. Each hour's common component is the exact active-member
cross-sectional median log return. Asset residual volatility is the population
standard deviation after removing that common component.

The quality cohort is the intersection of the lowest volatility quartile in
the first 84h, second 84h and full 168h windows. All required membership, close,
quarantine and lifecycle authority must be complete; no replacement or current-
membership backfill is allowed. The 336h anchor interval makes primary episodes
non-overlapping.

The reference is strictly the next expected 5m open, never a later search.
Paths are observed at 24h, 72h, 168h and 336h. The primary Gates require 80
complete IS episodes, projected 110 full and 30 sealed-OOS episodes, broad
year/symbol/month coverage, median relative and absolute cohort displacement of
at least 1.80%, at least 60% positive relative persistence, and zero authority
or traversal-order mismatches.

This protocol creates no fill, position, equity or formal return. It opens no
OOS and authorizes only an exact-head independent review.
