# ADR-0003 M1F Freqtrade Lab Accepted

- Status: Accepted
- Date: 2026-07-09

## Context

M1F deployed and validated a Freqtrade feasibility lab. The lab passed Docker
smoke checks, public spot data download, and M1A backtest smoke checks without
API keys or live trading.

## Decision

Freqtrade Lab is accepted only as a research/backtest/WebUI framework candidate.
It is not approved for live trading, paper trading with real API, M2, or native
funding-arbitrage execution.

## Consequences

- Freqtrade may be used for research and backtest feasibility exploration.
- Any funding-arbitrage use must account for cross-leg coordination and
  reconciliation gaps.
- WebUI exposure and runtime artifacts remain constrained by M1F safety rules.

## Prohibited Misinterpretations

- Freqtrade Lab acceptance is not live-trading approval.
- Freqtrade Lab acceptance is not funding-arbitrage execution approval.
- Freqtrade WebUI availability is not permission to expose public trading access.
