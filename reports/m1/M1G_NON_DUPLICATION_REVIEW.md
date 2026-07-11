# M1G Non-Duplication Review

- Status: pass_design_level
- Candidate: M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION
- Compared with: M1A, M1D, M1E and DAILY-PANIC-MEAN-REVERSION
- Prior failed outcome used to select rules: no
- OOS accessed: no
- Strategy implementation authorized: no

## Comparison

| Candidate | Frozen family | M1G distinction |
| --- | --- | --- |
| M1A | Continuous daily trend following | Event-driven 1h downside dislocation and rebound hypothesis; no SMA/Donchian/ATR bundle |
| M1D | Generic completed-15m dislocation | Independently preregistered completed-1h forced-selling hypothesis; no 15m threshold rescaling |
| M1E | Compression followed by upside continuation | Downside urgent-liquidity event followed by partial reversion; no compression or breakout rule reuse |
| Daily panic | Daily extreme event mean reversion | Separate preregistered 1h operating hypothesis; daily thresholds may not be shortened or reused |

## Prohibited Reuse

- Do not invert M1E, reuse its frozen protocol, or derive M1G parameters from its failed outcomes.
- Do not translate an M1D or daily-panic threshold into hours.
- Do not reintroduce the M1A SMA200, Donchian 55/20 and ATR20 x2 bundle.
- Do not use volume without a new data-authority contract.

## Decision

M1G passes only at the economic-hypothesis level because its candidate identity
and hash were registered before M1E outcomes, and no event or parameter has been
chosen. Every later protocol and fixed rule must repeat this non-duplication
check. This report does not establish profitability or approve implementation.
