# U-20 Negative Coskewness Risk Premium Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U20-CROSS-SECTIONAL-NEGATIVE-COSKEWNESS-RISK-PREMIUM`
- Hypothesis hash: `9d17a514b9e13eff5dd885382ab7c9df5c14e9a71283a219d43c901648e46bdb`
- Design hash: `3995e92a9ae69fd64f8258b33b620c801d63e235e1ed90a254a3d99d70a1e5b5`

An asset whose common-adjusted return tends to be negative when the magnitude
of the completed active-universe common return is large exposes holders to
systematic higher-moment risk. Because those losses can coincide with states
in which marginal capital is valuable, investors may require compensation,
with any premium beginning no earlier than the next eligible open.

This design reads no data or outcome and selects no timeframe, history, common
return estimator, coskewness estimator, normalization, persistence rule,
threshold, horizon, cost Gate or strategy rule. It does not assume the premium
exists; a separately frozen Paper protocol must test the proposition. OOS
remains sealed.
