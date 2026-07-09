# Freqtrade / M0 Data Provenance

- Status: pass
- Generated UTC: 2026-07-09T20:19:49+00:00
- Scope: public spot research data comparison only
- M0 role: canonical audit authority
- Freqtrade role: reproducible runtime cache
- API key used: no
- Runtime data committed: no

| Symbol | Timeframe | Start UTC | End UTC | M0 rows | Freqtrade rows | Overlap | Missing timestamps | Field differences | M0 gaps | Freqtrade gaps | Status |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `BTCUSDT` | `1d` | `2017-08-17T00:00:00+00:00` | `2026-07-08T00:00:00+00:00` | 3248 | 3248 | 3248 | 0 | 0 | 0 | 0 | pass |
| `ETHUSDT` | `1d` | `2017-08-17T00:00:00+00:00` | `2026-07-08T00:00:00+00:00` | 3248 | 3248 | 3248 | 0 | 0 | 0 | 0 | pass |

## Hashes

### BTCUSDT 1d

- M0 normalized SHA256: `3c09234310a50a7148508835360614df38d59bfde5575d5ee5818f1826843d99`
- Freqtrade file SHA256: `ed732b4f9da82ebb72b3a41148d9e78b6d80fa92ea1247bf9c9ad1a78ea7175a`
- Overlap normalized SHA256: `3c09234310a50a7148508835360614df38d59bfde5575d5ee5818f1826843d99`

### ETHUSDT 1d

- M0 normalized SHA256: `1b3f68ae4cda078831a56bcc75ae3ebdf031d202fc8b03c126bb4d637d112a95`
- Freqtrade file SHA256: `9d9c07f14edd67fbbd26a2e0b57eaf61ec75a82cddcaf55ebaef57bb80ec9745`
- Overlap normalized SHA256: `1b3f68ae4cda078831a56bcc75ae3ebdf031d202fc8b03c126bb4d637d112a95`

## Decision

Freqtrade cache may be deleted and regenerated. Any mismatch remains blocked until explained against M0; this report does not approve M2 or trading.
