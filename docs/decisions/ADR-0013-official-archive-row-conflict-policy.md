# ADR-0013: Official Archive Row Conflict Policy

- Status: Proposed draft; not adopted
- Date: 2026-07-15
- Scope: Binance public spot kline monthly/daily archives used by liquid-universe qualification
- Depends on: ADR-0011, ADR-0012, PR #73 adjudication evidence
- Proposed successor contract: `LIQUID-SPOT-USDT-TOP15-V3`

## Context

ADR-0012 correctly makes the V2 qualification contract fail closed on every
invalid or duplicated official row. The U-03E public run then found three
checksum-verified blockers that are not project parser defects and have not
been corrected by archive republication:

- BTTUSDT 2019-01 monthly 1d contains one negative `base_volume` row.
- BTTUSDT 2019-02 monthly 1d contains four negative `base_volume` rows.
- AXSUSDT 2026-02 monthly and daily 1d each contain two byte-identical rows for
  2026-02-10.

The bound machine evidence is
`reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json`
with content hash
`8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`.
The current official archive checksums are unchanged. For the BTT rows,
official daily ZIPs and both public REST hosts agree on positive rows while all
other authoritative fields match the monthly rows. The volume delta has an
unsigned 64-bit, eight-decimal overflow signature, but that signature is
explanatory evidence only. For AXS, both public REST hosts return one row that
matches the byte-identical archive rows.

V2 gives monthly archives primary authority, allows daily archives to fill
only missing dates, and never permits REST to overwrite an archive. It also
does not permit duplicate collapse. Therefore V2 cannot admit these rows
without a policy change.

## Draft Decision

This ADR proposes a general kline-row conflict policy for independent review.
It is asset-neutral, time-neutral, deterministic, checksum-bound, and
fail-closed. This document does **not** adopt the policy, modify V2, authorize a
rerun, or grant any research permission.

### Covered Data

The proposal applies to official Binance spot kline monthly and daily archives
at every interval consumed by liquid-universe qualification, including 1d
ranking rows and 5m qualified-panel rows. Derived 1h rows inherit the resulting
canonical 5m provenance. It does not apply to futures, funding, trades,
orderbooks, account data, or private endpoints without another ADR.

### Row Validity

A source row is structurally invalid when any of these conditions holds:

- the schema is not the expected 12-column kline schema;
- timestamps are invalid, off-grid, or inconsistent with the archive scope;
- OHLC ordering is illegal;
- any numeric field is non-finite;
- base volume, quote volume, taker-buy base volume, or taker-buy quote volume is
  negative;
- trade count is negative or non-integral.

An invalid value must never be replaced with zero, absolute-valued, inferred from another field, dropped silently, or repaired with an asset/date special case.

### Duplicate Definitions

- `byte_identical_duplicate`: same normalized timestamp and identical raw
  12-field CSV values.
- `semantic_identical_duplicate`: same normalized timestamp and equal parsed
  authoritative values, but raw formatting differs.
- `conflicting_duplicate`: same normalized timestamp with any different parsed
  authoritative value.
- `parser_created_duplicate`: distinct raw timestamps collide only after an
  incorrect conversion or merge.

The draft permits collapse only for `byte_identical_duplicate`, and only in a
derived canonical layer after the verified raw archive is retained unchanged.
The evidence manifest must record archive checksum, raw row hashes, line
numbers, multiplicity, canonical retained-row hash, and the collapse decision.
This is not `drop_duplicates`: the duplicate remains visible in quarantine and
provenance. Semantic-identical and conflicting duplicates remain blocked.
Parser-created duplicates require a general parser fix and a same-contract
fault-tested rebuild, not this policy.

### Authority And Invalid Monthly Rows

The proposed authority order is:

1. A currently published monthly ZIP with matching official checksum is the
   default primary source when its row is valid and unique.
2. A currently published daily ZIP with matching official checksum may become
   a correction candidate only when the monthly row is structurally invalid.
3. Both official public REST comparators must independently return exactly one
   row for the timestamp and agree with the daily row in every authoritative
   field. REST is corroboration and never a standalone replacement authority.
4. A source-owner statement is provenance only. It cannot automatically
   override row evidence or the active contract.

An invalid monthly row may be quarantined and replaced in the derived canonical
layer by the daily row only if all of the following hold:

- monthly and daily archives and checksums are available and valid;
- the monthly timestamp has no valid alternative row in the same archive;
- daily ZIP and both REST comparators agree exactly in all authoritative fields;
- monthly and daily rows agree in every field except the structurally invalid
  field or fields;
- the current monthly checksum has not changed during the evidence run;
- the manifest binds every source URL, checksum, payload hash, row hash, line
  number and field-level difference;
- no data value is derived algebraically from the invalid monthly value.

If any condition is absent, unavailable, contradictory, or non-deterministic,
qualification remains blocked. A later corrected monthly archive takes
precedence only after its new checksum and full row contents are frozen and the
entire qualification is rebuilt from scratch.

### Isolation And Blocking

An exact duplicate or invalid row cannot be ignored because the asset misses
the final Top-15. Source qualification occurs before membership is trusted.
Conflicting duplicates, semantic-only duplicates, unsupported schema changes,
missing comparison evidence, REST disagreement, and any unclassified source
revision are blocking. No replacement member, interpolation, synthetic bar,
or manual symbol exclusion is allowed.

## Historical Reconstruction Impact

If adopted in a future task, the policy would change canonical source handling
and therefore requires a new contract and manifest schema version. The project
must rebuild source, eligibility, membership, quarantine, qualified-panel and
summary manifests for the full 2020-01 through latest-complete-month range.
Cold, warm-cache, and worker-variant builds must match exactly.

The rerun must regenerate both V2/V3 and historical V1/V3 diagnostic diffs.
No membership outcome is assumed by this ADR. Top 15, prior 90 days, minimum
365 days, category exclusions, UTC activation, and deterministic tie-break
remain unchanged.

## Alternatives Rejected

- Keep V2 permanently blocked: safe but leaves checksum-verified official
  defects unusable even when independent official evidence is exact.
- Prefer daily over monthly globally: weakens the frozen primary authority and
  may introduce a different source revision without proof.
- Use REST as primary history: not archive-replayable and may vary over time.
- Take absolute values or infer overflow corrections: manufactures data and is
  prohibited.
- Silently keep one duplicate: destroys multiplicity evidence and is
  prohibited.
- Exclude the affected symbols or dates: creates a hidden outcome-dependent
  universe rule and is prohibited.

## Adoption Gate

Before this proposal can become active, a separate explicit review must:

1. approve or reject the general policy;
2. assign a new contract/schema version and canonical hash;
3. implement generic code without symbol/date conditions;
4. add fault fixtures for all duplicate, invalid-row and evidence-availability
   cases;
5. rerun U-03E from scratch with cold, warm and worker variants;
6. merge truthful requalification evidence;
7. run U-03F only in a later independent task if requalification passes.

Merging or reviewing this Draft ADR alone does not satisfy any adoption Gate.

## Authorization

- V2 contract modified: no
- Policy adopted: no
- U-03E rerun authorized: no
- U-03F authorized: no
- U-04 authorized: no
- Hypothesis preregistration: no
- Strategy code: no
- Event scan: no
- Returns/backtesting: no
- OOS opened: no
- API/trading: no
- M2: no
