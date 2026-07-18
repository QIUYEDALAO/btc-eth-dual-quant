# U-23 Frozen-Source Data Qualification

- Status: `pass_local_complete`
- Contract hash: `37c1c9b0bdbb13639aea36a1da525163ba4a8142ec1f808bc8cbe1ca0aed7909`
- Qualification hash: `08166fb534daf691e069f6ae743b472f0c06879dd060c58f816e4f2d5acef2c5`
- Protocol/review: `52807bd0...3e5611` / `f2a8a5fd...37c4a4`

All 27,736 frozen archives and 19 production manifests remain exact. Normal,
reverse and deterministic-shuffled source traversal produce one source
identity, and the same timestamp-only ZIP reader produces one structural
identity in all three orders.

The preflight verifies every active member's seven-day 5m slot history, the
current completed 4h boundary and next 24h path availability, including the
point-in-time membership, lifecycle and invalid-interval mask order. It finds
7,122 structurally eligible decisions and a maximum 1,031 independent 24h
episodes, above the frozen minimum 400; every IS year has ample ceiling.

No OHLC field, range, return, candidate, event, path, formal return or OOS
value was decoded or generated. Exactly one sealed-IS Paper observation is
authorized. Strategy, backtesting, OOS, API/trading, `execution/live` and M2
remain false.
