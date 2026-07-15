# ADR-0014 Independent Policy Review

- Verdict: `approve_with_required_changes`
- Reviewed PR: `#81`
- Reviewed PR head: `cd4a1d8fb53870cdf8a3a683a4942a2c81b58f44`
- Reviewed base: `main@d2d876af192a23ff1879d6a09cb2737c3f12133f`
- ADR blob / content SHA256: `35c492acfb3cbd1af5291ffdd68384429f1d8ce9` / `7350d691e2b7158a9cd985b3e53cf0c504a1147c39791c844d2ad4b4b5ede8a9`
- PR changed-file-list SHA256: `5de2d40f14ab74b905f8a924a3f89acd0e2f10d1350c87665097cbc3bce99315`
- KLAY evidence hash: `6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a`
- Generated UTC: `2026-07-15T12:45:07Z` (excluded from content identity)
- Review content hash: `3d7e089e3322970a8602dda8a4c4c82d01f5604276688567754d77319c932a15`

## Executive Decision

The proposed Draft is safe as a review-only artifact, but it is not adoption-ready. Its row category is tied to the malformed 2024-10-30 record while the same official monthly archive contains a normal-duration, flat, zero-volume 2024-10-29 placeholder after the 2024-10-28T03:00:00Z cessation. The real policy object must therefore be a versioned availability lifecycle event, not a single invalid row.

There are no critical findings, but ten unresolved high findings prevent `approve`. The verdict is `approve_with_required_changes`; all eleven machine-verifiable changes below block adoption. PR #81 must remain Draft and unchanged.

## Frozen Source Observation

- Last real intraday market close: `2024-10-28T02:59:59.999Z`.
- `2024-10-28`: real cessation-day partial row; it is not a complete UTC day.
- `2024-10-29`: flat zero-volume/trade row with normal daily duration, but entirely after cessation.
- `2024-10-30`: flat zero-volume/trade row whose close precedes open and equals cessation minus 1 ms.
- Quarantining only 2024-10-30 would leave a false complete day in ranking and history evidence.

## Severity Summary

| Severity | Count |
| --- | ---: |
| critical | 0 |
| high | 10 |
| medium | 1 |
| low | 0 |
| informational | 1 |

## Review Questions

| ID | Pass | Severity | Question | Finding | Mandatory change |
| --- | --- | --- | --- | --- | --- |
| Q01 | no | `high` | Does the Draft cover the lifecycle event rather than only one malformed row? | The row category is over-fitted. A normal-duration post-cessation placeholder can enter complete-history, 90-day ranking and 365-day eligibility calculations even if the 2024-10-30 row is quarantined. | MC-01 |

Evidence for Q01:
- ADR B1 requires close_time < open_time and therefore selects only the 2024-10-30 malformed row.
- KLAY monthly archive previous_raw_fields/hash fde7b404... records 2024-10-29 as flat, zero volume/trades and normal daily duration after cessation.
- The 2024-10-28 row ends at 2024-10-28T02:59:59.999Z and is a genuine partial lifecycle day.
- Rationale: The policy must bind the availability event and all affected rows, not one blocker signature.

| Q02 | no | `high` | Are availability intervals, timeframe boundaries and expected-grid order uniquely defined? | The Draft permits multiple incompatible 5m/1h/1d implementations and can misclassify post-cessation absence as gaps or partial days as complete days. | MC-02 |

Evidence for Q02:
- ADR B2 says stop expecting bars after cessation but defines no inclusive/exclusive epoch, partial-day mask, cross-boundary rule or grid construction order.
- Rationale: Exact availability_start_inclusive/end_exclusive and pre-grid application are required for deterministic qualification.

| Q03 | no | `high` | Does point-in-time reconstruction separate when evidence was known from when cessation became effective? | The Draft does not prevent future information from altering historical availability before it was public or rewriting month-start membership. | MC-03 |

Evidence for Q03:
- KLAY evidence records publication 2024-10-16 and effective cessation 2024-10-28, but B2 has no known_at/effective_at or retrospective reconstruction semantics.
- Rationale: Knowledge time and market-effective time are distinct facts and must be independently bound.

| Q04 | no | `high` | Are monthly membership and timestamped active universe separate machine concepts? | Downstream research could treat lifecycle termination as missing data, zero return, cash or stale-price continuity. | MC-04 |

Evidence for Q04:
- ADR B2 preserves membership and marks termination but defines neither separate counts nor a complete status vocabulary.
- Rationale: Point-in-time membership is fixed monthly while active availability can change intramonth; both must be explicit.

| Q05 | no | `high` | Does the data policy explicitly avoid defining prices, returns or position settlement? | A future backtest could silently infer a favorable or arbitrary settlement from a data-qualification boundary. | MC-05 |

Evidence for Q05:
- ADR B2 describes availability only, but it does not explicitly prohibit exit price, token conversion, stale fill or cross-cessation return semantics.
- Rationale: Lifecycle data admissibility and held-position execution are separate policies and review Gates.

| Q06 | no | `medium` | Is optional replacement symbol metadata unambiguously non-authoritative? | The current name can be misread as replacement authority even though the prose denies continuity. | MC-06 |

Evidence for Q06:
- B2 calls the field optional replacement symbol while separately denying automatic KLAY/KAIA splice.
- Rationale: Rename it announced_successor_symbol and prohibit inheritance or conversion semantics in schema and tests.

| Q07 | no | `high` | Are lifecycle policy and event resolution records separate and fail closed? | Unknown events, checksum changes, new rows and conflicting registry entries are not uniquely governed. | MC-07 |

Evidence for Q07:
- B3 requests a versioned lifecycle resolution registry but does not define separate policy/event schemas, required fields or change detection.
- Rationale: Generic policy and evidence-bound event instances require separate identities and failure modes.

| Q08 | no | `high` | Can the model represent relisting, reactivation and ticker reuse without history splice? | A single terminal boundary can permanently kill a ticker or incorrectly join a new economic asset to old history. | MC-08 |

Evidence for Q08:
- B2 emits one symbol_availability_boundary and has no epoch identity or later start boundary.
- Rationale: Availability must be a versioned set of non-overlapping epochs, each with independent identity and eligibility history.

| Q09 | no | `high` | Is lifecycle evidence sufficient and generalized beyond the KLAY signature? | The Draft does not distinguish permanent cessation, temporary suspension, maintenance, migration and archive absence, nor freeze scope semantics. | MC-09 |

Evidence for Q09:
- B1 combines KLAY-specific flat/zero/close-boundary features with announcement evidence.
- The scope scan found partial-duration ORN/SCR rows, proving non-full duration alone is not a universal cessation class.
- Missing intraday archives can also be a public-archive gap.
- Rationale: Archive absence is not lifecycle proof; validated lifecycle evidence and interval integrity must agree.

| Q10 | no | `high` | Are future V4 machine artifacts, authority activation and counters complete? | A V4 run could pass without proving active counts, partial-day exclusion, post-cessation quarantine or zero synthetic/replacement artifacts. | MC-10 |

Evidence for Q10:
- B3 mentions contract/registry binding and three rebuilds but omits availability, active-universe, complete-day and expected-grid manifests and required disclosures.
- Rationale: Machine evidence, not Markdown, must close every policy consequence before V4 authority can activate.

| Q11 | no | `high` | Does the Draft freeze adequate boundary and fault-injection tests before adoption? | The policy is not adoption-ready without deterministic tests for boundaries, placeholders, source contradictions, event types, epochs and non-execution behavior. | MC-11 |

Evidence for Q11:
- PR #81 CI has 88 passing static/guard tests, but the Draft tests verify markers and zero authority rather than the full lifecycle state machine.
- Rationale: Passing Draft CI proves scope safety, not complete lifecycle semantics.

| Q12 | yes | `informational` | Does the current Draft safely avoid adoption, implementation and downstream authorization? | The Draft is safely proposed-only and does not mutate runtime authority. | none |

Evidence for Q12:
- ADR B6 keeps every authorization false; PR #81 changes only Draft governance/checker/tests/CI files; all 88 checks passed.
- Rationale: The review can be merged independently while PR #81 remains Draft and unchanged.

## Mandatory Changes Before Adoption

### MC-01 Promote row category to a lifecycle availability event

Replace the close_time<open_time row-only category with a versioned lifecycle event that freezes the affected interval and complete affected-row set. It must distinguish cessation-day partial rows, post-cessation normal-duration placeholders, malformed placeholders and legitimate zero-volume rows. Every newly observed post-cessation row must fail closed until its evidence is bound.

Acceptance:
- The KLAY event binds the 2024-10-28 partial day and both 2024-10-29/30 post-cessation rows by raw hash.
- No post-cessation row can contribute to complete-history, 90-day ranking or 365-day eligibility counts.
- A new post-cessation row or changed affected-row hash blocks qualification.

Required tests:
- normal-duration zero-volume placeholder is excluded
- close-before-open placeholder is excluded
- multiple/new post-cessation placeholders fail closed

Blocks adoption: `yes`

### MC-02 Freeze exact availability and expected-grid semantics

Define symbol_availability_epochs with availability_start_inclusive and availability_end_exclusive. Apply epochs before expected-grid generation. Define legal partial, crossing and post-boundary behavior for 5m, 1h and 1d; incomplete child sets cannot form complete parents. Separate raw-row quarantine, lifecycle-event quarantine and research-panel availability masks.

Acceptance:
- open>=end_exclusive is not expected and never reported as a gap
- a bar crossing end_exclusive is blocked or partial by explicit timeframe rule
- a lifecycle partial UTC day is excluded from complete-day windows while preserved as raw evidence
- pre-boundary gaps continue to block

Required tests:
- UTC-day, 5m, 1h and off-grid boundary fixtures
- 12 complete 5m children required for a complete 1h bar
- partial lifecycle day excluded from 90/365 windows
- post-boundary absence does not become a gap

Blocks adoption: `yes`

### MC-03 Add point-in-time lifecycle knowledge semantics

Bind known_at/publication_time separately from effective_at, archive publication/revision time and resolution approval time. Month-start membership remains immutable; mid-month events alter only active availability. Retrospective evidence unavailable at the historical time must be disclosed and cannot be used as if known earlier.

Acceptance:
- machine event contains known_at and effective_at
- no event influences state before known_at
- month membership and rank are unchanged by later evidence
- retrospective reconstruction status is explicit

Required tests:
- publication after effective time
- late archive revision
- replacement performance cannot rewrite old membership

Blocks adoption: `yes`

### MC-04 Separate membership from active universe

Preserve monthly point-in-time membership and derive timestamped active availability separately. Expose distinct membership_count and active_count plus active_complete, active_partial, lifecycle_terminated, data_quarantined and unresolved_blocked states. A terminated member is not missing data, zero return, cash or a stale-price position.

Acceptance:
- membership does not change mid-month
- active count decreases after cessation without adding rank 16
- status and count fields are separate and machine checked

Required tests:
- member and non-member event fixtures
- active count decline without replacement
- terminated state cannot be coerced to missing/zero/cash/stale

Blocks adoption: `yes`

### MC-05 Keep execution and returns outside the data policy

State that availability does not define exit, liquidation, settlement, conversion, stale fill, cross-cessation return, -100%, zero return or cash treatment. U-04 may design a hypothesis, but fixed-rule or backtest work is blocked by a separately reviewed delisting/execution policy whenever a lifecycle event can intersect a position.

Acceptance:
- ADR contains an explicit non-target section
- authorization matrix keeps returns and execution false
- downstream Gate is machine represented

Required tests:
- no stale-price forward-fill
- no cross-boundary return
- no implicit -100%, zero or cash settlement

Blocks adoption: `yes`

### MC-06 Make successor metadata non-authoritative

Rename replacement symbol to announced_successor_symbol and define it as provenance only. It grants no continuity, conversion, equivalence, listing age, volume, rank or complete-history inheritance. Any KLAY/KAIA splice requires a separate ADR; the successor must independently satisfy 365/90-day point-in-time rules.

Acceptance:
- field name and schema state provenance_only
- successor cannot fill the old symbol gap or inherit metrics
- economic continuity is separately unauthorized

Required tests:
- announced successor without automatic replacement
- successor receives independent age/rank/volume history

Blocks adoption: `yes`

### MC-07 Split lifecycle policy from event registry

Create separate hash-bound lifecycle policy and lifecycle event resolution registries. Event entries must bind exchange, market, symbol/pair, epoch, cessation/effective/known times, last valid time, expected-grid end, official evidence and archive/raw/intraday/scope hashes, policy version, adjudication hash, announced successor metadata and authorization status.

Acceptance:
- new/changed events, hashes, cessation times or post-event rows fail closed
- overlapping/conflicting entries fail closed
- implementation contains no symbol/date branch

Required tests:
- unregistered event
- checksum/evidence/registry hash changes
- cessation-time change
- new post-cessation row
- no symbol/date special case

Blocks adoption: `yes`

### MC-08 Support multiple availability epochs and ticker identity

Represent relisting, reactivation, migration and ticker reuse as distinct symbol_availability_epochs with identity/version and evidence. A new epoch cannot inherit the prior epoch's 365-day history, volume, rank or price continuity.

Acceptance:
- multiple non-overlapping epochs are representable
- same ticker/different asset identity remains separate
- epoch overlap blocks qualification

Required tests:
- same ticker relisting
- ticker reused for a different economic asset
- overlapping epochs

Blocks adoption: `yes`

### MC-09 Raise lifecycle evidence sufficiency above archive absence

Limit this policy to proven permanent cessation/migration events. Archive absence alone is not lifecycle proof. Require validated official lifecycle evidence plus integrity-checked interval evidence, and distinguish temporary suspension, maintenance, delisting and migration. Freeze the similar-scope scan definition and hash.

Acceptance:
- permanent and temporary states have different outcomes
- missing intraday data without announcement remains a data blocker
- continued intraday trading contradicts cessation and blocks
- scope and scan hash are machine bound

Required tests:
- temporary suspension
- maintenance
- archive absence without announcement
- announcement while trading continues
- scope hash change

Blocks adoption: `yes`

### MC-10 Define V4 machine authority and disclosures

Require lifecycle_policy_manifest, lifecycle_resolution_registry, symbol_availability_manifest, active_universe_manifest, complete_day_mask, expected_grid_manifest, raw_row_quarantine_manifest, qualification_summary and V3/V4 diff. Use canonical serialization and hash bindings; Markdown is never input. V4 becomes active only after cold/warm/worker equality, truthful requalification PASS and later U-03F independent recomputation.

Acceptance:
- summary discloses lifecycle events, terminated symbol-months, partial days, quarantined post-cessation rows, membership/active counts and unresolved lifecycle rows
- synthetic fills and replacement members are zero
- V3 remains authority until a V4 pass

Required tests:
- cold/warm/worker machine hash equality
- Markdown mutation cannot affect qualification
- V4 blocked evidence cannot become active authority

Blocks adoption: `yes`

### MC-11 Freeze lifecycle fault-injection coverage

Adoption must include the complete fault-injection matrix listed in this independent review. Tests must exercise boundary alignment, partial and placeholder rows, source disagreement, evidence timing, event types, epochs, membership/active counts, complete-day masking and non-execution semantics.

Acceptance:
- every named fault-injection case maps to an automated test ID
- unknown and contradictory cases fail closed
- tests do not run qualification or mutate production evidence during policy adoption review

Required tests:
- cessation exactly at a UTC day boundary
- cessation exactly at a 5m boundary
- cessation exactly at a 1h boundary
- cessation not aligned to any bar boundary
- cessation-day partial daily row
- post-cessation normal-duration zero-volume placeholder
- post-cessation close-before-open placeholder
- multiple post-cessation placeholders
- monthly/daily/REST disagreement
- intraday archive absence without lifecycle announcement
- lifecycle announcement while intraday trading continues
- temporary suspension
- permanent delisting
- migration
- announced successor
- same ticker relisted as a new epoch
- evidence publication later than effective time
- official checksum update
- registry content-hash change
- unregistered lifecycle event
- overlapping availability epochs
- member and non-member lifecycle events
- no replacement member
- active member count decline
- 90/365 complete-day windows exclude partial lifecycle day
- post-cessation absence does not create a gap
- pre-cessation gap remains blocking
- no stale-price forward-fill or cross-boundary return
- no symbol/date special case

Blocks adoption: `yes`

## Required Boundary Semantics

- Every availability epoch must expose `availability_start_inclusive` and `availability_end_exclusive`.
- The availability mask is applied before expected-grid construction.
- A lifecycle partial day can retain raw OHLCV evidence but cannot count toward 90/365 complete-day windows.
- Monthly membership remains fixed; timestamped active membership and counts change at the lifecycle boundary.
- Archive absence is not lifecycle proof. Validated official lifecycle evidence and integrity-checked interval evidence must agree.
- `announced_successor_symbol` is provenance only and grants no price, age, volume, rank, conversion or economic-continuity authority.

## Non-Targets And Downstream Gate

This data policy must not define exit price, liquidation, settlement, conversion, stale fill, cross-cessation return, -100%, zero-return or cash treatment. U-04 may later design a hypothesis, but fixed-rule or backtest work must remain blocked until a separate delisting/execution policy review covers positions intersecting lifecycle events.

## Fault-Injection Matrix

- cessation exactly at a UTC day boundary
- cessation exactly at a 5m boundary
- cessation exactly at a 1h boundary
- cessation not aligned to any bar boundary
- cessation-day partial daily row
- post-cessation normal-duration zero-volume placeholder
- post-cessation close-before-open placeholder
- multiple post-cessation placeholders
- monthly/daily/REST disagreement
- intraday archive absence without lifecycle announcement
- lifecycle announcement while intraday trading continues
- temporary suspension
- permanent delisting
- migration
- announced successor
- same ticker relisted as a new epoch
- evidence publication later than effective time
- official checksum update
- registry content-hash change
- unregistered lifecycle event
- overlapping availability epochs
- member and non-member lifecycle events
- no replacement member
- active member count decline
- 90/365 complete-day windows exclude partial lifecycle day
- post-cessation absence does not create a gap
- pre-cessation gap remains blocking
- no stale-price forward-fill or cross-boundary return
- no symbol/date special case

## Authorization Matrix

- ADR-0014 adopted authorized: no
- PR #81 Ready authorized: no
- PR #81 merge authorized: no
- Contract mutation authorized: no
- Registry mutation authorized: no
- V4 implementation authorized: no
- V3/V4 requalification authorized: no
- Cold/warm/worker build authorized: no
- U-03F authorized: no
- U-04 authorized: no
- Strategy design/code authorized: no
- Event scan authorized: no
- Returns/backtesting authorized: no
- OOS access authorized: no
- API/trading authorized: no
- execution/live authorized: no
- M2 authorized: no

Stop condition: PR #81 remains Proposed draft and unchanged. No adoption, implementation, registry mutation, requalification or downstream research is authorized by this review.
