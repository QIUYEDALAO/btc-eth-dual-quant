# Next Action

## U-07 Outcome-Blind Hypothesis Design

Decision `58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5`
authorizes exactly one economically independent U-07 hypothesis design. It
binds the closed U-04/U-05/U-06 single-run results, their sealed OOS status,
the passing 19/19 ADR-0015 audit and the exact frozen V4 source authority.

The current task is design only. It must define one economic mechanism, causal
timing, failure regimes and non-duplication without choosing a timeframe,
threshold, horizon, signal or trading rule. Prior event signs, observed paths
and failed Gate values may not be inverted, relabeled or used as a rule source.

After design-level validation, only a separate outcome-blind Paper protocol may
be frozen and independently reviewed. Event scanning, returns, strategy rules,
Freqtrade code, backtesting and OOS remain prohibited at this stage.

U-06 remains closed under run `2f715394...1382a`: 56 complete episodes and its
two 24h economic diagnostics failed. It may not be tuned or rerun.

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
