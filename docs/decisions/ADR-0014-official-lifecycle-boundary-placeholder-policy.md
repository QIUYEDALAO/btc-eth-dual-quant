# ADR-0014: Lifecycle Availability Event Policy

- Status: Accepted for V4 implementation and fixed-range public requalification only
- Date: 2026-07-15
- Adoption date: 2026-07-16
- Scope: official Binance spot lifecycle availability evidence
- Prior review: PR #82, `approve_with_required_changes`
- Prior review content hash: `3d7e089e3322970a8602dda8a4c4c82d01f5604276688567754d77319c932a15`
- Adoption evidence: PR #84, `approve`, merge `5c839cdf8b825e18546a5bdbfe3fd9ca1f2f1328`
- Adoption evidence content hash: `d2b0dfa7fdd9c8cc5bef2c716600f6e79ec6272651fa067dc23a3d0915271bc7`
- KLAY adjudication evidence hash: `6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a`
- Adopted future contract: `LIQUID-SPOT-USDT-TOP15-V4`

This adoption preserves the independently reviewed MC-01 through MC-11
semantics exactly. The docs-only machine semantics remain frozen in:

- `docs/decisions/proposals/adr0014_lifecycle_policy_model.json`
- `docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json`
- `docs/decisions/proposals/adr0014_mc_conformance.json`

Those files remain review evidence, not runtime inputs or registry entries.

## Adoption Scope

ADR-0014 is adopted only to authorize implementation of the generic V4
lifecycle policy, its evidence-bound lifecycle event registry, fixture and
fault-injection validation, and one fixed-range public requalification for
`2020-01` through `2026-06`. Implementation must pass an independent review
before any public requalification begins.

This adoption does not authorize U-03F, U-04, hypothesis or strategy work,
event or signal research, returns, backtesting, OOS access, API/trading,
`execution/live`, or M2.

## MC-01: Versioned Lifecycle Availability Event

The policy object is a `versioned_lifecycle_availability_event`, not a rule for
one malformed row. It binds event identity, exchange, market, symbol, economic
asset identity, event type, knowledge and effective times, availability
boundary, affected interval and raw-row set, every affected raw-row hash,
official evidence, similar-scope scan, policy version, and adjudication hash.

It distinguishes cessation-day partial rows, normal-duration post-cessation
placeholders, malformed post-cessation placeholders, legitimate zero-volume
rows, valid pre-cessation rows, and unresolved rows. The frozen KLAY example
therefore includes all three official daily rows:

- 2024-10-28: cessation-day partial row;
- 2024-10-29: normal-duration flat zero-volume post-cessation placeholder;
- 2024-10-30: close-before-open post-cessation malformed placeholder.

No post-cessation row contributes to complete history, the 90-day ranking
window, or the 365-day eligibility window. A new post-cessation row or changed
affected-row hash fails closed and requires a new adjudication. The generic
event model prohibits production symbol/date exceptions.

## MC-02: Availability Epochs And Expected Grid

`symbol_availability_epochs` have independent epoch ID, identity version,
inclusive start, exclusive end, knowledge and effective times, resolution
reference, and evidence hashes. Qualification order is fixed:

1. validate raw data;
2. load and validate lifecycle policy;
3. load and validate event registry;
4. build availability epochs;
5. apply availability mask;
6. build expected grid;
7. detect gaps;
8. build complete timeframes;
9. build complete-day mask;
10. rank and evaluate eligibility.

The expected grid is never built before the availability mask. For 5m, both
open and actual close must precede `availability_end_exclusive`; a crossing bar
is partial or blocked and is never truncated or rewritten. A complete 1h bar
requires 12 contiguous complete 5m bars in one epoch. A complete UTC day must
fit wholly inside one epoch with complete legal coverage. A partial cessation
day remains raw evidence but cannot enter complete-day windows.

The model separately records `raw_row_quarantine`,
`lifecycle_event_quarantine`, `research_panel_availability_mask`, and
`unresolved_data_quarantine`.

## MC-03: Point-In-Time Knowledge

The model separates `known_at`, `publication_time`, `effective_at`,
`archive_first_available_at`, `archive_revision_at`, `adjudication_at`, and
`resolution_approved_at`. Physical market availability follows `effective_at`;
research knowledge cannot precede `known_at`. Retrospective reconstruction may
confirm a physical boundary only when it discloses whether that evidence was
known then. When `known_at > effective_at`, evidence is marked
`retrospective_evidence_lag` and no feature may use the lifecycle label before
`known_at`.

Later announcements or adjudications never rewrite month-start membership.
Mid-month events alter only timestamped active availability. Later successor
performance cannot modify old membership.

## MC-04: Membership Versus Active Universe

`monthly_membership` is frozen at month start. `timestamped_active_universe`
is independently masked by availability epochs. Outputs disclose both
`membership_count` and `active_count`, using the states `active_complete`,
`active_partial`, `lifecycle_terminated`, `data_quarantined`,
`unresolved_blocked`, and `not_yet_available`.

Lifecycle termination means physical unavailability. It is not missing data,
zero return, cash, stale price, or automatic replacement. Active count may
fall mid-month while membership count stays fixed. The sixteenth-ranked asset
is not inserted.

## MC-05: Data Policy Non-Targets

This data policy defines no exit price, liquidation, settlement, token
conversion, swap ratio, stale fill, stale-price forward-fill,
cross-cessation return, minus-100-percent return, zero return, cash treatment,
position migration, or forced exit.

If a future strategy could hold an asset through a lifecycle event, U-04 may
design an economic hypothesis, but a fixed-rule contract, Freqtrade backtest,
or return validation cannot begin until an independent delisting/execution
policy review passes. This is a machine-checked downstream Gate.

## MC-06: Successor Metadata

The sole field is `announced_successor_symbol`, with `provenance_only`
authority. It asserts no economic equivalence, price continuity, conversion,
or automatic swap. A successor inherits no listing age, 90/365-day history,
volume, rank, or membership and cannot fill the old symbol's gap. It must
qualify on its own point-in-time data. KLAY/KAIA history splice requires a
separate ADR.

## MC-07: Policy And Event Registry Separation

The future lifecycle policy contract owns generic rules. A separate lifecycle
event resolution registry owns evidence-bound event instances. Each registry
entry binds resolution, venue, pair, symbol, asset identity, event and epoch,
availability boundaries, knowledge/effective/last-valid times, expected-grid
end, all announcement/archive/raw/intraday/scope hashes, policy version,
adjudication evidence, non-authoritative successor metadata, and authorization
status.

Unregistered events, new post-event rows, checksum or evidence changes,
cessation-time changes, overlaps, conflicts, registry-hash changes, and event
type changes all fail closed. Production symbol/date branches are forbidden.

## MC-08: Multiple Epochs And Ticker Reuse

The model supports relisting, reactivation, migration, ticker reuse, and the
same pair string representing different economic assets. Epochs have distinct
IDs and identity versions and cannot overlap. A new epoch inherits no
365-day history, 90-day ranking window, volume, rank, price continuity, or
membership from an old epoch.

## MC-09: Evidence Sufficiency

Only jointly evidenced permanent cessation, delisting, and migration cessation
are in scope. Temporary suspension, maintenance, and unknown events never
become permanent lifecycle events automatically. Archive absence and missing
intraday archives are not proof. An announcement is provenance, not canonical
override authority.

Resolution jointly requires official lifecycle evidence, archive integrity,
intraday interval evidence, event time, and a frozen similar-scope scan. That
scan binds scope, data authority, intervals, archive set, algorithm, and hash.
Trading observed after announced cessation blocks resolution.

## MC-10: Future V4 Machine Authority

A future V4 must emit canonical, hash-bound `lifecycle_policy_manifest`,
`lifecycle_resolution_registry`, `symbol_availability_manifest`,
`active_universe_manifest`, `complete_day_mask`, `expected_grid_manifest`,
`raw_row_quarantine_manifest`, `lifecycle_event_quarantine_manifest`,
`qualification_summary`, and `V3_V4_diff`. Markdown is never an input.

V3 remains active historical authority until V4 passes. A blocked V4 never
activates. Cold, warm-cache, and worker results must match exactly, and U-03F
must independently recompute the evidence. The summary discloses lifecycle
events, terminated symbol-months, partial days, quarantined rows, membership
and active counts, unresolved rows, overlapping epochs, synthetic fills, and
replacement members. PASS requires zero synthetic fills, replacement members,
overlapping epochs, and unresolved lifecycle rows.

## MC-11: Fault-Injection Contract

The docs-only fault matrix freezes unique test IDs, preconditions, mutations,
expected results and states, and blocking status for every boundary, row class,
source conflict, event type, epoch/reuse case, evidence revision, membership
case, gap case, and prohibited execution interpretation required by MC-11.
The conformance model maps every MC to acceptance criteria and fault IDs.

## Forbidden Shortcuts

- No raw-row deletion, timestamp repair, synthetic candle, REST replacement,
  stale-price fill, implicit settlement, or cross-boundary return.
- No KLAY/KAIA splice, successor inheritance, sixteenth-ranked replacement, or
  retrospective membership rewrite.
- No symbol/date production branch or Markdown-driven runtime rule.
- No event or registry mutation before policy adoption and independent review.

## Adoption Authorization Matrix

- Lifecycle policy adopted: true
- V4 contract implementation: true
- V4 lifecycle policy implementation: true
- V4 lifecycle event registry implementation: true
- Fixture validation: true
- Fault injection: true
- Fixed-range V4 public requalification: true
- U-03F: false
- U-04: false
- Hypothesis preregistration: false
- Strategy code: false
- Event scan: false
- Signals: false
- Returns: false
- Backtesting: false
- OOS: false
- API/trading: false
- execution/live: false
- M2: false

## Adoption Dependency Order

1. A: merge this conditional adoption.
2. B: implement V4 without running public requalification.
3. C: independently review the exact V4 implementation, then merge it only on
   an approve verdict with an unchanged target head.
4. D: run the fixed `2020-01` through `2026-06` cold/warm/worker public
   requalification; stop truthfully after cold if an unknown conflict appears.
5. E: close governance after the truthful V4 outcome.

Skipping or reordering these dependencies is prohibited. A V4 pass still does
not authorize U-03F; U-03F requires a separate future task after closeout.
