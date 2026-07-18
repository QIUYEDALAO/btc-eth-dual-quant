# U-18 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `39a766c50de5a0855d7ee85c2aab743ec8b738e5`
- Protocol hash: `7571d2cb2408e30ac03d626544243f1e00595dc9ed85e6a7107b7d9a2062c671`
- Critical/high findings: `0/0`
- Review hash: `5fb6a8d2d8efe95c6b2970b3368c78c40f17b187a5239f0b907f37ce341e1dd3`

The exact target causally constructs 168 completed hourly candidate-specific
residuals and splits them into two disjoint 84h halves. Each half independently
uses median/MAD scale, requires at least two robust left-tail points, at least
25% downside-tail energy and no more than 65% contribution from one tail point.
No mean-return direction or terminal-bar Gate can select the candidate.

Membership, lifecycle and invalid-interval masks precede hourly construction.
Future state is used only to right-censor incomplete Paper paths, never to form
events. Tie-break, 24h clustering, strict next open, projections, costs and
economic Gates are deterministic and frozen.

All 16 review dimensions pass. Approval authorizes only structural data
qualification, sample-ceiling proof, synthetic complexity and result-free
preflight. It does not authorize residual/tail/event/path scans, returns,
strategy, OOS or trading.
