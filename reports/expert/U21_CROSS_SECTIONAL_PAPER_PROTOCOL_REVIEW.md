# U-21 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `d76714752825f9018427e9cd55cdd69802928d42`
- Protocol hash: `b8cad855459c0cb10cff0b1abb927c9bac84b9e54686cc2ea7277aac5f73551e`
- Critical/high findings: `0/0`
- Review hash: `809dcdf63d096d8b2742c13004c83151780a7e8078dcde85da7cc65946a355ff`

The exact target uses 336 completed candidate-specific common-adjusted and
peer-common returns split into two disjoint 168h halves. Each half centers and
standardizes both series, then computes the unsigned fourth comoment
`E[z_candidate² × z_common²]`. Zero or non-finite scales fail closed.

Both halves must pass `1.50` and the highest cross-sectional quarter. Ranking
covers every eligible point-in-time active member before filtering. Mean
direction, signed coskewness, volatility, tails, drawdown and terminal direction
cannot select a candidate. Membership/lifecycle/masks precede construction;
future path defects only right-censor an event.

All 16 dimensions pass. Approval authorizes only frozen-source qualification,
sample-ceiling proof, synthetic complexity and result-free preflight. It does
not authorize common-adjusted returns, cokurtosis, events, paths, formal
returns, strategy, OOS or trading.
