# M1E 1H Data Qualification Report

- Status: blocked
- Scope: public-data qualification only
- Qualification range: 2020-01-01 through 2026-06-30T23:59:59.999000+00:00
- Research start: 2020-07-01
- Manifest SHA256: `5dcb9d9f036d268958499388b37f6e9f8518f9bdb4facc1dccc14f525ab9daa9`
- Candidate evaluated: no
- OOS prices/returns accessed: no
- Strategy code authorized: no
- Freqtrade backtesting run: no
- API key used: no
- Private data used: no
- Runtime artifacts committed: no
- M2 authorized: no

## Data Summary

| Symbol | Timeframe | Rows | Canonical SHA256 |
| --- | --- | ---: | --- |
| BTCUSDT | 5m | 630719 | `5823a73280a35cdad956e4fa6441c4e728ee3994b2858fa51ea7c8e043455cc2` |
| BTCUSDT | 1h | 52555 | `facd726ae7603448b9281b8898b7e2b0de60dfe01f0a97d241262b0f209e20b1` |
| BTCUSDT | 4h | 13129 | `2214c978664e9019877da3ef7fd7ba4da7cc749d6b89b3621a8121078da3b6ef` |
| ETHUSDT | 5m | 630719 | `1f3a87a12211cd2fa428d1711e5e46bca8686f6c756740447d622e63d8b6200a` |
| ETHUSDT | 1h | 52555 | `446ed30dbe3772269d24cfa49f095a436d6f91ed62f769a444e19ea2a8fa2bab` |
| ETHUSDT | 4h | 13129 | `e09fba2ec95274c076df34f3c6a4ad4ca35f86537d8ac19ea780009b846bdfdf` |

## Month Qualification

- audit_complete: 62
- audit_complete_with_confirmed_outage: 10
- blocked: 6
- Confirmed outage 5m rows: 470
- Isolated 1h buckets: 47
- Isolated 4h buckets: 26
- Quarantine SHA256: `29e8a8febcffc2e9713bad6a5db9af3443e6f1e911dac2f623b3093004742966`
- Official monthly ZIP payload hashes: 468
- Public fetch failures: 0
- Confirmed outages are not filled or tradable; future rolling windows must fully rewarm.

### Blocking Months In The Contract Research Range

| Month | Reasons |
| --- | --- |

## Aggregate Parity

| Timeframe | Overlap | Numeric differences | Format-only fields | Unexplained timestamps | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| 1h | 113810 | 40 | 0 | 0 | blocked |
| 4h | 28424 | 50 | 0 | 0 | blocked |
| 2020-12 | BTCUSDT:1h:invalid_or_conflict, BTCUSDT:5m:invalid_or_conflict, ETHUSDT:1h:invalid_or_conflict, ETHUSDT:5m:invalid_or_conflict, untracked_5m_early_close |
| 2021-01 | BTCUSDT:4h:numeric_difference, ETHUSDT:4h:numeric_difference |
| 2021-04 | BTCUSDT:1h:numeric_difference, BTCUSDT:4h:numeric_difference, ETHUSDT:1h:numeric_difference, ETHUSDT:4h:numeric_difference |
| 2021-09 | BTCUSDT:1h:numeric_difference, BTCUSDT:4h:numeric_difference |
| 2021-11 | ETHUSDT:1h:numeric_difference, ETHUSDT:4h:numeric_difference |
| 2022-04 | BTCUSDT:4h:numeric_difference, ETHUSDT:4h:numeric_difference |

## REST Evidence

- Samples: 10
- Overlap rows: 3672
- Field differences: 0
- Status: pass
- REST is compare-only and never overwrites ZIP data.

## Liquidity And Runtime

- Fixed monthly 1m p95 spread-proxy maximum: 0.0030
- Qualified common six-month window: 2020-01 through 2020-06
- Freqtrade image: `freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`
- Freqtrade list-data: pass
- Runtime evidence location: external_public_runtime
- Freqtrade operation: list-data only; no strategy or backtesting command was run.

## Gate

- Public ZIP qualification: blocked
- Official 1h/4h numeric differences zero outside isolated outages: blocked
- Freqtrade cache readable: pass
- Sample-budget stage authorized: no
- Strategy code authorized: no
- Candidate OOS returns authorized: no
- M2 authorized: no
