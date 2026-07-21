# ADR-0017: Current-Route Selection and Runtime Authorization

- Status: Adopted
- Scope: final pre-runtime governance decision for the frozen ADR-0016 public spot strategy route
- OOS status: sealed and unauthorized

## Context

ADR-0016 froze twenty source records, six candidates, runtime identity, data,
cost, portfolio, safety and OOS contracts. PR #113 and PR #112 were approved at
exact heads and merged without changing the approved PR #112 tree.

The M1A/M1B/M1C observations remain valid historical ledger entries, but their
instruments, scopes, windows and return processes differ from the current
public spot strategy route. They therefore remain reported and append-only but
are not treated as a same-distribution DSR reference sample for this route.

## Decision

The current-route DSR family consists only of every materialized original and
modified trial from the six frozen candidates. Base and CostX2 form separate
sequences; StressA and StressB are mandatory diagnostics but do not add trials.

DSR must be computed and reported and is the primary ranking statistic. It is
not an absolute IS hard Gate. `all_hard_gates_pass` means all frozen non-DSR
performance, sample, benchmark, causal and reconciliation Gates pass.

The immutable order is:

1. all non-DSR hard Gates pass;
2. Base DSR descending;
3. CostX2 DSR descending;
4. CostX2 daily-MTM Sharpe descending;
5. CostX2 MaxDD ascending;
6. turnover ascending;
7. candidate ID ascending.

Each trial permanently stores its equity-recomputed Sharpe, PSR, MaxDD and
return. A trial may record DSR at materialization and its reference-sequence
hash, but that value is not the final selection DSR because later append-only
trials change the reference sequence.

After every original and permitted modified trial closes, the system generates
`reports/m1/evidence/external_strategy_selection/final_is_selection.json`
exactly once. That report contains the complete current-route sequences, final
Base/CostX2 DSR, all hard Gates, the fixed ranking, one selected candidate or
null, and its own canonical hash.

## Authorization

After this ADR is merged, the orchestrator may continuously perform fixed
runtime identity verification, exact compatibility loads, causal validation,
one original IS trial for every causal PASS candidate, and at most one
pre-registered modification for each of at most three eligible original
candidates. IS begins automatically only if at least five of the six candidates
pass the causal Gate. Ordinary code, container and test failures are repaired
continuously without opening a new governance cycle.

OOS, dry-run, APIs, private endpoints, paper/live trading, order placement,
`execution/live` and M2 remain prohibited. The route must stop at
`pending_explicit_unique_oos_authorization` after a truthful final selection or
at the first frozen hard-stop condition.

## Finality

This is the last pre-runtime governance change. A new pre-runtime review cycle
is permitted only for a P0 safety defect, license defect, OOS leakage or
numerical-calculation error. Formatting, wording and non-blocking improvements
cannot create another governance loop.
