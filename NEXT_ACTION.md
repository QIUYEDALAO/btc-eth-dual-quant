# Next Action

## Immediate Task

Design and freeze one outcome-blind paper protocol for
`U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL`.

- Design content hash:
  `b384e6484180a0ec358125fbb0338d7376b860372ab065fe7043667931f178b8`.
- Hypothesis hash:
  `85e9fc11e8f6b69597fecdb6a40485611eb24163a20cea4534e81d0f08e5ec7a`.
- U-04 authorization:
  `84d9b499329169719a880af80b1e2e7f0d5d5cbbc6c62a6aa762cd738aa04e89`.
- Qualified artifact set:
  `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`.
- Source freeze: `c86310f8...ec6c`.
- Membership manifest: `bcd93c0a...7ec5`.
- Membership authority: `52aa8cc9...93e2`.
- Lifecycle registry: `a78c52b1...904d`.
- Invalid-interval policy/algorithm: `0ac074cf...2d04` / `8f8a3668...a4ff`.

The protocol-design task must freeze exactly one completed observation
timeframe, common-market estimator, asset-specific residual definition, event
threshold, clustering rule, future observation windows, sample/concentration
Gates, cost-coverage Gate, future entry detail and IS/OOS boundary. It must do
so before reading any event or outcome.

The protocol must remain a machine-verifiable preregistration. It cannot run
the event scan, inspect paths or returns, select a fixed trading rule, write a
Freqtrade strategy or open OOS. A separately authorized execution task may
follow only after the protocol itself is frozen and validated.

## Current Design Decision

- Family: asset-specific negative residual after removal of the active
  cross-section's contemporaneous common move, followed by possible partial
  reversal.
- Universe: exact point-in-time active liquid Binance spot USDT membership.
- Direction: spot long/cash only.
- Earliest possible future entry: next eligible open after a completed
  decision.
- Candidate events evaluated: no.
- Returns computed: no.
- OOS opened: no.
- Lifecycle crossing assumed: no.

## Historical Governance Bindings

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; U-04 design work does not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and its later blocked cold
run remain immutable. ADR-0015 requalification separately quarantined 119 physical
invalid rows plus the valid-minority slot.

## Prohibited

- Do not execute the U-04 protocol or access public outcome data in the
  protocol-design task.
- Do not scan events, compute signals or returns, inspect OOS values, tune
  parameters or derive rules from prior failed candidates.
- Do not replace historical members, use current membership hindsight, fill
  quarantined slots or weaken source/lifecycle/invalid-interval authority.
- Do not define lifecycle exit, conversion or return treatment. A separate
  reviewed delisting/execution policy is required before lifecycle-intersecting
  fixed-rule work.
- Freqtrade-first remains mandatory for any future single-leg implementation;
  Python must not become a second return engine.
- No strategy is eligible for M2. Do not enter M2.
- Do not use API keys, trading permissions, paper/live trading,
  `execution/live`, order placement, cancellation or matching.
- Continue local Git only; do not push, create a PR or run GitHub Actions unless
  the user explicitly requests publication.
