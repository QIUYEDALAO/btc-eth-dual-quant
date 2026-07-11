# Liquid Spot Universe Qualification Report

- Status: implementation_pass_runtime_qualification_pending
- Contract: LIQUID-SPOT-USDT-TOP15-V1
- Intended range: 2020-01-01 through the latest complete UTC month
- Historical discovery completed: no
- Monthly Top-15 manifests generated from public history: no
- Official 5m qualification completed: no
- Derived 1h qualification completed: no
- Strategy design authorized: no
- Strategy/events/signals/returns computed: no
- OOS accessed: no
- M2 authorized: no
- Runtime artifacts committed: no

## Implemented Evidence Controls

- Monthly daily evidence has precedence; daily evidence fills missing timestamps only.
- Membership uses only rows strictly before the effective UTC month.
- Prior 90 complete days, 365 complete history days, deterministic symbol tie-break and exclusions are enforced by the frozen contract.
- Historical members are independent of current exchangeInfo, preserving delisted assets when their point-in-time evidence qualifies.
- One-hour evidence requires exactly twelve consecutive canonical 5m bars; interpolation is forbidden.
- Membership manifests have a deterministic canonical hash.

## Current Blocker

The broader-universe official archive run has not yet been executed. This report
therefore does not claim that any month or asset is qualified and does not authorize
a cross-sectional hypothesis design. The next data-run task must discover historical
USDT spot symbols, obtain official daily and selected-member 5m archives, emit the
ignored detailed manifests, and replace this status only with real public evidence.
