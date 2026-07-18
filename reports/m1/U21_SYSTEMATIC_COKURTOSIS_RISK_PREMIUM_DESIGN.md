# U-21 Systematic Cokurtosis Risk Premium Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U21-CROSS-SECTIONAL-SYSTEMATIC-COKURTOSIS-RISK-PREMIUM`
- Hypothesis hash: `90761268042081c9f80a4fb446ed7e805242608ec6700f6c18b8419bf24420b6`
- Design hash: `a45075371103acf28981ce3a1f0cd47a029b15f5cf3ef9a878b5c682e248568b`

An asset whose squared common-adjusted return tends to be large when the
squared completed active-universe common return is large exposes holders to
systematic fourth-moment risk. Joint extreme risk can consume liquidity and
risk capital when marketwide volatility is already high, so investors may
require compensation beginning no earlier than the next eligible open.

This design reads no data or outcome and selects no timeframe, history, common
return estimator, cokurtosis estimator, normalization, persistence rule,
threshold, horizon, cost Gate or strategy rule. It does not assume the premium
exists; a separately frozen Paper protocol must test it. OOS remains sealed.
