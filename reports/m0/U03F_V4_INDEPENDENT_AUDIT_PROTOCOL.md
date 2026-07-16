# U-03F V4 Independent Audit Protocol

- Status: frozen_before_independent_audit_result
- Candidate evaluated: no
- Production evidence modified: no
- Production requalification rerun: no
- U-04 authorized: no
- Strategy/events/returns/backtesting/OOS: no
- API/trading/execution/live/M2: no

## Binding

This protocol binds starting main `1b6026499cb247f02f0a471eb5a33370769376d9`,
PR #89 merge `77cb0969980978e65f3560f38f50924c73dfee6e`, PR #90,
the fixed range `2020-01` through `2026-06`, source freeze
`c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`,
the V4 contract, lifecycle policy/event registry, ADR-0013 registry, KLAY
adjudication, all 15 production manifest identities, the V4 artifact set and
the production run manifest listed in the machine protocol.

The committed qualification report SHA256 is `ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a`.
The run manifest records `dec61cf9d0cdd2a1182b5622e85cfdf9dbc6043e7342ba4f2400fa66245bc2b3`;
the independent audit must adjudicate this exact difference rather than edit
either authority. The V3/V4 diff report SHA256 is
`b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06`.

## Independent Recalculation

The auditor must independently recalculate raw provenance, monthly/daily
authority, ADR-0013 row resolution, ADR-0014 lifecycle availability,
eligibility, 78 monthly Top-15 memberships and 1,170 membership rows, 5m
expected grids, gap/quarantine attribution, complete-day masks, 1h
availability, timestamped active universe, qualified panel, every production
manifest, qualification summary, V3/V4 diff, run manifest and artifact-set
identity.

Production builders and production Markdown are not computation inputs. Exact
and semantic comparisons are both mandatory. There is no tolerance for
membership, rank, timestamp or status differences and no economic-materiality
exception. Wrapper or generated-time differences are judged only by the
frozen canonical identity rule.

## Verdict Gate

The only verdicts are `pass`, `failed_audit`, `blocked_missing_evidence` and
`blocked_protocol_violation`. The audit method and Gates are frozen before any
result. A change requires a new protocol version or ADR. A mismatch must not
be used to reshape the comparator. A passing audit still does not authorize
U-04; U-04 requires a later explicit task.
