# U-20 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `6a2207c05c7045e82b47f9685c01a5c2d0b30755`
- Protocol hash: `d909cd57bbed8c1eaa859905909ce0503d8e653d671b499af0868b1713e2dec9`
- Critical/high findings: `0/0`
- Review hash: `eb452e7440b5058b6516629f65a9793f06dfa5748961c58e87229d4c3a1e20f5`

The exact target causally constructs 336 completed candidate-specific hourly
common-adjusted returns and peer-common returns, then splits both series into
two disjoint 168h halves. Each half independently centers both series and
computes the normalized third comoment of candidate-adjusted return with the
squared common return. Zero or non-finite scales fail closed.

Both halves must independently pass the absolute `-0.20` upper bound and the
lowest cross-sectional quarter rank. Ranking covers the entire eligible
point-in-time active set before filtering. Mean-return direction, volatility,
tails, drawdown and terminal-bar direction cannot select a candidate.

Membership, lifecycle and invalid-interval masks precede history construction;
future path defects only right-censor an already formed Paper event. The
representative tie-break, 24h clustering, strict next open, costs, sample,
distribution/economic Gates and OOS isolation are deterministic and frozen.

All 16 review dimensions pass. Approval authorizes only frozen-source data
qualification, structural sample-ceiling proof, synthetic complexity and
result-free preflight. It does not authorize common-adjusted returns,
coskewness, events, paths, formal returns, strategy, OOS or trading.
