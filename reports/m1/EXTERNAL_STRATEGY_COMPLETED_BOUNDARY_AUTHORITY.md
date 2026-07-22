# External-Strategy Completed Membership-Exit Boundary Authority

- Status: `pass_frozen_pending_separate_exact_head_review_and_merge`
- Scope: result-blind, IS-only forced-exit lookup
- Authority records: 92/92
- Original IS authorized: `false`
- Selection trials: `0`
- OOS state: `false/false/0/0`

## Review and authorization chain

PR #118 exact head `89965820c3281caf4f759a055ace271151d32622`
was independently approved with zero critical/high findings under review
`6f57e1da0efa6f233308809d9d5bd33a6a591737c032b5d73206379713e3a94c`.
Exact-head Main Regression run `29877334519` succeeded and the reviewed head
was ordinary-merged as `02673d1bebfb7a9efa5370a8025f1ea185c172b5`.
The merge authorized completion of the result-blind boundary authority; it did
not authorize original IS.

The completed set is the exact one-for-one ADR-0018 revision of qualification
`e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa`:

- removed: `RNDRUSDT@2024-08-01T00:00:00Z`;
- added: `RNDRUSDT@2024-07-22T02:55:00Z`;
- unchanged identities: 91;
- additions or deletions beyond that replacement: 0.

## Result-blind acquisition and exact-row validation

The single authorized acquisition requested 91 new official Binance daily ZIP
archives and 91 checksum files. The already frozen PR #118 RNDR archive was
reused without another request. The frozen authority contains 92 archives,
47 symbols and 1,116,059 archive bytes. It decoded exactly 92 unique boundary
rows and no row outside the fixed boundary set.

Every record binds source path and URL, checksum URL, acquisition time/tool,
archive byte size and SHA-256, official checksum, archive member identity and
SHA-256, raw line and SHA-256, and exact open/close timestamps. Every row has
`close_time = open_time + 299999 ms`, legal finite OHLCV, qualified prior
membership, no prior lifecycle cessation except the frozen ADR-0018 RNDR
cessation, and no invalid-interval event or mask.

The raw archives remain ignored repository-external inputs under
`storage/raw/external_strategy_boundary_authority/`; all 92 local snapshot
files are read-only and none is tracked by Git.

## Determinism and frozen identities

Normal, reverse and deterministic-shuffled passes each independently reopened
and inspected all 92 archives. Their canonical result identity is identical:

`5b05fbf68b46bcb5bb5a80d86e53edb8383252d371495308424b35bfc140ebec`

Their traversal trace hashes are intentionally distinct:

- normal: `e94ad0ed41e8878724d8b9d2290479861ae744cbe951444881fcb29c0316290b`;
- reverse: `91e50449aaf91cea41340a246a093a8b0158ba7f63d2c2a2054367dd8ceb0836`;
- deterministic-shuffled: `699133bf497088805b9df0e769fcd50741fa95ea4b1f54840601710345f00f49`.

This satisfies the frozen NB-01 requirement: three real full-set constructions,
not three labels over one construction.

Machine evidence:

- authority canonical hash: `9829e22b0c0b21bf69dac2d8d84de845650e2da31e13f239578e6a43dba96ada`;
- authority byte hash: `056a31f07c3548480a26dc4f9bdb997e2d2c5ec18e2e78778965d500a9b4b56b`;
- command canonical hash: `2674853239a7c185d35a0e751bf71e31cc89c5556e8c573a95415e42006771a7`;
- command byte hash: `3f438735cc2c3a423b646ea2354bc46927e7bf5ea3529a0bf64dce3f544a2737`.

## Runtime isolation contract

The boundary rows are frozen for execution-side forced-exit lookup only. They
must never be appended to candidate OHLCV or indicator history. A future IS
runner must segment active membership intervals, discard indicator state at an
inactive transition, reset at readmission and rewarm only from the current
active interval. Stitched discontinuous feeds are explicitly insufficient and
entry before rewarm completion is prohibited.

## Safety accounting and next Gate

- strategy result rows read: 0;
- IS trials materialized: 0;
- selection trial count: 0;
- OOS rows decoded: 0;
- dry-run/API/private endpoint/paper/live/order/`execution/live`/M2: false.

This frozen authority still requires a separate exact-head independent review,
successful Gate and merge. Until all three occur, `original_is_authorized`
remains `false` and no selection trial may materialize.
