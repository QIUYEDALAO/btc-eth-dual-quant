# AGENTS.md

## Required Context Flow

Before any task, every agent must read:

- `PROJECT_STATE.yaml`
- `PROJECT_LEDGER.md`
- `NEXT_ACTION.md`
- `reports/INDEX.md`
- `AGENTS.md`

Before coding, the agent must summarize:

- `current_phase`
- prohibited actions
- active blockers
- intended files to modify

After any task, the agent must update:

- `PROJECT_STATE.yaml`
- `PROJECT_LEDGER.md`
- `NEXT_ACTION.md`
- `reports/INDEX.md` if reports changed

## Current Stage

- Current phase: M1B funding-rate-arbitrage research validation.
- M0 final status: accepted.
- M1A trend final status: failed_validation.
- M1F Freqtrade Lab final status: accepted_as_feasibility_lab.
- M1B PR #5 is open / under_review.
- M1B permits offline funding-rate-arbitrage backtest validation only.
- M2 is not allowed.

## Hard Guardrails

- No live trading.
- No paper trading with real API.
- Do not create or use `execution/live`.
- Do not implement or call order placement, order cancellation, `create_order`, `cancel_order`, or `place_order`.
- Do not implement simulated matching, matching engines, or execution modules.
- Do not call trading-permission APIs.
- Do not read, request, print, or require API keys.
- Do not run private smoke unless the user explicitly starts a future approved private-smoke task.
- Do not hardcode an 8-hour funding interval; infer funding cadence from data sources.
- Do not use future data in backtests.
- Do not allow same-bar close fills; signals after a bar close may only become effective no earlier than the next bar open.
- Do not tune parameters, lower payback thresholds, remove cost stress, remove OOS checks, or otherwise reshape validation to pass.
- Do not rewrite `failed_validation` to `pass` without new evidence and an explicit approval path.
- Do not merge PRs unless checks and ledger are updated.
- Backtest modules may contain offline validation accounting only; they must not become paper/live execution logic.

## Commit Hygiene

- Do not commit `.env`, `.env.*`, API keys, secrets, PEM/key files, `storage/raw/`, DuckDB files/databases, `storage/logs/`, Freqtrade runtime data, or private smoke raw output.
- `reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md` is local-only and must not be committed.
- All future development must start from a new branch. Do not push directly to `main`.
