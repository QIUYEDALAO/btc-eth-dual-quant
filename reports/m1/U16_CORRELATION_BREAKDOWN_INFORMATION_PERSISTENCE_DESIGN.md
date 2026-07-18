# U-16 Correlation-Breakdown Information Persistence Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U16-CROSS-SECTIONAL-CORRELATION-BREAKDOWN-INFORMATION-PERSISTENCE`
- Hypothesis hash: `781093529714314144be705cef84c0563a59630e71243827950b47cf6c15f2f1`
- Design hash: `8574e5c5aa068f10a561d8cfae26d4a45d5b9eb17287156912fa4d8b5fd075d1`

The hypothesis is an asset-specific information mechanism. Using only a
completed prior path and the complete point-in-time peer set, positive relative
price displacement that appears while the asset decouples from the peer common
path may represent information being incorporated gradually rather than a
common market move. Any continuation can begin no earlier than the next
eligible open.

This design reads no data or outcome and selects no timeframe, history length,
common-component estimator, correlation estimator, decoupling threshold,
relative-displacement threshold, clustering rule, horizon, cost Gate or
strategy rule. It uses no taker field and does not repair U-15. OOS remains
sealed.
