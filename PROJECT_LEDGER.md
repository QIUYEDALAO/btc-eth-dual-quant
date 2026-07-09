# Project Ledger

This ledger is append-only. Add new records at the bottom. Do not store API keys,
server private keys, account data, raw payloads, balances, income amounts, or
private exchange responses here.

---

## 2026-07-09 - M0 Accepted

- Date UTC: 2026-07-09
- Task ID: M0-FINAL-ACCEPTANCE
- Phase: M0 data engineering
- Branch: main
- Commit: 6b78180
- PR: #1, #2
- Request summary: Complete read-only data engineering acceptance with public data, scheduler dry-run, anomaly review, and private read-only smoke sanitized status.
- Completed: M0 final status accepted; no execution/live; no order placement; no private payload committed.
- Not completed: M1 strategy validation and any trading approval.
- Validation: M0 Validate success; final acceptance recorded in `reports/m0/M0_FINAL_ACCEPTANCE.md`.
- Decision: M0 data engineering accepted.
- Blockers: None for M0; M1 remained backtest-validation only.
- Next action: Proceed only to offline M1 validation.

## 2026-07-09 - M1A Trend Failed Validation

- Date UTC: 2026-07-09
- Task ID: M1A-TREND-FAILED-VALIDATION
- Phase: M1A trend backtest validation
- Branch: main
- Commit: 4ee17aa
- PR: #3
- Request summary: Record fixed-parameter BTC/ETH trend validation truthfully.
- Completed: M1A report and review decision merged as failed_validation.
- Not completed: Trend strategy approval for M2, paper trading, or live trading.
- Validation: M0 Validate and M1A Validate success.
- Decision: Trend leg is not eligible for M2 or live trading.
- Blockers: OOS Sharpe below threshold, trade count below threshold, delete-best-3 result below breakeven.
- Next action: Funding-rate-arbitrage validation may be explored only as a separate offline M1B track.

## 2026-07-09 - M1F Freqtrade Feasibility Accepted

- Date UTC: 2026-07-09
- Task ID: M1F-FREQTRADE-FEASIBILITY
- Phase: M1F Freqtrade feasibility lab
- Branch: main
- Commit: 98693bb
- PR: #4
- Request summary: Accept Freqtrade Lab as a research/backtest/WebUI framework candidate after VPS and Docker smoke checks.
- Completed: Freqtrade Lab accepted_as_feasibility_lab; final acceptance report merged.
- Not completed: Funding-arbitrage execution support, live trading, paper trading with real API, M2 approval.
- Validation: M0 Validate, M1A Validate, and M1F Validate success.
- Decision: Freqtrade is useful as a research/backtest/WebUI candidate; not approved for live trading or funding-arbitrage execution.
- Blockers: Funding arbitrage requires external arbitrage coordinator or further suitability review.
- Next action: Review Freqtrade suitability before deciding whether M1B should use Freqtrade or a custom offline accounting engine.

## 2026-07-09 - M1B PR #5 Under Review

- Date UTC: 2026-07-09
- Task ID: M1B-PR5-UNDER-REVIEW
- Phase: M1B funding-rate-arbitrage research validation
- Branch: m1b-funding-arbitrage-offline-backtest
- Commit: PR #5 head 8d710bc
- PR: #5 open
- Request summary: Implement and then pause custom M1B funding-arbitrage offline backtest pending Freqtrade suitability review.
- Completed: PR #5 is open and CI passed on its branch; PR body says no result approves live trading.
- Not completed: Real M1B numerical report on main; final M1B decision; M2 approval.
- Validation: PR #5 checks passed on branch, but PR remains open and unmerged.
- Decision: Do not continue custom M1B numerical validation until Freqtrade suitability is reviewed.
- Blockers: Need suitability decision A/B/C for Freqtrade funding-arbitrage backtest capability.
- Next action: Review Freqtrade suitability for spot-long plus perpetual-short funding-arbitrage backtest before continuing custom numerical report.

## 2026-07-09 - Project Context System

- Date UTC: 2026-07-09
- Task ID: PROJECT-CONTEXT-SYSTEM
- Phase: Project governance
- Branch: project-ledger-and-context-system
- Commit: project-ledger-and-context-system PR head
- PR: pending
- Request summary: Add repository-level project state, ledger, next action, report index, ADRs, and context validation scripts.
- Completed: Added project state, append-only ledger, next-action file, reports index, ADRs, context summary/check scripts, project validation script, and project validation workflow.
- Not completed: No strategy validation, M1B numerical report generation, M2 approval, live trading, paper trading, private smoke, or trading logic changes.
- Validation: `python3 scripts/project_context_check.py` pass; `python3 scripts/context_summary.py` pass; `bash scripts/project_validate.sh` pass with PASS=6 FAIL=0.
- Decision: Future tasks must read context files before acting and update the ledger after completion.
- Blockers: None expected.
- Next action: Run `bash scripts/project_validate.sh`, commit, push, and open PR.
