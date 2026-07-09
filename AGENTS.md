# AGENTS.md

## Current Stage

- Current phase: M1A trend backtest validation only.
- M0 final status: accepted.
- M1A permits offline backtest validation only.

## Hard Guardrails

- Do not create or use `execution/live`.
- Do not implement or call order placement, order cancellation, `create_order`, `cancel_order`, or `place_order`.
- Do not implement live trading or paper trading.
- Do not implement simulated matching, matching engines, or execution modules.
- Do not call trading-permission APIs.
- Do not read, request, print, or require API keys.
- Do not hardcode an 8-hour funding interval; infer funding cadence from data sources.
- Do not allow same-bar close fills; signals after a bar close may only become effective no earlier than the next bar open.
- Backtest modules may contain offline next-open fill assumptions for validation only; they must not become paper/live execution logic.

## Commit Hygiene

- Do not commit `.env`, `.env.*`, API keys, secrets, PEM/key files, `storage/raw/`, DuckDB files/databases, `storage/logs/`, or private smoke raw output.
- `reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md` is local-only and must not be committed.
- All future development must start from a new branch. Do not push directly to `main`.
