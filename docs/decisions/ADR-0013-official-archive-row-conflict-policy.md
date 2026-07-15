# ADR-0013: Official Archive Row Conflict Policy

- Status: Accepted for V3 implementation and U-03E requalification only
- Date: 2026-07-15
- Scope: Binance public spot kline monthly/daily archives used by liquid-universe qualification
- Depends on: ADR-0011, ADR-0012, PR #73 adjudication evidence, PR #75 independent review
- Successor contract: `LIQUID-SPOT-USDT-TOP15-V3`
- Independent review verdict: `approve_with_required_changes`
- Independent review evidence hash: `c964048091870270344a9139b7656b3f35cb02925fc725a7c03fa0b2c65dd7d3`
- Adjudication evidence hash: `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`

## Context And Decision

V2 correctly blocks five BTTUSDT 1d rows with negative monthly
`base_volume` and the byte-identical AXSUSDT 2026-02-10 duplicate. PR #73
proved that the archives are checksum-valid, that the BTT daily rows agree
with two public REST comparators, and that the AXS monthly/daily duplicates are
byte-identical. The unsigned-overflow signature is explanatory only and may
never generate a replacement value.

This ADR adopts a generic, asset-neutral, time-neutral, deterministic,
checksum-bound and fail-closed policy for a new V3 contract. It does not alter
V2 historical evidence. It authorizes only generic V3 implementation, a
versioned conflict-resolution registry, and a fixed-range U-03E V3 public
requalification. It does not itself resolve a row or assert a qualification
pass.

## Covered Data

The policy covers official Binance spot kline monthly and daily archives at
intervals consumed by liquid-universe qualification. It does not apply to
futures, funding, trades, orderbooks, account data or private endpoints.

## A1: Frozen Comparator Evidence And Resolution Registry

V3 must use `config/liquid_spot_source_conflict_resolutions_v3.json`. Every
resolution must be versioned and bound by a canonical hash. Each entry contains:

- `resolution_id`, `conflict_id`, symbol, interval and UTC open timestamp;
- conflict class;
- monthly archive key, checksum and raw-row hash;
- daily archive key, checksum and raw-row hash;
- both REST endpoint identities, frozen normalized rows and payload hashes;
- adjudication evidence hash;
- approved action, policy version and effective contract version.

Qualification must never query live REST and immediately adopt the response.
REST is frozen corroboration only, not historical primary authority. An absent entry or any changed source/evidence hash is `blocked_pending_adjudication`.

## A2: Normative Processing Order

V3 must execute this order without reordering:

1. verify ZIP bytes, official checksum, CRC and CSV schema;
2. retain every raw row and line number;
3. group all rows by the canonical row key;
4. classify the complete duplicate group;
5. collapse only a group whose every member is byte-identical;
6. block the complete key if any member differs;
7. structurally validate the single canonical candidate;
8. for an invalid monthly candidate, query only the approved offline registry;
9. validate the daily correction candidate;
10. emit one canonical row with complete provenance and `resolution_id`;
11. execute monthly-primary / daily-fill-only merge;
12. build eligibility, membership and qualified panel.

No earlier collapse, merge, ranking or membership result may hide a conflict.

## A3: Canonical Key And Field Semantics

The canonical row key is `(symbol, interval, open_time UTC)`. The raw CSV has
exactly these 12 fields in order:

1. `open_time`
2. `open`
3. `high`
4. `low`
5. `close`
6. `base_volume`
7. `close_time`
8. `quote_volume`
9. `trade_count`
10. `taker_buy_base_volume`
11. `taker_buy_quote_volume`
12. `ignore`

Timestamps are unsigned integer epochs normalized to UTC milliseconds for
semantic comparison. Prices and volumes are finite `Decimal` values.
`trade_count` is a non-negative integer. `ignore` is an authoritative equality field and is compared as its exact raw string; differing values conflict.

`byte_identical_duplicate` means all original 12 strings match exactly.
`semantic_identical_duplicate` means timestamps, Decimals, integer trade count
and `ignore` normalize equal while raw formatting differs. `conflicting_duplicate`
means any authoritative normalized field differs. Correction comparison uses
parsed canonical equality, never textual decimal formatting.

A row is invalid for malformed schema/timestamps, wrong grid/scope, illegal
OHLC ordering, non-finite numeric values, negative volume fields, or negative
or non-integral trade count. No value may be absolute-valued, zeroed,
algebraically inferred, silently dropped, or repaired by symbol/date logic.

## A4: Complete Duplicate Groups

- The complete canonical-key group is classified before any collapse.
- Multiplicity of at least two is collapsible only when every original 12-field
  row is byte-identical.
- Canonical output contains one row; raw storage retains every row.
- Provenance records multiplicity, line numbers, every raw-row hash and the
  retained canonical hash.
- Two identical rows plus one different row block the entire key.
- Semantic-identical and conflicting duplicates remain blocked.
- Parser-created duplicates require a parser fix and cannot use this policy.
- Generic `drop_duplicates`, keep-first and keep-last behavior is prohibited.

## A5: Daily Correction Candidate Qualification

A daily correction is eligible only when all conditions pass:

- its official ZIP checksum, CRC and 12-column schema are valid;
- its canonical timestamp is unique, or its complete group is an allowed
  byte-identical duplicate processed by the same pipeline;
- timestamps, OHLCV, trade count and all structural fields are legal;
- it equals both frozen official REST normalized rows by parsed canonical
  equality;
- it equals the invalid monthly row in every field except the field or fields
  whose invalidity triggered resolution;
- no other conflict or missing evidence exists.

Semantic/conflicting duplicates, invalid daily values, a missing comparator or
one REST disagreement block the candidate. Canonical values come only from the
checksum-verified daily row, never from an overflow formula.

## A6: Fail-Closed Resolution

Canonical resolution is permitted only when ADR-0013 is accepted, the V3
contract hash and registry hash match, the `conflict_id` is registered, every
row/source checksum matches, and frozen evidence hashes match. A broad policy
match alone is insufficient. Every unknown or changed conflict is
`blocked_pending_adjudication`; the runtime cannot extend the registry.

## A7: Quarantine And Counters

V3 keeps two separate scopes:

- `raw_row_quarantine`: retained invalid or duplicate source rows that do not
  directly enter the canonical layer;
- `research_panel_quarantine`: a full window or symbol-month excluded because
  a conflict/gap remains unresolved.

An approved replacement is `canonical_source_resolution`, not a synthetic
fill. Reports and manifests must expose `duplicate_collapses`,
`monthly_rows_quarantined`, `daily_corrections_admitted`,
`unresolved_row_conflicts`, `blocked_symbol_months`, and
`synthetic_fills = 0`.

## A8: Fixed First V3 Range

The first V3 public run is fixed to `2020-01-01` through `2026-06` inclusive.
It may not add later months. Data accrual requires a separate post-audit task.

## A9: Contract Hash Bindings

The V3 contract hash must bind all of the following:

- asset eligibility registry hash;
- conflict policy hash;
- conflict resolution registry hash;
- adjudication evidence hash and schema;
- source manifest schema;
- canonicalization schema;
- authorization matrix.

Changing any binding changes the V3 contract hash. Cold, warm-cache and
worker-variant builds must produce byte-identical and hash-identical source,
resolution, eligibility, membership, quarantine, panel, summary and report
artifacts.

## A10: Governance SHA Semantics

`evidence_commit` is the first commit that froze the reviewed ADR content:
`4a95a28142d13aa2f03f271baf660ae95ba67e78`. The independent review examined
PR #74 at `reviewed_head_sha = 8dc9ee034fdd172147485f7718117f8a76713cdf`.

`head_sha` means the current PR head obtained from Git/GitHub at validation
time. It is runtime metadata and must never be populated with
`evidence_commit` or the old `reviewed_head_sha`. A committed document cannot
self-contain its own final commit identity; the state checker must resolve and
report the current head externally while keeping the two immutable evidence
fields distinct.

## Unchanged Universe Policy

ADR-0011 membership remains unchanged: monthly Top 15, prior 90 complete UTC days median quote volume, 365 complete history days, UTC month activation,
category exclusions and ascending-symbol tie-break. No excluded symbol,
replacement member, result-dependent rule or strategy outcome may influence
source resolution.

## Required V3 Evidence

V3 must preserve V1 and blocked V2 evidence, use only registry-driven generic
code, add duplicate/correction/fault fixtures, and run the fixed range from
scratch. A V3 qualification failure remains truthful blocked evidence. U-03F
may be authorized only by a later governance closeout after a V3 pass; it is
not run by this ADR.

## Alternatives Rejected

- Global daily-over-monthly precedence.
- Live REST as primary or runtime repair authority.
- Absolute-value, zero, inferred overflow or synthetic values.
- Silent deduplication, keep-first/last or symbol/date conditions.
- Excluding BTT/AXS, adding replacement members or changing ranking rules.

## Authorization

- V2 contract modified: no
- Policy adopted: yes, for V3 implementation and U-03E requalification only
- V3 contract implementation: true
- Conflict resolution registry implementation: true
- U-03E V3 rerun: true
- U-03F: false
- U-04: false
- Hypothesis preregistration: false
- Strategy code: false
- Event scan: false
- Returns/backtesting: false
- OOS: false
- API/trading: false
- M2: false
