# U-11 Paper Observation Adjudication

- Status: `failed_execution_invalid_observation`
- Attempt hash: `0a55b61c83daea4c2f7c61e35db06b50c563a108c23cb74d35b1cb55888a9521`
- Candidate closed: `true`
- Retry authorized: `false`

The one attempted run is deterministic across all three traversal orders, but
it is not valid economic evidence. The observation implementation constructed
4h common returns only when all end-time active members also had a prior-boundary
close in the active-month reader. Monthly membership transitions therefore
introduced common-series holes. A 360-observation lookback nearly always spans
such a boundary: 9,925 of 9,931 decision times were rejected before capture,
leaving only six evaluated decisions and zero events.

The metadata qualification ceiling did not cover this implementation/data-scope
interaction, so it could not authorize a trustworthy result run. The generated
`failed_feasibility` manifest remains immutable attempt evidence but must not be
interpreted as an economic hypothesis result.

Fail closed: do not repair or rerun U-11, do not lower thresholds, and do not
enter result review, rules, strategy, backtesting or OOS. Only a separately
authorized, economically independent U-12 design may follow.
