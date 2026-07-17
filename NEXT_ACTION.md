# Next Action

## Immediate Task

The ADR-0015 fixed-range requalification is complete and passed locally from
the exact 27,736 frozen archives over `2020-01` through `2026-06`.

- Cold/warm/worker artifact set:
  `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`.
- Requalification run manifest:
  `a2f122244e34408071c49f457b96f90b6eba219c6b1304bcdcd9ab7d7d89cdf9`.
- Deterministic mismatches: `0`.
- Synchronized invalid-interval events: `8`.
- Invalid physical rows quarantined: `119`.
- Valid-minority rows quarantined with the complete active slot: `1`.
- Total active-member slots quarantined: `120`.
- Processing errors / unresolved gaps / policy blockers: `0 / 0 / 0`.
- Synthetic fills / replacement members: `0 / 0`.

The only authorized next task is to design and freeze a new independent audit
protocol bound to the exact run and artifact-set hashes above. The protocol
task must not execute the audit.

## Completed Dependency

The controlled integration prerequisite completed in PR #111 at
`e2112a31908f1587eb657a4123f1f114cf2016fe`. Selective run `29572828915` and
main run `29573400780` passed. Reviewed implementation head
`67e7d29eaed63a3edb903dd618184bc9f02c5748` remains an ancestor and the seven
reviewed implementation blobs remain exact.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: the policy review remains `approve` under review
hash `893d056e...85a3`; its semantics were not changed by requalification.

## U-03F Repair Exact-Head Review

Historical review marker: the prior repair review remains immutable. Its later
cold run truthfully stopped on 119 physical invalid-interval rows; ADR-0015 now
quarantines those rows only through the separately reviewed generic policy.

## Allowed Next Work

1. Create one local branch for the new independent audit protocol.
2. Bind the protocol to source freeze `c86310f8...ec6c`, requalification run
   `a2f12224...cdf9`, artifact set `8784b564...348c3`, runtime policy
   `0ac074cf...62d04` and algorithm `8f8a3668...ea4ff`.
3. Freeze independent normal/reverse/deterministic-shuffled recomputation,
   exact manifest comparisons, severity rules and fail-closed stop conditions.
4. Do not run the real audit until that protocol task is complete.
5. Continue using local Git only: one branch and one final local commit; no
   GitHub push, PR or Actions unless the user explicitly requests publication.

## Prohibited

- Freqtrade-first remains the architecture for any future single-leg research.
- No strategy is eligible for M2.
- Do not enter M2.
- Do not mutate or replace any frozen archive or historical evidence.
- Do not download public data, add date/symbol exceptions, repair timestamps,
  fill gaps, replace members or lower a Gate.
- Do not execute the new independent audit in the protocol task.
- Do not enter U-04, strategy design, event scanning, returns, backtesting or
  OOS.
- Do not access API keys, trading permissions, paper/live trading,
  `execution/live`, order placement, cancellation or matching.
- M2 remains blocked.
