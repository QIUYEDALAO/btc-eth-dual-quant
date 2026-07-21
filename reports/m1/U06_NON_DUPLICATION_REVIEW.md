# U-06 Non-Duplication Review

- Status: `pass_design_level`
- Candidate: `U06-CROSS-SECTIONAL-VOLUME-SHARE-ABSORPTION-REPRICING`

U-06 studies a price/quote-volume disagreement that may indicate absorption
before repricing. It is not derived from either prior cross-sectional result.

- U-04 uses negative price residuals and expects reversal; U-06 uses prior-only
  quote-volume share and requires no residual sign.
- U-05 requires broad common positive price participation; U-06 concerns an
  asset-specific activity/price disagreement and makes no breadth-persistence claim.
- M1C selects a price winner; U-06 does not rank prior price winners.
- M1E studies compression/breakout, M1G absolute panic, M1H settled funding,
  and M1A the SMA/Donchian/ATR bundle; none is reused.

Removing any boundary invalidates design-level non-duplication.
