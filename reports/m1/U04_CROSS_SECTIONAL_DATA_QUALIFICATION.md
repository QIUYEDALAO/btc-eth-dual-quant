# U-04 Cross-Sectional Data Qualification

- Status: `pass`
- Contract hash: `fc45ba3a07776aa94ec8805d6e855bc34905a9aaac7d9a27af098a3f80352af2`
- Qualification hash: `4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c`
- Protocol/review: `7b0e462d...9629d6` / `34fe2efd...646b1`

## Frozen source and authority

- Frozen ZIP identity and CRC: 27,736/27,736 exact.
- Independently audited V4 authority manifests: 19/19 exact.
- Membership, expected 5m grid and qualified 1h panel rows: 1,170 / 1,170 / 1,170.
- Normal, reverse and deterministic-shuffled source identity: `ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa`.
- Source revisions, unresolved gaps, processing errors, replacements and fills remain zero.
- Invalid-interval authority remains exactly 8 events, 119 invalid physical rows, 1 valid-minority row and 120 masked active slots.

## Isolation

- IS value boundary: `[2020-01-01T00:00:00Z, 2024-09-11T00:00:00Z)`.
- Sealed OOS begins at `2024-09-11T00:00:00Z`.
- OOS archives were handled only as opaque bytes for size, SHA-256 and ZIP CRC checks.
- OOS OHLC values decoded: `0`.
- U-04 event, path and return rows generated: `0 / 0 / 0`.
- Network access and production-evidence mutation: `false / false`.

## Decision

The frozen authority and IS/OOS isolation pass. This authorizes exactly one sealed-IS paper observation under the reviewed protocol. It does not authorize a second scan, parameter changes, a position/equity curve or formal return calculation.

No strategy, backtest, OOS, API/trading, execution/live or M2 is authorized.
