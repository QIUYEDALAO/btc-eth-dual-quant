# U-20 Negative-Coskewness Risk Premium Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U20-03-NEGATIVE-COSKEWNESS-RISK-PREMIUM-PAPER-V1`
- Protocol hash: `d909cd57bbed8c1eaa859905909ce0503d8e653d671b499af0868b1713e2dec9`

At each completed UTC 4h decision, every active member requires 336 completed
hourly returns. Candidate-specific peer medians define the common return and
the candidate common-adjusted return. The history splits into two 168h halves.
In each half, coskewness is the standardized third comoment of the centered
candidate common-adjusted return with the squared centered peer-common return.

Both halves must have coskewness no greater than `-0.20` and rank inside the
lowest cross-sectional quarter, with ranking performed over all eligible active
members before threshold filtering. Mean return direction, volatility, tail,
drawdown and terminal-bar direction are not selection Gates. One deterministic
representative per decision and 24h connected clustering are frozen.

The strict next 5m open anchors 1/2/4/8/12/24h Paper paths. No fills, positions,
equity or formal returns are created. Exact-head review, a structural sample
ceiling and three synthetic million-row complexity passes must precede the only
sealed-IS observation. OOS remains sealed.
