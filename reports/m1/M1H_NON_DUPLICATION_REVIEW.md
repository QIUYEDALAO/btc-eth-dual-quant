# M1H Non-Duplication Review

- Status: pass_design_level
- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN
- Compared with: M1B, M1G, M1E and M1D
- Prior failed outcome used to select rules: no
- Existing candidate threshold reused: no
- OOS accessed: no
- Strategy implementation authorized: no

## Structural Difference Matrix

| Axis | M1H | M1G | M1B | Design conclusion |
| --- | --- | --- | --- | --- |
| Primary signal source | Settled public funding observation | Spot OHLC panic dislocation | Positive funding and payback economics | Structurally different |
| Decision time | At or after funding settlement | After completed 1h spot candle | After funding event with two-leg accounting | Separately defined |
| Return source | Later spot appreciation after crowding unwind | Spot panic mean reversion | Funding cashflow plus basis/leg PnL | Structurally different |
| Position | Spot long or cash | Spot long or cash | Spot long plus perpetual short | No futures position |
| Funding role | Sentiment information only | Not a primary input | Income and entry economics | No funding capture |
| Execution family | Future single-leg Freqtrade lifecycle | Single-leg Freqtrade lifecycle | Offline two-leg accounting | No coordinator or hedge |

## Prohibited Interpretations

- A spot-price panic threshold may not replace funding as the primary trigger.
- M1G's decline, range, close-location, target, stop or cooldown may not be reused.
- M1B's positive-funding, payback, holding-income, basis hedge or perpetual-short rules may not be reused.
- Funding income, basis convergence and futures PnL may not be reported as M1H returns.
- Failed M1E/M1G outcomes may not select M1H rules.
- A smaller timeframe or more leverage may not be used as a rescue.

## Decision

M1H is distinct at the signal-source, timing, return-source and position axes.
The registered hypothesis and hash predate this review, and no parameter or
event outcome was selected. Non-duplication passes only at design level and
must be rechecked at every later Gate.
