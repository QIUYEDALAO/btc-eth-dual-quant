# External Strategy RNDR Original-Symbol Boundary Preflight

## Status

**PASS — single RNDR original-symbol archive and exact row only.**

ADR-0018 was independently approved at exact head
`bb22a08cc7bcd31c458ca7d362e536d88c0ca1e2`, passed GitHub run
`29871317869`, and was ordinary-merged as
`336563c67a6b23cc9ebbf91c7abd007db0df048b`. Only after that merge, this
stage acquired the fixed official archive:

`https://data.binance.vision/data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-07-22.zip`

No other boundary archive was requested or downloaded.

## Official source and exact row

- HTTP status: `200`
- Archive size: `1720` bytes
- Archive SHA-256 and official checksum:
  `e2da006ea431071e7eb1796dddaa72da8646f57ba1ecf75e0127c6e769491587`
- ZIP member: `RNDRUSDT-5m-2024-07-22.csv`
- Member SHA-256:
  `b321e6a21cc704ca8535e35f964f693c7b380482115448692dbffc0386e5f72c`
- Exact open: `2024-07-22T02:55:00Z`
- Exact close: `2024-07-22T02:59:59.999Z`
- Raw-line SHA-256:
  `89be4f1712abbe2ffe08277e6ac6cafbe28666513734be5595afc0a10dfe4f50`
- Verified OHLC: `7.07700000 / 7.07800000 / 7.02600000 / 7.03000000`

The row is finite, has legal OHLCV, is on the exact 5m grid, belongs to the
qualified July 2024 RNDR membership, and is not covered by the frozen
invalid-interval event or slot mask. It is earlier than the sealed OOS boundary.

## Isolation and accounting

- Archive requests: `1`
- Checksum requests: `1`
- Other 91 archive requests/downloads: `0 / 0`
- Market rows decoded: `1`
- Market rows decoded outside the fixed boundary: `0`
- Strategy results read: `0`
- IS / selection trials: `0 / 0`
- OOS rows decoded: `0`

The row is frozen for a future execution-side forced-exit lookup only. It was
not appended to candidate OHLCV or indicator history. Normal, reverse, and
deterministic-shuffled traversals of this one archive produced one exact row
identity and three distinct traversal traces.

## Evidence identity and remaining stop

- Machine evidence:
  `eceafea174381268c22df88b3262a3702a828a3aac079b8e060000686c9b38be`
- Command evidence:
  `cf3d7f83730ca93b5df679806cf87f47ee3b3b485f38073779854632d4e72d1f`
- PR #117 review:
  `41f4360976a3b2dff2408bf3262fff548b23b3bf1460314d3c8882c1e9ad780f`

This pass removes only the RNDR one-item preflight blocker. The completed
92-boundary authority is **not frozen**, NB-01 is **not yet satisfied for the
completed authority**, and original IS remains unauthorized. A later stage may
construct the complete revised 92-boundary authority, but it must independently
acquire and validate the remaining 91 sources, run genuinely independent
normal/reverse/deterministic-shuffled full constructions, receive a separate
exact-head review, and merge before any IS materialization.

OOS, dry-run, API/private endpoints, paper/live, orders, `execution/live`, and
M2 remain false.
