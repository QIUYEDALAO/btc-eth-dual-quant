# U-07 Cross-Sectional Frozen-Source Data Qualification

- Status: `pass`
- Contract hash: `0dd9a159382f1d515fed0269c9122adcd042a1fd726431bc36a9e4f6e01d5fb8`
- Qualification hash: `fa65f34089854cd5faf950234b3488eb64b3058d1ab47f3dab500bbfb395e123`
- Protocol target: `3aed4c337ff984b3e07ad9a4c7cda898425b3791`
- Protocol review: `fa9d90f7ebb30d4072662a9d8a733760a703eb04031abda23f3b6b0846bc70b6`

## Qualification result

- Frozen ZIP identities and CRCs: `27,736/27,736`
- Audited V4 manifests: `19/19`
- Traversal identity: `ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa`
- Expected active-member 4h blocks: `213,570`
- Constituent 1h rows: `854,280`
- Membership rows: `1,170`
- OOS OHLC values decoded: `0`
- Market-stress, relative-resilience, event, path and return rows generated: `0 / 0 / 0 / 0 / 0`
- Network accessed: no
- Production evidence mutated: no

Normal, reverse and deterministic-shuffled traversal are identical. Membership,
lifecycle, complete 4h/1h/5m grids and ADR-0015 invalid-interval authorities
remain exact. OOS archives were handled only as opaque identity and CRC objects.

This pass authorizes exactly one sealed-IS Paper observation under the frozen
protocol. No second run, tuning or OOS decode is allowed. No strategy, backtest,
formal return, API/trading, `execution/live` or M2 is authorized.
