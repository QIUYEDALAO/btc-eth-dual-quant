# Next Action

## U-07 Paper Protocol Exact-Head Independent Review

U-07 is frozen as
`U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION` under
design `272eabd4ab1737566698309b98cc13b952a8d39b86c457674d58ff56de021795`
and hypothesis `3130450cd7bd7cddab4bce0c89b274ae93e50bed278379011cc4d09e15fb3de3`.

The mechanism is state-conditioned relative resilience: broad contemporaneous
selling pressure plus one asset retaining unusually strong relative price may
reveal inelastic asset-specific demand that persists after stress subsides.

Protocol `d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195`
is frozen before results. It fixes completed UTC 4h stress (`median <= -2.50%`,
negative breadth at least 80%), candidate resilience (relative at least +2.00%,
absolute at least -0.50%), 48h clustering, strict next 5m reference, fixed
event-time peers and all sample, distribution and 24h economic Gates.

The current task is a separate independent review of the immutable exact target
commit. It must bind every target file and verify causal timing, membership,
lifecycle, invalid-interval, OOS isolation, deterministic tie-breaks and zero
downstream authority. The target files may not be modified during review.

Public data, event scanning, paths, returns, fixed rules, Freqtrade code,
backtesting and OOS remain prohibited until an `approve` review with zero
critical/high findings authorizes data qualification only.

## U-04 Closed Historical Evidence

`U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL` is `failed_feasibility` and has no
authorized continuation within U-04.

- Frozen run: `9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2`.
- Complete independent episodes: 397.
- Median 24h relative recovery: `-0.8556%` versus `+1.80%` required.
- Median 24h absolute close displacement: `-0.7946%` versus `+1.80%` required.
- OOS opened: false; OOS rows decoded: 0.

Do not tune the protocol, lower either Gate, rerun the observation, conduct the
paper-result review, create lifecycle/fixed-rule contracts, implement a strategy
or enter a backtest. Stages 6-20 of the U-04 mainline were not entered.

U-05 is a separate candidate authorization. It may not invert or reuse the U-04
result as its mechanism or rule source.

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
