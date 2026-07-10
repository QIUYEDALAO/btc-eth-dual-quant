# AGENTS.md

## Required Context Flow

Before any task, every agent must read:

- `PROJECT_STATE.yaml`
- `PROJECT_LEDGER.md`
- `NEXT_ACTION.md`
- `reports/INDEX.md`
- `AGENTS.md`
- `PROJECT_EXECUTION_CHECKLIST.md`

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
- `PROJECT_EXECUTION_CHECKLIST.md`

## Current Stage

- Current phase: P2 M1C Freqtrade implementation and time-semantics validation.
- Architecture: Freqtrade-first with an independent M0 and event-time audit sidecar.
- The four Freqtrade-first hardening PRs (#8-#11) are merged.
- M0 final status: accepted.
- M1A trend final status: failed_validation.
- M1F Freqtrade Lab final status: accepted_as_feasibility_lab.
- M1B funding-rate-arbitrage final status: failed_validation.
- M0 public dual-source REST connectivity is complete through a disclosed approved loopback proxy, but the audit remains blocked by official source revisions and missing daily archives.
- Strategy failure diagnostics are complete: freeze M1A, retain M1B as sample-limited offline research, and require a design review before any new Freqtrade strategy code.
- The approved P0-P8 roadmap is canonical; execute `PROJECT_EXECUTION_CHECKLIST.md` strictly in dependency order.
- P0 governance merged in PR #14. P1 design_pass merged in PR #15. P2 may implement only the fixed M1C Freqtrade strategy and independent timestamp checks.
- P2 must prove same-open cross-pair rotation in the pinned Freqtrade runtime or stop as `blocked_framework_capability`.
- P2 static and pinned-runtime checks passed in run 29059474678; PR #16 must merge before P3 starts.
- P0-P4 are authorized sequentially. P5-P8 are not authorized.
- No strategy is eligible for M2.
- Future work must be diagnostics or design review only.
- Diagnostics must not lower validation thresholds.
- Design review must not implement execution.
- M2 is not allowed.

## Architecture Ownership

- New single-leg strategies, public research-data downloads, backtests, and WebUI belong in Freqtrade.
- M0 Python owns canonical data lineage, append-only storage, DuckDB queries, and data-quality evidence.
- Python backtest helpers may enforce time semantics and perform offline two-leg accounting only.
- The self-managed M1A trend engine is frozen as a historical failed-validation artifact.
- Two-leg funding-arbitrage automation is prohibited without a future explicitly approved coordinator and execution phase.

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
