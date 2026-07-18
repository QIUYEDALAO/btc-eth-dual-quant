# Next Action

## Immediate Task

Execute the one authorized U-04 sealed-IS paper observation.

- Protocol: `7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6`.
- Protocol review: `34fe2efdf4788b20b915f34b3b6442f60ddaa364103ae90b920dc2cacf9646b1`.
- Data qualification: `4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c`.
- IS: `[2020-01-01T00:00:00Z, 2024-09-11T00:00:00Z)`.
- OOS: sealed at and after `2024-09-11T00:00:00Z`.

Run the frozen 1h median/MAD residual event definition, deterministic simultaneous
selection, 24h connected clustering and the six preregistered path horizons. Use
the exact point-in-time active membership, lifecycle end-exclusive authority and
invalid-interval mask. Normal, reverse and deterministic-shuffled results must
have identical event, episode, path, accounting and manifest hashes.

This is the only paper-observation run. Do not tune, lower a Gate, change a
threshold or rerun based on the result. Any failed Paper Gate closes the candidate
as `failed_feasibility`.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; U-04 observation does not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and blocked cold run remain
immutable. ADR-0015 separately qualified the 119 physical invalid rows and full
120-slot mask.

## Prohibited

- No strategy is eligible for M2. Do not enter M2.
- Freqtrade-first remains mandatory for future single-leg implementation.
- Do not open or decode OOS data.
- Do not create fills, positions, equity curves or formal strategy returns.
- Do not change the reviewed protocol, thresholds, costs, Gates or authorities.
- Do not implement strategy/fixed-rule/backtest logic.
- No API keys, dry-run/live trading, `execution/live` or order operations.
- Local Git only; no push, PR or GitHub Actions.
