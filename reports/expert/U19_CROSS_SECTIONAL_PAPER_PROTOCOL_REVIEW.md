# U-19 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `8b8b03f0869463c046668e28fbb22618383addf4`
- Protocol hash: `8f50ee407a79f2787de53e79b1a4a6de27af89c9ca1c58b5409271039ffd40f9`
- Critical/high findings: `0/0`
- Review hash: `d215e444595036412cc680b83cc0adf8449edbe6c283ac82b632c67e623f4a91`

The exact target causally constructs 336 completed candidate-specific hourly
residuals, splits them into two disjoint 168h halves and uses seven
non-overlapping 24h residual-RMS blocks per half. Each half independently uses
the frozen median block-volatility base and normalized `1.4826 × MAD / median`
variability. Zero or non-finite bases fail closed.

Both halves must independently pass the absolute `0.25` variability threshold
and the highest cross-sectional quarter rank. Ranking covers the eligible
point-in-time active set before filtering. Base volatility, return direction,
tail sign and terminal-bar direction cannot select a candidate.

Membership, lifecycle and invalid-interval masks precede history construction;
future path defects only right-censor an already formed Paper event. The
representative tie-break, 24h clustering, strict next open, cost references,
sample/distribution/economic Gates and OOS isolation are deterministic and
frozen.

All 16 review dimensions pass. Approval authorizes only frozen-source data
qualification, structural sample-ceiling proof, synthetic complexity and
result-free preflight. It does not authorize residual/volatility/event/path
scans, formal returns, strategy, OOS or trading.
