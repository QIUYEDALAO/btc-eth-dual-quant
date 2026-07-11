# M1G IS Paper-Feasibility Report

- Status: pass
- Scope: exact frozen M1G sealed-IS paper protocol
- Candidate evaluated: paper events only
- Formal strategy returns computed: no
- Equity curve computed: no
- OOS prices/returns accessed: no
- OOS opened: no
- Protocol SHA256: `b77feb6725ee80837f67a56513a67bf7f305ea043dc81f4087c762fc4a61e91d`
- IS snapshot manifest SHA256: `196766378f11d5773b66cb8202f6b636fc9c093e41b481ea8d1c5acf2725c946`
- Event evidence SHA256: `ed46d31164c195618320f73ec59fd0c32838f774f81a055e61742b93ae5b5d50`

## Event Budget

- Raw panic candidates: 316
- 24h cluster representatives: 213
- Complete events: 210
- Right-censored events: 3
- Projected full events: 300
- Projected sealed-OOS events: 90
- Longest no-event period: 77.83 days

## Path And Tail Evidence

- Combined median 24h MFE: 2.6908%
- Combined median 24h MAE: -3.3118%
- Worst 24h MAE: -21.5829%
- Maximum rolling 24h event count: 2
- Maximum rolling 7d event count: 7

| Horizon | Count | Mean displacement | Median | Positive | P05 | P95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1h | 210 | 0.0923% | 0.1592% | 56.19% | -2.2976% | 2.4797% |
| 2h | 210 | 0.0633% | 0.0962% | 51.90% | -2.8121% | 3.3636% |
| 4h | 210 | -0.0587% | -0.0184% | 49.05% | -4.3550% | 4.2066% |
| 8h | 210 | 0.1013% | 0.0596% | 50.48% | -4.9372% | 4.9494% |
| 12h | 210 | 0.3087% | 0.0155% | 50.48% | -5.4075% | 6.8141% |
| 24h | 210 | 0.5736% | 0.2268% | 52.86% | -7.5969% | 9.4207% |

## Symbol Evidence

| Symbol | Events | Median 24h MFE | Median 24h MAE | Worst 24h MAE |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 88 | 2.6997% | -3.0170% | -13.7975% |
| ETHUSDT | 122 | 2.6409% | -3.7139% | -21.5829% |

## Year Distribution

- 2020: 13
- 2021: 59
- 2022: 80
- 2023: 23
- 2024: 35

## Paper Gate

| Gate | Result |
| --- | --- |
| projected_full_events | pass |
| projected_oos_events | pass |
| combined_median_mfe | pass |
| each_symbol_events | pass |
| each_symbol_median_mfe | pass |
| year_distribution | pass |
| single_year_concentration | pass |
| quarantine_or_unrewarmed_events | pass |

## Interpretation

- The preregistered paper Gate passes, but MFE is an opportunity envelope, not a realizable exit.
- Median 24h close displacement is 0.2268%, below both the 0.30% Base and 0.60% Cost x2 roundtrip references.
- Median 24h MAE is -3.3118% versus median MFE 2.6908%; worst MAE is -21.5829%.
- A fixed contract must therefore derive one target, one invalidation stop, a holding limit, position cap and cluster cooldown without parameter search.
- Paper pass does not establish positive expectancy, acceptable drawdown or implementability.

- Fixed rule contract authorized: yes
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- OOS authorized: no
- M2 authorized: no

This is price-path evidence after preregistered IS events, not a strategy backtest. It contains no fill, exit, position, fee-adjusted return or equity curve.
