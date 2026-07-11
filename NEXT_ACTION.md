# Next Action

## Current Decision

M1H-03 is complete. Public funding-data qualification passed, then the one
frozen sealed-IS paper observation failed feasibility without changing the
protocol or opening OOS.

- Independent market episodes: 131.
- Projected full / sealed-OOS episodes: 187 / 56.
- Combined median 24h close displacement: 0.0714% versus 1.80% required.
- BTCUSDT / ETHUSDT median 24h close displacement: 0.0731% / 0.0132%.
- Maximum single-year episode share: 48.09% versus 45% allowed.
- Median 24h MFE: 2.3108%, disclosed as path evidence only and not a Gate override.

M1H is `failed_feasibility`; M1H fixed rules, strategy implementation,
backtesting and OOS opening are blocked. M1E, M1G and M1H have now exhausted
the frozen ADR-0010 BTC/ETH two-asset candidate queue.

## Allowed Next Work

1. Complete and merge the truthful M1H-03 failure record.
2. Continue M0 public dual-source audit diagnostics without private data; or
3. Create a new product ADR for a broader, historically reconstructable set of high-liquidity USDT spot pairs.

The broader-universe route must first address dynamic membership, listings and
delistings, survivorship bias, liquidity admission, cross-sectional UTC
alignment, maximum holdings and concentration. It does not inherit permission
to write a strategy, access OOS or enter M2.

## Prohibited

- Freqtrade-first remains the architecture for any future single-leg research.
- No strategy is eligible for M2.
- Do not enter M2.
- Do not change the M1H percentile, 365-day window, horizons, interval policy, clustering or Gates.
- Do not add a fourth BTC/ETH indicator candidate or reuse this sealed IS outcome for parameter selection.
- Do not write M1H fixed rules, strategy code, Freqtrade implementation or a backtest.
- Do not open OOS or increment the DSR opened-trial count.
- Do not access API keys, private data, private smoke, dry-run/live, orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.
- M2 remains blocked and no strategy is approved for trading.
