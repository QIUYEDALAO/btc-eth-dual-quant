# M1G IS Validation Report

- Status: failed_validation
- Generated UTC: 2026-07-11T08:24:06+00:00
- Scope: frozen M1G IS performance validation and independent execution repricing only
- IS range: 2020-07-01T00:00:00Z to 2024-09-11T00:00:00Z (end exclusive)
- OOS opened: no
- OOS prices/returns accessed: no
- Parameters changed after protocol freeze: no
- API key/private data used: no
- Live/paper/execution implemented: no

## Decision

M1G failed its frozen IS Gate. The strategy loses money under Base and Cost x2, daily-MTM risk-adjusted performance is below the preregistered thresholds, and the conservative execution audit does not preserve every native exit bar. OOS remains sealed. No parameter, target, stop, cooldown, cost, or Gate may be changed to rescue this candidate.

## Fixed Run Matrix

| Scenario | Trades | Native return | Audited return | Native Sharpe | Audited Sharpe | Native PSR | Audited PSR | Native MaxDD | Audited MaxDD | Benchmark return | Exit-bar mismatches | Archive SHA256 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| base | 179 | -22.6272% | -21.3551% | -1.3195 | -1.2911 | 0.0013 | 0.0014 | 23.9747% | 22.4729% | 281.8782% | 66 | `e2230534fc5e6d01b876b53c6ca6ffe10bd59b0d7e1825146beadbc041a1b4a9` |
| cost_x2 | 177 | -28.3540% | -31.5286% | -1.6457 | -1.9391 | 0.0001 | 0.0000 | 29.5509% | 32.2821% | 279.0936% | 83 | `6b292574cf451a2ba2dcedab8156c11ee7cb6ade43e6b49e1ecd8c6f28230ff0` |
| stress_a | 177 | -33.8995% | -37.5124% | -1.9457 | -2.3508 | 0.0000 | 0.0000 | 34.9724% | 38.0426% | 277.2478% | 84 | `796867ccbb1b4d3847c795a8144cc8d8eb693221aa69171c8cb6e526f5628f71` |
| stress_b | 176 | -41.6030% | -45.7401% | -2.4026 | -2.9116 | 0.0000 | 0.0000 | 42.5089% | 46.0387% | 274.4951% | 91 | `7d9e5b3fe99242decbaf587c670e811a268ec8a8518b7c1ba20bad3e78a7b398` |

## Conservative Execution Audit

- base: stop=54, target=104, timeout=21; native/audited exit-bar mismatches=66.
- cost_x2: stop=53, target=103, timeout=21; native/audited exit-bar mismatches=83.
- stress_a: stop=53, target=103, timeout=21; native/audited exit-bar mismatches=84.
- stress_b: stop=53, target=102, timeout=21; native/audited exit-bar mismatches=91.
- The audit consumed only exported trade lifecycles and canonical public 5m OHLC.
- It did not detect events, select pairs, create trades, or alter the frozen signal sequence.
- Same-bar ambiguity resolves to stop; target gaps fill at target; stop gaps use the worse of threshold/open; timeout uses the first 5m open at or after 24h.
- Because the frozen protocol requires exact exit-bar agreement, every non-zero mismatch count is an audit Gate failure.

## Gate Matrix

| Gate | Result |
| --- | --- |
| Complete IS trades >= 56 | pass |
| Base native total return > 0 | fail |
| Base native daily MTM Sharpe >= 1.0 | fail |
| Base native PSR >= 0.95 | fail |
| Base native MaxDD <= 15% | fail |
| Base native delete-best-3 return >= 0 | fail |
| Base native positive segments >= 3/4 | fail |
| Base native Sharpe >= benchmark | fail |
| Base native MaxDD <= benchmark | pass |
| Base native return > benchmark | fail |
| Base conservative total return > 0 | fail |
| Base conservative daily MTM Sharpe >= 1.0 | fail |
| Base conservative PSR >= 0.95 | fail |
| Base conservative MaxDD <= 15% | fail |
| Base conservative delete-best-3 return >= 0 | fail |
| Base conservative positive segments >= 3/4 | fail |
| Base conservative Sharpe >= benchmark | fail |
| Base conservative MaxDD <= benchmark | pass |
| Base conservative return > benchmark | fail |
| Base conservative exit bar matches native | fail |
| Cost x2 native total return > 0 | fail |
| Cost x2 native daily MTM Sharpe >= 1.0 | fail |
| Cost x2 native PSR >= 0.95 | fail |
| Cost x2 native MaxDD <= 15% | fail |
| Cost x2 native delete-best-3 return >= 0 | fail |
| Cost x2 native positive segments >= 3/4 | fail |
| Cost x2 native Sharpe >= benchmark | fail |
| Cost x2 native MaxDD <= benchmark | pass |
| Cost x2 native return > benchmark | fail |
| Cost x2 conservative total return > 0 | fail |
| Cost x2 conservative daily MTM Sharpe >= 1.0 | fail |
| Cost x2 conservative PSR >= 0.95 | fail |
| Cost x2 conservative MaxDD <= 15% | fail |
| Cost x2 conservative delete-best-3 return >= 0 | fail |
| Cost x2 conservative positive segments >= 3/4 | fail |
| Cost x2 conservative Sharpe >= benchmark | fail |
| Cost x2 conservative MaxDD <= benchmark | pass |
| Cost x2 conservative return > benchmark | fail |
| Cost x2 conservative exit bar matches native | fail |
| Lookahead analysis pass | pass |
| Recursive analysis pass | pass |
| Unexplained data gaps = 0 | pass |

## Diagnostics

### base

- Native delete-best-3 return: -23.9765%
- Audited delete-best-3 return: -22.4743%
- Native four-segment returns: -3.7183%, -8.4012%, -3.7043%, -6.8033%
- Audited four-segment returns: -4.7547%, -7.3145%, -1.8208%, -7.4651%
- Best native trade PnL: 450.76418248 USDT
- Worst native trade PnL: -1078.22854390 USDT
- Median holding: 5.00 hours
- Longest sleep: 77 days
- Best-three share of positive PnL: 3.3896%

### cost_x2

- Native delete-best-3 return: -29.7043%
- Audited delete-best-3 return: -32.4191%
- Native four-segment returns: -5.2393%, -10.3029%, -5.3601%, -7.4518%
- Audited four-segment returns: -7.9364%, -11.5170%, -3.5585%, -8.5167%
- Best native trade PnL: 451.39471419 USDT
- Worst native trade PnL: -1152.06836466 USDT
- Median holding: 5.83 hours
- Longest sleep: 77 days
- Best-three share of positive PnL: 3.7120%

### stress_a

- Native delete-best-3 return: -35.2506%
- Audited delete-best-3 return: -38.2514%
- Native four-segment returns: -8.9247%, -11.6317%, -5.8147%, -7.5284%
- Audited four-segment returns: -10.4903%, -13.7023%, -4.4673%, -8.8525%
- Best native trade PnL: 451.90860419 USDT
- Worst native trade PnL: -1201.29404678 USDT
- Median holding: 7.17 hours
- Longest sleep: 77 days
- Best-three share of positive PnL: 4.0474%

### stress_b

- Native delete-best-3 return: -42.9546%
- Audited delete-best-3 return: -46.2528%
- Native four-segment returns: -13.0804%, -14.1887%, -6.5102%, -7.8238%
- Audited four-segment returns: -14.2797%, -16.7046%, -5.6006%, -9.1553%
- Best native trade PnL: 452.15555133 USDT
- Worst native trade PnL: -1275.13091212 USDT
- Median holding: 8.38 hours
- Longest sleep: 77 days
- Best-three share of positive PnL: 4.7631%

## Data And Runtime Evidence

- Signal data: canonical public Binance spot 1h OHLC.
- Detail and repricing data: canonical public Binance spot 5m OHLC.
- Runtime: official pinned Freqtrade 2026.6 image from the frozen protocol.
- Lookahead analysis: pass (20 signals, zero biased entries/exits/indicators).
- Recursive analysis: pass (startup 170/250/340, zero indicator variance and no lookahead).
- Unexplained data gaps: 0; qualified common exchange-outage windows remain excluded by the canonical contract.
- Runtime archives, canonical OHLC, DuckDB, raw data and logs committed: no.

## Authorization

- M1G OOS opening: no
- M1G parameter rescue: no
- M1H design review after this failure record merges: yes
- M2: no
- Dry-run/live/API trading: no

This report is research validation evidence and is not investment advice.
