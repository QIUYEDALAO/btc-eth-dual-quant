# M0 Audit Revalidation Report

- Status: blocked
- Generated UTC: 2026-07-09T21:59:14+00:00
- Scope: BTCUSDT/ETHUSDT 1h official public REST versus official public ZIP
- Evidence method: multi-network, exact Decimal and timestamp-set comparison
- API key used: no
- Private smoke rerun: no
- Raw data committed: no
- Trading approval: no

## Evidence Summary

| Dataset | Symbol | Planned scopes | Scopes with valid evidence | Revisions | Timestamp mismatches | Invalid OHLCV | Network blocked | ZIP unavailable | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `index_price_klines` | `BTCUSDT` | 9 | 0 | 0 | 0 | 0 | 18 | 0 | blocked |
| `index_price_klines` | `ETHUSDT` | 9 | 0 | 0 | 0 | 0 | 18 | 0 | blocked |
| `mark_price_klines` | `BTCUSDT` | 10 | 0 | 0 | 0 | 0 | 20 | 0 | blocked |
| `mark_price_klines` | `ETHUSDT` | 7 | 0 | 0 | 0 | 0 | 14 | 0 | blocked |
| `premium_index_klines` | `BTCUSDT` | 8 | 0 | 0 | 0 | 0 | 16 | 0 | blocked |
| `premium_index_klines` | `ETHUSDT` | 7 | 0 | 0 | 0 | 0 | 14 | 0 | blocked |
| `spot_klines` | `BTCUSDT` | 16 | 14 | 14 | 1 | 0 | 0 | 0 | blocked |
| `spot_klines` | `ETHUSDT` | 17 | 15 | 14 | 1 | 0 | 0 | 0 | blocked |
| `um_futures_klines` | `BTCUSDT` | 6 | 0 | 0 | 0 | 0 | 12 | 0 | blocked |
| `um_futures_klines` | `ETHUSDT` | 6 | 0 | 0 | 0 | 0 | 12 | 0 | blocked |

## Blocking Evidence

| Node | Dataset | Symbol | Month | Classification | Open time UTC | Field | ZIP value | REST value | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `high` | `22665.35000000` | `22774.00000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close` | `22646.53000000` | `22681.32000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `volume` | `2830.34558700` | `3685.45440500` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close_time` | `1608559199999` | `1608558440521` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `quote_volume` | `63790349.91077578` | `83180713.81558070` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `trade_count` | `44795` | `62654` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_base_volume` | `1428.55237100` | `1815.00048700` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_quote_volume` | `32189044.97410345` | `40955894.79935769` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | `timestamp_mismatch` | `2020-12-21T14:00:00+00:00` | `open_time` | `1608559200000` | `` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `51080.59000000` | `51048.59000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `11667.63216200` | `11815.24808200` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `593144862.93087132` | `600681216.08495300` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `276379` | `279380` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `5428.08513400` | `5505.78496500` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `276430919.50983045` | `280397730.73104759` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `high` | `608.82000000` | `613.29000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close` | `608.31000000` | `610.45000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `volume` | `26146.58875000` | `34927.37209000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close_time` | `1608559199999` | `1608558440528` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `quote_volume` | `15866207.11148880` | `21219132.19507340` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `trade_count` | `14393` | `19857` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_base_volume` | `14284.12764000` | `19843.88555000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_quote_volume` | `8669079.80611710` | `12059602.91269320` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `timestamp_mismatch` | `2020-12-21T14:00:00+00:00` | `open_time` | `1608559200000` | `` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `2325.82000000` | `2321.44000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `187368.61418000` | `188766.41365000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `436821371.55040100` | `440066845.48382460` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `181462` | `182900` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `84489.57317000` | `85129.16935000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `196993734.15928340` | `198479364.97862700` | official sources contain different canonical values |

## Source Availability Blockers

| Node | Dataset | Symbol | Error category | Affected scopes |
| --- | --- | --- | --- | ---: |
| `local` | `index_price_klines` | `BTCUSDT` | `timeout` | 9 |
| `local` | `index_price_klines` | `ETHUSDT` | `timeout` | 9 |
| `local` | `mark_price_klines` | `BTCUSDT` | `timeout` | 10 |
| `local` | `mark_price_klines` | `ETHUSDT` | `timeout` | 7 |
| `local` | `premium_index_klines` | `BTCUSDT` | `timeout` | 8 |
| `local` | `premium_index_klines` | `ETHUSDT` | `timeout` | 7 |
| `local` | `um_futures_klines` | `BTCUSDT` | `timeout` | 6 |
| `local` | `um_futures_klines` | `ETHUSDT` | `timeout` | 6 |
| `remote` | `index_price_klines` | `BTCUSDT` | `url_error_oserror` | 9 |
| `remote` | `index_price_klines` | `ETHUSDT` | `url_error_oserror` | 9 |
| `remote` | `mark_price_klines` | `BTCUSDT` | `url_error_oserror` | 10 |
| `remote` | `mark_price_klines` | `ETHUSDT` | `url_error_oserror` | 7 |
| `remote` | `premium_index_klines` | `BTCUSDT` | `url_error_oserror` | 8 |
| `remote` | `premium_index_klines` | `ETHUSDT` | `url_error_oserror` | 7 |
| `remote` | `um_futures_klines` | `BTCUSDT` | `url_error_oserror` | 6 |
| `remote` | `um_futures_klines` | `ETHUSDT` | `url_error_oserror` | 6 |

## Required Gate

- Status: blocked
- Blockers:
  - index_price_klines:BTCUSDT:1h:2020-01: network_blocked
  - index_price_klines:BTCUSDT:1h:2020-03: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-04: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-07: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-08: network_blocked
  - index_price_klines:BTCUSDT:1h:2022-10: network_blocked
  - index_price_klines:BTCUSDT:1h:2023-02: network_blocked
  - index_price_klines:BTCUSDT:1h:2023-04: network_blocked
  - index_price_klines:BTCUSDT:1h:2026-06: network_blocked
  - index_price_klines:ETHUSDT:1h:2020-01: network_blocked
  - index_price_klines:ETHUSDT:1h:2020-03: network_blocked
  - index_price_klines:ETHUSDT:1h:2021-05: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-07: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-08: network_blocked
  - index_price_klines:ETHUSDT:1h:2022-10: network_blocked
  - index_price_klines:ETHUSDT:1h:2023-02: network_blocked
  - index_price_klines:ETHUSDT:1h:2023-04: network_blocked
  - index_price_klines:ETHUSDT:1h:2026-06: network_blocked
  - mark_price_klines:BTCUSDT:1h:2020-01: network_blocked
  - mark_price_klines:BTCUSDT:1h:2020-03: network_blocked
  - mark_price_klines:BTCUSDT:1h:2021-06: network_blocked
  - mark_price_klines:BTCUSDT:1h:2021-07: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-07: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-08: network_blocked
  - mark_price_klines:BTCUSDT:1h:2022-10: network_blocked
  - mark_price_klines:BTCUSDT:1h:2023-02: network_blocked
  - mark_price_klines:BTCUSDT:1h:2023-04: network_blocked
  - mark_price_klines:BTCUSDT:1h:2026-06: network_blocked
  - mark_price_klines:ETHUSDT:1h:2020-01: network_blocked
  - mark_price_klines:ETHUSDT:1h:2020-03: network_blocked
  - mark_price_klines:ETHUSDT:1h:2021-05: network_blocked
  - mark_price_klines:ETHUSDT:1h:2022-10: network_blocked
  - mark_price_klines:ETHUSDT:1h:2023-02: network_blocked
  - mark_price_klines:ETHUSDT:1h:2023-04: network_blocked
  - mark_price_klines:ETHUSDT:1h:2026-06: network_blocked
  - premium_index_klines:BTCUSDT:1h:2020-01: network_blocked
  - premium_index_klines:BTCUSDT:1h:2020-12: network_blocked
  - premium_index_klines:BTCUSDT:1h:2021-06: network_blocked
  - premium_index_klines:BTCUSDT:1h:2021-07: network_blocked
  - premium_index_klines:BTCUSDT:1h:2022-10: network_blocked
  - premium_index_klines:BTCUSDT:1h:2023-02: network_blocked
  - premium_index_klines:BTCUSDT:1h:2023-04: network_blocked
  - premium_index_klines:BTCUSDT:1h:2026-06: network_blocked
  - premium_index_klines:ETHUSDT:1h:2020-01: network_blocked
  - premium_index_klines:ETHUSDT:1h:2020-12: network_blocked
  - premium_index_klines:ETHUSDT:1h:2021-06: network_blocked
  - premium_index_klines:ETHUSDT:1h:2021-07: network_blocked
  - premium_index_klines:ETHUSDT:1h:2022-10: network_blocked
  - premium_index_klines:ETHUSDT:1h:2023-04: network_blocked
  - premium_index_klines:ETHUSDT:1h:2026-06: network_blocked
  - spot_klines:BTCUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:BTCUSDT:1h:2021-04: source_revision
  - spot_klines:ETHUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:ETHUSDT:1h:2021-04: source_revision
  - um_futures_klines:BTCUSDT:1h:2020-01: network_blocked
  - um_futures_klines:BTCUSDT:1h:2020-03: network_blocked
  - um_futures_klines:BTCUSDT:1h:2021-07: network_blocked
  - um_futures_klines:BTCUSDT:1h:2023-04: network_blocked
  - um_futures_klines:BTCUSDT:1h:2024-10: network_blocked
  - um_futures_klines:BTCUSDT:1h:2026-06: network_blocked
  - um_futures_klines:ETHUSDT:1h:2020-01: network_blocked
  - um_futures_klines:ETHUSDT:1h:2020-03: network_blocked
  - um_futures_klines:ETHUSDT:1h:2021-05: network_blocked
  - um_futures_klines:ETHUSDT:1h:2023-04: network_blocked
  - um_futures_klines:ETHUSDT:1h:2024-10: network_blocked
  - um_futures_klines:ETHUSDT:1h:2026-06: network_blocked

## Decision

- M0 audit status: audit_revalidation_required
- Detailed field evidence: `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md`
- M1A and M1B remain failed_validation.
- M2 remains prohibited.
- No live trading, real-API paper trading, execution, order, or API permission is approved.
