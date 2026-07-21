# U-06 Cross-Sectional Volume-Share Absorption Repricing Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U06-CROSS-SECTIONAL-VOLUME-SHARE-ABSORPTION-REPRICING`
- Hypothesis SHA-256: `e6cb136b5bfaa4948b1681696b33496a43b7f9ab1f4fc25dcea63714700c259b`
- Design content hash: `694e5a4344481bf785b09ff9f69a7c170d6c3d7061407902306cee70176966a5`

## Economic hypothesis

An asset whose share of completed quote volume rises relative to the exact
point-in-time active universe, while its relative price has not advanced
commensurately, may be undergoing liquidity absorption or slow information
diffusion. Latent demand may then produce delayed repricing after the next
eligible open.

This is spot long/cash only. It selects no timeframe, baseline, threshold,
horizon, entry, exit, stop, position size or performance Gate.

## Causal boundary

Only completed prior price and quote-volume observations from every exact
active member may contribute. The volume-share denominator may not use current
membership backfill, replacement members or post-outcome selection. Any future
entry can occur no earlier than the next eligible open.

## Failure mechanisms

- Wash trading or non-directional churn can inflate quote volume.
- High activity without price response can represent distribution.
- Listing/lifecycle events can make volume histories incomparable.
- A large member's volume collapse can mechanically inflate other shares.
- Regime shifts, costs or data-authority drift can erase or invalidate the edge.

## Authorization

Only a separate result-blind Paper protocol design may follow. No event scan,
signal, return, fixed rule, Freqtrade code, backtest, OOS, API/trading,
`execution/live` or M2 is authorized.
