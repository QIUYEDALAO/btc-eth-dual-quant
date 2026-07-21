# ADR-0015 Invalid-Interval Independent Audit Protocol

- Status: `frozen_before_independent_auditor_implementation_or_result`
- Protocol stage executed the real audit: no
- Production evidence or frozen source modified: no
- U-04, strategy, returns, backtesting, OOS or M2 authorized: no
- API, trading or `execution/live` authorized: no

## Exact Binding

This protocol starts from local requalification commit `a16b844` and binds the
exact reviewed implementation head `67e7d29eaed63a3edb903dd618184bc9f02c5748`,
integration merge `e2112a31908f1587eb657a4123f1f114cf2016fe`, source
freeze `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`,
runtime policy `0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04`,
algorithm `8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff`,
requalification artifact set
`8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3`
and run manifest
`a2f122244e34408071c49f457b96f90b6eba219c6b1304bcdcd9ab7d7d89cdf9`.

All 19 production manifest identities are frozen in the machine protocol. The
fixed source range is `2020-01` through `2026-06`, comprising 78 membership
months, 1,170 membership rows and exactly 27,736 frozen local archives.

## Independent Method

A later auditor must independently verify ZIP/member/archive/raw-row identity,
parse integer timestamps, rebuild source authority, row-conflict and lifecycle
state, reconstruct point-in-time membership, and independently adjudicate the
ADR-0015 event predicate and full active-slot mask. The valid minority is part
of the mask, not an exception.

The auditor must then reconstruct the post-mask 5m grid, 1h availability,
complete-day mask, timestamped active universe, qualified panel, all 19
manifests, qualification summary, V3/V4 diff, run-manifest identity and
artifact-set identity. Normal, reverse and deterministic-shuffled traversal
must be byte-identical under canonical identity.

Production builders, the production invalid-interval module and production
Markdown are not allowed as the audit algorithm or computation input. They may
be inspected only as comparison targets after the independent result exists.

## Pass And Severity Gate

`pass` requires 19/19 exact manifest comparisons, zero semantic mismatches,
zero traversal mismatches, zero critical findings and zero high findings. The
independent accounting must reproduce 8 events, 119 invalid physical rows, 1
valid-minority row and 120 total masked active-member slots.

Source/raw identity drift, independence failure, membership/lifecycle or
active-denominator mismatch, invalid-event/full-mask mismatch, qualified-panel
or verdict mismatch, evidence mutation and Gate bypass are critical. Every
other manifest mismatch, accounting mismatch, order dependence, or report/run/
artifact binding mismatch is high. No economic-materiality waiver is allowed.

The only verdicts are `pass`, `failed_audit`, `blocked_missing_evidence` and
`blocked_protocol_violation`. Any method or Gate change requires a new protocol
version before results are inspected.

## Authorization Boundary

After this protocol is locally frozen, only independent auditor fixture
implementation, fault injection and a later exact-head review are authorized.
The real audit remains disabled until those prerequisites separately pass.
Nothing in this protocol authorizes U-04, research, strategy, returns,
backtesting, OOS, API/trading, `execution/live` or M2.
