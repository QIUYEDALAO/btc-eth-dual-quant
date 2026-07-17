# Next Action

## Immediate Task

The ADR-0015 independent audit protocol is frozen locally before any auditor
implementation or real audit result.

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
- Real audit executed or authorized: no.

The only authorized next task is a separate independent auditor fixture
implementation. It may implement independent primitives, synthetic fixtures,
fault injection and an exact-head review package. It must not execute the real
frozen-source audit.

## Required Next Implementation

1. Create one new local branch from the frozen protocol commit.
2. Implement independent ZIP/raw-row, integer-time, membership, lifecycle,
   ADR-0015 event/mask/accounting, post-mask grid/hour/day, panel and manifest
   recomputation without importing production builders as the audit algorithm.
3. Cover normal, reverse and deterministic-shuffled fixture orders.
4. Cover source/hash/member/timestamp/membership/threshold/full-slot/order and
   authorization fault injection.
5. Freeze one exact implementation head and perform a separate exact-head
   review before any real audit is authorized.
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
- Do not execute the real independent audit during auditor implementation.
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
