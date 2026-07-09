# Next Action

Generate the real M1B funding-arbitrage numerical report using local M0 public data from raw/DuckDB storage.

Context:

- PR #5 suitability conclusion B is accepted.
- Freqtrade is partially suitable but not sufficient as native funding-arbitrage backtest/execution engine.
- Custom offline portfolio/accounting/funding backtester remains a research candidate.
- Numerical validation is still pending.

Rules:

- Do not enter M2.
- Do not merge PR #5 as completed numerical validation until a real report exists.
- Do not run live trading.
- Do not run paper trading with real API.
- Do not request, read, or use API keys.
- Do not run private smoke.
- Do not commit storage/raw, DuckDB, logs, or Freqtrade runtime data.

Expected output:

- M1B numerical report with base cost, cost x2, cycles, OOS, drawdown, funding income, basis PnL, and final M1B gate status.
