# T1 Canonical Public Minute Data Report

- Status: pass
- Scope: public BTC/ETH spot 1m archive and liquidity qualification only
- API key used: no
- Private data used: no
- Strategy returns computed: no
- Raw data committed: no
- Requested range: 2017-08-01T00:00:00+00:00 through 2026-06-30T23:59:59.999000+00:00
- Research start: 2023-10-01
- Manifest SHA256: `028dff16ed73f0148d578334ce936aaec89ff0bf7fc8a1fb2ee6bbcfcd8061ee`

## Method

Monthly official ZIP is the base. Official daily ZIP may add only missing timestamps. Deterministic REST windows are comparison evidence and never overwrite ZIP rows.
Liquidity proxy is the p95 two-bar Corwin-Schultz estimate using only 1m high/low inputs; the fixed threshold is 0.10%.

## Summary

| Symbol | Months | Complete | Qualified | Missing rows | Invalid rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | 107 | 82 | 58 | 8610 | 21602 |
| ETHUSDT | 107 | 82 | 37 | 8611 | 21602 |

## Actual Data Range

| Symbol | First 1m open UTC | Last 1m open UTC |
| --- | --- | --- |
| BTCUSDT | 2017-08-17T04:00:00+00:00 | 2026-06-30T23:59:00+00:00 |
| ETHUSDT | 2017-08-17T04:00:00+00:00 | 2026-06-30T23:59:00+00:00 |

## REST Samples

| Month | Reason | Overlap | Field differences | Status | Archive hash | REST hash |
| --- | --- | ---: | ---: | --- | --- | --- |
| 2017-08 | first | 1000 | 0 | pass | `9bc99e2dff12a3f2fced24de6e5636d1c6407d5ea6f76a39b0c81d82742ca828` | `9bc99e2dff12a3f2fced24de6e5636d1c6407d5ea6f76a39b0c81d82742ca828` |
| 2020-03 | stress | 1000 | 0 | pass | `4c835795ef8d75246ba20345292a22dd625be88add533e52288d3cd0614bfff1` | `4c835795ef8d75246ba20345292a22dd625be88add533e52288d3cd0614bfff1` |
| 2020-05 | deterministic_random | 1000 | 0 | pass | `5c0e84aa568fb0b062ff87eec7399b8b1f1555a8eb5c3d1468935679cac1ebdc` | `5c0e84aa568fb0b062ff87eec7399b8b1f1555a8eb5c3d1468935679cac1ebdc` |
| 2021-05 | stress | 1000 | 0 | pass | `8a30ae4afc042b21bfadfa43a9f5564ad042d95e01a9e768a1e1cfd86e277b4a` | `8a30ae4afc042b21bfadfa43a9f5564ad042d95e01a9e768a1e1cfd86e277b4a` |
| 2021-09 | deterministic_random | 1000 | 0 | pass | `9a52edf0f51511293c29a071edf5178f70e6f59cd9fb1691acd4585b23cb6e2e` | `9a52edf0f51511293c29a071edf5178f70e6f59cd9fb1691acd4585b23cb6e2e` |
| 2021-12 | deterministic_random | 1000 | 0 | pass | `33e2940be7ad3dceee8875efa2182917b332355341be3d825f13ce27781bd93f` | `33e2940be7ad3dceee8875efa2182917b332355341be3d825f13ce27781bd93f` |
| 2022-01 | middle | 1000 | 0 | pass | `2ebcf575c8c50e9005b667c01a59b1796142c5959b7e135d3092eb00a25ff63d` | `2ebcf575c8c50e9005b667c01a59b1796142c5959b7e135d3092eb00a25ff63d` |
| 2022-05 | stress | 1000 | 0 | pass | `2027cde405bbaec0cd32c94f850430e4190e24e16c213cae5f847b2d2c5cd957` | `2027cde405bbaec0cd32c94f850430e4190e24e16c213cae5f847b2d2c5cd957` |
| 2022-11 | stress | 1000 | 0 | pass | `f50c11b87808ab725facccdb74d4b118551dc427a13c68ea7550237eea3aaf15` | `f50c11b87808ab725facccdb74d4b118551dc427a13c68ea7550237eea3aaf15` |
| 2026-06 | latest_complete | 1000 | 0 | pass | `68740ac8bccb52adf20dcdfb76cca8b2cae8dea9ff0940f77b127f86f7394afd` | `68740ac8bccb52adf20dcdfb76cca8b2cae8dea9ff0940f77b127f86f7394afd` |
| 2017-08 | first | 1000 | 0 | pass | `d3f019afc579d7574400ce631c274c3534ce635d8509647395aa3beaf8b87e1a` | `d3f019afc579d7574400ce631c274c3534ce635d8509647395aa3beaf8b87e1a` |
| 2018-01 | deterministic_random | 1000 | 0 | pass | `ae0fd49ef559c49f3c41d9bf26b8bccc8763da7ce3c09a9aff8b2dae4b849aec` | `ae0fd49ef559c49f3c41d9bf26b8bccc8763da7ce3c09a9aff8b2dae4b849aec` |
| 2020-03 | stress | 1000 | 0 | pass | `103216ba2a608ef5a7821c7043443ab8beebb55ed42e5414bfe961d9984ca1c0` | `103216ba2a608ef5a7821c7043443ab8beebb55ed42e5414bfe961d9984ca1c0` |
| 2020-09 | deterministic_random | 1000 | 0 | pass | `4c781c40841cef0cf15dfc2d75cfe9cc59af0aa994b0fc7a3164fbbdcfac9a24` | `4c781c40841cef0cf15dfc2d75cfe9cc59af0aa994b0fc7a3164fbbdcfac9a24` |
| 2021-05 | stress | 1000 | 0 | pass | `4a94be850bcbe7f769e52c2a3efea55e149c3d889529d47a8bc27e782fc4c23e` | `4a94be850bcbe7f769e52c2a3efea55e149c3d889529d47a8bc27e782fc4c23e` |
| 2022-01 | middle | 1000 | 0 | pass | `19664cd89ac43aa82a5e139cc1e61fd0f53609246397596a11177880af936c92` | `19664cd89ac43aa82a5e139cc1e61fd0f53609246397596a11177880af936c92` |
| 2022-05 | stress | 1000 | 0 | pass | `bf9083d06e0d3199a10cf11ab779fd1eadcaefb2f30cff552fae2e2458ae38d6` | `bf9083d06e0d3199a10cf11ab779fd1eadcaefb2f30cff552fae2e2458ae38d6` |
| 2022-11 | stress | 1000 | 0 | pass | `ee834bc01d435fa12baae1c05d31ad45e1dfb83c27b289f67b6d67390a86cfa7` | `ee834bc01d435fa12baae1c05d31ad45e1dfb83c27b289f67b6d67390a86cfa7` |
| 2023-01 | deterministic_random | 1000 | 0 | pass | `12df19ec4ee84ddd85f17dc5ee5c83ad155798b32c81b4d518cc87159e5896df` | `12df19ec4ee84ddd85f17dc5ee5c83ad155798b32c81b4d518cc87159e5896df` |
| 2026-06 | latest_complete | 1000 | 0 | pass | `438c10c730e3dc4a1bde2685024d8a411830c1e6371c4ab3b776d31410f27e7f` | `438c10c730e3dc4a1bde2685024d8a411830c1e6371c4ab3b776d31410f27e7f` |

## Quarantined or Blocking Months

| Dataset | Month | State | Research relevance | Missing | Max gap | Invalid | Daily failures | Completeness | p95 spread |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | 2017-09 | blocked | pre-start quarantine | 419 | 419 | 0 | 0 | 0.9903009259 | 0.0023673237 |
| BTCUSDT | 2017-12 | blocked | pre-start quarantine | 125 | 64 | 20401 | 0 | 0.9971998208 | 0.0043336547 |
| BTCUSDT | 2018-01 | blocked | pre-start quarantine | 125 | 125 | 0 | 0 | 0.9971998208 | 0.0038340314 |
| BTCUSDT | 2018-02 | blocked | pre-start quarantine | 2060 | 2011 | 1201 | 0 | 0.9489087302 | 0.0034565141 |
| BTCUSDT | 2018-06 | blocked | pre-start quarantine | 705 | 600 | 0 | 0 | 0.9836805556 | 0.0012624147 |
| BTCUSDT | 2018-07 | blocked | pre-start quarantine | 457 | 457 | 0 | 0 | 0.9897625448 | 0.0010072550 |
| BTCUSDT | 2018-10 | blocked | pre-start quarantine | 210 | 210 | 0 | 0 | 0.9952956989 | 0.0006662688 |
| BTCUSDT | 2018-11 | blocked | pre-start quarantine | 420 | 420 | 0 | 0 | 0.9902777778 | 0.0017250842 |
| BTCUSDT | 2019-03 | blocked | pre-start quarantine | 360 | 360 | 0 | 0 | 0.9919354839 | 0.0005887185 |
| BTCUSDT | 2019-05 | blocked | pre-start quarantine | 600 | 600 | 0 | 0 | 0.9865591398 | 0.0015811390 |
| BTCUSDT | 2019-06 | blocked | pre-start quarantine | 61 | 61 | 0 | 0 | 0.9985879630 | 0.0015879134 |
| BTCUSDT | 2019-08 | blocked | pre-start quarantine | 480 | 480 | 0 | 0 | 0.9892473118 | 0.0011298082 |
| BTCUSDT | 2019-11 | blocked | pre-start quarantine | 263 | 140 | 0 | 0 | 0.9939120370 | 0.0010327640 |
| BTCUSDT | 2020-02 | blocked | pre-start quarantine | 414 | 354 | 0 | 0 | 0.9900862069 | 0.0009209202 |
| BTCUSDT | 2020-03 | blocked | pre-start quarantine | 128 | 128 | 0 | 0 | 0.9971326165 | 0.0024636635 |
| BTCUSDT | 2020-04 | blocked | pre-start quarantine | 150 | 150 | 0 | 0 | 0.9965277778 | 0.0011375199 |
| BTCUSDT | 2020-06 | blocked | pre-start quarantine | 210 | 210 | 0 | 0 | 0.9951388889 | 0.0006364637 |
| BTCUSDT | 2020-11 | blocked | pre-start quarantine | 60 | 60 | 0 | 0 | 0.9986111111 | 0.0011881959 |
| BTCUSDT | 2020-12 | blocked | pre-start quarantine | 290 | 230 | 0 | 0 | 0.9935035842 | 0.0012601510 |
| BTCUSDT | 2021-02 | blocked | pre-start quarantine | 79 | 79 | 0 | 0 | 0.9980406746 | 0.0018679448 |
| BTCUSDT | 2021-03 | blocked | pre-start quarantine | 90 | 90 | 0 | 0 | 0.9979838710 | 0.0014345928 |
| BTCUSDT | 2021-04 | blocked | pre-start quarantine | 434 | 284 | 0 | 0 | 0.9899537037 | 0.0012228812 |
| BTCUSDT | 2021-08 | blocked | pre-start quarantine | 270 | 270 | 0 | 0 | 0.9939516129 | 0.0010741250 |
| BTCUSDT | 2021-09 | blocked | pre-start quarantine | 120 | 120 | 0 | 0 | 0.9972222222 | 0.0011296929 |
| BTCUSDT | 2023-03 | blocked | pre-start quarantine | 80 | 80 | 0 | 0 | 0.9982078853 | 0.0010518714 |
| ETHUSDT | 2017-09 | blocked | pre-start quarantine | 419 | 419 | 0 | 0 | 0.9903009259 | 0.0022688030 |
| ETHUSDT | 2017-12 | blocked | pre-start quarantine | 125 | 64 | 20401 | 0 | 0.9971998208 | 0.0053552433 |
| ETHUSDT | 2018-01 | blocked | pre-start quarantine | 125 | 125 | 0 | 0 | 0.9971998208 | 0.0040330666 |
| ETHUSDT | 2018-02 | blocked | pre-start quarantine | 2060 | 2011 | 1201 | 0 | 0.9489087302 | 0.0035426748 |
| ETHUSDT | 2018-06 | blocked | pre-start quarantine | 705 | 600 | 0 | 0 | 0.9836805556 | 0.0016339489 |
| ETHUSDT | 2018-07 | blocked | pre-start quarantine | 457 | 457 | 0 | 0 | 0.9897625448 | 0.0012500604 |
| ETHUSDT | 2018-10 | blocked | pre-start quarantine | 210 | 210 | 0 | 0 | 0.9952956989 | 0.0009391121 |
| ETHUSDT | 2018-11 | blocked | pre-start quarantine | 420 | 420 | 0 | 0 | 0.9902777778 | 0.0020842057 |
| ETHUSDT | 2019-03 | blocked | pre-start quarantine | 360 | 360 | 0 | 0 | 0.9919354839 | 0.0008486407 |
| ETHUSDT | 2019-05 | blocked | pre-start quarantine | 600 | 600 | 0 | 0 | 0.9865591398 | 0.0019134677 |
| ETHUSDT | 2019-06 | blocked | pre-start quarantine | 61 | 61 | 0 | 0 | 0.9985879630 | 0.0015510545 |
| ETHUSDT | 2019-08 | blocked | pre-start quarantine | 480 | 480 | 0 | 0 | 0.9892473118 | 0.0010242203 |
| ETHUSDT | 2019-11 | blocked | pre-start quarantine | 263 | 140 | 0 | 0 | 0.9939120370 | 0.0009918587 |
| ETHUSDT | 2020-02 | blocked | pre-start quarantine | 414 | 354 | 0 | 0 | 0.9900862069 | 0.0015904972 |
| ETHUSDT | 2020-03 | blocked | pre-start quarantine | 128 | 128 | 0 | 0 | 0.9971326165 | 0.0026164759 |
| ETHUSDT | 2020-04 | blocked | pre-start quarantine | 150 | 150 | 0 | 0 | 0.9965277778 | 0.0013136147 |
| ETHUSDT | 2020-06 | blocked | pre-start quarantine | 210 | 210 | 0 | 0 | 0.9951388889 | 0.0007280802 |
| ETHUSDT | 2020-11 | blocked | pre-start quarantine | 60 | 60 | 0 | 0 | 0.9986111111 | 0.0015018092 |
| ETHUSDT | 2020-12 | blocked | pre-start quarantine | 291 | 231 | 0 | 0 | 0.9934811828 | 0.0014632282 |
| ETHUSDT | 2021-02 | blocked | pre-start quarantine | 79 | 79 | 0 | 0 | 0.9980406746 | 0.0021968066 |
| ETHUSDT | 2021-03 | blocked | pre-start quarantine | 90 | 90 | 0 | 0 | 0.9979838710 | 0.0015603279 |
| ETHUSDT | 2021-04 | blocked | pre-start quarantine | 434 | 284 | 0 | 0 | 0.9899537037 | 0.0017902272 |
| ETHUSDT | 2021-08 | blocked | pre-start quarantine | 270 | 270 | 0 | 0 | 0.9939516129 | 0.0013637252 |
| ETHUSDT | 2021-09 | blocked | pre-start quarantine | 120 | 120 | 0 | 0 | 0.9972222222 | 0.0016092260 |
| ETHUSDT | 2023-03 | blocked | pre-start quarantine | 80 | 80 | 0 | 0 | 0.9982078853 | 0.0009198859 |

## Gate

- Exact public range recorded: pass
- REST sampling plan completed: pass
- Historical source anomalies registered: pass
- Zero unexplained relevant gaps: pass
- Liquidity-qualified start frozen: pass
- T2 authorized: yes
- M1D strategy code authorized: no
- M2 authorized: no
