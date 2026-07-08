# AGENTS.md

## Current Stage

- Current phase: M0-DATA-RUN hardening.
- M1 remains blocked.

## Hard Guardrails

- Do not create or use `execution/live`.
- Do not implement or call order placement, order cancellation, `create_order`, `cancel_order`, or `place_order`.
- Do not implement simulated matching.
- Do not call trading-permission APIs.
- Do not hardcode an 8-hour funding interval; infer funding cadence from data sources.
- Do not allow same-bar close fills; signals after a bar close may only become effective no earlier than the next bar open.

## Commit Hygiene

- Do not commit `.env`, `.env.*`, API keys, secrets, PEM/key files, `storage/raw/`, DuckDB files/databases, `storage/logs/`, or private smoke raw output.
- `reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md` is local-only and must not be committed.
- All future development must start from a new branch. Do not push directly to `main`.
