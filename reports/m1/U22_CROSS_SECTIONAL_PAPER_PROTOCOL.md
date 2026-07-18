# U-22 Outcome-Blind Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U22-03-DISPERSION-EXPANSION-LEADER-CONTINUATION-PAPER-V1`
- Protocol hash: `0fdc7eb264e5f9a24dbcb746bbee6af0b1af2218cc101d6674099769f5d1b4fa`
- Pre-freeze synthetic feasibility: `4476d5b5...e6940b` (`3/3` pass)

At every completed UTC hour, the protocol uses all point-in-time active members'
24 completed hourly returns. It compares the median robust cross-sectional
dispersion in the newest 12 hours with the oldest 12 hours. A candidate exists
only when recent dispersion is at least `0.40%` and `1.50x` baseline, and the
largest 12-hour peer-relative leader exceeds `2.40%` simple-equivalent with at
least eight positive hours, positive displacement in both six-hour halves and
no single positive hour contributing more than 50%.

Events cluster across all symbols for 24 hours. Observation begins strictly at
the next expected 5m open and records only preregistered 1/2/4/8/12/24h path
diagnostics. It creates no fill, position, equity or formal return. The exact
core passed three result-blind million-row synthetic checks before this hash
was frozen. Public data and OOS were not read. Only an exact-head independent
review is authorized next.
