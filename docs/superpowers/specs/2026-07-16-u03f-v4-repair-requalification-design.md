# U-03F V4 Repair And Requalification Design

- Design status: approved_by_explicit_delegation
- Starting main: `513d321b69750d6c8bb47bddbf006d4caac04828`
- Current authority: `audit_blocked` / `revalidation_required`
- Research, U-04, strategy, returns, OOS, API/trading and M2 authorization: none

## Decision

Use a versioned repair protocol and a six-PR dependency chain: protocol freeze,
implementation, exact-head independent review, fixed-range public
requalification, new independent audit, and governance closeout. Historical PR
#89 and #95 evidence is immutable. New evidence receives new hashes and may not
overwrite or reinterpret prior results.

Two alternatives were rejected. Editing the historical V4 evidence would erase
the audit trail. Treating the independent auditor output as the new production
authority would collapse production/audit independence and would bypass the
required public requalification.

## Repair Boundary

The repair is limited to integer UTC conversion, strict 5m row interval
validation, propagation of invalid-row effects through grid/source/panel/summary
artifacts, and deterministic qualification-report/run-manifest binding. It may
not change universe ranking, lifecycle policy, row-conflict policy, gap policy,
the fixed public range, source archives, or validation thresholds.

The implementation PR does not run the public qualification. Its exact head is
reviewed independently and may merge only after an `approve` verdict with zero
critical and zero high findings.

## Data Flow And Failure Handling

Frozen archive bytes enter the repaired production parser. Integer-only time
normalization occurs before every 5m validity decision. Invalid rows are
retained in source provenance but excluded from valid-grid and aggregation
counts; their effects propagate deterministically into quarantine and blocking
evidence. The final report is rendered before the run manifest is finalized,
and the manifest binds the exact report bytes.

Every mismatch fails closed. Cold failure stops warm and worker builds. A
source-freeze drift stops without downloading a replacement. A changed exact
implementation head invalidates its review. Any new audit mismatch, critical
finding, high finding or algorithm-hash drift keeps V4 blocked.

## Verification

Fault tests cover IEEE-754 precision loss, reintroduction of float timestamp
paths, ADAUSDT 2020-02 invalid interval counting, invalid close boundaries,
post-write report drift and run-manifest binding. Requalification must produce
identical cold/warm/worker artifact-set hashes over `2020-01` through `2026-06`
using the original 27,736-archive source freeze. The new independent audit must
produce identical normal/reverse/shuffled identities and 15/15 exact production
manifest comparisons.

Even a passing audit does not authorize U-04. A later explicit task is still
required.
