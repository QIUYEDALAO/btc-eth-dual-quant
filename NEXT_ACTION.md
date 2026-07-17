# Next Action

## Immediate Task

The ADR-0015 independent auditor fixture implementation is complete locally
and must now receive a separate exact-head independent review.

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
  `b4bc01d5508975447664b82b2ccc79d21aedb916001855f267bbdb74a2f6004c`.
- Synthetic/targeted checks: 24 passed; complete unit regression: 699 passed.
- Historical frozen auditor modified: no.
- Real audit executed or authorized: no.

The only authorized next task is an exact-head independent review of the
completed implementation. The review must bind the final local commit and the
implementation content hash, inspect independence and all frozen Gates, and
reach `approve` with 0 critical / 0 high before it may authorize the real audit.

## Required Next Review

1. Freeze one local implementation commit without changing the reviewed files.
2. Create a separate local review branch from that exact commit.
3. Bind the protocol, implementation file hashes, exact target commit and all
   19-manifest/accounting/order Gates.
4. Record a deterministic review verdict and 0/0 critical/high counts.
5. Only an `approve` review may separately authorize the frozen-source audit.
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
