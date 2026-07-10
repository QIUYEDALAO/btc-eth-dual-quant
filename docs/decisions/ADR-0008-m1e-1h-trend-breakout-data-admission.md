# ADR-0008 M1E 1h Trend-Breakout Data Admission

- Status: Accepted for data qualification only
- Date: 2026-07-11

## Context

M1D cannot satisfy its fixed 540-day sealed-OOS calendar requirement because its
qualified minute-data range begins in October 2023. A different candidate may
proceed only as a separately registered trial with a separately justified data
contract. The capital owner selected a one-hour trend-breakout family for this
new trial.

## Decision

- Register `M1E-1H-TREND-BREAKOUT` as a sealed, unopened trial.
- Use Binance BTC/USDT and ETH/USDT spot, long/cash only, without leverage.
- Use completed UTC 1h bars as signal-data authority, 5m bars only for future
  fill detail and deterministic 1h reconstruction, and completed 4h bars only
  as a future regime-filter input.
- Treat official monthly ZIP archives as primary. Daily ZIP archives may fill
  missing timestamps but cannot overwrite monthly rows. Public REST is
  comparison evidence only.
- Fix the data search range to `2020-01-01` through the latest complete UTC
  month and the monthly 1m p95 spread-proxy limit to 0.30%.
- Require the first common six-month qualified BTC/ETH window before choosing a
  research start. Data quality and liquidity alone choose that date.
- Preserve exchange-wide confirmed outages as explicit non-tradable gaps. Do
  not synthesize or interpolate bars.
- Prohibit reuse of M1A's combined `SMA200 + Donchian 55/20 + ATR 2x` rule
  bundle. M1E is not an M1A timeframe rescue.
- Keep the OOS sealed. This ADR authorizes data qualification and, only after a
  data pass, a metadata-only sample-budget check. It does not authorize strategy
  rules, Freqtrade backtesting, candidate returns, or M2.

## Consequences

- M1A, M1B, M1C, and M1D retain their recorded historical statuses.
- A data conflict, single-symbol gap, unexplained aggregate mismatch, or
  insufficient calendar stops M1E without threshold changes.
- Future strategy design must pass a separate non-duplication review before any
  strategy code exists.
- Live trading, dry-run with real API, private data, credentials, order methods,
  matching, and `execution/live` remain prohibited.
