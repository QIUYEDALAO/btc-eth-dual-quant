# ADR-0015 Invalid-Interval Policy Implementation Status

- Status: `implementation_pass_fixture_only_pending_exact_head_review`
- Base main: `141481fa445bdc03b453844a666dbd2639c3cdf7`
- Adoption PR / exact head / merge: `#108` / `01d98b60ce8a9a0b33082777c946cec70d380fc7` / `141481fa445bdc03b453844a666dbd2639c3cdf7`
- Adoption main Gate: run `29554620941`, success
- Runtime policy hash: `0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04`
- Algorithm hash: `8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff`
- Public data read or executed: no
- Fixed-range cold/warm/worker requalification run: no
- Fixed-range requalification authorized: no
- New audit protocol or audit authorized: no
- Exact-head independent implementation review required: yes
- U-04, strategy, backtesting, OOS, API/trading, execution/live and M2 authorized: no

## Implemented Semantics

The generic runtime policy verifies exact official ZIP size, SHA-256, CRC and
single-member identity before retaining every physical CSV row and its hash.
It binds monthly point-in-time membership plus lifecycle end-exclusive state,
groups rows by integer `open_time_ms`, and accepts only the sole close-boundary
defect at the frozen minimum of two affected active members and integer 80%
threshold.

An accepted event emits one deterministic identity and a separate full-slot
mask for every active member. Valid minority rows remain immutable physical
evidence but are masked with the invalid rows. The masked 5m grid is processed
before complete 1h and UTC-day eligibility. No row is rewritten, filled,
replaced or selected through a known date or symbol.

## Fixture Evidence

- Accepted cases: 15/15, 14/15 with valid-minority masking, exact 12/15, and a
  lifecycle-reduced active denominator.
- Time reconstruction: two accepted slots in one hour remove that hour once
  and make the UTC day ineligible.
- Determinism: normal, reverse and deterministic-shuffled inputs produce one
  exact canonical evaluation and manifest identity.
- Fault injection: all `ADR0015-FI-001` through `ADR0015-FI-016` execute a
  fail-closed path, including source, membership, raw-row, mask and order drift.
- Runtime artifacts: policy, event, slot-mask and accounting manifests are
  separately hash-bound; generation time is outside content identity.

All fixtures use temporary synthetic ZIP files. No frozen archive, public run,
historical evidence or prior V4 manifest was modified.

## Next Gate

Freeze the final implementation head only after local and selective PR
validation pass. A separate independent review must bind that exact head and
return `approve` with zero critical/high findings before this implementation
may merge or any fixed-range requalification may start.
