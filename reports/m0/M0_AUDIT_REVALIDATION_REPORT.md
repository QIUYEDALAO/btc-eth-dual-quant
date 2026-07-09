# M0 Audit Revalidation Report

- Status: blocked
- Generated UTC: 2026-07-09T22:58:22+00:00
- Scope: BTCUSDT/ETHUSDT 1h official public REST versus official public ZIP
- Evidence method: multi-network, exact Decimal and timestamp-set comparison
- Transport modes: direct,rest_local_https_proxy_zip_direct
- Loopback proxy transport used: yes
- API key used: no
- Private smoke rerun: no
- Raw data committed: no
- Trading approval: no

## Evidence Summary

| Dataset | Symbol | Planned scopes | Scopes with valid evidence | Revisions | Timestamp mismatches | Invalid OHLCV | Network blocked | ZIP unavailable | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `index_price_klines` | `BTCUSDT` | 9 | 8 | 0 | 24 | 0 | 0 | 0 | blocked |
| `index_price_klines` | `ETHUSDT` | 9 | 8 | 0 | 24 | 0 | 0 | 0 | blocked |
| `mark_price_klines` | `BTCUSDT` | 10 | 9 | 0 | 24 | 0 | 0 | 0 | blocked |
| `mark_price_klines` | `ETHUSDT` | 7 | 6 | 0 | 24 | 0 | 0 | 0 | blocked |
| `premium_index_klines` | `BTCUSDT` | 8 | 7 | 0 | 24 | 0 | 0 | 0 | blocked |
| `premium_index_klines` | `ETHUSDT` | 7 | 6 | 0 | 24 | 0 | 0 | 0 | blocked |
| `spot_klines` | `BTCUSDT` | 16 | 14 | 14 | 1 | 0 | 0 | 0 | blocked |
| `spot_klines` | `ETHUSDT` | 17 | 15 | 14 | 1 | 0 | 0 | 0 | blocked |
| `um_futures_klines` | `BTCUSDT` | 6 | 5 | 18 | 0 | 0 | 0 | 0 | blocked |
| `um_futures_klines` | `ETHUSDT` | 6 | 5 | 18 | 0 | 0 | 0 | 0 | blocked |

## Archive Findings

- Monthly archive omissions recovered exactly by official daily ZIP: 936 rows
- Supplemental daily ZIP requests completed: 41
- Supplemental daily ZIP requests unavailable or invalid: 6
- Monthly/daily ZIP field differences jointly confirmed against REST: 36
- Supplemental evidence never replaces a conflicting monthly archive row.

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
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `51080.59000000` | `51048.59000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `11667.63216200` | `11815.24808200` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `593144862.93087132` | `600681216.08495300` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `276379` | `279380` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `5428.08513400` | `5505.78496500` | official sources contain different canonical values |
| `local` | `spot_klines` | `BTCUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `276430919.50983045` | `280397730.73104759` | official sources contain different canonical values |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `open` | `69566.10` | `69605.80` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `high` | `69566.10` | `69691.10` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `low` | `69566.10` | `69389.00` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `close` | `69566.10` | `69500.00` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `volume` | `0` | `5536.706` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `quote_volume` | `0` | `384850459.03950` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `trade_count` | `0` | `77957` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `taker_buy_base_volume` | `0` | `2912.252` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `taker_buy_quote_volume` | `0` | `202434171.18060` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `open` | `69650.00` | `69623.00` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `high` | `69776.80` | `69766.20` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `low` | `69480.30` | `69603.10` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `close` | `69770.20` | `69650.00` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `volume` | `3992.340` | `1395.290` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `quote_volume` | `278100132.91630` | `97216942.77100` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `trade_count` | `61306` | `22739` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `taker_buy_base_volume` | `2139.989` | `748.539` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `taker_buy_quote_volume` | `149079569.17770` | `52155314.67320` | monthly and supplemental official daily ZIP agree and differ from REST |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `high` | `608.82000000` | `613.29000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close` | `608.31000000` | `610.45000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `volume` | `26146.58875000` | `34927.37209000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `close_time` | `1608559199999` | `1608558440528` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `quote_volume` | `15866207.11148880` | `21219132.19507340` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `trade_count` | `14393` | `19857` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_base_volume` | `14284.12764000` | `19843.88555000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | `source_revision` | `2020-12-21T13:00:00+00:00` | `taker_buy_quote_volume` | `8669079.80611710` | `12059602.91269320` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `close` | `2325.82000000` | `2321.44000000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `volume` | `187368.61418000` | `188766.41365000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `quote_volume` | `436821371.55040100` | `440066845.48382460` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `trade_count` | `181462` | `182900` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_base_volume` | `84489.57317000` | `85129.16935000` | official sources contain different canonical values |
| `local` | `spot_klines` | `ETHUSDT` | `2021-04` | `source_revision` | `2021-04-23T01:00:00+00:00` | `taker_buy_quote_volume` | `196993734.15928340` | `198479364.97862700` | official sources contain different canonical values |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `open` | `2503.77` | `2505.93` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `high` | `2503.77` | `2516.49` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `low` | `2503.77` | `2504.13` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `close` | `2503.77` | `2516.41` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `volume` | `0` | `47283.244` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `quote_volume` | `0` | `118707131.60361` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `trade_count` | `0` | `61637` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `taker_buy_base_volume` | `0` | `30567.553` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T20:00:00+00:00` | `taker_buy_quote_volume` | `0` | `76746106.62568` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `open` | `2518.92` | `2515.96` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `high` | `2550.00` | `2520.00` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `low` | `2516.54` | `2514.54` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `close` | `2543.70` | `2518.92` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `volume` | `142679.794` | `16286.043` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `quote_volume` | `361731925.26645` | `40995382.83058` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `trade_count` | `141257` | `16917` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `taker_buy_base_volume` | `85920.066` | `9579.553` | monthly and supplemental official daily ZIP agree and differ from REST |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `source_revision` | `2024-10-28T21:00:00+00:00` | `taker_buy_quote_volume` | `217812131.53576` | `24110548.75032` | monthly and supplemental official daily ZIP agree and differ from REST |

## Timestamp Mismatch Summary

| Node | Dataset | Symbol | Month | Count | First UTC | Last UTC | Note |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `local` | `spot_klines` | `BTCUSDT` | `2020-12` | 1 | `2020-12-21T14:00:00+00:00` | `2020-12-21T14:00:00+00:00` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `local` | `spot_klines` | `ETHUSDT` | `2020-12` | 1 | `2020-12-21T14:00:00+00:00` | `2020-12-21T14:00:00+00:00` | ZIP-only timestamp is absent from the selected and adjacent official REST scopes |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |
| `proxy_local` | `index_price_klines` | `ETHUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |
| `proxy_local` | `mark_price_klines` | `ETHUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2026-06` | 24 | `2026-06-29T00:00:00+00:00` | `2026-06-29T23:00:00+00:00` | REST-only timestamp is absent from the selected, supplemental, and adjacent official ZIP scopes |

## Supplemental Daily ZIP Outcomes

| Node | Dataset | Symbol | Month | Day | HTTP/error status |
| --- | --- | --- | --- | --- | --- |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-04` | `2022-04-27` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-24` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-25` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-27` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-28` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-30` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-31` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2023-02` | `2023-02-13` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2023-02` | `2023-02-24` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2023-04` | `2023-04-07` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2023-04` | `2023-04-08` | `200:none` |
| `proxy_local` | `index_price_klines` | `BTCUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `index_price_klines` | `ETHUSDT` | `2022-07` | `2022-07-31` | `200:none` |
| `proxy_local` | `index_price_klines` | `ETHUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `index_price_klines` | `ETHUSDT` | `2023-02` | `2023-02-24` | `200:none` |
| `proxy_local` | `index_price_klines` | `ETHUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `2021-07-01` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `2021-07-24` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `2021-07-25` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `2021-07-26` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2021-07` | `2021-07-27` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2022-07` | `2022-07-31` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2023-02` | `2023-02-24` | `200:none` |
| `proxy_local` | `mark_price_klines` | `BTCUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `mark_price_klines` | `ETHUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `mark_price_klines` | `ETHUSDT` | `2023-02` | `2023-02-24` | `200:none` |
| `proxy_local` | `mark_price_klines` | `ETHUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `2021-07-01` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `2021-07-24` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `2021-07-25` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `2021-07-26` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2021-07` | `2021-07-27` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2023-02` | `2023-02-24` | `200:none` |
| `proxy_local` | `premium_index_klines` | `BTCUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `2021-07-01` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `2021-07-24` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `2021-07-25` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `2021-07-26` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2021-07` | `2021-07-27` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2022-10` | `2022-10-02` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2023-04` | `2023-04-09` | `200:none` |
| `proxy_local` | `premium_index_klines` | `ETHUSDT` | `2026-06` | `2026-06-29` | `404:http_404` |
| `proxy_local` | `um_futures_klines` | `BTCUSDT` | `2024-10` | `2024-10-28` | `200:none` |
| `proxy_local` | `um_futures_klines` | `ETHUSDT` | `2024-10` | `2024-10-28` | `200:none` |

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
  - index_price_klines:BTCUSDT:1h:2026-06: timestamp_mismatch
  - index_price_klines:ETHUSDT:1h:2026-06: timestamp_mismatch
  - mark_price_klines:BTCUSDT:1h:2026-06: timestamp_mismatch
  - mark_price_klines:ETHUSDT:1h:2026-06: timestamp_mismatch
  - premium_index_klines:BTCUSDT:1h:2026-06: timestamp_mismatch
  - premium_index_klines:ETHUSDT:1h:2026-06: timestamp_mismatch
  - spot_klines:BTCUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:BTCUSDT:1h:2021-04: source_revision
  - spot_klines:ETHUSDT:1h:2020-12: source_revision,timestamp_mismatch
  - spot_klines:ETHUSDT:1h:2021-04: source_revision
  - um_futures_klines:BTCUSDT:1h:2024-10: source_revision
  - um_futures_klines:ETHUSDT:1h:2024-10: source_revision

## Decision

- M0 audit status: audit_revalidation_required
- Detailed field evidence: `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md`
- M1A and M1B remain failed_validation.
- M2 remains prohibited.
- No live trading, real-API paper trading, execution, order, or API permission is approved.
