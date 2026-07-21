# U-12 Frozen-Source Data Qualification and Same-Reader Preflight

- Status: `pass_local_complete`
- Contract hash: `a65aa923b256d83eeb79aa0afb4483525e33ad28eda9bc9adc823008fc324ed3`
- Qualification hash: `c9a5b5480081ef0583604910ce2550029086b9c9f7bd0a147c723006859a0510`
- Protocol target: `11caf6f5160bfd03a127b6fc3565ad0b84c43d82`
- Protocol/review: `a8cfc0b74e82bdf455bae5dda7a620bc5c0c53f1022d39494800f1053dd80b8a` / `81262bf19b2c32d7cfb37a6d42106ec7bc21bd674a4d0d106b3e0ccfd58b8813`

## Frozen Authority

All 27,736 frozen source archives and all 19 V4 manifests retain exact identity.
Normal, reverse and deterministic-shuffled source traversals share
`ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa`.
Membership, lifecycle, invalid-interval mask, source freeze and V4 artifact set
remain exact.

## Same-Reader Preflight

The preflight used the future observation's monthly ZIP/member, point-in-time
membership and invalid-slot-mask paths, but decoded only 5m open timestamps.
It decoded no OHLCV values and computed no common component or return.

- Same-reader task set: `962` symbol-month archives.
- Three traversal orders share identity `5dfc833dc7897f14a9cb691738c2e5fc4b7770254c36d3b1ac316d0cafc02af3`.
- Complete active-member UTC days with all 288 unmasked slots and prior-boundary close: `1,623`.
- Ineligible days: `74` missing previous-boundary close and `18` daily-slot/mask failures.
- Decisions where all 52 scheduled same-weekday cells were checked: `1,275`.
- Metadata-eligible calendar decision days: `1,275`.
- Maximum non-overlapping theoretical 24h episodes: `647`, above the frozen minimum `300` and Paper count Gate `90`.

The 91 unavailable requested prior-month archives are preserved as missing
inputs. They are not filled or replaced; their affected boundary days are
excluded before any historical cell can qualify.

## Isolation and Authorization

OOS remains sealed with zero OOS OHLCV values decoded. Common-component,
candidate, event, path and return rows are all zero. No network was accessed and
no production evidence was modified.

This pass authorizes exactly one frozen sealed-IS U-12 Paper observation. It
does not authorize a second result run, formal returns, strategy rules,
Freqtrade code, backtesting, OOS, API/trading, `execution/live` or M2.
