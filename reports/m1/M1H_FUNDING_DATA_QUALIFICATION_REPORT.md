# M1H Funding Data Qualification Report

- Status: pass
- Scope: M1H-03A public funding-data qualification only
- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN
- Funding event scan executed: no
- Funding event count computed: no
- MFE/MAE/recovery computed: no
- Formal strategy returns computed: no
- OOS funding values parsed: no
- OOS spot OHLC parsed: no
- OOS opened: no
- API key used: no
- Private data used: no

## Lineage And Settlement Semantics

- Funding source: Binance public monthly USD-M fundingRate ZIP, preserved in M0 append-only raw envelopes.
- Symbols: BTCUSDT, ETHUSDT.
- Qualified boundary: before 2024-09-11T00:00:00Z.
- fundingTime is the public settlement timestamp in UTC epoch milliseconds.
- A funding observation is available no earlier than its fundingTime.
- Per-event intervals are inferred from adjacent settlement timestamps and checked against each public row's declared interval.
- No default funding cadence is supplied.

## Funding Qualification

| Symbol | Unique rows | Raw duplicates | Conflicts | Invalid rows | Invalid intervals | Missing settlements | Start UTC | End UTC | SHA256 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| BTCUSDT | 5145 | 5145 | 0 | 0 | 0 | 0 | 2020-01-01T00:00:00Z | 2024-09-10T16:00:00Z | `7e91af6817394708813da8298ffc4c2fc5266978519e8f51b3d716b3dd311328` |
| ETHUSDT | 5145 | 5145 | 0 | 0 | 0 | 0 | 2020-01-01T00:00:00Z | 2024-09-10T16:00:00Z | `9e98bc6bfc278fbfa36cabd022cf7b858bd4d689331c0edaae89650ea8cb86a5` |

### Public Raw Payload Hashes

- BTCUSDT: `6f451ef667f58142e5f2cf255f456cd6a1e660f3f4a2b4ec8fd682dca3155046`, `beb140bc73e6c027c4e67888185b6db1660ec0aa28ed90bbcee14a7250363e76`
- ETHUSDT: `f669cdd9cd69018eaad4186ec260a931c804b47160c73d94c0ac136c8db99960`, `7dd319341b6f2f86ee5d485d9388ba88e0267e6bb9fa9dc8ddf1f55a68401eac`

Identical duplicate timestamps come from repeated append-only public backfills; they are canonicalized only after their rate and declared interval agree exactly.

## Canonical Spot 5m Dependency

| Symbol | IS rows | Known gaps | Start UTC | End UTC | SHA256 |
| --- | ---: | ---: | --- | --- | --- |
| BTCUSDT | 441215 | 11 | 2020-07-01T00:00:00Z | 2024-09-10T23:59:59.999000Z | `2bc55152255948b3c10a693f4ba210288aa2c0ae7921fec0a31dc7562c38d8a3` |
| ETHUSDT | 441215 | 11 | 2020-07-01T00:00:00Z | 2024-09-10T23:59:59.999000Z | `9b4770b0c7f343858b43b5d7a7046f0ef1609516f4bbb648b50da02bc094fb67` |

Known canonical gaps remain explicit. No missing bar is filled or shifted; a later paper observation touching one is censored or invalid under the frozen protocol.

## Qualification Gate

- Funding lineage: pass
- Settlement timestamps/order/timezone: pass
- Per-event interval continuity: pass
- Duplicate/conflict handling: pass
- Canonical spot 5m dependency: pass
- OOS isolation: pass
- M1H-03B authorized in this task: yes
- Strategy code authorized: no
- Backtesting authorized: no
- OOS authorized: no
- M2 authorized: no
