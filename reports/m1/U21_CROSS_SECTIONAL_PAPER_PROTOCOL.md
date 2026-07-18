# U-21 Systematic Cokurtosis Risk Premium Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U21-03-SYSTEMATIC-COKURTOSIS-RISK-PREMIUM-PAPER-V1`
- Protocol hash: `b8cad855459c0cb10cff0b1abb927c9bac84b9e54686cc2ea7277aac5f73551e`

At each completed UTC 4h decision, every active member requires 336 completed
hourly returns. Candidate-specific peer medians define the common return and
candidate common-adjusted return. The history splits into two 168h halves. In
each half, systematic cokurtosis is `E[z_candidate² × z_common²]`; independent
finite-variance series have reference value `1.0`.

Both halves must be at least `1.50` and rank inside the highest cross-sectional
quarter over all eligible active members. Mean direction, signed coskewness,
volatility, tail, drawdown and terminal-bar direction are not selection Gates.
One representative per decision and 24h connected clustering are frozen.

The strict next 5m open anchors 1/2/4/8/12/24h Paper paths. No fills, positions,
equity or formal returns are created. Exact-head review, structural ceiling and
three synthetic million-row complexity passes must precede the only sealed-IS
observation. OOS remains sealed.
