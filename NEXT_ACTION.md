# Next Action

## U-04 Closed

`U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL` is `failed_feasibility` and has no
authorized successor.

- Frozen run: `9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2`.
- Complete independent episodes: 397.
- Median 24h relative recovery: `-0.8556%` versus `+1.80%` required.
- Median 24h absolute close displacement: `-0.7946%` versus `+1.80%` required.
- OOS opened: false; OOS rows decoded: 0.

Do not tune the protocol, lower either Gate, rerun the observation, conduct the
paper-result review, create lifecycle/fixed-rule contracts, implement a strategy
or enter a backtest. Stages 6-20 of the U-04 mainline were not entered.

Any future research candidate requires a separate explicit authorization, a new
candidate identity and an outcome-blind design review. There is no automatic
fallback candidate.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; the failed U-04 result does not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and blocked cold run remain
immutable. ADR-0015 separately qualified the 119 physical invalid rows and full
120-slot mask.

## Prohibited

- No strategy is eligible for M2. Do not enter M2.
- Freqtrade-first remains mandatory for any future authorized single-leg research.
- Do not open or decode U-04 OOS data.
- Do not create fills, positions, equity curves or formal strategy returns.
- Do not modify or rerun the failed U-04 protocol.
- No API keys, dry-run/live trading, `execution/live` or order operations.
- Local Git only; no push, PR or GitHub Actions.
