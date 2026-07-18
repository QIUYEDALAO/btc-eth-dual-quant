# U-19 Idiosyncratic Volatility-of-Volatility Risk Premium Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U19-03-IDIOSYNCRATIC-VOLATILITY-OF-VOLATILITY-RISK-PREMIUM-PAPER-V1`
- Protocol hash: `8f50ee407a79f2787de53e79b1a4a6de27af89c9ca1c58b5409271039ffd40f9`

At each completed UTC 4h decision, every active member requires 336 completed
hourly returns. Candidate-specific peer medians define the common component.
The residual history splits into two 168h halves and each half into seven
non-overlapping 24h blocks. Block idiosyncratic volatility is residual RMS;
normalized volatility-of-volatility is `1.4826 × MAD` of the seven block
volatilities divided by their median.

Both halves must be at least 0.25 and rank inside the highest cross-sectional
quarter, with ranking performed over every eligible active member before the
threshold filter. Base-volatility level and return direction are not selection
Gates. One deterministic representative per decision and 24h connected
clustering are frozen.

The strict next 5m open anchors 1/2/4/8/12/24h Paper paths. No fills, positions,
equity or formal returns are created. Exact-head review, structural ceiling and
three synthetic million-row complexity passes must precede the only sealed-IS
observation. OOS remains sealed.
