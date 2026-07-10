# BTC/ETH 15m Short-Horizon Event Quant System

## Status

- Product conditions: approved by the capital owner
- Governance implementation: T0 completed in PR #19
- Strategy implementation: not authorized before T5 and T6 pass
- M2, dry-run, live, API credentials, and order operations: prohibited
- Primary strategy framework: Freqtrade 2026.6
- Canonical data and audit authority: M0 Python

## Objective

Build a BTC/ETH spot short-horizon event system whose objective is:

> Maximize net excess return over the fixed policy benchmark, subject to daily
> mark-to-market drawdown, PSR, cost stress, data quality, and event-time Gates.

The product does not optimize absolute return, force a daily trade count, fix a
holding duration, use leverage, or rescue a failed candidate with OOS tuning.

## Frozen Historical Evidence

- M1A, M1B, and M1C remain `failed_validation`.
- The independent expert recompute reproduces all four Freqtrade M1C Sharpe
  values and corrects OOS daily-MTM results to:
  - Base Sharpe 0.7882, MaxDD 23.47%, PSR 0.902;
  - Cost x2 Sharpe 0.7528, MaxDD 24.47%, PSR 0.892.
- The corrected measurement does not reverse any frozen decision.
- The daily panic-only candidate is removed from the current product path for
  insufficient operating frequency, but remains an unopened registered idea.

## Product Contract

### Market and ownership

- Market: Binance spot.
- Tradeable pairs: `BTC/USDT`, `ETH/USDT`.
- Quote asset: USDT; cash return is zero.
- Freqtrade owns single-leg signals, backtests, research commands, and WebUI.
- M0 owns append-only raw data, lineage, golden datasets, and quality evidence.
- Python audit code may recompute timing, equity, and metrics only; it must not
  become a second single-leg strategy engine.
- `max_open_trades = 1`; no shorting, leverage, position adjustment, martingale,
  grid, or loss averaging.

### Strategy shape

Cost x2 is 0.60% round trip. A viable event therefore needs a prior gross edge
of at least 1.5%-2.0% to retain execution margin. M1D is restricted to discrete
large-dislocation events on completed 15m candles.

The current candidate family excludes continuous ordinary moving-average, RSI,
or repeated small-breakout signal streams whose typical 15m move is consumed by
the cost model. A rejected family may return only as a new registered candidate
with a new hypothesis hash and multiple-test penalty.

### Time semantics

- Main signal timeframe: 15m.
- Authoritative final backtest detail: 1m.
- 5m is development and granularity-sensitivity evidence only.
- Signals use completed 15m candles and execute no earlier than the next 15m open.
- 1m and 5m data cannot form or modify a 15m signal.
- Detail data is available only after entry to resolve trade path, stop, target,
  callback, and MTM timing.
- Same-bar-close fills are prohibited.

### Holding and trade frequency

- Holding time is an output of the frozen exit rules.
- Daily trade count has no minimum or maximum quota.
- One independent 15m event may create at most one entry candidate.
- After exit, re-entry requires a new completed 15m event.
- Frequency is reported as daily/monthly/yearly completed trades, duration
  distribution, rolling turnover, repeat entries, longest sleep, cost-to-equity,
  and 95%/99%/99.9% historical order-frequency percentiles.
- Future abnormal-order-rate controls are operational guards, not strategy quotas.

### Exit degrees of freedom

M1D may use only:

- one mean-reversion target;
- one time-expiry exit;
- one independent hard-risk stop.

Multi-level ROI tables and trailing-ROI searches are prohibited. Target and
expiry are derived once from IS event-decay evidence, frozen in the candidate
contract, and never selected from OOS.

## Data Authority

### Canonical minute data

- Download Binance public BTCUSDT and ETHUSDT spot 1m data from earliest
  availability through the latest complete UTC minute.
- Monthly ZIP is the base; daily ZIP fills omissions; REST is sampled for known
  conflict neighborhoods, first/middle/latest months, stress months, and a
  deterministic random month sample.
- REST must not mirror the full 4.5M-row-per-symbol history.
- Source conflicts are recorded and quarantined; no source silently overwrites another.
- Derive 5m and 15m deterministically from the same 1m golden dataset.
- Self-aggregated 15m rows must match official Binance 15m ZIP rows except in
  explicitly quarantined missing-minute windows.

### Liquidity-qualified start

The research start is chosen before strategy returns are computed:

```text
max(2019-01-01,
    first day of the month after BTC and ETH both pass six consecutive months)
```

A qualifying month requires 1m completeness >=99.9%, no unexplained contiguous
gap, completed ZIP/REST evidence, and p95 historical effective-spread proxy
<=0.10%. The qualification report must disclose the proxy formula and raw inputs.

### Audit states

- `audit_complete`: complete evidence, no unresolved relevant conflict.
- `audit_complete_with_quarantine`: conflicts are registered and both official
  variants produce the same Gate decisions.
- `pending_archive`: the latest official archive is not yet published and only
  results using that period are blocked.
- `blocked`: missing or conflicting evidence can change a strategy Gate.

Formal validation runs the golden version and official conflict alternatives.
Any Gate reversal blocks the candidate.

## Costs and Execution Granularity

| Scenario | Per side | Round trip | Role |
| --- | ---: | ---: | --- |
| Base | 0.15% | 0.30% | normal conservative Gate |
| Cost x2 | 0.30% | 0.60% | hard stress Gate |
| Event Stress A | 0.40% | 0.80% | x2 plus 0.10% per event side |
| Event Stress B | 0.55% | 1.10% | x2 plus 0.25% per event side |

Event stress is mandatory diagnostic evidence. Base and Cost x2 are hard Gates.

The frozen strategy runs in three modes: 15m coarse, 15m+5m detail, and
15m+1m detail. Gate status must be identical. Additional tolerances are:

- complete-trade count difference <=5%;
- annualized Sharpe absolute difference <=0.15;
- MaxDD absolute difference <=2 percentage points;
- ending-equity relative difference <=5%.

Any Gate reversal is `failed_execution_granularity_fragility`; 1m remains the
authoritative numerical result.

## Unified Metrics and Benchmark

All decision metrics use one daily MTM equity curve:

- equity = cash + liquidation-value position;
- UTC daily sampling; flat days return zero;
- arithmetic returns, `std(ddof=1)`, `sqrt(365)`, risk-free rate zero;
- Sharpe, MaxDD, Sortino, and Calmar use the same curve;
- OOS starts with fresh capital and no IS position;
- Freqtrade summary Sharpe/Drawdown is cross-check evidence only.

The policy benchmark is 25% BTC, 25% ETH, and 50% USDT, rebalanced at the
first Monday 15m open with identical modeled costs.

Hard validation requires:

- OOS is the final 30% of eligible calendar time and at least 540 days;
- OOS covers a preregistered BTC or ETH drawdown >=30%;
- OOS Sharpe >=1.0 and PSR(SR*=0) >=0.95;
- strategy Sharpe >= benchmark Sharpe;
- strategy MaxDD <= benchmark MaxDD and <=15%;
- strategy OOS net total-return excess over benchmark >0;
- Base and Cost x2 full/OOS return >0;
- at least 80 complete trades and 20 OOS complete trades;
- deleting the best three trades leaves non-negative return;
- lookahead-analysis and recursive-analysis pass;
- data-source and granularity variants do not reverse any Gate.

The 15% MaxDD is the capital owner's fixed risk limit. Most candidates are
expected to fail the combined Sharpe/PSR Gates; repeated failure never permits
threshold relaxation.

## Candidate Formation

Before OOS is opened, M1D uses IS only to measure event frequency, gross and net
edge, tail loss, clustering, capital occupancy, and returns after 1, 2, 4, 8,
12, and 24 completed 15m bars. This evidence fixes the one target, expiry, risk
stop, and constant position size.

The paper feasibility Gate requires projected >=120 full-sample and >=30 OOS
events, positive mean net edge under Cost x2, no dependence on a few extreme
events, a feasible 15% stress-path risk budget, deterministic Freqtrade
expression, and a return hypothesis distinct from M1A/M1B/M1C.

Failure stops before strategy code. Any post-freeze rule change creates a new
candidate ID and increases the DSR multiple-test count.

## Compute and Artifact Boundaries

- Static CI runs tests, fixed fixtures, security scans, and small public smokes.
- Eight-year BTC/ETH 1m-detail validation runs locally or on the VPS, not as a
  required GitHub-hosted job.
- Only sanitized reports, manifests, hashes, and provenance are committed.
- Raw minute data, DuckDB, Freqtrade caches/results, logs, and private payloads
  remain ignored.

## Authorization

After T0 merges, only T1-T4 foundations and T5 feasibility are authorized in
dependency order. T6-T9 require their preceding Gates. M2, dry-run, live,
credentials, orders, cancellation, and execution remain not authorized.
