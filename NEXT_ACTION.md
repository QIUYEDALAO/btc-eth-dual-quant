# Next Action

Under the Freqtrade-first architecture, M1D remains stopped by its fixed
calendar Gate. M1E canonical-data contract v2 now passes locally under
ADR-0009 and merged in PR #40, while the original ADR-0008 blocked report remains historical evidence.

The canonical layer uses monthly official 5m ZIP as base, applies 12 daily 5m
revisions only where public REST independently confirms them, and derives all
1h/4h bars deterministically. There are zero unresolved canonical conflicts and
zero unexpected incomplete child buckets. A pinned Freqtrade 2026.6 container
read all six caches on the VPS. Higher-timeframe archive revisions are retained
as audit quarantine and cannot be used by a future volume-based rule.

Field-level source diagnostics now confirm 30 reproducible conflict rows. All
36 affected monthly ZIPs retain their original hashes on fresh download. Public
REST supports the daily archive in 16 December 2020 conflicts, the published
higher timeframe in 10 rows, the child aggregation in 2 rows, and a third
version in 2 rows. No evidence path makes the official sources arithmetically
consistent under ADR-0008. This diagnostic record merged in PR #35.

A sanitized source-owner package is now prepared for Binance public-data issue
#475. The existing issue covers 16 December 2020 rows; the package adds 14
cross-timeframe rows and 36 stable archive hashes. It was submitted with explicit
approval and is now `submitted_awaiting_response` at issue comment 4939090508.
Monitor the official response; do not treat submission itself as a Gate pass.

The immediate sequence is:

1. Create only the metadata-only M1E 1800/540-day sample-budget Gate.
2. Calculate the split from the qualified `2020-07-01` start through `2026-06-30` without reading prices, signals, events, or returns.
3. Do not read OOS prices/returns, define strategy rules, or run Freqtrade backtesting.
4. Continue Binance source-owner monitoring for provenance; do not make it an operational dependency.

The first six-month clean suffix after the final blocked month starts
`2022-11-01`. It contains 1338 full days and 402 sealed-OOS days through
2026-06-30, so it still fails the fixed 1800/540-day calendar Gate. This suffix
is diagnostic only and must not replace the registered `2020-07-01` start.

Official 1h ZIP is signal-data authority. Official 5m ZIP provides future fill
detail and 1h aggregate parity; 4h is future regime-filter data only. Daily ZIP
may fill missing monthly timestamps but never overwrite them. REST is evidence
only. The monthly 1m p95 spread proxy threshold is fixed at 0.30%.

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

M1E is a new trial, not a shorter M1A. The M1A SMA200 + Donchian 55/20 + ATR20
2x rule bundle is forbidden. No alternative entry, exit, position, or risk
parameter is selected yet. M1E must not access OOS returns, run Freqtrade
backtesting, or add strategy code during data admission.

The first common six-month data/liquidity window is January through June 2020,
so the fixed research start is `2020-07-01`. Six later months are blocked by
official OHLCV aggregate differences or monthly/daily source conflict:
2020-12, 2021-01, 2021-04, 2021-09, 2021-11, and 2022-04. REST samples matched,
all public downloads completed, and pinned Freqtrade `list-data` passed on the
VPS. Those facts do not override the ZIP parity failures.

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
