# U-13 Frozen-Source Data Qualification and Same-Reader Preflight

- Status: `pass_local_complete`
- Contract: `e9b820855abbd5e5278d3f433ab3f06f7e17a73e792f04de924bed685a0e5ce7`
- Result: `5c4a61efc177415b1bd0a03697f4a3028f9ab8bed908adc12100bc03e9b90590`
- Protocol target: `6ef1024033aa9a86ef3c8f07558ba966270625a7`
- Review: `be552dad055234b0107810a7299656793ccea2a97f09a2cba22fa8ffc33ed5e0`

All 27,736 frozen archives and 19 V4 manifests remain exact. Normal, reverse
and deterministic-shuffled source traversals share one identity, and the three
same-reader traversals share `5dfc833d...2af3`.

The metadata-only reader found 40,383 complete active-member 1h intervals,
36,716 structurally eligible decision hours and a maximum 1,490 independent
24h episodes versus the frozen minimum 400. It verified previous-boundary
closes, twelve 5m slots per complete hour, 2,160h histories, four-hour
historical followups, point-in-time membership, lifecycle and masks.

No OHLCV field was decoded during preflight, no OOS OHLCV value was decoded,
and common-component, candidate, event, path and return row counts are all zero.
Only the unique sealed-IS U-13 Paper observation is authorized next. Strategy,
backtesting, OOS, API/trading, `execution/live` and M2 remain false.
