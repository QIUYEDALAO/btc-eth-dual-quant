# Freqtrade-First BTC/ETH Quant System End-to-End Roadmap

## Status

- Design status: approved
- Current authorization: P0 through P4 only
- M2, dry-run, live trading, and trading API permissions: blocked
- Primary framework: Freqtrade
- Data authority: M0 Python audit sidecar

## Objective

Build an auditable BTC/ETH spot quant system that can progress from a fixed
research hypothesis to independently verified Freqtrade results and, only
after future approvals, controlled automation. A successful research result
never grants automatic permission to enter a later stage.

## Ownership

| Capability | Owner |
| --- | --- |
| Single-leg strategy, public downloads, backtesting, WebUI, future automation | Freqtrade |
| Registry, lineage, append-only raw storage, DuckDB, data quality | M0 Python |
| Lookahead and next-open time-semantics audit | Python audit sidecar |
| Spot-long plus perpetual-short offline accounting | Python M1B sidecar |
| Two-leg execution | Prohibited without a future coordinator and execution approval |

Freqtrade is the only source of single-leg strategy-return truth. Python must
not grow a second complete single-leg backtest engine.

## Stage Model

| Stage | Purpose | Exit gate | Authorized now |
| --- | --- | --- | --- |
| P0 | Governance and master checklist | CI and context consistency | yes |
| P1 | Fixed M1C strategy design | No ambiguous rule or parameter | yes |
| P2 | Freqtrade implementation | Static, behavior, and timing tests | yes |
| P3 | Historical validation | Every fixed numerical gate passes | yes |
| P4 | Independent audit | M0/Freqtrade/Python evidence agrees | yes |
| P5 | M2 readiness design | New ADR and explicit approval | no |
| P6 | Freqtrade dry-run | Future approval and 90-day evidence | no |
| P7 | Limited-capital automation | Future approval and hard controls | no |
| P8 | Operations and scaling | Continuous audit | no |

## M1C Fixed Hypothesis

The first new candidate is a BTC/ETH/cash weekly rotation implemented on UTC
daily spot candles:

- Universe: `BTC/USDT`, `ETH/USDT`.
- Sunday completed-candle close is the only weekly decision point.
- A decision can take effect no earlier than the next daily open.
- Absolute eligibility: close above SMA(200) and 90-day return above zero.
- Relative score: `close / close.shift(90) - 1`.
- Hold the eligible asset with the higher score; hold cash when neither is
  eligible; exact ties select BTC deterministically.
- Maximum one position, no shorting, no leverage, no position adjustment.
- Maximum stake is 50% of available equity; at least 50% remains cash.
- Emergency stop is -20%; no ROI exit, trailing stop, martingale, grid, or
  hyperopt.

If Freqtrade cannot deterministically express the unique-winner signal or
same-open exit-before-entry rotation, P1 is
`blocked_framework_capability`. The project must not disguise the limitation
with a second custom strategy engine.

## Historical Validation Contract

- Public data range: 2017-08-17 through the latest complete UTC day.
- Final 30% of time is sealed OOS.
- The first 70% is split into four contiguous robustness segments.
- Base effective cost: 0.15% per side.
- Cost x2 effective cost: 0.30% per side.
- No result may change the fixed strategy rules or select parameters.

The M1C numerical gate requires:

- at least 80 complete trades overall and 20 complete OOS trades;
- OOS Sharpe at least 1.0;
- positive full-period and OOS return under base and cost x2;
- maximum drawdown no greater than 15%;
- non-negative return after deleting the best three trades;
- at least three of four robustness segments positive;
- passing lookahead and recursive analyses;
- no unexplained data gaps.

Any failed item produces `failed_validation`. Passing all numerical items can
produce only `under_review` until P4 completes.

## Independent Audit Contract

P4 must verify:

- M0 and Freqtrade symbol/range/row/OHLCV/hash provenance;
- signal time after the source candle close;
- next-daily-open fills only;
- BTC and ETH ranking on the same UTC cross-section;
- exact entry and exit timestamps;
- independently recalculated fees and PnL within absolute error `1e-8`.

M2 remains blocked unless the relevant M0 dual-source audit is pass. If the
strategy gates pass while M0 remains blocked, the maximum status is
`passed_numerical_data_audit_blocked`.

## Future Stages

P5 through P8 are design-only placeholders. They cannot be implemented by
this approval. Future work requires a new ADR and explicit approval before
dry-run, API credentials, order behavior, or live trading is introduced.

## Failure and Rollback

- P1 framework failure: stop M1C and record the capability blocker.
- P2 behavior failure: fix implementation without changing the hypothesis.
- P3 gate failure: record `failed_validation`; do not tune or lower gates.
- P4 evidence failure: repair data or audit semantics; do not alter returns.
- Any later operational incident returns the project to P5 or earlier.
