# M1H IS Paper-Feasibility Report

- Status: failed_feasibility
- Scope: one frozen M1H sealed-IS market-reaction observation
- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN
- Candidate evaluated: paper event mechanism only
- Formal strategy returns computed: no
- PnL/equity/Sharpe computed: no
- Backtest executed: no
- OOS events/prices/returns accessed: no
- OOS opened: no
- Protocol SHA256: `ffd80444e381a0499831d47db1ad61082dc38e2d092bfe29c58d83b873cf9081`
- Qualification manifest SHA256: `8952e81e7ef4202e9c474ca67576ebc903f9a8940a1931c2c8404c30acd5c7fb`
- Event evidence SHA256: `4acbcc86111c6470dbe71a2a588ffe488d27f4a9e7f5e8717b2cd540b5c06904`

## Event And Episode Budget

- Raw frozen funding extremes: 405
- Same-symbol 24h representatives: 167
- Complete symbol observations: 167
- Independent cross-symbol market episodes: 131
- Right-censored observations: 0
- Invalid observations: 0
- Projected full independent episodes: 187
- Projected sealed-OOS episodes: 56 (IS event rate and calendar length only)

## Frozen Reaction Horizons

| Horizon | Complete | Median close displacement | Positive share | P05 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1h | 167 | 0.0033% | 50.90% | -1.1163% | 1.8243% |
| 2h | 167 | 0.0063% | 50.30% | -1.6644% | 1.8060% |
| 4h | 167 | 0.0025% | 50.30% | -3.4100% | 3.3339% |
| 8h | 167 | -0.0277% | 49.10% | -4.1910% | 4.3811% |
| 12h | 167 | 0.0565% | 50.30% | -5.0290% | 5.6982% |
| 24h | 167 | 0.0714% | 52.10% | -6.4001% | 9.1660% |

## Mandatory Path Diagnostics

- Median 24h MFE: 2.3108%
- Median 24h close displacement: 0.0714%
- MAE minimum / P05 / median / P95: -21.7403% / -10.2390% / -1.9031% / -0.2893%
- Recovery share: 93.41%
- Recovery median / P90: 5.0 / 47.5 minutes
- Unrecovered within 24h: 11
- MFE is path evidence only and is not a standalone Gate or realizable profit.

## Symbol Evidence

| Symbol | Complete events | Median 24h close displacement | Median 24h MFE |
| --- | ---: | ---: | ---: |
| BTCUSDT | 86 | 0.0731% | 2.0269% |
| ETHUSDT | 81 | 0.0132% | 2.5120% |

## Independent Episode Year Distribution

- 2021: 25
- 2022: 63
- 2023: 20
- 2024: 23

- Years with at least ten independent episodes: 4
- Maximum single-year episode share: 48.09%

## Frozen Paper Gate

| Gate | Result |
| --- | --- |
| projected_full_independent_episodes | pass |
| projected_sealed_oos_episodes | pass |
| combined_median_24h_close_displacement | fail |
| each_symbol_complete_events | pass |
| each_symbol_median_24h_close_displacement | fail |
| year_distribution | pass |
| single_year_concentration | fail |
| invalid_data_events | pass |

## Interpretation And Permissions

This report measures post-settlement spot paths under the frozen protocol. It does not define entries, exits, positions, fees, PnL, Sharpe, equity or a trading result.
No protocol threshold, horizon, interval, clustering rule, year or symbol definition was changed after observing the evidence.
- M1H Fixed Rule Contract Design authorized next: no
- Strategy code authorized: no
- Freqtrade implementation authorized: no
- Backtesting authorized: no
- OOS authorized: no
- API/trading authorized: no
- M2 authorized: no
