# U-13 Outcome-Blind Common-Shock Lagged-Diffusion Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U13-CROSS-SECTIONAL-COMMON-SHOCK-LAGGED-DIFFUSION`
- Protocol hash: `1cf6dade6e75900278ba5aeee30018d3f0ff93d83d982e212d58033800993288`

The protocol uses complete 1h returns derived from qualified 5m rows. Historical
lag behavior is estimated over the preceding 2,160 completed hours: qualifying
positive common shocks require median log return at least 0.20% and at least
60% positive breadth; a candidate must have a nonnegative absolute return but
an immediate residual no greater than -0.10%, then show positive relative
catch-up over the next four completed hours.

At least 30 historical occurrences and 12 in each chronological half are
required. Full/half median catch-up must reach 0.40%/0.20%, and the median
immediate residual plus catch-up must be nonnegative to exclude permanent
weakness.

A current event requires a completed common return of at least 0.60%, at least
70% positive breadth, a nonnegative candidate return and residual no greater
than -0.40%. One deterministic representative is kept, followed by 24h
connected clustering and 1/2/4/8/12/24h diagnostics from the first expected 5m
open strictly after the completed 1h boundary.

All parameters and Paper Gates are frozen before data access. Exact-head review
and then a separate same-reader qualification/preflight are mandatory. No
event, path, formal return, OOS value, strategy or trading operation is
authorized by this protocol.
