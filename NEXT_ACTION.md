# Next Action

## Current Decision

The ADR-0011 public archive run discovered 676 historical USDT spot symbols and
rebuilt 78 monthly Top-15 snapshots with 1,170 membership rows. All 151 original
blocked symbol-month observations are attributed: 15 unique synchronous Binance
outage windows produced 225 per-symbol gap runs, while LUNAUSDT 2022-05 and
RNDRUSDT 2024-07 are isolated without replacement. Processing errors and
unresolved gaps are zero. Qualification is `pass_with_quarantine`.

ADR-0011 is frozen pending review. It defines a monthly point-in-time Top-15
Binance USDT spot universe using the prior 90 complete UTC days' median daily
quote volume, 365 complete history days, deterministic symbol tie-break and
conservative asset exclusions. BTC and ETH remain eligible and also serve as
regime/risk benchmarks.

M1H-03 is complete. Public funding-data qualification passed, then the one
frozen sealed-IS paper observation failed feasibility without changing the
protocol or opening OOS.

- Independent market episodes: 131.
- Projected full / sealed-OOS episodes: 187 / 56.
- Combined median 24h close displacement: 0.0714% versus 1.80% required.
- BTCUSDT / ETHUSDT median 24h close displacement: 0.0731% / 0.0132%.
- Maximum single-year episode share: 48.09% versus 45% allowed.
- Median 24h MFE: 2.3108%, disclosed as path evidence only and not a Gate override.

M1H is `failed_feasibility`; PR #65 merged the truthful stop record at
`57c2b1c`. M1H fixed rules, strategy implementation, backtesting and OOS
opening are blocked. M1E, M1G and M1H have exhausted the frozen ADR-0010
BTC/ETH two-asset candidate queue.

## Allowed Next Work

1. Review PR #68 and require all CI checks to pass before merge; or
2. Continue M0 public dual-source audit diagnostics without private data.

This qualification pass does not authorize a cross-sectional hypothesis,
strategy code, event scan, returns, OOS, backtesting or M2.

ADR-0011 must freeze point-in-time membership, listings and delistings,
survivorship controls, liquidity admission and cross-sectional UTC alignment.
It may authorize a later asset-qualification stage only. It does not inherit
permission to choose a strategy, scan events, calculate returns, access OOS or
enter M2.

## Prohibited

- Freqtrade-first remains the architecture for any future single-leg research.
- No strategy is eligible for M2.
- Do not enter M2.
- Do not change the M1H percentile, 365-day window, horizons, interval policy, clustering or Gates.
- Do not add a fourth BTC/ETH indicator candidate or reuse this sealed IS outcome for parameter selection.
- Do not rescue M1B, M1G or M1H through a broader symbol list.
- Do not write M1H fixed rules, strategy code, Freqtrade implementation or a backtest.
- Do not open OOS or increment the DSR opened-trial count.
- Do not access API keys, private data, private smoke, dry-run/live, orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.
- M2 remains blocked and no strategy is approved for trading.
