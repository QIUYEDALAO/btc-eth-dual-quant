# U-14 Downside-Rejection Persistence Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U14-CROSS-SECTIONAL-DOWNSIDE-REJECTION-PERSISTENCE`
- Hypothesis hash: `b88f2321269863e385129465c93fbee8ecd35fa0dc6bc19e10bacf12d851b87d`
- Design hash: `a6c3cc47c3cadf33e5673e59ce47c639d6df1d49c57f88c51cc1c8579b446691`

The hypothesis is an auction/microstructure demand mechanism. After a completed
common selling-pressure observation, an asset that traded materially lower but
was bought back to an unusually strong position inside its completed range,
relative to every complete active peer, may reveal passive demand that persists
after the next eligible open.

This design does not select a timeframe, selling-pressure state, range floor,
close-location formula, relative estimator, persistence rule, threshold,
horizon, cost Gate or strategy rule. It reads no public data or outcome and
keeps OOS sealed.

The next task, if any, is a separate outcome-blind Paper protocol with a
result-blind complexity benchmark before the unique result run.
