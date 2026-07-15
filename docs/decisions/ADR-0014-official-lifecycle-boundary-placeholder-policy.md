# ADR-0014: Official Lifecycle-Boundary Placeholder Policy

- Status: Proposed draft; not adopted
- Date: 2026-07-15
- Scope: official Binance spot archive rows at a documented symbol cessation boundary
- Depends on: ADR-0011, ADR-0012, ADR-0013, PR #79 adjudication evidence
- KLAY adjudication evidence hash: `6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a`
- Proposed successor contract: `LIQUID-SPOT-USDT-TOP15-V4`

## Context

PR #79 proved that KLAYUSDT 2024-10-30 is a checksum-bound official-source
artifact at the KLAY trading cessation boundary. ADR-0013 has no authority to
admit, repair, replace or quarantine this monthly/daily/REST-identical invalid
row. This ADR therefore proposes a generic policy for independent review. It
does not adopt that policy, change V3, create a registry entry or authorize a
requalification.

## B1: Proposed Lifecycle-Boundary Placeholder Category

The proposed category is `official_lifecycle_boundary_placeholder`. A future
version may assign it only when every condition below is machine-proven:

- monthly and daily official archives are checksum verified and CRC valid;
- monthly and daily raw rows and semantic rows are identical;
- two frozen public REST comparators each return exactly one row identical to the archive row;
- the row is flat OHLC: open = high = low = close;
- base volume, quote volume, both taker volumes and trade count are all zero;
- close_time is less than open_time;
- affected open_time is not earlier than official cessation_time;
- close_time equals official cessation_time minus exactly 1 millisecond;
- the affected UTC day has no official intraday trading bars;
- the final intraday close equals official cessation_time minus exactly 1 millisecond;
- official lifecycle evidence is checksum/hash bound;
- the row is not a parser bug, duplicate or archive republication;
- similar-scope scan finds no broader unexplained schema defect.

Any missing, unavailable, changed or contradictory condition remains blocked.
A lifecycle announcement alone is provenance and never data override authority.

## B2: Proposed General Handling Semantics

If a future adopted version proves all B1 conditions, it would:

- preserve the original monthly, daily and REST evidence permanently;
- place the invalid source row in `raw_row_quarantine` and exclude it from canonical OHLCV;
- create no replacement daily row, synthetic fill or normal zero-volume candle;
- emit a machine-readable `symbol_availability_boundary` containing symbol,
  cessation time, last valid market time, optional replacement symbol, official
  lifecycle evidence hash, affected archive hashes, resolution ID and policy version;
- stop expecting normal bars for the old symbol after cessation;
- preserve existing point-in-time universe membership and valid pre-cessation panel data;
- mark post-cessation availability as `lifecycle_terminated`, without adding a replacement member;
- permit the cross-sectional asset count to fall rather than fabricate continuity;
- require future ranking windows to use only real, legal and then-tradable complete daily rows.

There is no automatic KLAY/KAIA history splice. Any replacement-symbol,
renaming or economic-continuity mapping requires a separate ADR and policy.

## B3: Required New Version Before Any Implementation

Adoption would require a new `LIQUID-SPOT-USDT-TOP15-V4` contract, never an
in-place V3 mutation, plus a versioned lifecycle resolution registry. The
contract hash would bind the lifecycle-policy hash, registry hash, KLAY
adjudication evidence hash, lifecycle evidence schema and availability-boundary
schema. V1, V2 and V3 remain immutable historical evidence.

The first authorized V4 run would remain fixed to `2020-01 through 2026-06` and
would require deterministic `cold, warm-cache and worker-variant` rebuilds.
Every unknown or changed conflict would continue to fail closed. Governance
would require a truthful V4 requalification PASS before U-03F, and U-03F PASS
and separate authorization before U-04.

## B4: Forbidden Shortcuts

- Do not rewrite close_time as open_time plus one day minus 1 millisecond.
- Do not construct a normal zero-volume candle.
- Do not replace the daily row with an intraday aggregation.
- Do not replace the archive row with REST data.
- Do not delete the raw row.
- Do not splice KLAY history into KAIA automatically.
- Do not add a symbol/date special case.
- Do not ignore the conflict because Top-15 membership is unchanged.
- Do not add the sixteenth-ranked asset after a mid-month cessation.
- Do not rewrite historical ranks or membership.
- Do not mutate a registry before policy adoption.
- Do not treat a lifecycle announcement as canonical data override authority.

## B5: Independent Review And Future Adoption Sequence

1. Independently review this proposed ADR-0014 draft.
2. Record an approve or reject verdict without implementation.
3. If approved, open a separate policy-adoption PR.
4. Implement the generic V4 contract and lifecycle-boundary machinery.
5. Pass deterministic fixtures and fault-injection tests.
6. Create and hash-bind the versioned lifecycle resolution registry.
7. Run the fixed-range cold, warm-cache and worker-variant rebuilds.
8. Record truthful PASS or blocked machine evidence.
9. Require V4 requalification PASS before U-03F.
10. Require U-03F PASS and separate authorization before U-04.

## B6: Draft Authorization Matrix

- Policy adopted: false
- Policy implemented: false
- Contract modified: false
- Registry modified: false
- V3/V4 requalification run: false
- U-03F: false
- U-04: false
- Hypothesis preregistration: false
- Strategy code: false
- Event scan: false
- Returns/backtesting: false
- OOS: false
- API/trading: false
- M2: false

This Draft proposes reviewable policy text only. It is not canonical runtime
authority and must not be parsed as a registry, contract or qualification input.
