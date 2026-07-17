# ADR-0015: Synchronized Official Invalid-Interval Quarantine Policy

- Status: Accepted for generic policy implementation and exact-head implementation review only
- Historical Draft status: Proposed Draft; non-authoritative pending independent policy review
- Date: 2026-07-17
- Scope: frozen official Binance spot 5m physical interval-boundary defects
- Adoption basis: PR #107 exact-head independent review, merged at `1573abf2bef7d02df6c3b0624ee25cd3557ff2c6`
- Reviewed Draft head: `03d2b8736abab277e60db1153ba73f0899d7696f`
- Independent review head: `f3cf2131798f8bf3bd319b21480dca196517f3fe`
- Independent review content hash: `893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3`
- Diagnostic protocol: PR #102, exact head `07e4fc13d4a6d027e4881863b9224906be776e9a`
- Diagnostic evidence: PR #103, exact head `e4b6f6e70bf6df2b10dbd7acc71a734f107d5076`
- Diagnostic content hash: `ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677`
- Diagnostic run content hash: `df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33`
- Runtime authority: generic implementation authorized; no requalification or active data authority

## Context

The failed U-03F audit and the blocked repair requalification remain immutable
historical evidence. The separately frozen diagnostic verified all 27,736
frozen archives in normal, reverse and deterministic-shuffled order. It found
119 exact physical invalid rows grouped into eight synchronous 5m windows.
Each window met the protocol's pre-outcome evidence threshold of at least two
affected active members and at least 80% of the active membership. The result
was `new_policy_adr_required`, not a qualification pass or a policy adoption.

The physical rows, frozen archives and prior reports must remain unchanged.
This adoption does not reinterpret the existing V2 gap policy, does not repair
source data and does not authorize a rerun.

## Decision

Define a new generic policy family named
`synchronized_official_invalid_interval_quarantine`. A candidate event exists
only when all of the following are independently reproduced from a hash-bound
frozen official source and the bound point-in-time membership authority:

1. the market is Binance spot and the source interval is 5m;
2. every candidate row belongs to an active member at one grid-aligned
   `open_time_ms`;
3. archive size, SHA-256, ZIP CRC and the single CSV member all verify before
   parsing, and every affected raw row has a stable hash;
4. all non-time fields satisfy the existing strict physical-row checks;
5. `open_time_ms % 300000 == 0` and the sole defect is
   `close_time_ms != open_time_ms + 299999`;
6. at least two active members have that exact defect at the same open time;
7. affected active members divided by all active members at that open time is
   at least 0.80; and
8. duplicate, missing, non-member, off-grid, source-revision and authority
   conflicts are all absent.

The event identity is derived from the bound source, membership, algorithm,
policy version and open time. It is never selected from a registry of known
dates or symbols.

If a future separately adopted and reviewed implementation accepts an event,
it must quarantine the entire 5m slot for every active member. This includes a
valid minority row in a qualifying window. Full-slot quarantine preserves a
synchronized panel boundary and avoids conditioning membership treatment on
which source row happened to carry the invalid close time. Physical rows stay
in immutable raw evidence; they are excluded only through a separate,
hash-bound policy mask.

## Required Accounting Invariants

- Exactly one policy event is emitted per accepted open time.
- The pre-mask active-member set equals the bound membership set.
- The quarantine set equals the full pre-mask active-member set.
- Invalid, valid-minority and total quarantined counts reconcile exactly.
- No row is rewritten, truncated, filled, synthesized or replaced.
- No sixteenth-ranked or other substitute member enters the panel.
- Complete 1h and UTC-day eligibility is rebuilt from the masked 5m grid.
- Cold, warm-cache and worker outputs must be content-identical.
- Unknown or ambiguous evidence remains `unresolved_blocked`.

## Explicit Non-Applicability

This policy cannot classify an event when the open time is off-grid, any
non-time field is malformed or non-finite, OHLCV legality fails, rows are
missing or duplicated, the affected row is not an active member, membership is
ambiguous, archive or evidence hashes drift, a source revision is detected, or
the affected fraction is below the frozen threshold. These cases fail closed
under their existing authority; they do not inherit this quarantine rule.

The V2 gap-policy contract remains an immutable referenced baseline. Its hash
`051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51`
is not adopted as authority for this new defect class.

## Forbidden Shortcuts

- No date, symbol, row or known-window exception registry.
- No raw-row deletion, timestamp correction, truncation or normalization.
- No REST/daily replacement, redownload, synthetic candle or forward fill.
- No partial masking that drops only invalid rows and preserves valid minority
  rows in an accepted synchronous event.
- No reuse of Markdown as a runtime input.
- No Gate reduction, threshold tuning or reinterpretation of prior evidence.
- No automatic policy adoption, implementation, requalification or audit.

## Independent Policy Review Result

PR #107 independently reviewed the exact Draft head
`03d2b8736abab277e60db1153ba73f0899d7696f`. The unchanged review head
`f3cf2131798f8bf3bd319b21480dca196517f3fe` returned `approve` with zero
critical and zero high findings and merged at
`1573abf2bef7d02df6c3b0624ee25cd3557ff2c6`. Its review content hash is
`893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3`.

The review verified the exact evidence and model bindings, pre-outcome
thresholds, adversarial hard blocks, full-slot masking of valid minority rows,
accounting invariants, separation from V2 gap authority and the all-false Draft
authorization matrix. This adoption is conditional on those bindings remaining
exact. Any later drift fails closed and requires a new policy review.
Any mismatch, critical finding or high finding stops the chain.

## Adoption Scope

This ADR now authorizes only a separate generic policy implementation with
synthetic fixtures, fault injection and a later exact-head independent
implementation review. The implementation stage must not run public data,
requalification or an audit. The frozen docs-only Draft model remains unchanged
and non-runtime; this ADR plus the deterministic adoption manifest are the
governance authority for the limited next step.

## Adoption Dependency Chain

1. Draft PR #105 merged after all Draft CI checks passed.
2. Exact-head independent review PR #107 approved with zero critical/high
   findings and merged unchanged.
3. This separate governance stage conditionally adopts the policy.
4. Implement the generic policy without running public requalification.
5. Independently review the exact implementation head.
6. After implementation review approval only, run fixed-range public
   requalification from `2020-01` through `2026-06` in cold, warm and worker
   modes under identical frozen inputs.
7. After a truthful requalification pass only, freeze a new independent-audit
   protocol and then execute the audit separately.
8. Close governance truthfully after the audit result.
9. Consider U-04 only under a separate explicit authorization after a truthful
   audit pass.

Skipping or reordering dependencies is prohibited.
A future audit pass still does not automatically authorize U-04.

## Adoption Authorization Matrix

- ADR-0015 adopted: true
- Generic policy implementation: true
- Synthetic fixture validation: true
- Fault injection: true
- Exact-head implementation review: true
- Production pipeline modified in this adoption stage: false
- Fixed-range public requalification: false
- New independent audit: false
- U-04: false
- Hypothesis or strategy: false
- Event scan, signals or returns: false
- Backtesting or OOS: false
- API or trading: false
- execution/live: false
- M2: false
