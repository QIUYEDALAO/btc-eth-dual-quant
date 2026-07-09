# Freqtrade Primary Framework Hardening

- Status: pass
- Generated UTC: 2026-07-09T20:21:53Z
- Scope: Freqtrade primary single-leg research framework only
- M2 approval: no
- Live trading approval: no
- Paper trading with real API approval: no
- API key used: no

## Immutable Runtime

- Image: `freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`
- Observed Freqtrade version: `freqtrade 2026.6`
- Observed Python version: `3.14.6`
- Observed CCXT version: `4.5.61`
- Runtime manifest validation: pass
- Compose tag/digest/version consistency: pass

## Approved Research Surface

The single entrypoint is `freqtrade_lab/scripts/ft_research.sh` and accepts only:

- `download-data`
- `list-data`
- `backtesting`
- `lookahead-analysis`
- `recursive-analysis`
- `webserver`, bound to `127.0.0.1:8080`

No repository entrypoint starts a trading runner, live mode, or paper mode with real API credentials.

## VPS Public Smoke

| Check | Result |
|---|---|
| Pinned image pull | pass |
| Runtime version/digest verification | pass |
| Public BTC/ETH spot download | pass |
| `list-data` | pass |
| Historical M1A reproduction backtest | pass |
| `lookahead-analysis` | pass; no bias detected in five targeted signals |
| `recursive-analysis` | pass; no recursive variance or indicator lookahead detected |
| Webserver command help without starting a service | pass |
| Error-log guard after configuration correction | pass |

The historical M1A reproduction produced 33 trades and is retained only as a framework smoke artifact. Its profitability output is not a strategy approval; M1A remains `failed_validation` and is not eligible for M2.

Freqtrade 2026.6 emitted an asynchronous connector cleanup warning after the completed lookahead and recursive analyses. The commands completed and their analysis results were emitted, but this warning remains a runtime limitation to monitor on future pinned upgrades.

## Data Provenance

- Evidence: `reports/m1/FREQTRADE_M0_DATA_PROVENANCE.md`
- BTCUSDT 1d: 3,248 M0 rows = 3,248 Freqtrade rows; zero missing timestamps; zero field differences.
- ETHUSDT 1d: 3,248 M0 rows = 3,248 Freqtrade rows; zero missing timestamps; zero field differences.
- Range: 2017-08-17 through 2026-07-08 UTC.
- Result: pass.
- Runtime data, raw data, DuckDB, logs, sqlite, and backtest results committed: no.

## Ownership Decision

- Freqtrade is the only active framework for new single-leg strategy research.
- The self-managed M1A engine is deprecated and frozen.
- M0 remains the canonical audit-data authority.
- Python remains active for strict event-time checks and offline two-leg accounting only.
- Funding-arbitrage execution still requires a future separately approved coordinator and remains prohibited.
- M0 audit revalidation remains blocked by the separate evidence in `reports/m0/M0_AUDIT_REVALIDATION_REPORT.md`.

This framework hardening does not approve M2, real capital, live trading, order placement, cancellation, simulated matching, API trading permissions, or `execution/live`.
