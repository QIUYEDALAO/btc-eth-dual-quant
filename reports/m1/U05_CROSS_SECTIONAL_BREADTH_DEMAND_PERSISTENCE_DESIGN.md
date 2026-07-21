# U-05 Cross-Sectional Breadth-Demand Persistence Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE`
- Hypothesis SHA-256: `ad164b1d9a94d9d61145bf7431a805cfa795a77a6c8aef2cdc488f6bd9e7349b`
- Design content hash: `ae12172aeea45c8447cb40d39dc7d83c4cd85852138a3ee994bf977112b8c2bb`

## Economic hypothesis

At a completed observation time, broadly distributed positive participation
across the exact point-in-time active liquid spot universe may reflect
diversified capital demand and information diffusion rather than an isolated
asset move. That common demand may persist after the next eligible open.

This is a spot long/cash hypothesis only. It does not select a timeframe,
breadth fraction, price threshold, observation horizon, entry rule, exit rule,
stop, position size or performance Gate.

## Causal boundary

Only completed, prior-available observations from every exact active member may
contribute. Current membership backfill, replacement members, missing-member
substitution, post-outcome winner selection and lifecycle crossing are
prohibited. Any future entry can occur no earlier than the next eligible open
after the completed decision.

## Failure mechanisms

- Concentrated large-member moves can imitate breadth.
- A synchronized rise can mark exhaustion or short covering rather than demand.
- Cross-sectional dependence can exaggerate independent confirmation.
- Participation may reverse before covering conservative costs.
- Broad volatility expansion can create unacceptable long-only downside.
- Lifecycle, membership or data-authority drift invalidates the observation.

## Authorization

Only a separate result-blind Paper protocol design may follow. No event scan,
signal, return, fixed rule, Freqtrade code, backtest, OOS, API/trading,
`execution/live` or M2 is authorized.
