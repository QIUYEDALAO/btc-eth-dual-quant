# ADR-0013 Independent Review

- Verdict: `approve_with_required_changes`
- Policy adopted: no
- Reviewed main: `7477c34a403cdbdcf0a7dcc36c4646d32e6d5b83`
- Reviewed PR #74 head: `8dc9ee034fdd172147485f7718117f8a76713cdf`
- ADR evidence commit: `4a95a28142d13aa2f03f271baf660ae95ba67e78`
- ADR draft SHA256: `c285a6cfea04c127ca17a537d9c97d4a8931400c3aefe0c2c7c19654e2bcecfc`
- PR #73 adjudication evidence: `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`

## Executive Decision

The general policy direction is defensible: exact raw duplicates may be collapsed only in a derived canonical layer, and an invalid monthly row may use a checksum-verified daily correction only when independent frozen official evidence agrees. The current Draft is not adoption-ready because it does not yet freeze the resolution registry, complete-key processing order, field semantics, quarantine accounting, first comparison range, hash bindings, or governance SHA meanings.

ADR-0013 therefore remains proposed. V2 remains truthfully blocked. No V3 implementation or rerun is authorized by this review.

## Review Questions

| ID | Topic | Assessment | Finding | Required change |
| --- | --- | --- | --- | --- |
| Q01 | Exact duplicate collapse is information-lossless | `approve_with_required_changes` | Canonical collapse can be lossless only when every raw row, line number, multiplicity and hash remains immutable provenance. | Freeze the raw-preservation and canonical-collapse manifest contract in A4/A7. |
| Q02 | Raw multiplicity is permanently retained | `approve_with_required_changes` | The draft states retention but does not define a machine schema that proves all raw members remain present. | Bind multiplicity, all raw-row hashes and retained canonical hash in A4. |
| Q03 | Invalid monthly to daily replacement has sufficient official evidence | `approve_with_required_changes` | The five BTT rows have checksum-verified daily ZIP evidence and two agreeing public REST comparators, but runtime use must not depend on mutable REST. | Freeze comparator payloads and row evidence in the A1 registry and enforce A5 candidate qualification. |
| Q04 | REST remains corroboration | `approve_with_required_changes` | The draft correctly rejects REST as primary history. | Make frozen REST evidence registry-only and prohibit live REST adoption during qualification under A1/A6. |
| Q05 | Offline deterministic replay | `approve_with_required_changes` | The draft is not replay-complete because it has no versioned resolution registry or hash binding. | Add A1, A6 and A9 before adoption. |
| Q06 | Live REST drift | `approve_with_required_changes` | The evidence probe is networked and current REST can change; using it during qualification would make results time-dependent. | Qualification must consume only frozen comparator evidence and fail on binding mismatch. |
| Q07 | Conflicting duplicate cannot be misclassified | `approve_with_required_changes` | The classifier distinguishes exact, semantic and conflicting groups, but the policy must classify the complete key group rather than a selected pair. | Freeze the complete-group rule, including two-identical-plus-one-conflicting, in A2/A4. |
| Q08 | Collapse cannot hide a later conflict | `approve_with_required_changes` | Collapsing before complete-key grouping can hide a third differing row. | Group all raw rows before any collapse and block any heterogeneous group under A2. |
| Q09 | No source-order or thread-order dependency | `approve_with_required_changes` | The proposed result is deterministic in principle, but the exact processing order and order-independent hashes are not specified. | Freeze A2 and require cold/warm/worker equality in the first V3 rerun. |
| Q10 | No asset or date special cases | `approve_with_required_changes` | The proposal is asset- and time-neutral and rejects special cases. | V3 must enforce registry-driven generic resolution and static fault tests under A6. |
| Q11 | Membership rules remain unchanged | `pass` | Top-15, prior-90-day median, 365-day history, UTC activation and tie-break are explicitly unchanged. | None |
| Q12 | No outcome dependence | `pass` | The policy uses source validity and frozen provenance, not membership or strategy outcomes. | None |
| Q13 | Fail-closed behavior | `approve_with_required_changes` | The draft intends fail-closed behavior but an unknown conflict could still match a broad rule without a registry. | Require exact conflict/source/evidence bindings and blocked_pending_adjudication in A6. |
| Q14 | New schemas are required | `approve_with_required_changes` | V2 cannot represent approved canonical source resolutions without changing authority semantics. | Create V3 contract, resolution registry, canonicalization and manifest schemas bound by A9. |
| Q15 | Future U-03F auditability | `approve_with_required_changes` | Independent audit is feasible if raw and canonical quarantines, resolution IDs, source hashes and deterministic manifests are separately exposed. | Implement A7/A9; U-03F remains unauthorized until a truthful V3 qualification pass. |

## Mandatory Changes Before Adoption

- **A1 Frozen comparator evidence**: Create a versioned hash-bound resolution registry; qualification must not query live REST to adopt a row.
- **A2 Fixed processing order**: Freeze ZIP/schema verification, raw retention, full-key grouping, duplicate classification, candidate validation, registry resolution, provenance, merge, eligibility and panel order.
- **A3 Canonical key and 12-field semantics**: Freeze symbol/interval/open_time UTC key, exact field names/types, Decimal equality and the equality role of ignore.
- **A4 Complete duplicate-group rules**: Collapse only complete groups whose every raw 12-field string is identical; preserve all members; block semantic, conflicting and parser-created groups.
- **A5 Daily correction candidate qualification**: Require checksum/schema/uniqueness/validity, complete duplicate processing, two frozen REST matches, monthly equality except invalid fields and no unresolved conflict.
- **A6 Fail-closed resolution registry**: Resolve only exact registered conflict/source/evidence hashes under an adopted V3 contract; every unknown conflict becomes blocked_pending_adjudication.
- **A7 Two quarantine layers**: Separate raw_row_quarantine from research_panel_quarantine and report duplicate collapses, monthly quarantine, admitted corrections, unresolved conflicts, blocked months and zero synthetic fills.
- **A8 Fixed first V3 range**: Freeze the first V3 public comparison to 2020-01-01 through 2026-06; later accrual is a separate task.
- **A9 Contract hash bindings**: Bind eligibility registry, conflict policy, resolution registry, adjudication evidence/schema, source/canonical schemas and authorization matrix into the V3 contract hash.
- **A10 Governance SHA semantics**: Store current PR head_sha separately from the first frozen evidence_commit and validate that neither field impersonates the other.

## Evidence Conclusions

- BTTUSDT: five negative monthly `base_volume` rows are checksum-bound official monthly/daily conflicts. Daily ZIP rows and two public REST comparators agree; the unsigned-overflow signature is explanatory only and may never generate a value.
- AXSUSDT: the monthly and daily archives each contain two byte-identical rows for one canonical key; REST returns one matching row. Any canonical collapse must retain raw multiplicity and both raw row hashes.
- Existing V2 helpers distinguish byte-identical, semantic-identical, conflicting and parser-created duplicates, but V3 must classify the entire key group before collapse.
- REST can corroborate frozen evidence but cannot become historical authority or a live qualification dependency.
- Top-15, 90-day median quote volume, 365-day history, UTC activation, exclusions and symbol tie-break remain unchanged.

## Authorization

- V3 implementation authorized: no
- U-03E V3 rerun authorized: no
- U-03F authorized: no
- U-04 authorized: no
- Strategy, events, returns, backtesting, OOS, API/trading and M2 authorized: no

Machine evidence hash: `c964048091870270344a9139b7656b3f35cb02925fc725a7c03fa0b2c65dd7d3`
