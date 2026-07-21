# U-04 Non-Duplication Review

- Status: `pass_design_level`
- Candidate: `U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL`
- Prior failed outcome used to select rules: no
- Event or return evidence accessed: no
- OOS opened: no

## Comparison

| Prior candidate | Prior family | U-04 distinction |
| --- | --- | --- |
| M1C | BTC/ETH long-horizon winner momentum | Active Top-15 asset-specific negative residual and reversal; no 90-day winner ranking or weekly rotation |
| M1G | Absolute single-asset 1h panic reversal | Cross-sectional common-move removal is mandatory; an absolute decline alone cannot identify U-04 |
| M1E | Compression followed by upside continuation | Relative downside dislocation and partial repair; no compression or breakout continuation rule |
| M1H | Settled funding crowding | Spot-price cross-section only; no funding, derivatives sentiment or funding cashflow input |
| M1A | Daily trend following | No SMA200, Donchian 55/20 or ATR20 x2 bundle |

## Prohibited Reuse

- Do not reuse M1C momentum horizons, rankings, rotation rules or failed outcomes.
- Do not relabel M1G absolute panic events as cross-sectional residuals.
- Do not invert M1E or reuse its compression/breakout protocol.
- Do not use funding observations, futures positions or funding cashflows.
- Do not derive any U-04 rule from prior candidate outcomes.

## Decision

U-04 passes only at the economic-hypothesis level. Its point-in-time active
cross-section, mandatory common-move removal and asset-specific negative
residual distinguish it from the prior candidates. All numerical and executable
choices remain deferred to a separate outcome-blind protocol.
