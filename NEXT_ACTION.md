# Next Action

## Immediate Task

The source-order fix has replacement exact-head `approve` with 0 critical/high.
The real three-order audit is again the only authorized task.

- Protocol: `ADR0015-LIQUID-UNIVERSE-V4-INDEPENDENT-AUDIT-V1`.
- Protocol content hash:
  `9a1768f01e7891f8c76f74293fb3836339e75fafa039fe12ebf3a7ddfdbb970b`.
- Requalification run:
  `a2f122244e34408071c49f457b96f90b6eba219c6b1304bcdcd9ab7d7d89cdf9`.
- Production artifact set:
  `8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`.
- Source freeze: `c86310f8...ec6c`; exact archive count: `27,736`.
- Frozen comparison Gate: 19/19 exact manifests, zero semantic/order
  mismatches and zero critical/high findings.
- Frozen accounting: 8 events, 119 physical invalid rows, 1 valid-minority
  row and 120 total masked active-member slots.
- Auditor implementation content hash:
  `f0c0ee6d1fae740c5c306925408760bb2a3f6b94b7115652c4da24d178188d5e`.
- Synthetic/targeted checks: 25 passed; complete unit regression: 700 passed.
- Historical frozen auditor modified: no.
- Exact reviewed target: `4bebdf32786818b7f451474c864ba9ee3109a26b`.
- Review content hash: `77abc29349c2ef347e8c975d8d30cbb5083c7759f48d159baa3f4d38ca2010f0`.
- Exact reviewed target: `301e910ea669c702a34598e500826a456663a5fb`.
- Review content hash: `f04f87f849966d188dc39cff0bc72f12a71d6c1d601249d202a08ce4686b7c26`.
- Exact reviewed target: `e935d6b287eaf66f825d9f73181fa35160cb5225`.
- Review content hash: `fb63d2f3b3e0843927a348fb5a9fb94a5b3873d15a132d8bd968d10fe7980fe0`.
- Real audit completed: no; authorized: yes.
- Prior failed preflight produced no result evidence.

The only authorized next task is the real audit. The 19/19 Gate remains unchanged.

## Required Audit Run

1. Run only from the exact review-bound implementation and frozen protocol.
2. Traverse the frozen archive set in all three required orders.
3. Compare all 19 independently rebuilt manifests byte-semantically.
4. Verify 8 events, 119 invalid rows, 1 valid minority and 120 masked slots.
5. Fail closed on any hash, count, order or scope mismatch.
6. Continue local Git only; no GitHub push, PR or Actions unless the user asks.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; protocol work did not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and its later blocked cold
run remain immutable. ADR-0015 requalification separately quarantined all 119
physical invalid rows plus the valid-minority slot.

## Prohibited

- Freqtrade-first remains the architecture for any future single-leg research.
- No strategy is eligible for M2. Do not enter M2.
- Do not execute anything beyond the now-authorized real independent audit.
- Do not mutate frozen archives, requalification evidence or historical audit
  evidence.
- Do not use production builders, production Markdown or the production policy
  module as the independent audit algorithm.
- Do not add date/symbol/row exceptions, repair timestamps, fill gaps, replace
  members, waive manifest mismatches or lower any Gate.
- Do not enter U-04, hypothesis design, event scanning, returns, backtesting or
  OOS.
- Do not access API keys, trading permissions, paper/live trading,
  `execution/live`, order placement, cancellation or matching.
- M2 remains blocked.
