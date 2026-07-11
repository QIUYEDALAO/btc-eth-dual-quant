# M1E IS Paper-Feasibility Report

- Status: failed_feasibility
- Scope: M1E-06 IS-only paper diagnostics
- Candidate evaluated: paper events only
- Formal strategy returns computed: no
- Equity curve computed: no
- OOS prices/returns accessed: no
- OOS opened: no
- Protocol SHA256: `fcd16d409498e07435252039c79b1e360d0af49c4870da75700fe44bcabaa995`
- IS snapshot manifest SHA256: `196766378f11d5773b66cb8202f6b636fc9c093e41b481ea8d1c5acf2725c946`
- Event evidence SHA256: `a01843e2393db8dd10266ce795a0dd0555335441e57584184889cf09311e98e5`

## Event Budget

- Raw expansion candidates: 177
- 24h cluster representatives: 139
- Complete events: 139
- Right-censored events: 0
- Projected full events: 198
- Projected sealed-OOS events: 59
- Longest no-event period: 191.92 days

## Path Evidence

- Combined median 24h MFE: 1.4005%
- Combined median 24h MAE: -1.4565%

| Horizon | Count | Mean displacement | Median | Positive | P05 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1h | 139 | -0.0645% | -0.0984% | 41.01% | -1.1708% | 0.9721% |
| 2h | 139 | -0.0314% | -0.0540% | 44.60% | -1.3839% | 1.3548% |
| 4h | 139 | 0.1190% | -0.0593% | 45.32% | -1.7182% | 2.0772% |
| 8h | 139 | 0.1953% | -0.0127% | 48.92% | -2.6484% | 3.5239% |
| 12h | 139 | 0.2733% | 0.1210% | 54.68% | -3.0228% | 3.7551% |
| 24h | 139 | 0.2098% | -0.0987% | 49.64% | -4.3454% | 5.4353% |

## Symbol Evidence

| Symbol | Events | Median 24h MFE | Median 24h MAE |
| --- | ---: | ---: | ---: |
| BTCUSDT | 66 | 1.4658% | -1.4363% |
| ETHUSDT | 73 | 1.4005% | -1.5623% |

## Year Distribution

- 2022: 56
- 2023: 38
- 2024: 45

## Paper Gate

| Gate | Result |
| --- | --- |
| projected_full_events | pass |
| projected_oos_events | pass |
| combined_median_mfe | fail |
| each_symbol_events | pass |
| each_symbol_median_mfe | fail |
| year_distribution | pass |
| single_year_concentration | pass |
| quarantine_or_unrewarmed_events | pass |

- M1E-07 fixed rule contract authorized: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- OOS authorized: no
- M2 authorized: no

This report measures price paths after preregistered IS events. It is not a strategy backtest and contains no entry, exit, position, fee-adjusted trade return or equity curve.
