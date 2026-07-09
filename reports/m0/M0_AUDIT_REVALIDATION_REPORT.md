# M0 Audit Revalidation Report

- Status: blocked
- Generated UTC: 2026-07-09T20:04:18+00:00
- Scope: public-data audit revalidation only
- Private smoke rerun: no
- API key used: no
- Raw data committed: no
- DuckDB committed: no
- Data start: 2019-09-01T00:00:00+00:00
- Data end: 2026-07-08T23:59:59+00:00
- Profile: BTCUSDT and ETHUSDT 1h spot/UM futures/mark/index/premium plus funding history

## ZIP/REST Evidence

| Dataset | Rows | Gaps | Missing rows | Overlap | Field differences | Scope | REST SHA256 | ZIP SHA256 |
|---|---:|---:|---:|---:|---:|---|---|---|
| `spot_klines:BTCUSDT` | 60036 | 17 | 1 | 11484 | 6 | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` | `c910882db65d0840470104c126e3b7f8142adaedbb4ce41a864b71c008643b77` | `c21d7dd650f320ef8372e3274f1b62d444c929ff53f3f61c9b9d90ab7ebd4c07` |
| `um_futures_klines:BTCUSDT` | 56952 | 0 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `9a4d50f25b326a15b656f9a913334b7251688bf375419a50ddc7bb200631f132` |
| `mark_price_klines:BTCUSDT` | 56736 | 6 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `77165404cbf17ee6a15c224d0f2a225b4e876e7b8945636fc3223f61b7d1df24` |
| `index_price_klines:BTCUSDT` | 56640 | 9 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `287c0661f8cc5fbc27460b56bcd3f49730b1cb71e665618b73aa350c20e7e461` |
| `premium_index_klines:BTCUSDT` | 56759 | 6 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `a8acd9fb2a5784623e82de0c0a1935bc485ee060b92a83cfa09d515b41d2abfd` |
| `spot_klines:ETHUSDT` | 60036 | 17 | 1 | 12228 | 7 | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2021-05,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` | `242234b280fbc2f1a67d57e82a35724a85091d59f428491629ab2d18c38142d7` | `b3080c40101fd4de1f5f08b1c21d546abfb0d1c9e48d6ad6e5c3547a0b0045f3` |
| `um_futures_klines:ETHUSDT` | 56952 | 0 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `a8062b511cc9573105a92176f59ae82a8b5ebe40b6f6259850ac4d01e593e753` |
| `mark_price_klines:ETHUSDT` | 56880 | 3 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `7af9e4e365444b388a152405b47b85fcec848269e2bd8c3a05fdd35d0c36c7e0` |
| `index_price_klines:ETHUSDT` | 56856 | 4 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `7c1f0f066a28f77b3c1cdb4c17bb32ce4a3c030776c9744fa4016050bdc546b4` |
| `premium_index_klines:ETHUSDT` | 56759 | 6 | not_available_rest_failed | not_available_rest_failed | not_available_rest_failed | `not_run` | `not_available_rest_failed` | `6a81538dd4e295915ffb9851ab5a1007043c110d88bad9cdf4664ed611bbe7b3` |

## Funding Interval Evidence

Each historical settlement retains its inferred interval; no fixed global cadence is substituted.

| Symbol | Funding events with interval | Interval distribution | Warnings |
|---|---:|---|---|
| `BTCUSDT` | 7119 | `8h=7119` | none |
| `ETHUSDT` | 7119 | `8h=7119` | none |

## Required Checks

| Check | Status | Detail |
|---|---|---|
| `spot_klines:BTCUSDT / 1h interval` | pass | `1h` |
| `spot_klines:BTCUSDT / rows present` | pass | `60036` |
| `spot_klines:BTCUSDT / gaps dual-source confirmed` | blocked | `17` |
| `spot_klines:BTCUSDT / ZIP/REST fields equal` | blocked | `6` |
| `spot_klines:BTCUSDT / ZIP/REST timestamp sets equal` | blocked | `1` |
| `spot_klines:BTCUSDT / ZIP/REST overlap present` | pass | `11484` |
| `spot_klines:BTCUSDT / REST payload hash` | pass | `c910882db65d0840470104c126e3b7f8142adaedbb4ce41a864b71c008643b77` |
| `spot_klines:BTCUSDT / ZIP payload hash` | pass | `c21d7dd650f320ef8372e3274f1b62d444c929ff53f3f61c9b9d90ab7ebd4c07` |
| `spot_klines:BTCUSDT / scope first` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:BTCUSDT / scope middle` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:BTCUSDT / scope latest_complete` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:BTCUSDT / anomaly months audited` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `um_futures_klines:BTCUSDT / 1h interval` | pass | `1h` |
| `um_futures_klines:BTCUSDT / rows present` | pass | `56952` |
| `um_futures_klines:BTCUSDT / gaps dual-source confirmed` | pass | `0` |
| `um_futures_klines:BTCUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `um_futures_klines:BTCUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `um_futures_klines:BTCUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `um_futures_klines:BTCUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `um_futures_klines:BTCUSDT / ZIP payload hash` | pass | `9a4d50f25b326a15b656f9a913334b7251688bf375419a50ddc7bb200631f132` |
| `um_futures_klines:BTCUSDT / scope first` | blocked | `not_run` |
| `um_futures_klines:BTCUSDT / scope middle` | blocked | `not_run` |
| `um_futures_klines:BTCUSDT / scope latest_complete` | blocked | `not_run` |
| `um_futures_klines:BTCUSDT / anomaly months audited` | blocked | `not_run` |
| `mark_price_klines:BTCUSDT / 1h interval` | pass | `1h` |
| `mark_price_klines:BTCUSDT / rows present` | pass | `56736` |
| `mark_price_klines:BTCUSDT / gaps dual-source confirmed` | blocked | `6` |
| `mark_price_klines:BTCUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `mark_price_klines:BTCUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `mark_price_klines:BTCUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `mark_price_klines:BTCUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `mark_price_klines:BTCUSDT / ZIP payload hash` | pass | `77165404cbf17ee6a15c224d0f2a225b4e876e7b8945636fc3223f61b7d1df24` |
| `mark_price_klines:BTCUSDT / scope first` | blocked | `not_run` |
| `mark_price_klines:BTCUSDT / scope middle` | blocked | `not_run` |
| `mark_price_klines:BTCUSDT / scope latest_complete` | blocked | `not_run` |
| `mark_price_klines:BTCUSDT / anomaly months audited` | blocked | `not_run` |
| `index_price_klines:BTCUSDT / 1h interval` | pass | `1h` |
| `index_price_klines:BTCUSDT / rows present` | pass | `56640` |
| `index_price_klines:BTCUSDT / gaps dual-source confirmed` | blocked | `9` |
| `index_price_klines:BTCUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `index_price_klines:BTCUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `index_price_klines:BTCUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `index_price_klines:BTCUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `index_price_klines:BTCUSDT / ZIP payload hash` | pass | `287c0661f8cc5fbc27460b56bcd3f49730b1cb71e665618b73aa350c20e7e461` |
| `index_price_klines:BTCUSDT / scope first` | blocked | `not_run` |
| `index_price_klines:BTCUSDT / scope middle` | blocked | `not_run` |
| `index_price_klines:BTCUSDT / scope latest_complete` | blocked | `not_run` |
| `index_price_klines:BTCUSDT / anomaly months audited` | blocked | `not_run` |
| `premium_index_klines:BTCUSDT / 1h interval` | pass | `1h` |
| `premium_index_klines:BTCUSDT / rows present` | pass | `56759` |
| `premium_index_klines:BTCUSDT / gaps dual-source confirmed` | blocked | `6` |
| `premium_index_klines:BTCUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `premium_index_klines:BTCUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `premium_index_klines:BTCUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `premium_index_klines:BTCUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `premium_index_klines:BTCUSDT / ZIP payload hash` | pass | `a8acd9fb2a5784623e82de0c0a1935bc485ee060b92a83cfa09d515b41d2abfd` |
| `premium_index_klines:BTCUSDT / scope first` | blocked | `not_run` |
| `premium_index_klines:BTCUSDT / scope middle` | blocked | `not_run` |
| `premium_index_klines:BTCUSDT / scope latest_complete` | blocked | `not_run` |
| `funding_rate_history:BTCUSDT` | pass | `rows=7119; interval=funding_period` |
| `funding interval events:BTCUSDT` | pass | `8h=7119` |
| `spot_klines:ETHUSDT / 1h interval` | pass | `1h` |
| `spot_klines:ETHUSDT / rows present` | pass | `60036` |
| `spot_klines:ETHUSDT / gaps dual-source confirmed` | blocked | `17` |
| `spot_klines:ETHUSDT / ZIP/REST fields equal` | blocked | `7` |
| `spot_klines:ETHUSDT / ZIP/REST timestamp sets equal` | blocked | `1` |
| `spot_klines:ETHUSDT / ZIP/REST overlap present` | pass | `12228` |
| `spot_klines:ETHUSDT / REST payload hash` | pass | `242234b280fbc2f1a67d57e82a35724a85091d59f428491629ab2d18c38142d7` |
| `spot_klines:ETHUSDT / ZIP payload hash` | pass | `b3080c40101fd4de1f5f08b1c21d546abfb0d1c9e48d6ad6e5c3547a0b0045f3` |
| `spot_klines:ETHUSDT / scope first` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2021-05,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:ETHUSDT / scope middle` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2021-05,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:ETHUSDT / scope latest_complete` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2021-05,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `spot_klines:ETHUSDT / anomaly months audited` | pass | `first=2019-09;middle=2023-02;latest_complete=2026-06;anomaly=2020-03,2021-02,2021-05,2023-03;gap=2019-11,2020-02,2020-03,2020-04,2020-06,2020-11,2020-12,2021-02,2021-03,2021-04,2021-08,2021-09,2023-03` |
| `um_futures_klines:ETHUSDT / 1h interval` | pass | `1h` |
| `um_futures_klines:ETHUSDT / rows present` | pass | `56952` |
| `um_futures_klines:ETHUSDT / gaps dual-source confirmed` | pass | `0` |
| `um_futures_klines:ETHUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `um_futures_klines:ETHUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `um_futures_klines:ETHUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `um_futures_klines:ETHUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `um_futures_klines:ETHUSDT / ZIP payload hash` | pass | `a8062b511cc9573105a92176f59ae82a8b5ebe40b6f6259850ac4d01e593e753` |
| `um_futures_klines:ETHUSDT / scope first` | blocked | `not_run` |
| `um_futures_klines:ETHUSDT / scope middle` | blocked | `not_run` |
| `um_futures_klines:ETHUSDT / scope latest_complete` | blocked | `not_run` |
| `um_futures_klines:ETHUSDT / anomaly months audited` | blocked | `not_run` |
| `mark_price_klines:ETHUSDT / 1h interval` | pass | `1h` |
| `mark_price_klines:ETHUSDT / rows present` | pass | `56880` |
| `mark_price_klines:ETHUSDT / gaps dual-source confirmed` | blocked | `3` |
| `mark_price_klines:ETHUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `mark_price_klines:ETHUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `mark_price_klines:ETHUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `mark_price_klines:ETHUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `mark_price_klines:ETHUSDT / ZIP payload hash` | pass | `7af9e4e365444b388a152405b47b85fcec848269e2bd8c3a05fdd35d0c36c7e0` |
| `mark_price_klines:ETHUSDT / scope first` | blocked | `not_run` |
| `mark_price_klines:ETHUSDT / scope middle` | blocked | `not_run` |
| `mark_price_klines:ETHUSDT / scope latest_complete` | blocked | `not_run` |
| `mark_price_klines:ETHUSDT / anomaly months audited` | blocked | `not_run` |
| `index_price_klines:ETHUSDT / 1h interval` | pass | `1h` |
| `index_price_klines:ETHUSDT / rows present` | pass | `56856` |
| `index_price_klines:ETHUSDT / gaps dual-source confirmed` | blocked | `4` |
| `index_price_klines:ETHUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `index_price_klines:ETHUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `index_price_klines:ETHUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `index_price_klines:ETHUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `index_price_klines:ETHUSDT / ZIP payload hash` | pass | `7c1f0f066a28f77b3c1cdb4c17bb32ce4a3c030776c9744fa4016050bdc546b4` |
| `index_price_klines:ETHUSDT / scope first` | blocked | `not_run` |
| `index_price_klines:ETHUSDT / scope middle` | blocked | `not_run` |
| `index_price_klines:ETHUSDT / scope latest_complete` | blocked | `not_run` |
| `index_price_klines:ETHUSDT / anomaly months audited` | blocked | `not_run` |
| `premium_index_klines:ETHUSDT / 1h interval` | pass | `1h` |
| `premium_index_klines:ETHUSDT / rows present` | pass | `56759` |
| `premium_index_klines:ETHUSDT / gaps dual-source confirmed` | blocked | `6` |
| `premium_index_klines:ETHUSDT / ZIP/REST fields equal` | blocked | `not_available_rest_failed` |
| `premium_index_klines:ETHUSDT / ZIP/REST timestamp sets equal` | blocked | `not_available_rest_failed` |
| `premium_index_klines:ETHUSDT / ZIP/REST overlap present` | blocked | `not_available_rest_failed` |
| `premium_index_klines:ETHUSDT / REST payload hash` | blocked | `not_available_rest_failed` |
| `premium_index_klines:ETHUSDT / ZIP payload hash` | pass | `6a81538dd4e295915ffb9851ab5a1007043c110d88bad9cdf4664ed611bbe7b3` |
| `premium_index_klines:ETHUSDT / scope first` | blocked | `not_run` |
| `premium_index_klines:ETHUSDT / scope middle` | blocked | `not_run` |
| `premium_index_klines:ETHUSDT / scope latest_complete` | blocked | `not_run` |
| `funding_rate_history:ETHUSDT` | pass | `rows=7119; interval=funding_period` |
| `funding interval events:ETHUSDT` | pass | `8h=7119` |

## Blockers

- spot_klines:BTCUSDT / gaps dual-source confirmed
- spot_klines:BTCUSDT / ZIP/REST fields equal
- spot_klines:BTCUSDT / ZIP/REST timestamp sets equal
- um_futures_klines:BTCUSDT / ZIP/REST fields equal
- um_futures_klines:BTCUSDT / ZIP/REST timestamp sets equal
- um_futures_klines:BTCUSDT / ZIP/REST overlap present
- um_futures_klines:BTCUSDT / REST payload hash
- um_futures_klines:BTCUSDT / scope first
- um_futures_klines:BTCUSDT / scope middle
- um_futures_klines:BTCUSDT / scope latest_complete
- um_futures_klines:BTCUSDT / anomaly months audited
- mark_price_klines:BTCUSDT / gaps dual-source confirmed
- mark_price_klines:BTCUSDT / ZIP/REST fields equal
- mark_price_klines:BTCUSDT / ZIP/REST timestamp sets equal
- mark_price_klines:BTCUSDT / ZIP/REST overlap present
- mark_price_klines:BTCUSDT / REST payload hash
- mark_price_klines:BTCUSDT / scope first
- mark_price_klines:BTCUSDT / scope middle
- mark_price_klines:BTCUSDT / scope latest_complete
- mark_price_klines:BTCUSDT / anomaly months audited
- index_price_klines:BTCUSDT / gaps dual-source confirmed
- index_price_klines:BTCUSDT / ZIP/REST fields equal
- index_price_klines:BTCUSDT / ZIP/REST timestamp sets equal
- index_price_klines:BTCUSDT / ZIP/REST overlap present
- index_price_klines:BTCUSDT / REST payload hash
- index_price_klines:BTCUSDT / scope first
- index_price_klines:BTCUSDT / scope middle
- index_price_klines:BTCUSDT / scope latest_complete
- index_price_klines:BTCUSDT / anomaly months audited
- premium_index_klines:BTCUSDT / gaps dual-source confirmed
- premium_index_klines:BTCUSDT / ZIP/REST fields equal
- premium_index_klines:BTCUSDT / ZIP/REST timestamp sets equal
- premium_index_klines:BTCUSDT / ZIP/REST overlap present
- premium_index_klines:BTCUSDT / REST payload hash
- premium_index_klines:BTCUSDT / scope first
- premium_index_klines:BTCUSDT / scope middle
- premium_index_klines:BTCUSDT / scope latest_complete
- spot_klines:ETHUSDT / gaps dual-source confirmed
- spot_klines:ETHUSDT / ZIP/REST fields equal
- spot_klines:ETHUSDT / ZIP/REST timestamp sets equal
- um_futures_klines:ETHUSDT / ZIP/REST fields equal
- um_futures_klines:ETHUSDT / ZIP/REST timestamp sets equal
- um_futures_klines:ETHUSDT / ZIP/REST overlap present
- um_futures_klines:ETHUSDT / REST payload hash
- um_futures_klines:ETHUSDT / scope first
- um_futures_klines:ETHUSDT / scope middle
- um_futures_klines:ETHUSDT / scope latest_complete
- um_futures_klines:ETHUSDT / anomaly months audited
- mark_price_klines:ETHUSDT / gaps dual-source confirmed
- mark_price_klines:ETHUSDT / ZIP/REST fields equal
- mark_price_klines:ETHUSDT / ZIP/REST timestamp sets equal
- mark_price_klines:ETHUSDT / ZIP/REST overlap present
- mark_price_klines:ETHUSDT / REST payload hash
- mark_price_klines:ETHUSDT / scope first
- mark_price_klines:ETHUSDT / scope middle
- mark_price_klines:ETHUSDT / scope latest_complete
- mark_price_klines:ETHUSDT / anomaly months audited
- index_price_klines:ETHUSDT / gaps dual-source confirmed
- index_price_klines:ETHUSDT / ZIP/REST fields equal
- index_price_klines:ETHUSDT / ZIP/REST timestamp sets equal
- index_price_klines:ETHUSDT / ZIP/REST overlap present
- index_price_klines:ETHUSDT / REST payload hash
- index_price_klines:ETHUSDT / scope first
- index_price_klines:ETHUSDT / scope middle
- index_price_klines:ETHUSDT / scope latest_complete
- index_price_klines:ETHUSDT / anomaly months audited
- premium_index_klines:ETHUSDT / gaps dual-source confirmed
- premium_index_klines:ETHUSDT / ZIP/REST fields equal
- premium_index_klines:ETHUSDT / ZIP/REST timestamp sets equal
- premium_index_klines:ETHUSDT / ZIP/REST overlap present
- premium_index_klines:ETHUSDT / REST payload hash
- premium_index_klines:ETHUSDT / scope first
- premium_index_klines:ETHUSDT / scope middle
- premium_index_klines:ETHUSDT / scope latest_complete

## Decision

- M0 audit status: audit_revalidation_required
- This report does not approve M2, paper trading, live trading, order placement, or API trading permissions.
