# Project Execution Checklist

This is the canonical task-status view for the Freqtrade-first BTC/ETH system.
Statuses are `pending`, `in_progress`, `completed`, `blocked`, or
`not_authorized`.

| Task ID | Phase | Status | Dependency | Branch / PR | Output | Acceptance gate | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | P0 governance | completed | none | `codex/strategy-failure-diagnostics` / #14 | End-to-end roadmap spec | Approved plan recorded | none |
| P0-02 | P0 governance | completed | P0-01 | `codex/strategy-failure-diagnostics` / #14 | Implementation plan | P0-P8 dependencies and rollback fixed | none |
| P0-03 | P0 governance | completed | P0-02 | `codex/strategy-failure-diagnostics` / #14 | This checklist | Required columns and statuses present | none |
| P0-04 | P0 governance | completed | P0-03 | `codex/strategy-failure-diagnostics` / #14 | Five context files updated | Context check pass | none |
| P0-05 | P0 governance | completed | P0-04 | `codex/strategy-failure-diagnostics` / #14 | Merged governance PR | Local and GitHub checks pass | none |
| P1-01 | P1 design | completed | P0-05 | `codex/m1c-btc-eth-rotation-design` | Fixed M1C specification and machine-readable contract | No ambiguous rule or parameter | none |
| P1-02 | P1 design | completed | P1-01 | same P1 PR | Pinned Freqtrade capability evidence | Unique winner and rotation ordering proven | P2 runtime fixture still required |
| P1-03 | P1 design | completed | P1-02 | `codex/m1c-btc-eth-rotation-design` / #15 | Design decision | `design_pass` plus PR/CI review required | none |
| P2-01 | P2 implementation | completed | P1-03 | `codex/m1c-btc-eth-rotation-validation` / #16 | Freqtrade strategy and public config | Behavior tests pass | none |
| P2-02 | P2 implementation | completed | P2-01 | same P2 PR | Guarded research commands | No trade/live command | none |
| P2-03 | P2 implementation | completed | P2-02 | `codex/m1c-btc-eth-rotation-validation` / #16 | Time-semantics and runtime tests | Next-open, same-open switch, UTC ranking, lookahead and recursive pass | none |
| P3-01 | P3 validation | completed | P2-03 | `codex/m1c-btc-eth-rotation-backtest` / #17 | Public Freqtrade data and provenance | Exact used range has no unexplained gap | none |
| P3-02 | P3 validation | completed | P3-01 | same validation PR | Base/cost-x2, OOS, segment results | Every fixed numerical gate evaluated | none |
| P3-03 | P3 validation | completed | P3-02 | `codex/m1c-btc-eth-rotation-backtest` / #17 | M1C failed-validation report | Truthful `failed_validation` merged | none |
| P4-01 | P4 audit | blocked | P3-03 pass required | `codex/m1c-independent-audit` | Independent timing and PnL audit | Timestamp exact, error <= 1e-8 | P3 failed: trade count, OOS Sharpe, and drawdown gates |
| P4-02 | P4 audit | blocked | P4-01 | same P4 PR | Final M1C research status | M0 and numerical gates combined | P4 not allowed after P3 failure |
| P5-01 | P5 M2 design | not_authorized | P4-02 plus explicit approval | future branch | M2 ADR | Separate approval | M2 prohibited |
| P6-01 | P6 dry-run | not_authorized | P5-01 plus explicit approval | future branch | 90-day dry-run report | 12 weekly decisions and no live orders | dry-run prohibited |
| P7-01 | P7 limited live | not_authorized | P6-01 plus explicit approval | future branch | Limited-capital acceptance | Hard risk controls and separate approval | live prohibited |
| P8-01 | P8 operations | not_authorized | P7-01 | future branch | Operations and scaling loop | Continuous audit | live prohibited |
| T0-01 | Short-horizon governance | completed | M1C closed | `codex/short-horizon-product-governance` / PR #19 | Approved specification, ADR-0007, expert evidence, trial ledger | Isolated recompute, automated ledger hash check, context, CI, merge | none |
| T1-01 | Canonical minute data | completed | T0-01 completed | `codex/short-horizon-t1-minute-data` / PR #21 | BTC/ETH spot 1m source archive and liquidity qualification | Exact range, hashes, completeness, preregistered start | none |
| T2-01 | Golden data and quarantine | completed | T1-01 completed | `codex/short-horizon-t2-golden-data` / PR #23 | Golden 1m, quarantine, 5m/15m derivatives, Freqtrade jsongz cache | Complete research range, 66 official 15m parity checks, pinned runtime readability, T2 Validate 9/0, CI and merge pass | none |
| T3-01 | Unified metrics | completed | T2-01 completed | `codex/short-horizon-t3-unified-metrics` / PR #25 | General daily-MTM, PSR/DSR, diagnostics and policy benchmark | Sealed M1C regression, 157 tests, T3 Validate 10/0, CI and merge pass | none |
| T4-01 | Feasibility harness | completed | T3-01 completed | `codex/short-horizon-t4-feasibility-harness` / PR #27 | IS-only event decay, fixed costs, frequency, clustering, path risk, occupancy and sample-budget tooling | 169 tests, T4 Validate 10/0, no candidate evaluation, no OOS return access, CI and merge pass | none |
| T5-01 | M1D feasibility | blocked | T4-01 completed | `codex/short-horizon-t5-sample-budget-precheck` / PR #29 | Metadata-only M1D sample-budget precheck | 178 tests, T5 Validate 10/0, sealed OOS, no return access, CI and merge pass | 302 OOS days < fixed 540-day minimum; earliest projected resolution 2028-09-03 |
| T6-01 | M1D fixed design | blocked | T5-01 pass | future branch | Fixed contract and hash | No TBD, optional ROI, or OOS choice | T5 failed calendar Gate; M1D stopped |
| T7-01 | M1D Freqtrade implementation | pending | T6-01 | future branch | 15m strategy, 1m/5m research commands, tests | Behavior, timing, bias and no-live pass | T6 must pass |
| T8-01 | M1D historical validation | pending | T7-01 | future branch | Full/OOS/cost/granularity/data-variant report | Every numerical and data Gate evaluated | T7 must pass |
| T9-01 | M1D independent audit | pending | T8-01 pass | future branch | Timing, equity, benchmark and sensitivity audit | Evidence exact and all Gates pass | T8 must pass |
| M1E-01 | M1E product/data contract | in_progress | separately approved new trial | `codex/m1e-1h-product-data-contract` / PR #31 | ADR-0008, sealed trial identity, machine-readable contract | Contract, non-reuse, ledger, context, safety and CI pass | strategy/OOS/backtesting remain unauthorized |
| M1E-02 | M1E public-data qualification | pending | M1E-01 completed | `codex/m1e-1h-public-data-qualification` | Official 5m/1h/4h golden data, parity, quarantine, cache and report | Common six-month data/liquidity qualification and Freqtrade list-data pass | PR1 must merge first |
| M1E-03 | M1E sample budget | pending | M1E-02 pass | `codex/m1e-1h-sample-budget` | Metadata-only 70/30, 1800/540-day report | Actual qualified calendar passes both fixed minimums | create only after data qualification passes |
| M1E-04 | M1E IS-only rule design | not_authorized | M1E-03 pass plus separate approval | future branch | Non-M1A trend-breakout rule contract | No duplicate rule bundle and no OOS access | data and calendar Gates not yet passed |

## Current Gate

- Authorized work: M1E product/data contract, followed conditionally by public-data qualification and metadata-only sample budget.
- Active implementation: M1E contract only; candidate evaluated `no`, OOS opened `no`, strategy code authorized `no`.
- T5 final status: `blocked_insufficient_oos_calendar`; 302 OOS days < 540 required days.
- No M1D event definition, feasibility return run, or strategy code is authorized.
- Stop reason for M1C: failed P3 fixed numerical gates; its P4 remains blocked.
- M1A status: `failed_validation`.
- M1B status: `failed_validation`.
- M0 audit status: `audit_revalidation_required`.
- M2 status: blocked.
- Trading approval: none.
- Short-horizon product: discrete 15m events, 1m authoritative detail, 5m sensitivity, no fixed holding time or daily trade quota.
