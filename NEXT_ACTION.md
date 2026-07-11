# Next Action

The user granted automatic approval for sequential research approvals in the
current session. This removes repeated confirmation prompts but does not waive
any dependency, frozen Gate, OOS single-use rule or safety boundary.

M1E-04 merged in PR #46. M1E is defined as a
completed-1h compression-to-directional-expansion state transition whose
potential edge comes from delayed repricing and forced liquidity. It is not a
daily continuous trend rule and may not reuse or relabel the M1A SMA200,
Donchian 55/20 and ATR20 x2 bundle. No compression, expansion, exit, stop,
position, cooldown or warmup parameter has been selected.

M1E-05 merged in PR #47. The audit sidecar created ignored, physically bounded
IS snapshots for BTC/ETH 1h and 4h. Candidate code receives no row at or after
`2024-09-11`; OOS OHLC was not parsed. Eleven common outage gaps create twelve
continuous segments per dataset, and each row records its segment age so the
future fixed warmup can be applied without filling or interpolation.

M1E-06 merged in PR #49 with `failed_feasibility`. The protocol was committed before
outcomes were read. Its 139 complete IS events projected to 198 full and 59 OOS
events, so sample count and distribution Gates passed. The decisive frozen
cost-coverage Gates failed: combined median 24h MFE was 1.4005%, BTC 1.4658%,
and ETH 1.4005%, all below 1.80%. OOS remained unopened and no formal strategy
return, equity curve, Freqtrade strategy or backtest was produced.

PR #55 merged as `d9e43dd` with every check successful. The capability decision
is now canonical: native Freqtrade owns M1G signal selection and trade lifecycle,
while a mandatory Python audit may only conservatively reprice exported trades.

The exact implementation merged in PR #57. Freqtrade 2026.6 found zero bias
across 20 targeted signals and no recursive indicator variance across startup
windows 170/250/340. The Python audit accepts exported trades only and applies
the frozen conservative 5m target, stop, gap and timeout semantics.

Immediate sequence:

1. Review and merge the already frozen machine-readable IS protocol with all checks successful.
2. Only after that protocol merges, run Base, Cost x2, Stress A and Stress B on the sealed IS once.
3. Apply daily-MTM, benchmark and conservative execution-audit Gates without changing the contract.
4. Keep OOS sealed unless every frozen IS Gate passes.

The fixed contract is +1.80% target, -4.00% invalidation stop, 24h timeout,
25% current-equity cap, maximum one position and 72h global cooldown. Same-5m
target/stop ambiguity resolves to stop; stop gaps use the worse open. A planned
stop therefore risks about 1% of equity before costs and gap slippage.

M1G's prospective edge is a partial rebound after completed 1h forced-selling
and urgent-liquidity dislocation. It is not an inversion of M1E, a 15m M1D
rescue, a shortened daily-panic rule, or an M1A trend variant. Before the frozen
paper run, no threshold, target, holding horizon, stop, position size, cooldown,
event or return had been selected. The merged protocol preregistered a completed
1h decline of at least 2.40%, prior-168h median-based return and range expansion,
bottom-quartile close and 24h first-event clustering.

The frozen protocol has now run once on sealed IS. It found 210 complete events,
projecting 300 full and 90 OOS events. Median 24h MFE was 2.6908% for the
combined sample, 2.6997% for BTC and 2.6409% for ETH, so every paper Gate passed.
The same evidence shows median MAE -3.3118%, worst MAE -21.5829%, and median
24h close displacement only 0.2268%; therefore this is opportunity-envelope
evidence, not positive-expectancy evidence.

Q-01/Q-02 candidate governance merged in PR #44. The
immutable research order is M1E one-hour volatility-compression expansion,
M1G one-hour panic-dislocation mean reversion, then M1H funding-extreme spot
contrarian. M1H aliases the existing registered hypothesis rather than
creating a duplicate trial. Failure of all three stops BTC/ETH two-asset
indicator research.

The historical DSR trial count is three because M1A, M1B, and M1C opened OOS.
M1D, M1E, M1G, the daily-panic hypothesis, and M1H remain unopened. Common
cost, sealed-OOS, daily-MTM, PSR, drawdown, concentration, benchmark, and
no-rescue rules are machine checked in
`config/strategy_candidate_queue.json`.

M1E is `failed_feasibility` with OOS unopened. M1G has passed only its IS paper
Gate and awaits a fixed-rule contract; M1H remains `declared_unopened`.

Q-01/Q-02 do not authorize strategy rules, strategy code, Freqtrade
backtesting, M2, dry-run, paper trading, live trading, API keys, or execution.

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

The M1E metadata-only calendar Gate now passes locally: 2191 full days, 1533 IS
days, and 658 sealed OOS days. The sealed OOS begins `2024-09-11`; no OOS
price, signal, event, trade, or return was read.

The completed M1E sample-budget sequence remains a dependency record:

1. Treat PR #42 as the completed metadata-only sample-budget evidence.
2. M1E-04 design was approved and merged in PR #46.
3. Keep OOS sealed and do not implement strategy code or run Freqtrade backtesting.
4. Continue Binance source-owner monitoring for provenance only.

The first six-month clean suffix after the final blocked month starts
`2022-11-01`. It contains 1338 full days and 402 sealed-OOS days through
2026-06-30, so it still fails the fixed 1800/540-day calendar Gate. This suffix
is diagnostic only and must not replace the registered `2020-07-01` start.

Under ADR-0009, evidenced official 5m rows are canonical. Canonical 1h and 4h
bars are deterministic derivatives; official higher-timeframe rows remain
audit comparators. A future volume-based rule requires a new data contract. The
monthly 1m p95 spread-proxy threshold remains fixed at 0.30%.

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
