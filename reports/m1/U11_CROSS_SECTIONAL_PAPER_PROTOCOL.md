# U-11 Outcome-Blind Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U11-CROSS-SECTIONAL-ASYMMETRIC-MARKET-CAPTURE-QUALITY-PERSISTENCE`

At each completed UTC 4h boundary, the protocol uses the preceding 360 complete
4h observations. Every historical common component is the median return of
that observation's exact active members. Positive and negative common states
are separated, and zero-intercept upside/downside capture is estimated over the
full window and two non-overlapping 180-observation halves.

A candidate must have at least 60 positive and 60 negative full-window states,
24 of each state in each half, upside capture at least 0.80, downside capture at
most 0.70 and full asymmetry at least 0.30. Its asymmetry must rank in the top
quartile in both halves and the full window. One deterministic representative
is retained per decision time and all events use a 72h connected cluster.

Before any common-state or price scan, calendar, membership-history and monthly
path metadata must prove at least 200 theoretical eligible 72h episodes versus
the frozen complete-sample Gate of 90. The strict next 5m open begins
1/2/4/8/12/24/48/72h path diagnostics.

Paper Gates require 90 complete IS episodes, projected 120 full and 30 sealed-
OOS episodes, broad year/symbol/month coverage, median 72h relative and absolute
displacement of at least 1.80%, at least 60% positive relative persistence and
zero authority/order mismatches.

The protocol creates no fill, position, equity or formal return. It opens no
OOS and authorizes only an exact-head independent review.
