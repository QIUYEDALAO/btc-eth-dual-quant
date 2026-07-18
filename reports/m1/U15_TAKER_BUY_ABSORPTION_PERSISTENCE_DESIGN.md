# U-15 Taker-Buy Absorption Persistence Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U15-CROSS-SECTIONAL-TAKER-BUY-ABSORPTION-PERSISTENCE`
- Hypothesis hash: `5b99a5d830f40a6d9a5744771dafd3e85a64a55ea172b107465c46b10de115dd`
- Design hash: `14ba25a0d8f3c50b3acd6a1ae50720dd4a113554d3bdc17776bf190b51b57b1c`

The hypothesis is a spot microstructure mechanism. After a completed
observation, an asset with unusually high aggressive taker-buy participation
but muted contemporaneous relative price response may be meeting finite
passive sell inventory. If that inventory exhausts while unresolved buy demand
persists, positive relative price adjustment may occur no earlier than the next
eligible open.

This design reads no market data or result. It does not assume that the frozen
V4 research artifacts already qualify the required taker-buy fields. A separate
result-blind protocol must define and bind the exact field semantics, prove that
the official archive and frozen-source path preserve them consistently, and
fail closed before any event scan if that authority cannot be established.

Timeframe, imbalance estimator, muted-response estimator, normalization,
lookback, threshold, clustering, horizon, costs and all strategy rules remain
unresolved. OOS remains sealed.
