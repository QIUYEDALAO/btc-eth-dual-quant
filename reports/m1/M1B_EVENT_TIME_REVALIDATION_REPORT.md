# M1B Event-Time Revalidation Report

- Status: failed_validation
- Scope: funding-rate-arbitrage offline event-time revalidation only
- Historical report remains unchanged and invalidated for future approval
- No live trading
- No paper trading with real API
- No execution/live
- No order placement or cancellation
- No API key or private data
- This report does not approve M2
- Not investment advice

## Data Authority

- Source: local M0 append-only public data
- Required profile: BTCUSDT and ETHUSDT 1h spot, UM perpetual, mark, index, premium, plus funding history
- M0 audit status: audit_revalidation_required; source-level ZIP/REST blockers remain separate
- Freqtrade role: futures short/funding framework smoke only; not the two-leg portfolio truth
- Portfolio range: 2020-01-01 00:00:00 UTC -> 2024-12-31 23:59:59 UTC
- BTCUSDT range: 2020-01-01 00:00:00 UTC -> 2024-12-31 23:59:59 UTC
- ETHUSDT range: 2020-01-01 00:00:00 UTC -> 2024-12-31 23:59:59 UTC

## Event-Time Contract

- A funding event at T becomes visible only at T.
- Entry uses the first common spot/perpetual 1h open strictly after T.
- The triggering funding event is excluded from funding income.
- While held, funding at T is credited using the latest mark bar with close_time <= T.
- Exit signals are evaluated after the held-position funding at T and execute at the next common 1h open.
- The low-funding exit requires the trailing mean to remain below 2% APR for three consecutive days.
- Positions without a legal exit price at data end are incomplete and do not count as complete cycles.

## Fixed Rules And Costs

- expected_hold_days: 14
- roundtrip_cost_base: 0.5000%
- min_payback_ratio: 2.0
- payback-required APR: 26.0714%
- 8% APR alone is rejected by the payback gate.
- Fees use actual entry and exit notionals for spot and perpetual fills.
- Slippage is charged separately on all four fill directions.

## Base Cost Portfolio

- total_return: 142.0455%
- annualized_return: 19.3151%
- annualized_volatility: 2.4732%
- sharpe: 7.1534
- max_drawdown: 1.5502%
- complete_cycles: 13
- incomplete_positions: 2
- funding_income_total: 1.44172580
- basis_pnl_total: 0.01814877
- fees_total: 0.02365196
- slippage_total: 0.01576738
- worst_cycle: 0.0836%
- best_cycle: 144.6781%
- longest_sleep_days: 713.00

## Cost X2 Portfolio

- total_return: 138.1036%
- annualized_return: 18.9243%
- annualized_volatility: 2.5404%
- sharpe: 6.8357
- max_drawdown: 1.5738%
- complete_cycles: 13
- incomplete_positions: 2
- funding_income_total: 1.44172580
- basis_pnl_total: 0.01814877
- fees_total: 0.04730392
- slippage_total: 0.03153475
- worst_cycle: -0.4014%
- best_cycle: 143.0077%
- longest_sleep_days: 713.00

## BTCUSDT

- total_return: 91.4956%
- annualized_return: 13.8597%
- annualized_volatility: 2.1158%
- sharpe: 6.1455
- max_drawdown: 2.0919%
- complete_cycles: 7
- incomplete_positions: 1
- funding_income_total: 0.92700922
- basis_pnl_total: 0.02428667
- fees_total: 0.02180506
- slippage_total: 0.01453528
- worst_cycle: 0.0836%
- best_cycle: 65.5244%
- longest_sleep_days: 713.00
- cost_x2_total_return: 87.8615%
- interval_distribution: {'8h': 5481}
- interval_warnings: ['none']
- diagnostics_status: partial
- mark/index/premium diagnostics: {'funding_events': 5481, 'missing_mark_events': 1, 'missing_index_events': 1, 'missing_premium_events': 1, 'mean_mark_index_spread': -9.998322149674981e-05, 'max_abs_mark_index_spread': 0.14824320067405103, 'mean_abs_premium_consistency_error': 0.00045607851434280273, 'input_quality': {'spot_klines': {'raw_rows': 43817, 'valid_completed_1h_rows': 43810, 'invalid_close_boundary_rows': 7, 'observed_gap_boundaries': 16}, 'um_futures_klines': {'raw_rows': 43848, 'valid_completed_1h_rows': 43848, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 0}, 'mark_price_klines': {'raw_rows': 43656, 'valid_completed_1h_rows': 43656, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}, 'index_price_klines': {'raw_rows': 43560, 'valid_completed_1h_rows': 43560, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 8}, 'premium_index_klines': {'raw_rows': 43679, 'valid_completed_1h_rows': 43679, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}}}

## ETHUSDT

- total_return: 192.5955%
- annualized_return: 23.9229%
- annualized_volatility: 3.2418%
- sharpe: 6.6332
- max_drawdown: 1.6616%
- complete_cycles: 6
- incomplete_positions: 1
- funding_income_total: 1.95644239
- basis_pnl_total: 0.01201087
- fees_total: 0.02549886
- slippage_total: 0.01699947
- worst_cycle: 2.2157%
- best_cycle: 144.6781%
- longest_sleep_days: 670.33
- cost_x2_total_return: 188.3457%
- interval_distribution: {'8h': 5481}
- interval_warnings: ['none']
- diagnostics_status: partial
- mark/index/premium diagnostics: {'funding_events': 5481, 'missing_mark_events': 1, 'missing_index_events': 1, 'missing_premium_events': 1, 'mean_mark_index_spread': -8.753918882995132e-06, 'max_abs_mark_index_spread': 0.01100063896534263, 'mean_abs_premium_consistency_error': 0.0001716217594586438, 'input_quality': {'spot_klines': {'raw_rows': 43817, 'valid_completed_1h_rows': 43810, 'invalid_close_boundary_rows': 7, 'observed_gap_boundaries': 16}, 'um_futures_klines': {'raw_rows': 43848, 'valid_completed_1h_rows': 43848, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 0}, 'mark_price_klines': {'raw_rows': 43800, 'valid_completed_1h_rows': 43800, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 2}, 'index_price_klines': {'raw_rows': 43776, 'valid_completed_1h_rows': 43776, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 3}, 'premium_index_klines': {'raw_rows': 43679, 'valid_completed_1h_rows': 43679, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}}}

## Complete Cycles

| symbol | entry signal UTC | entry open UTC | exit signal UTC | exit open UTC | funding events | funding | basis | fees | slippage | net return | reason |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| BTCUSDT | 2020-01-17 16:00:00 UTC | 2020-01-17 17:00:00 UTC | 2020-03-13 00:00:00 UTC | 2020-03-13 01:00:00 UTC | 166 | 0.06957423 | 0.01371232 | 0.00228096 | 0.00151864 | 7.9487% | negative_funding_streak |
| ETHUSDT | 2020-01-20 08:00:00 UTC | 2020-01-20 09:00:00 UTC | 2020-03-13 16:00:00 UTC | 2020-03-13 17:00:00 UTC | 160 | 0.11207088 | 0.00120956 | 0.00262017 | 0.00174690 | 10.8913% | negative_funding_streak |
| ETHUSDT | 2020-05-02 16:00:00 UTC | 2020-05-02 17:00:00 UTC | 2020-09-21 00:00:00 UTC | 2020-09-21 01:00:00 UTC | 424 | 0.14699347 | 0.00172752 | 0.00412261 | 0.00274846 | 14.1850% | negative_funding_streak |
| BTCUSDT | 2020-05-09 08:00:00 UTC | 2020-05-09 09:00:00 UTC | 2020-05-22 08:00:00 UTC | 2020-05-22 09:00:00 UTC | 39 | 0.00366595 | 0.00202010 | 0.00290982 | 0.00194003 | 0.0836% | negative_funding_streak |
| BTCUSDT | 2020-07-27 08:00:00 UTC | 2020-07-27 09:00:00 UTC | 2020-09-15 08:00:00 UTC | 2020-09-15 09:00:00 UTC | 150 | 0.04467816 | 0.00171685 | 0.00307040 | 0.00204708 | 4.1278% | negative_funding_streak |
| ETHUSDT | 2020-10-22 00:00:00 UTC | 2020-10-22 01:00:00 UTC | 2021-06-19 08:00:00 UTC | 2021-06-19 09:00:00 UTC | 721 | 1.45891150 | 0.00457255 | 0.01002210 | 0.00668120 | 144.6781% | negative_funding_streak |
| BTCUSDT | 2020-11-19 16:00:00 UTC | 2020-11-19 17:00:00 UTC | 2021-05-23 08:00:00 UTC | 2021-05-23 09:00:00 UTC | 554 | 0.65995436 | 0.00256137 | 0.00436293 | 0.00290857 | 65.5244% | negative_funding_streak |
| ETHUSDT | 2021-08-16 00:00:00 UTC | 2021-08-16 01:00:00 UTC | 2021-09-25 00:00:00 UTC | 2021-09-25 01:00:00 UTC | 120 | 0.02484460 | 0.00203522 | 0.00283380 | 0.00188939 | 2.2157% | negative_funding_streak |
| BTCUSDT | 2021-09-01 16:00:00 UTC | 2021-09-01 17:00:00 UTC | 2021-09-24 08:00:00 UTC | 2021-09-24 09:00:00 UTC | 68 | 0.00893126 | 0.00127719 | 0.00287785 | 0.00191866 | 0.5412% | negative_funding_streak |
| ETHUSDT | 2021-10-16 00:00:00 UTC | 2021-10-16 01:00:00 UTC | 2022-01-10 08:00:00 UTC | 2022-01-10 09:00:00 UTC | 259 | 0.04432382 | 0.00127183 | 0.00272718 | 0.00181816 | 4.1050% | negative_funding_streak |
| BTCUSDT | 2021-10-16 16:00:00 UTC | 2021-10-16 17:00:00 UTC | 2022-01-13 00:00:00 UTC | 2022-01-13 01:00:00 UTC | 265 | 0.04583409 | 0.00156143 | 0.00258185 | 0.00172138 | 4.3092% | negative_funding_streak |
| ETHUSDT | 2023-11-11 16:00:00 UTC | 2023-11-11 17:00:00 UTC | 2024-08-05 08:00:00 UTC | 2024-08-05 09:00:00 UTC | 803 | 0.16929811 | 0.00119418 | 0.00317299 | 0.00211536 | 16.5204% | negative_funding_streak |
| BTCUSDT | 2023-12-27 00:00:00 UTC | 2023-12-27 01:00:00 UTC | 2024-04-19 00:00:00 UTC | 2024-04-19 01:00:00 UTC | 342 | 0.09437118 | 0.00143742 | 0.00372124 | 0.00248092 | 8.9606% | negative_funding_streak |

## Funding Contributions

| symbol | settlement UTC | interval hours | rate | mark | perp quantity | income | mark bar close UTC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| BTCUSDT | 2020-01-18 00:00:00 UTC | 8.0000 | 0.00010000 | 8914.02109157 | 0.000112663870 | 0.00010043 | 2020-01-17 23:59:59 UTC |
| BTCUSDT | 2020-01-18 08:00:00 UTC | 8.0000 | 0.00029182 | 8843.58184889 | 0.000112663870 | 0.00029076 | 2020-01-18 07:59:59 UTC |
| BTCUSDT | 2020-01-18 16:00:00 UTC | 8.0000 | 0.00032081 | 8902.78119252 | 0.000112663870 | 0.00032178 | 2020-01-18 15:59:59 UTC |
| BTCUSDT | 2020-01-19 00:00:00 UTC | 8.0000 | 0.00020041 | 8917.21065037 | 0.000112663870 | 0.00020134 | 2020-01-18 23:59:59 UTC |
| BTCUSDT | 2020-01-19 08:00:00 UTC | 8.0000 | 0.00039329 | 9084.66972887 | 0.000112663870 | 0.00040254 | 2020-01-19 07:59:59 UTC |
| BTCUSDT | 2020-01-19 16:00:00 UTC | 8.0000 | 0.00092467 | 8634.59332183 | 0.000112663870 | 0.00089953 | 2020-01-19 15:59:59 UTC |
| BTCUSDT | 2020-01-20 00:00:00 UTC | 8.0000 | 0.00029702 | 8704.10467538 | 0.000112663870 | 0.00029127 | 2020-01-19 23:59:59 UTC |
| BTCUSDT | 2020-01-20 08:00:00 UTC | 8.0000 | 0.00010000 | 8663.28041368 | 0.000112663870 | 0.00009760 | 2020-01-20 07:59:59 UTC |
| BTCUSDT | 2020-01-20 16:00:00 UTC | 8.0000 | 0.00010782 | 8674.96375577 | 0.000112663870 | 0.00010538 | 2020-01-20 15:59:59 UTC |
| BTCUSDT | 2020-01-21 00:00:00 UTC | 8.0000 | 0.00012057 | 8642.31228371 | 0.000112663870 | 0.00011740 | 2020-01-20 23:59:59 UTC |
| BTCUSDT | 2020-01-21 08:00:00 UTC | 8.0000 | 0.00015425 | 8634.19777469 | 0.000112663870 | 0.00015005 | 2020-01-21 07:59:59 UTC |
| BTCUSDT | 2020-01-21 16:00:00 UTC | 8.0000 | 0.00015740 | 8643.82277357 | 0.000112663870 | 0.00015328 | 2020-01-21 15:59:59 UTC |
| BTCUSDT | 2020-01-22 00:00:00 UTC | 8.0000 | 0.00010000 | 8736.16858687 | 0.000112663870 | 0.00009843 | 2020-01-21 23:59:59 UTC |
| BTCUSDT | 2020-01-22 08:00:00 UTC | 8.0000 | 0.00021392 | 8736.38695156 | 0.000112663870 | 0.00021056 | 2020-01-22 07:59:59 UTC |
| BTCUSDT | 2020-01-22 16:00:00 UTC | 8.0000 | 0.00010000 | 8656.55740976 | 0.000112663870 | 0.00009753 | 2020-01-22 15:59:59 UTC |
| BTCUSDT | 2020-01-23 00:00:00 UTC | 8.0000 | 0.00010000 | 8682.71905379 | 0.000112663870 | 0.00009782 | 2020-01-22 23:59:59 UTC |
| BTCUSDT | 2020-01-23 08:00:00 UTC | 8.0000 | 0.00010000 | 8580.28622458 | 0.000112663870 | 0.00009667 | 2020-01-23 07:59:59 UTC |
| BTCUSDT | 2020-01-23 16:00:00 UTC | 8.0000 | 0.00052304 | 8356.88996138 | 0.000112663870 | 0.00049245 | 2020-01-23 15:59:59 UTC |
| BTCUSDT | 2020-01-24 00:00:00 UTC | 8.0000 | 0.00054719 | 8407.46052672 | 0.000112663870 | 0.00051831 | 2020-01-23 23:59:59 UTC |
| BTCUSDT | 2020-01-24 08:00:00 UTC | 8.0000 | 0.00042124 | 8335.69586116 | 0.000112663870 | 0.00039560 | 2020-01-24 07:59:59 UTC |
| BTCUSDT | 2020-01-24 16:00:00 UTC | 8.0000 | 0.00017948 | 8506.67283279 | 0.000112663870 | 0.00017201 | 2020-01-24 15:59:59 UTC |
| BTCUSDT | 2020-01-25 00:00:00 UTC | 8.0000 | 0.00010000 | 8440.36339245 | 0.000112663870 | 0.00009509 | 2020-01-24 23:59:59 UTC |
| BTCUSDT | 2020-01-25 08:00:00 UTC | 8.0000 | 0.00010000 | 8316.36146643 | 0.000112663870 | 0.00009370 | 2020-01-25 07:59:59 UTC |
| BTCUSDT | 2020-01-25 16:00:00 UTC | 8.0000 | 0.00010000 | 8336.21474929 | 0.000112663870 | 0.00009392 | 2020-01-25 15:59:59 UTC |
| BTCUSDT | 2020-01-26 00:00:00 UTC | 8.0000 | 0.00010000 | 8340.51788604 | 0.000112663870 | 0.00009397 | 2020-01-25 23:59:59 UTC |
| BTCUSDT | 2020-01-26 08:00:00 UTC | 8.0000 | 0.00010000 | 8385.72951786 | 0.000112663870 | 0.00009448 | 2020-01-26 07:59:59 UTC |
| BTCUSDT | 2020-01-26 16:00:00 UTC | 8.0000 | 0.00010000 | 8459.26225281 | 0.000112663870 | 0.00009531 | 2020-01-26 15:59:59 UTC |
| BTCUSDT | 2020-01-27 00:00:00 UTC | 8.0000 | 0.00010000 | 8613.13051794 | 0.000112663870 | 0.00009704 | 2020-01-26 23:59:59 UTC |
| BTCUSDT | 2020-01-27 08:00:00 UTC | 8.0000 | 0.00010000 | 8658.79331943 | 0.000112663870 | 0.00009755 | 2020-01-27 07:59:59 UTC |
| BTCUSDT | 2020-01-27 16:00:00 UTC | 8.0000 | 0.00010000 | 8779.05266206 | 0.000112663870 | 0.00009891 | 2020-01-27 15:59:59 UTC |
| BTCUSDT | 2020-01-28 00:00:00 UTC | 8.0000 | 0.00010000 | 8908.16211410 | 0.000112663870 | 0.00010036 | 2020-01-27 23:59:59 UTC |
| BTCUSDT | 2020-01-28 08:00:00 UTC | 8.0000 | 0.00068689 | 9040.35261002 | 0.000112663870 | 0.00069961 | 2020-01-28 07:59:59 UTC |
| BTCUSDT | 2020-01-28 16:00:00 UTC | 8.0000 | 0.00054394 | 9027.13208436 | 0.000112663870 | 0.00055320 | 2020-01-28 15:59:59 UTC |
| BTCUSDT | 2020-01-29 00:00:00 UTC | 8.0000 | 0.00062324 | 9377.70986127 | 0.000112663870 | 0.00065847 | 2020-01-28 23:59:59 UTC |
| BTCUSDT | 2020-01-29 08:00:00 UTC | 8.0000 | 0.00108193 | 9365.58020268 | 0.000112663870 | 0.00114161 | 2020-01-29 07:59:59 UTC |
| BTCUSDT | 2020-01-29 16:00:00 UTC | 8.0000 | 0.00053694 | 9285.33087514 | 0.000112663870 | 0.00056170 | 2020-01-29 15:59:59 UTC |
| BTCUSDT | 2020-01-30 00:00:00 UTC | 8.0000 | 0.00023600 | 9302.58840569 | 0.000112663870 | 0.00024734 | 2020-01-29 23:59:59 UTC |
| BTCUSDT | 2020-01-30 08:00:00 UTC | 8.0000 | 0.00024877 | 9390.46777169 | 0.000112663870 | 0.00026319 | 2020-01-30 07:59:59 UTC |
| BTCUSDT | 2020-01-30 16:00:00 UTC | 8.0000 | 0.00034852 | 9386.79498604 | 0.000112663870 | 0.00036858 | 2020-01-30 15:59:59 UTC |
| BTCUSDT | 2020-01-31 00:00:00 UTC | 8.0000 | 0.00053551 | 9514.52609458 | 0.000112663870 | 0.00057404 | 2020-01-30 23:59:59 UTC |
| BTCUSDT | 2020-01-31 08:00:00 UTC | 8.0000 | 0.00077154 | 9374.20013192 | 0.000112663870 | 0.00081485 | 2020-01-31 07:59:59 UTC |
| BTCUSDT | 2020-01-31 16:00:00 UTC | 8.0000 | 0.00039858 | 9336.88767645 | 0.000112663870 | 0.00041928 | 2020-01-31 15:59:59 UTC |
| BTCUSDT | 2020-02-01 00:00:00 UTC | 8.0000 | 0.00074991 | 9351.14943875 | 0.000112663870 | 0.00079006 | 2020-01-31 23:59:59 UTC |
| BTCUSDT | 2020-02-01 08:00:00 UTC | 8.0000 | 0.00065667 | 9422.00024534 | 0.000112663870 | 0.00069707 | 2020-02-01 07:59:59 UTC |
| BTCUSDT | 2020-02-01 16:00:00 UTC | 8.0000 | 0.00049052 | 9337.03977673 | 0.000112663870 | 0.00051600 | 2020-02-01 15:59:59 UTC |
| BTCUSDT | 2020-02-02 00:00:00 UTC | 8.0000 | 0.00028263 | 9385.98568092 | 0.000112663870 | 0.00029887 | 2020-02-01 23:59:59 UTC |
| BTCUSDT | 2020-02-02 08:00:00 UTC | 8.0000 | 0.00034916 | 9371.59623502 | 0.000112663870 | 0.00036866 | 2020-02-02 07:59:59 UTC |
| BTCUSDT | 2020-02-02 16:00:00 UTC | 8.0000 | 0.00065524 | 9451.67808155 | 0.000112663870 | 0.00069774 | 2020-02-02 15:59:59 UTC |
| BTCUSDT | 2020-02-03 00:00:00 UTC | 8.0000 | 0.00060677 | 9330.83231755 | 0.000112663870 | 0.00063787 | 2020-02-02 23:59:59 UTC |
| BTCUSDT | 2020-02-03 08:00:00 UTC | 8.0000 | 0.00035862 | 9370.96335533 | 0.000112663870 | 0.00037862 | 2020-02-03 07:59:59 UTC |
| ... | ... | ... | ... | ... | ... | ... | truncated, total=4071 |

## Incomplete Positions

- count: 2
- BTCUSDT: entry=2024-11-12 17:00:00 UTC, last_event=2024-12-31 16:00:00 UTC, funding_periods=147, reason=data_end_without_legal_exit
- ETHUSDT: entry=2024-11-12 17:00:00 UTC, last_event=2024-12-31 16:00:00 UTC, funding_periods=147, reason=data_end_without_legal_exit

## OOS

- split: 2023-07-02 21:35:59 UTC
- OOS total return: 5.5561%
- OOS Sharpe: 9.4023
- OOS complete cycles: 2
- OOS carry-in cycles: 0
- Carry-in positions are reported separately and excluded from OOS complete-cycle count.

## UTC Portfolio Alignment

- diagnostics: {'utc_union_points': 5495, 'utc_intersection_points': 5482, 'symbols_aligned_by_utc_timestamp': True, 'component_diagnostics': {'BTCUSDT': {'funding_events': 5481, 'missing_mark_events': 1, 'missing_index_events': 1, 'missing_premium_events': 1, 'mean_mark_index_spread': -9.998322149674981e-05, 'max_abs_mark_index_spread': 0.14824320067405103, 'mean_abs_premium_consistency_error': 0.00045607851434280273, 'input_quality': {'spot_klines': {'raw_rows': 43817, 'valid_completed_1h_rows': 43810, 'invalid_close_boundary_rows': 7, 'observed_gap_boundaries': 16}, 'um_futures_klines': {'raw_rows': 43848, 'valid_completed_1h_rows': 43848, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 0}, 'mark_price_klines': {'raw_rows': 43656, 'valid_completed_1h_rows': 43656, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}, 'index_price_klines': {'raw_rows': 43560, 'valid_completed_1h_rows': 43560, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 8}, 'premium_index_klines': {'raw_rows': 43679, 'valid_completed_1h_rows': 43679, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}}}, 'ETHUSDT': {'funding_events': 5481, 'missing_mark_events': 1, 'missing_index_events': 1, 'missing_premium_events': 1, 'mean_mark_index_spread': -8.753918882995132e-06, 'max_abs_mark_index_spread': 0.01100063896534263, 'mean_abs_premium_consistency_error': 0.0001716217594586438, 'input_quality': {'spot_klines': {'raw_rows': 43817, 'valid_completed_1h_rows': 43810, 'invalid_close_boundary_rows': 7, 'observed_gap_boundaries': 16}, 'um_futures_klines': {'raw_rows': 43848, 'valid_completed_1h_rows': 43848, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 0}, 'mark_price_klines': {'raw_rows': 43800, 'valid_completed_1h_rows': 43800, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 2}, 'index_price_klines': {'raw_rows': 43776, 'valid_completed_1h_rows': 43776, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 3}, 'premium_index_klines': {'raw_rows': 43679, 'valid_completed_1h_rows': 43679, 'invalid_close_boundary_rows': 0, 'observed_gap_boundaries': 5}}}}}
- BTC and ETH component equity are joined only by UTC timestamps.

## Freqtrade Cross-Check Boundary

- Freqtrade 2026.6 remains the primary single-leg research framework.
- A futures-only short/funding smoke may cross-check the perpetual leg.
- Freqtrade does not provide the native combined spot-long plus perpetual-short portfolio truth.
- No two-bot workaround is treated as proof because leg synchronization and reconciliation remain external.

## Gates

| Gate | Status |
| --- | --- |
| Backtest code | pass |
| Funding interval not hardcoded | pass |
| Payback threshold | pass |
| Base cost positive | pass |
| Cost x2 positive | pass |
| Complete cycles >= 20 | fail |
| OOS Sharpe >= 1.0 | pass |
| Max drawdown <= 5% | pass |
| Funding dries up gracefully | pass |
| No lookahead | pass |
| Final M1B status | failed_validation |

## Decision

- Failed or blocked numerical gates: Complete cycles >= 20=fail
- Final M1B status: failed_validation
- Even if every numerical gate passes, the maximum automatic status is under_review.
- M1A and historical M1B remain failed_validation.
- No strategy is eligible for M2.
- No result here approves live trading, paper trading, API permissions, or execution.

## Known Limitations

- Public market data cannot model real two-leg fill synchronization, margin failures, or reconciliation incidents.
- M0 audit source discrepancies remain unresolved independently of this accounting correction.
- Freqtrade futures output is a single-leg smoke and is not substituted for two-leg accounting.
