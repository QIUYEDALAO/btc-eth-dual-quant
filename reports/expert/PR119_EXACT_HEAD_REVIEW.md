# PR #119 Exact-Head Independent Review

## Target

- Repository: `QIUYEDALAO/btc-eth-dual-quant`
- Pull request: `#119`
- Reviewed exact head: `380b50392b3a225bbaf7f0ff4f24041b8fb22666`
- Functional head: `5adc1101e4485fff0f312c352e04ad5fe9dcc12d`
- Base / PR #118 merge: `02673d1bebfb7a9efa5370a8025f1ea185c172b5`
- Completed authority: `9829e22b0c0b21bf69dac2d8d84de845650e2da31e13f239578e6a43dba96ada`

## Verdict

**APPROVE**

- Critical findings: **0**
- High findings: **0**

## Review conclusions

### Authorization chain and boundary set — PASS

The authority is bound to the approved PR #118 chain and implements the exact
ADR-0018 one-for-one revision: 91 original membership-exit identities remain,
`RNDRUSDT@2024-08-01T00:00:00Z` is removed, and
`RNDRUSDT@2024-07-22T02:55:00Z` is added. The revised set contains exactly 92
unique IS-only identities and no timestamp reaches the sealed OOS boundary.

### Source, archive, member and exact-row contract — PASS

The acquisition path is allowlisted to the frozen Binance daily archive and
checksum URLs. New sources require HTTP 200, no effective-URL drift, matching
official SHA-256, valid Content-Length, valid ZIP CRC, exactly one expected CSV
member and exactly one row at the fixed boundary timestamp. Every row is parsed
as a 12-field kline, checked for exact close time, finite legal OHLCV, qualified
prior membership and no lifecycle or invalid-interval conflict.

The frozen authority records 91 newly acquired official archives plus the
already reviewed RNDR archive, 92 exact rows, 47 symbols and 1,116,059 archive
bytes. It records no row outside the fixed set, no strategy-result row, no IS or
selection trial and no OOS row.

### Three full-set independent constructions — PASS

Normal, reverse and deterministic-shuffled passes each reopen and verify all 92
archive files. They produce the same canonical authority result:

`5b05fbf68b46bcb5bb5a80d86e53edb8383252d371495308424b35bfc140ebec`

and distinct traces:

- normal: `e94ad0ed41e8878724d8b9d2290479861ae744cbe951444881fcb29c0316290b`
- reverse: `91e50449aaf91cea41340a246a093a8b0158ba7f63d2c2a2054367dd8ceb0836`
- deterministic-shuffled: `699133bf497088805b9df0e769fcd50741fa95ea4b1f54840601710345f00f49`

This satisfies NB-01 as three real full-set constructions rather than three
labels over one construction.

### Runtime-consumption and safety contract — PASS

Boundary data is execution-side forced-exit lookup only. It cannot enter
candidate OHLCV or indicator history. State cannot cross inactive membership
intervals; every readmission requires segmentation, reset and rewarm from the
current active interval, and entry before rewarm completion is prohibited.

The frozen evidence continues to declare:

```text
IS trials             = 0
selection trials      = 0
OOS                    = false / false / 0 / 0
dry-run/API/live/M2   = false
```

### Validation and exact head — PASS, merge Gate pending

Functional head `5adc1101e4485fff0f312c352e04ad5fe9dcc12d` passed GitHub run `29879564234`.
Current exact head `380b50392b3a225bbaf7f0ff4f24041b8fb22666` adds one `[skip ci]` commit touching only the five
mandatory GitHub context files. No authority code, evidence, command document,
report or test identity changed.

The current exact head has no workflow run yet. PR #119 may be merged only after
it is marked Ready, the GitHub Gate succeeds on this exact head and the head is
confirmed unchanged. Any new commit invalidates this review.

After merge, the completed boundary-data Gate is closed. Original IS may then
proceed only under the existing ADR-0017 automated authority and frozen unified
protocol. This review grants no OOS, dry-run, API/private endpoint, paper/live,
order-placement, `execution/live` or M2 authority.

## Review assurance limitation

The 92 raw ZIP files are deliberately repository-external and no GitHub Actions
artifact exposes them. This reviewer environment could not perform a fresh
second download of all 92 binary objects. Command hashes and sample row hashes
were independently recomputed, and the full acquisition/validation algorithm,
frozen evidence, official-checksum bindings, tamper tests and functional-head CI
were reviewed. The approval is therefore not a claim of a second 92-object
network acquisition.

This limitation is non-blocking for the current immutable authority, but an
immutable external evidence bundle or explicit retention policy would improve
long-term reproducibility if Binance later replaces an archived file.

## GitHub write status

Attempts to submit the formal APPROVE review and mark PR #119 Ready failed with
`Resource not accessible by integration`. No GitHub state was changed.

Machine review content hash:

`203ff8488e5e8c44019a09653f4189ef6ff780185469ef77323a60672a7e3c1f`
