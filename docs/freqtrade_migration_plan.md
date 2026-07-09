# Freqtrade Migration Plan

The project no longer prioritizes building a full trading bot from scratch.
M0 and M1A remain valuable as data, validation, and risk-control baselines.
Freqtrade is now the primary framework for public single-leg data download,
backtesting, strategy diagnostics, and local-only WebUI hosting. M0 remains the
audit data authority, while Python keeps only strict time-semantics validation
and offline two-leg accounting.

## Current Stage

- Current phase: post-M1B Freqtrade-first hardening.
- This is not M2.
- M1A trend validation is complete and failed validation.
- The trend leg is not eligible for live trading, paper trading, or M2.

## Runtime Contract

- Official image: `freqtradeorg/freqtrade:2026.6` pinned by digest in Compose.
- Sanitized runtime metadata: `freqtrade_lab/runtime-manifest.json`.
- Approved research entry: `freqtrade_lab/scripts/ft_research.sh`.
- Freqtrade cache is disposable; M0 is authoritative when provenance differs.
- The custom M1A engine is deprecated and frozen.
- Freqtrade does not natively replace offline spot-long plus perpetual-short
  portfolio accounting.

## Hard Boundaries

- No live trading.
- No paper trading with real API credentials.
- No `execution/live`.
- No order placement or cancellation.
- No API trading permissions.
- No API keys in files, reports, logs, or git.
