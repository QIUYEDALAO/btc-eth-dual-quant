# ADR-0015: Synchronized Official Invalid-Interval Quarantine Policy

- Status: Proposed Draft; non-authoritative pending independent policy review
- Date: 2026-07-17
- Scope: frozen official Binance spot 5m physical interval-boundary defects
- Diagnostic protocol: PR #102, exact head `07e4fc13d4a6d027e4881863b9224906be776e9a`
- Diagnostic evidence: PR #103, exact head `e4b6f6e70bf6df2b10dbd7acc71a734f107d5076`
- Diagnostic content hash: `ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677`
- Diagnostic run content hash: `df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33`
- Runtime authority: none

## Context

The failed U-03F audit and the blocked repair requalification remain immutable
historical evidence. The separately frozen diagnostic verified all 27,736
frozen archives in normal, reverse and deterministic-shuffled order. It found
119 exact physical invalid rows grouped into eight synchronous 5m windows.
Each window met the protocol's pre-outcome evidence threshold of at least two
affected active members and at least 80% of the active membership. The result
was `new_policy_adr_required`, not a qualification pass or a policy adoption.

The physical rows, frozen archives and prior reports must remain unchanged.
This Draft does not reinterpret the existing V2 gap policy, does not repair
source data and does not authorize a rerun.

## Proposed Decision

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

## Independent Policy Review Gate

The exact Draft head must receive a separate independent policy review. The
review must verify evidence and hash bindings, threshold justification,
false-positive and adversarial cases, full-slot masking of valid minority rows,
accounting invariants, policy separation from the V2 gap authority, machine
test coverage and the all-false authorization matrix.
Any mismatch, critical finding or high finding stops the chain. An approve verdict is review evidence
only and still does not adopt this ADR.

## Future Dependency Chain

1. Merge this Draft after all Draft CI checks pass.
2. Independently review the exact Draft head.
3. If and only if the review approves with zero critical/high findings, use a
   separate governance PR to consider conditional policy adoption.
4. After separate adoption only, implement the generic policy without running
   public requalification.
5. Independently review the exact implementation head.
6. After implementation review approval only, run fixed-range public
   requalification from `2020-01` through `2026-06` in cold, warm and worker
   modes under identical frozen inputs.
7. After a truthful requalification pass only, freeze and execute a new
   independent audit.
8. Close governance truthfully after the audit result.

Skipping or reordering dependencies is prohibited.
A future audit pass still does not automatically authorize U-04.

## Draft Authorization Matrix

- ADR-0015 adopted: false
- Production policy implementation: false
- Production pipeline modification: false
- Fixed-range public requalification: false
- New independent audit: false
- U-04: false
- Hypothesis or strategy: false
- Event scan, signals or returns: false
- Backtesting or OOS: false
- API or trading: false
- execution/live: false
- M2: false
