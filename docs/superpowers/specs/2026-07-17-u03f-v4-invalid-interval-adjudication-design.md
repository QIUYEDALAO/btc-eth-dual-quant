# U-03F V4 Invalid-Interval Adjudication Design

- Design status: approved_by_explicit_follow_on
- Starting main: `3ba411d28563526a5357e3882a1e5759311f6179`
- Current authority: `audit_blocked` / `revalidation_required`
- Production repair, requalification, audit, U-04 and research authorization: none

## Decision

Use a protocol-first, evidence-second adjudication chain. The protocol PR freezes
the exact merged inputs, integer-only row test, cross-member grouping,
determinism requirements and zero downstream authorization. A later evidence PR
may read only the exact frozen local archives and render the row-level result.

Three approaches were considered. Waiting for an upstream archive revision is
safe but creates no reviewable path. Registering the 119 known rows directly as
exceptions would over-fit observed outcomes and bypass policy review. The chosen
approach treats synchronized invalid intervals as a policy question: diagnostics
may recommend a new ADR, but cannot adopt a rule or modify the runtime.

## Known Evidence And Open Question

PR #100 merged a cold-blocked result with 119 unique symbol-month stop reasons.
Read-only exploration shows one physical invalid row per stop reason, grouped at
eight UTC 5m opens. Seven groups cover all 15 active members and one covers 14
of 15. These observations motivate the protocol but are not policy authority.

The open question is whether strict invalid-row exclusion followed by existing
synchronous-gap attribution is an admissible generic policy. The current V4
contract does not answer that question. Therefore a successful diagnostic must
return `new_policy_adr_required`; it may not silently set processing errors to
zero or reuse the existing 80% gap threshold as adoption authority.

## Diagnostic Boundary

The diagnostic reads only archives bound by source-freeze content hash
`c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`.
It verifies canonical key, byte size, SHA256, ZIP CRC and a single CSV member
before parsing. Timestamps remain integers. A physical row is invalid when its
open is off the 300,000ms grid or its close is not exactly open plus 299,999ms.

Every invalid row record includes its archive binding, line number, raw-row hash,
integer open/close values and member-month identity. Rows are grouped only by
exact integer open time and compared with the frozen membership manifest. Daily
archives, REST, downloads, replacements, field repair and synthetic fills are
outside scope.

## Determinism And Failure Handling

The evidence runner must process the same inputs in normal, reverse and
deterministically shuffled order. Canonical machine content from all three orders
must hash identically. A missing, duplicated, unexpected or non-member invalid
row; archive/hash drift; float timestamp path; or traversal mismatch produces
`blocked_evidence_mismatch` and stops.

The Markdown report is an exact render of machine evidence. Any source or report
binding drift fails closed. Historical PR #89, #95 and #100 evidence remains
immutable.

## Dependency Chain

1. Merge the protocol PR after local and GitHub validation.
2. Run and merge one deterministic, evidence-only diagnostic PR.
3. If the evidence is exact and synchronous, create a separate Draft policy ADR.
4. Obtain an independent policy review before conditional adoption.
5. Only an adopted policy may authorize a separate runtime implementation.
6. Require exact-head implementation review with zero critical/high findings.
7. Run the fixed-range requalification; any blocker stops before a new audit.
8. Run a new independent audit only after a merged requalification pass.
9. Even an audit pass requires separate governance closeout and never auto-enters U-04.

## Verification

Protocol tests reject changed hashes, altered source counts, weakened synchronous
thresholds, removed traversal orders, enabled exception registries, network or
replacement access, production changes, and every downstream authorization.
The protocol checker also revalidates all immutable merged input files.

This task produces no production implementation, public-data rerun, strategy,
return, OOS access, API/trading behavior, `execution/live`, M2 or U-04 authority.
