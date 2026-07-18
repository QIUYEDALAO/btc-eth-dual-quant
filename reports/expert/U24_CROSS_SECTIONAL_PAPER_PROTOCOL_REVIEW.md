# U-24 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `cafbd5a90f5fd3a435d15ff03af0ecec2df98c3f`
- Protocol hash: `5110c3f455274f291391ed9b34affe6e5f61beb9198723d4fb0b8f07439c7ce7`
- Critical/high findings: `0/0`
- Review hash: `b032f88ab2f8c6cfd42c15a7665ebc3122187c72bdcc14d1a319b03bcb57db17`

The exact target uses every point-in-time active member's 336 completed hourly
returns, split into two 168h halves. Candidate-specific peer medians remove the
contemporaneous common component before the maximum positive residual in each
half defines right-tail lottery payoff.

Ranking occurs across every otherwise eligible active member before the fixed
8% ceiling is applied. The same symbol must remain in the lowest quarter in
both halves. The deterministic representative, completed 4h decision clock,
24h clustering, strict next expected 5m open and path censoring are causal.

All 16 dimensions pass, including exact pre-freeze synthetic evidence and core
blob. Approval authorizes only frozen-source structural qualification and
result-free preflight. It does not authorize return/result scanning, events,
paths, formal returns, strategy, OOS or trading.
