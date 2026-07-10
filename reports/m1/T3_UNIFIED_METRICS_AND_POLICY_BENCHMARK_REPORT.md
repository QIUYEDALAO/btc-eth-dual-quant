# T3 Unified Metrics and Policy Benchmark Report

- Status: pass
- Generated UTC: 2026-07-10T14:25:30+00:00
- Scope: unified measurement and policy-benchmark foundation only
- New strategy evaluated: no
- New candidate OOS opened: no
- Strategy returns computed: no; only sealed M1C regression evidence was recomputed
- API key used: no
- Live/paper/execution implemented: no

## Unified Convention

- One continuous UTC daily mark-to-market equity curve; flat days return zero.
- Arithmetic daily returns, sample standard deviation (`ddof=1`), `sqrt(365)`, and zero risk-free rate.
- Sharpe, MaxDD, Sortino, Calmar, PSR, and DSR share the same curve.
- Freqtrade summary metrics remain diagnostics only and cannot override unified metrics.
- Trade adapter consumes completed Freqtrade exports and public golden price marks; it does not generate signals.

## Fixed Policy Benchmark

- Allocation: 25% BTC, 25% ETH, 50% USDT.
- Rebalance: every Monday at the UTC open.
- Costs: identical modeled per-side costs applied to traded notional.
- Benchmark builder is fixture-tested here; no candidate comparison or new OOS return is produced in T3.

## Sealed M1C Regression

- Fixture: `reports/expert/m1c_oos_daily_equity.csv`
- Fixture SHA256: `842291287ca64967831fb36d1d1af2cbea4c77a80663f283d238f490e0a06bda`
- Range: 2023-11-08 through 2026-07-09 UTC

| Scenario | Observations | Total return | CAGR | Annual vol | Sharpe | MaxDD | Sortino | Calmar | PSR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Base | 975 | 53.4431% | 17.4039% | 23.9985% | 0.7882 | 23.4729% | 1.1976 | 0.7414 | 0.9024 |
| Cost x2 | 975 | 49.9456% | 16.3938% | 23.9719% | 0.7528 | 24.4688% | 1.1411 | 0.6700 | 0.8920 |

## Foundation Coverage

- Freqtrade completed-trade adapter and daily public-price MTM: implemented and fixture-tested.
- Policy benchmark with Monday-open rebalance and costs: implemented and fixture-tested.
- PSR and DSR with multiple-trial penalty: implemented and fixture-tested.
- Cost attribution: implemented and fixture-tested.
- Frequency, turnover, duration, sleep, and concentration diagnostics: implemented and fixture-tested.
- Granularity Gate comparison with mandatory Gate-status consistency: implemented and fixture-tested.

## Gate

| Check | Status |
|---|---|
| Sealed expert CSV hash | pass |
| Base Sharpe regression | pass |
| Base MaxDD regression | pass |
| Base PSR regression | pass |
| Cost x2 Sharpe regression | pass |
| Cost x2 MaxDD regression | pass |
| Cost x2 PSR regression | pass |
| Consecutive UTC daily observations | pass |

- T4 authorized: yes
- M1D feasibility authorized: no; T4 must pass first
- M1D strategy code authorized: no
- M2 authorized: no

Historical M1C remains `failed_validation`; this regression validates measurement code and does not rescue or approve that strategy.
