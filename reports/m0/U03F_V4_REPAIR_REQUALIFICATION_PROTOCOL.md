# U-03F V4 Repair And Requalification Protocol

- Status: frozen_before_repair_implementation
- Starting main: `513d321b69750d6c8bb47bddbf006d4caac04828`
- Historical evidence modified: no
- Frozen source replacement or download: no
- Public requalification executed: no
- New independent audit executed: no
- U-04 authorized: no
- Strategy/events/returns/backtesting/OOS: no
- API/trading/execution/live/M2: no

## Immutable Inputs

PR #95 merged the truthful `failed_audit` evidence with one critical and seven
high findings. The prior source freeze remains
`c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`.
The historical production artifact set remains
`4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6`;
the independent failed-audit artifact set remains
`c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236`.
Neither is future authority.

## Frozen Repair

The implementation must replace float/datetime timestamp authority in the V4
production paths with integer-only UTC conversion, validate every 5m row's
exact open/close interval before grid and aggregation accounting, propagate
invalid-row effects consistently through source, grid, panel, summary and diff
artifacts, and bind the final qualification-report bytes atomically into the
run manifest.

The implementation may not change membership ranking, lifecycle policy,
row-conflict policy, gap policy, the fixed range, source bytes or any Gate. It
may not run public requalification in the implementation PR.

## Dependency Gates

The exact implementation head requires an independent `approve` verdict with
zero critical and zero high findings before merge. Only the approved merged
repair may run the fixed `2020-01` through `2026-06` cold/warm/worker public
requalification against exactly 27,736 frozen archives. All three artifact-set
hashes must match, every blocking counter must be zero, and the final report
binding must be exact.

Only merged passing requalification evidence may enter a new independent audit.
Normal, reverse and deterministic shuffled recomputations must agree; 15/15
production manifests must be exact; critical and high findings must both be
zero; and the verdict must be `pass`.

Any mismatch, critical/high finding, exact-head drift, source/hash drift or
authorization expansion fails closed. A passing audit still does not authorize
U-04; U-04 requires a separate explicit future task.
