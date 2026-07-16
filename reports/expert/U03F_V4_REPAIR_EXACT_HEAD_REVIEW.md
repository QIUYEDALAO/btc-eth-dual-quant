# U-03F V4 Repair Exact-Head Review

- Verdict: `approve`
- Target PR: `#98`
- Exact base: `0e65cd41bfac590d40ae5cb0590cc7102019018c`
- Exact head: `27e6436c0a4b00ca7c8055bc763d533fcbcc9743`
- Changed-file-list hash: `ecee2bbb76d0da0a0822cf218efda607fd38dea7d8e737c13fb8b19ada978ac9`
- Repair implementation hash: `9c97200e7e7ad441eac5282b7bbdda742980b13d59694c97e54cb65c4becae3a`
- Frozen protocol hash: `9b771317d8257b397addefc262a1ffd48ded57ec1d79542372fe3c95cf8180c1`
- Frozen auditor algorithm hash: `7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1`
- Source freeze hash: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`
- Review content hash: `c60b1f8b451ea60ac8da267e90917b8c560655089bb1cd20dfb12999004bf1b4`
- Remaining critical/high: `0 / 0`

## Validation

- GitHub exact-head checks: 110/110
- Local exact-head unit tests: 602/602
- Frozen fault tests: 6/6
- Public requalification executed: no
- New independent audit executed: no

## Review Matrix

| Dimension | Result |
| --- | --- |
| exact_head_and_ci | pass |
| frozen_protocol_scope | pass |
| integer_time_authority | pass |
| strict_5m_physical_row_validity | pass |
| atomic_report_run_binding | pass |
| exact_frozen_source_consumption | pass |
| fresh_three_way_execution | pass |
| truthful_blocked_evidence | pass |
| historical_evidence_immutability | pass |
| auditor_algorithm_immutability | pass |
| zero_downstream_authorization | pass |

## Resolved During Review

- `high` `U03F-RR-H01`: Blocked evidence now requires the fail-closed determinism marker instead of the pass marker.
- `high` `U03F-RR-H02`: Every consumed source key, SHA256 and byte size is bound to the exact 27,736-entry freeze.
- `high` `U03F-RR-H03`: Resume was removed so cold, warm and worker must be regenerated under the current repair.

## Authorization

This review approves only the unchanged exact implementation head for merge. It does not
run or approve public requalification, a new independent audit, U-04, strategy work,
returns, backtesting, OOS, API/trading, execution/live or M2. Any target/hash drift
invalidates this approval and stops the chain.
