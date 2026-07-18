# U-18 Idiosyncratic Downside-Tail Risk Premium Design

- Status: `economic_hypothesis_pass_protocol_design_only`
- Candidate: `U18-CROSS-SECTIONAL-IDIOSYNCRATIC-DOWNSIDE-TAIL-RISK-PREMIUM`
- Hypothesis hash: `e6b84d1b6e9cb979dd973fed42c20821858704c362e24b4a342aef25359778c4`
- Design hash: `487d9b11883d2eb38f2171bf6fe57b1e2e5040b31032e03de73cea9bb5c62df8`

The hypothesis is a compensated downside-risk characteristic. After removing
the completed active-peer common component, persistent asset-specific left-tail
asymmetry may expose holders to crash, forced-liquidation and liquidity-
withdrawal risk. Investors may require compensation for bearing that risk, and
the premium can begin no earlier than the next eligible open.

This design reads no data or outcome and selects no timeframe, history length,
common estimator, tail estimator, persistence rule, threshold, horizon, cost
Gate or strategy rule. It does not treat a single panic bar as an event and
does not assume the risk premium exists; a separately frozen Paper protocol
must test that proposition. OOS remains sealed.
