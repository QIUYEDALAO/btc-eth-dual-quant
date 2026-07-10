# T2 Golden Data and Quarantine Report

- Status: pass
- Scope: golden 1m, deterministic 5m/15m, official 15m parity, and Freqtrade cache validation only
- API key used: no
- Private data used: no
- Strategy returns computed: no
- Runtime artifacts committed: no
- Research range: 2023-10-01 through 2026-06-30T23:59:59.999000+00:00
- Manifest SHA256: `7f77fa2285b76eb5cb6e3be54ea702126885655d8ba9b09e7a8bda4a4520ed6f`

## Golden and Derived Data

| Symbol | 1m rows | 1m hash | 5m rows | 5m hash | 15m rows | 15m hash | Incomplete 5m | Incomplete 15m |
| --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: |
| BTCUSDT | 1445760 | `cf8697a2a890f1f1cf7cb5436b36091d0fe43f92df843909781c815796fa80d1` | 289152 | `f78bbc13e8870cacad7edb2cb3342e4cf6152b926bab258503912fc6e7a0d4e0` | 96384 | `3ef889f1aa355e9583bd3e38779c10f01fbd1850dc8097f35cb9b067afd4cb73` | 0 | 0 |
| ETHUSDT | 1445760 | `1d18849c05a840f9543e00da69a8963a053bf07cfc65218fcf1a1499b513a081` | 289152 | `87af325c997d44d7dfb19da3456f68c3e1e29a88290a9a831b746b73d16f684b` | 96384 | `66dc988a58309ce11eac31d40a5008f5b5e7548bb00d252ffb943a857e4222b4` | 0 | 0 |

## Quarantine

- Pre-start quarantined symbol-months: 50
- Quarantine records: 60485
- Quarantine SHA256: `72ca4e1e2bed71057674fcad16ce25789ae788410c4934caf03ad21625d70df3`
- Monthly ZIP rows are never overwritten; daily ZIP rows only fill absent valid minute timestamps.

## Official 15m Parity

| Symbol | Months | Overlap | Numeric differences | Derived-only | Official-only | Invalid official | Format-only | Official ZIP bundle hash | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| BTCUSDT | 33 | 96384 | 0 | 0 | 0 | 0 | 0 | `910f206d54cdf5435e7d9718dcf72af2d71f42297eb1ebd23843d56437c12bb5` | pass |
| ETHUSDT | 33 | 96384 | 0 | 0 | 0 | 0 | 0 | `abe7cbc3c44f3d6e1b9ac9e0ee11bae61f50dca750c03b8d7b6ae014b69872cc` | pass |

## Freqtrade Cache

- Image: `freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`
- Data format: jsongz
- Command: `freqtrade list-data --show-timerange --data-format-ohlcv jsongz`
- Runtime status: pass
- Runtime note: Pinned Freqtrade 2026.6 container read all six BTC/ETH 1m, 5m, and 15m caches with exact ranges and row counts.

## Gate

- Research-range golden 1m complete: pass
- Deterministic 5m/15m complete: pass
- Official 15m numeric differences zero: pass
- Quarantine traceable by hash: pass
- Freqtrade list-data: pass
- T3 authorized: yes
- M1D strategy code authorized: no
- M2 authorized: no
