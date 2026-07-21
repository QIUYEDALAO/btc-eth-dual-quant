# External Strategy Boundary Authority Source Preflight Stop

## Decision

The authorized result-blind official-source preflight stopped before archive
acquisition. Of the fixed 92 membership-exit identities bound by qualification
`e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa`,
91 official Binance daily ZIP URLs answered successfully and one required URL
did not exist:

`https://data.binance.vision/data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-08-01.zip`

The official endpoint returned HTTP 404. The authorization requires 92/92 and
states that an unavailable official source is a hard stop. No substitute symbol,
REST response, earlier/later row, synthetic price, last price, forward search or
unfrozen source was used.

## Evidence

- Source preflight content hash: `5746b9824ddce364cbe291ea5d7f9b499246683cb8b909a5fc9e19383150537e`
- Fixed boundary count: 92
- Available official daily sources: 91
- Missing official daily sources: 1
- Archives downloaded: 0
- Archive bytes downloaded: 0
- Market rows decoded: 0
- Strategy result rows read: 0
- IS trials materialized: 0
- Selection trial count: 0
- OOS rows decoded: 0

The normal, reverse and deterministic-shuffled construction identities are
equal. The evidence validator fixes the missing identity to `RNDRUSDT` at
`2024-08-01T00:00:00Z` with HTTP 404 and fails on identity, permission, counter
or hash drift.

## Consequence

The membership-exit boundary authority is not frozen. Original IS remains
unauthorized. Resuming requires a new explicit decision that changes the source
or holding/universe contract; this branch does not make that decision.

The materializer was separately hardened to accept only membership rows whose
`eligibility_status` is explicitly `qualified`. That defensive change does not
expand data, runtime, IS, OOS or trading authority.
