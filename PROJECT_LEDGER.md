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
- Commit: 7a0f2bceb0ae7e70533ee6ce60ca61ce44d1980a
- PR: #6 open
- Request summary: Add repository-level project state, ledger, next action, report index, ADRs, and context validation scripts.
- Completed: Project context system added and PR #6 opened for review.
- Not completed: No strategy validation, no M2, no live/paper/API/private smoke/trading logic.
- Validation: project_context_check pass; context_summary pass; project_validate pass; M0/M1A/M1F/Project Validate GitHub Actions success.
- Decision: Future tasks must read context files before acting and update ledger/state/next action after completion.
- Blockers: PR #6 itself requires review/merge before the project context system is active on main.
- Next action: Review and merge PR #6 after checks pass; then use the context system for PR #5 suitability review.

## 2026-07-09 - PR #5 Suitability Review Pending

- Date UTC: 2026-07-09
- Task ID: PR5-SUITABILITY-REVIEW-PENDING
- Phase: M1B funding-rate-arbitrage research validation
- Branch: m1b-funding-arbitrage-offline-backtest
- Commit: PR #5 head 8d710bcdc3850b92e99fff82c7a57e2f6d33c502
- PR: #5 open
- Request summary: Record that PR #5 now contains a Freqtrade funding-arbitrage suitability finding that still needs review.
- Completed: PR #5 now contains Freqtrade suitability conclusion B.
- Not completed: PR #5 remains open and must not be merged as completed numerical validation.
- Validation: Conclusion B is a report finding on open PR #5, not an accepted main-branch decision.
- Decision: Conclusion B means Freqtrade is partially suitable, but funding-rate arbitrage still requires external portfolio/accounting/funding backtester.
- Blockers: Review whether to accept conclusion B and decide the custom M1B backtester path.
- Next action: Review whether to accept conclusion B and decide the custom M1B backtester path.
- Guardrails: M2/live/paper/API/trading remain prohibited.

## 2026-07-09 - PR #5 Suitability Conclusion B Accepted

- Date UTC: 2026-07-09
- Task ID: PR5-SUITABILITY-CONCLUSION-B-ACCEPTED
- Phase: M1B funding-rate-arbitrage research validation
- Branch: m1b-funding-arbitrage-offline-backtest
- Commit: f17389f06152921ffcc9a8cef6773019e8632fb4
- PR: #5 open
- Request summary: Review PR #5 Freqtrade suitability finding and decide whether to adopt conclusion B.
- Completed: Conclusion B accepted as project decision on PR #5.
- Not completed: No real numerical M1B funding-arbitrage report yet; no M2; no live/paper/API/trading.
- Validation: scripts/project_validate.sh and scripts/m1b_validate.sh pass.
- Decision: Freqtrade is partially suitable but needs external portfolio/accounting/funding backtester.
- Blockers: Numerical report still requires local M0 public raw/DuckDB data.
- Next action: Generate real numerical M1B funding-arbitrage report offline from public data.

## 2026-07-09 - M1B Numerical Report Generated

- Date UTC: 2026-07-09
- Task ID: M1B-NUMERICAL-REPORT-GENERATED
- Phase: M1B funding-rate-arbitrage research validation
- Branch: m1b-funding-arbitrage-offline-backtest
- Commit: 885c02961e7b5934675a6f64eca4c0bb63d85ee4
- PR: #5 open
- Request summary: Generate a real M1B funding-arbitrage numerical report using local M0 public data after accepting Freqtrade suitability conclusion B.
- Completed: Local M0 public ZIP fallback data was generated; M1B numerical report and public-data provenance were written.
- Not completed: No M2; no live trading; no paper trading with real API; no API keys; no execution/live; no PR #5 merge.
- Validation result: M1B final status is failed_validation.
- Decision: Do not promote funding-rate-arbitrage to M2 because the complete cycle-count gate failed.
- Key metrics from superseded cycle-level Sharpe report: base cost total return 119.1019%; cost x2 total return 111.6019%; complete cycles 15; OOS Sharpe 26.1582; max drawdown 1.1040%.
- Blockers: PR #5 still requires review as a truthful failed_validation research artifact.
- Next action: Review PR #5 numerical report and decide whether to merge the failed_validation artifact.

## 2026-07-09 - M1B Metrics Methodology Fixed

- Date UTC: 2026-07-09
- Task ID: M1B-METRICS-METHODOLOGY-FIX
- Phase: M1B funding-rate-arbitrage research validation
- Branch: m1b-funding-arbitrage-offline-backtest
- Commit: 3e0fe83b18dbec562458fb999ab2806c45d2a186
- PR: #5 open
- Request summary: Replace cycle-level Sharpe/volatility with funding-period time-indexed metrics.
- Completed: M1B report regenerated with funding-period time-indexed equity curve and time-based OOS split.
- Not completed: No M2; no live trading; no paper trading with real API; no API keys; no private smoke; no execution/live; no trading logic.
- Decision: Corrected M1B final status is failed_validation.
- Key metrics: base cost total return 59.5509%; cost x2 total return 55.8009%; annualized volatility 1.3287%; Sharpe 7.0355; OOS Sharpe 11.5406; complete cycles 15; max drawdown 0.9124%.
- Blockers: M1B failed validation because complete cycles 15 < 20; strategy is not eligible for M2.
- Next action: Review corrected PR #5 report and decide whether to merge it as a truthful failed_validation artifact.

## 2026-07-09 - M1B Failed Validation Merged

- Date UTC: 2026-07-09
- Task ID: M1B-FAILED-VALIDATION-MERGED
- Phase: M1B funding-rate-arbitrage research validation
- Branch: main
- Commit: 105fd0dc39607100f70210c79f4bfe5f7413e479
- PR: #5 merged
- Request summary: Merge PR #5 as truthful M1B failed_validation artifact and record final decision.
- Completed: M1B final status failed_validation recorded; metrics methodology fixed; PR #5 merged.
- Not completed: No M2; no live/paper/API/trading; no execution/live.
- Validation: M0/M1A/M1B/M1F/Project Validate success before merge; project validation pass after final record.
- Decision: M1B funding-rate-arbitrage is not eligible for M2 because complete cycles 15 < 20.
- Blockers: No strategy is currently eligible for M2. Future work requires explicit approval.
- Next action: Post-M1B review only.

## 2026-07-09 - Post-M1B Review Started

- Date UTC: 2026-07-09T17:53:53Z
- Task ID: POST-M1B-REVIEW-STARTED
- Phase: post-M1B review
- Branch: post-m1b-review-and-next-decision
- Commit: 9cb7be790eb10e68dfc98b95472ce534054c59a5
- PR: #7 open
- Completed:
  - M0/M1A/M1F/M1B statuses summarized
  - no-strategy-eligible-for-M2 decision drafted
- Not completed:
  - no diagnostics yet
  - no coordinator design yet
  - no M2
  - no live/paper/API/trading
- Decision:
  - next work must be either diagnostics or design review only
- Next action:
  - review POST_M1B_REVIEW.md and choose Option A/B/C
