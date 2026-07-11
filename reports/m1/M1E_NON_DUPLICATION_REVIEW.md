# M1E Non-Duplication Review

- Status: pass
- Candidate: M1E-1H-TREND-BREAKOUT
- Compared with: M1A-DAILY-TREND
- M1A rescue attempted: no
- OOS accessed: no
- Strategy implementation authorized: no

## Comparison

| Dimension | Frozen M1A | M1E design scope |
| --- | --- | --- |
| Economic family | Continuously evaluated daily trend following | Discrete 1h compression-to-expansion state transition |
| Regime | Close above SMA(200) | Not selected; completed 4h state only |
| Entry | Prior 55-day Donchian high | Not selected; must represent compression then expansion |
| Exit | Prior 20-day Donchian low | Not selected |
| Risk stop | ATR(20) times 2 | Not selected |
| Timing | Daily signal, next daily open | Completed 1h event, no earlier than next 5m open |

## Prohibited Reuse

The combined `SMA200 + Donchian 55 entry + Donchian 20 exit + ATR20 x2 stop`
bundle is forbidden. Replacing days with hours, renaming the channels, or making
small window changes would still be an M1A rescue and must fail this review.

M1E must preserve the causal sequence `compression state -> completed expansion
event -> later execution`. A generic highest-high breakout without independently
defined compression is not sufficient evidence of a distinct candidate.

## Decision

M1E-04 passes non-duplication at the economic-hypothesis level because no M1A
indicator or parameter has been selected and the proposed state-transition
mechanism is materially different. Every later fixed rule must be checked again;
this pass cannot validate a future implementation that reintroduces M1A.
