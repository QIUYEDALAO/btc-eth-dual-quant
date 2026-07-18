# U-05 Cross-Sectional Frozen-Source Data Qualification

- Status: `pass`
- Candidate: `U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE`
- Protocol target: `8d8652796e22a15285ba682b4524baa0218ca5a6`
- Protocol hash: `c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214`
- Protocol review hash: `8602f209c3e80ea31b4b1175967acfba2bb20252254d3fbdf5cc72ea128d914f`
- Contract hash: `f1374b5c7bf7a103be7dacf3985d45cd332388afe601bd849271b30d63f562c3`
- Qualification hash: `348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f`

## Frozen Authority

- Frozen archives verified by exact size, SHA-256 and ZIP CRC: `27,736/27,736`.
- Audited V4 manifests exact: `19/19`.
- Membership rows/months: `1,170 / 78`; every qualified month retains the frozen Top-15 authority without replacement.
- Expected-grid and qualified-panel rows: `1,170 / 1,170`.
- Invalid-interval accounting remains `8 / 119 / 1 / 120`; fills and replacement members remain zero.
- Normal, reverse and deterministic-shuffled identity: `ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa`.

## Signal and Isolation Gates

- Completed 4h grid authority: `pass`.
- Exact constituent 1h authority rows: `854,280`; aligned expected 4h member-blocks: `213,570`.
- Any quarantined 1h constituent makes its whole 4h block ineligible; no later block or member may substitute.
- IS boundary: `2020-01-01T00:00:00Z` through `2024-09-11T00:00:00Z` exclusive.
- OOS archive access: opaque identity and CRC only.
- OOS OHLC values decoded: `0`.
- Breadth/event/path/return rows generated: `0 / 0 / 0 / 0`.
- Network accessed: no; frozen production evidence mutated: no.

## Decision

Qualification passes and authorizes exactly one sealed-IS Paper observation
under the frozen protocol. That observation may calculate only the
pre-registered U-05 breadth events, episodes and path diagnostics inside IS.
No parameter change or second observation is permitted.

No strategy, backtest, OOS, API/trading, execution/live or M2 is authorized.
