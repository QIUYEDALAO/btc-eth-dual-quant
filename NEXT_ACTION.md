# Next Action

Under the Freqtrade-first architecture, the T5 metadata-only calendar precheck
merged in PR #29 and stopped M1D before event or return analysis.

T2 evidence now records:

1. Complete BTC/ETH golden 1m from `2023-10-01` through `2026-06-30`.
2. Deterministic 5m/15m derivatives with zero incomplete research buckets.
3. Zero numeric differences against 66 official monthly 15m archives.
4. Traceable pre-start quarantine kept outside formal research data.
5. Freqtrade 2026.6 pinned-container readability for all six jsongz caches.

T3 now provides one daily-MTM convention, Sharpe/MaxDD/Sortino/Calmar/PSR/DSR,
the fixed 25% BTC + 25% ETH + 50% cash benchmark, Freqtrade completed-trade
audit adaptation, and sealed M1C regression. It reproduces Base Sharpe 0.7882,
MaxDD 23.4729%, PSR 0.9024 and Cost x2 Sharpe 0.7528, MaxDD 24.4688%, PSR 0.8920.

T4 now provides ledger-locked event observations, next-open semantics, fixed
1/2/4/8/12/24-bar horizons, four immutable cost scenarios, decay, clustering,
path-risk, occupancy, and sample-budget diagnostics. It evaluated no candidate,
selected no events, and accessed no OOS returns.

The formal range has 1004 days: 702 IS days and 302 sealed OOS days. This is
238 days below the fixed 540-day OOS minimum. T5 status is
`blocked_insufficient_oos_calendar`; the threshold must not be lowered. At 30%
OOS, 1800 full days are required, with the earliest projected complete date
`2028-09-03`.

The next productive work is monthly public-data accrual and M0 audit diagnostics.
A different candidate may be considered only through a separately approved
design PR. M1D must not define event thresholds, read OOS prices or returns,
run a candidate, or proceed to T6.

Locked conditions: discrete completed-15m events, authoritative 1m detail, 5m
sensitivity, `max_open_trades=1`, no fixed holding duration, no daily trade
quota, daily-MTM MaxDD <=15%, OOS Sharpe >=1.0, and PSR >=0.95.

M1C remains `failed_validation` after expert correction. Its OOS daily-MTM
Sharpe is 0.7882/0.7528 and MaxDD is 23.47%/24.47%; do not tune or rescue it.

M0 source differences must be quarantined and sensitivity-tested. Never select
the more profitable official data version.

Rules:

- No strategy is eligible for M2.
- M0 remains accepted infrastructure but is audit_revalidation_required until step 2 passes.
- Historical M1A/M1B numerical claims marked superseded or invalidated must not support approval.
- The strict M1B event-time report is the current numerical evidence and remains failed_validation.
- Do not enter M2.
- Do not run live trading.
- Do not run paper trading with real API.
- Do not request, read, or use API keys.
- Do not implement execution/live.
- Do not place or cancel orders.
- Follow `PROJECT_EXECUTION_CHECKLIST.md` in dependency order.
