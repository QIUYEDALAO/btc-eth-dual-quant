# ADR-0015 Invalid-Interval Implementation Exact-Head Review

- Verdict: `approve`
- Target PR: `#109`
- Exact base: `141481fa445bdc03b453844a666dbd2639c3cdf7`
- Exact head: `67e7d29eaed63a3edb903dd618184bc9f02c5748`
- Target selective run: `29565196104`
- Runtime policy hash: `0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04`
- Algorithm hash: `8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff`
- Implementation content hash: `7cc4f9a3343de1f81ea7ac38e7c77efdd9fdb6bcbe3f8eeec099ddfca1dd020f`
- Review content hash: `9a0736431f4df6e27ce0b8e35d28e90d22838aef684e78fbd4c76bd79efe5af1`
- Remaining critical/high: `0 / 0`

## Validation

- GitHub selective Gate: 1/1
- Local unit tests: 670/670
- Implementation fixtures: 10/10
- Production-path regressions: 12/12
- Reviewed fault cases: 16/16
- Public data read or executed: no
- Fixed-range requalification executed: no
- New independent audit executed: no

## Review Matrix

| Dimension | Result |
| --- | --- |
| exact_head_base_changed_files_and_ci | pass |
| runtime_policy_and_algorithm_bindings | pass |
| archive_member_raw_row_identity | pass |
| integer_timestamp_and_sole_defect_semantics | pass |
| point_in_time_active_membership | pass |
| integer_two_and_eighty_percent_gate | pass |
| full_active_slot_and_valid_minority_mask | pass |
| event_identity_and_accounting_reconciliation | pass |
| mask_before_grid_hour_and_day_rebuild | pass |
| fault_injection_and_order_determinism | pass |
| v2_gap_policy_separation_and_no_shortcuts | pass |
| historical_evidence_and_zero_downstream_authorization | pass |

## Decision

The exact implementation head satisfies the adopted generic policy under synthetic
fixtures and fault injection. Approval is valid only while PR #109 remains at the exact
head above. Any target, policy, algorithm, membership, lifecycle, source, mask, ordering
or authorization drift invalidates this review and fails closed.

## Authorization

After this review PR merges, only the unchanged PR #109 implementation may be merged.
This review does not run or authorize fixed-range requalification, a new audit protocol,
a new audit, U-04, strategy/backtesting/OOS, API/trading, execution/live or M2.
