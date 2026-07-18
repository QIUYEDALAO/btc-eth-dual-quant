# U-18 Idiosyncratic Downside-Tail Risk Premium Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U18-03-IDIOSYNCRATIC-DOWNSIDE-TAIL-RISK-PREMIUM-PAPER-V1`
- Protocol hash: `7571d2cb2408e30ac03d626544243f1e00595dc9ed85e6a7107b7d9a2062c671`

At each completed UTC 4h decision, every active member requires 168 completed
hourly returns. Candidate-specific peer medians define the common component.
The 168 idiosyncratic residuals split into two disjoint 84h halves; each half
uses median and `1.4826 × MAD` and must contain at least two residuals at or
below median minus two scales.

In both halves, downside-tail energy must be at least 25% of total residual
energy and no single tail point may contribute more than 65% of tail energy.
This prevents one panic bar from defining the characteristic. One deterministic
representative per decision and 24h connected clustering are frozen.

The strict next 5m open anchors 1/2/4/8/12/24h Paper paths. No fills, positions,
equity or formal returns are created. Exact-head review, structural ceiling and
three synthetic million-row complexity passes must precede the only sealed-IS
observation. OOS remains sealed.
