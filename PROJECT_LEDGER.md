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

## 2026-07-09 - Freqtrade-First Architecture Hardening Started

- Date UTC: 2026-07-09T18:57:19Z
- Task ID: FREQTRADE-FIRST-ARCHITECTURE-HARDENING
- Phase: post-M1B architecture hardening
- Branch: codex/freqtrade-first-architecture-governance
- Commit: f96a8d2
- PR: #8 open
- Request summary: Adopt Freqtrade as the primary single-leg research framework and retain Python only for M0 audit, event-time verification, and offline two-leg accounting.
- Completed: Design approved; ADR-0006, architecture specification, README, and historical evidence notices drafted.
- Not completed: M0 audit corrections, immutable Freqtrade runtime pinning, M1B event-time revalidation, M2, live/paper/API/trading.
- Decision: Historical reports remain immutable; affected M1A metrics are superseded and M1B numerical evidence is invalidated pending revalidation.
- Blockers: No strategy is eligible for M2; M0 audit and M1B event-time methodology require revalidation.
- Next action: Complete and review the four independent hardening PRs without implementing execution.

## 2026-07-09 - Freqtrade-First Architecture Governance Merged

- Date UTC: 2026-07-09T19:03:27Z
- Task ID: FREQTRADE-FIRST-GOVERNANCE-MERGED
- Phase: post-M1B architecture hardening
- Branch: main
- Commit: ee7a3ba2a438aa224e6768fbdde47d7f733930e3
- PR: #8 merged
- Completed: ADR-0006, the Freqtrade-first design specification, ownership boundaries, and historical evidence notices were merged.
- Not completed: M0 audit revalidation, immutable Freqtrade runtime pinning, M1B event-time revalidation, M2, live/paper/API/trading.
- Decision: Freqtrade owns single-leg research; M0 and Python remain audit and offline two-leg accounting sidecars.
- Blockers: M0 audit correctness and M1B event-time evidence still require revalidation.
- Next action: Complete M0 public audit correctness without private API access.

## 2026-07-09 - M0 Audit Correctness Hardening Started

- Date UTC: 2026-07-09T19:27:07Z
- Task ID: M0-AUDIT-CORRECTNESS-HARDENING
- Phase: M0 audit revalidation
- Branch: codex/m0-audit-correctness-hardening
- Commit: 021bb19
- PR: #9 open
- Completed so far: funding cadence candidates now require complete periods; historical event intervals are preserved; raw dataset and DuckDB identifiers are validated; DuckDB read failures are explicit; ZIP/REST evidence records overlap, hashes, and audit scope.
- Not completed: sanitized real 1h public audit report and PR review.
- Validation: 70 repository tests passed before the final M0 audit additions; local spot REST/ZIP probe passed through the official public market-data host.
- Decision: ZIP-only fallback cannot satisfy the audit gate. Missing selected ZIP months or unavailable REST evidence must block revalidation.
- Blockers: Production Binance REST is unreachable from local and VPS networks; run the manual no-secret GitHub public audit workflow after publishing this branch.
- Next action: Publish the branch, run `M0 Public Audit`, inspect the report artifact, and restore M0 audit pass only if every check passes.
- Guardrails: No private smoke, API keys, M2, live/paper trading, order operations, or execution/live.

## 2026-07-09 - M0 Public Audit Revalidation Blocked Truthfully

- Date UTC: 2026-07-09T20:04:18Z
- Task ID: M0-PUBLIC-AUDIT-REAL-RUN
- Phase: M0 audit revalidation
- Branch: codex/m0-audit-correctness-hardening
- Commit: 379d552
- PR: #9 open
- Workflow: M0 Public Audit run 29046010878
- Completed: BTCUSDT/ETHUSDT 1h public profile ran from 2019-09-01 through 2026-07-08; spot REST/ZIP scope covered first, middle, latest complete, anomaly, and gap months; funding histories retained 7,119 inferred event intervals per symbol.
- Validation result: M0 audit remains blocked. Funding interval evidence normalized to data-derived 8h for this history, but spot has 6/7 field differences and one timestamp-set difference for BTC/ETH; futures REST returned HTTP 451, so futures ZIP/REST evidence is unavailable.
- Decision: Do not reinterpret ZIP-only fallback as dual-source pass and do not restore M0 audit status.
- Blockers: A compliant network is required for futures REST comparison, and spot differences require source-level investigation.
- Next action: Merge the correctness hardening only after CI passes, then continue Freqtrade primary-framework hardening while all strategy approval and M2 gates remain blocked.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Audit Correctness Hardening Merged

- Date UTC: 2026-07-09T20:07:25Z
- Task ID: M0-AUDIT-CORRECTNESS-MERGED
- Phase: M0 audit revalidation
- Branch: main
- Commit: 8c33d67dd1c5b3ed7108d5578b36f96a05fd320c
- PR: #9 merged
- Completed: Funding cadence, per-event interval, ZIP/REST evidence, gap/timestamp-set comparison, raw path validation, DuckDB identifier/counting, and explicit index-failure hardening merged.
- Not completed: M0 audit pass, M2, live/paper/API/trading.
- Decision: M0 infrastructure stays accepted but audit status remains revalidation_required because the real public audit is blocked.
- Blockers: Futures REST HTTP 451 and recorded spot source differences.
- Next action: Pin and validate Freqtrade as the primary single-leg research framework.

## 2026-07-09 - Freqtrade Primary Framework Hardening Started

- Date UTC: 2026-07-09T20:23:04Z
- Task ID: FREQTRADE-PRIMARY-HARDENING
- Phase: Freqtrade primary framework hardening
- Branch: codex/freqtrade-primary-framework-hardening
- Commit: 00f1607
- PR: #10 open
- Completed so far: Official `2026.6` image pinned to digest `sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6`; runtime manifest and validator added; unified research entry added; self-managed M1A marked frozen; VPS public download/list/backtest/lookahead/recursive smoke passed after correcting a configuration-error false positive.
- Data provenance: BTCUSDT and ETHUSDT each matched 3,248 canonical M0 1d rows with zero missing timestamps and zero OHLCV differences from 2017-08-17 through 2026-07-08.
- Not completed: PR review/merge, M1B event-time revalidation, M0 audit pass, M2, live/paper/API/trading.
- Decision: Framework smoke and provenance establish Freqtrade as the primary single-leg research framework, not as strategy or trading approval.
- Known limitation: Freqtrade 2026.6 emitted asynchronous connector cleanup warnings after completed analysis commands; monitor on future pinned upgrades.
- Next action: Run full validation, publish the independent PR, and merge only after checks pass.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - Freqtrade Primary Framework Hardening Merged

- Date UTC: 2026-07-09T20:27:35Z
- Task ID: FREQTRADE-PRIMARY-HARDENING-MERGED
- Phase: Freqtrade primary framework hardening
- Branch: main
- Commit: 7dabe38f7d8633ce8f04eab9a3747b2d9206bf19
- PR: #10 merged
- Completed: Official Freqtrade 2026.6 image digest, runtime manifest, unified research entry, no-live guard, public VPS smoke, lookahead/recursive analysis, and M0/Freqtrade provenance were merged.
- Decision: Freqtrade is the primary single-leg research/data/backtest/WebUI framework; this is not strategy, M2, paper, or live approval.
- Blockers: M0 public audit evidence remains blocked and M1B event-time evidence still requires revalidation.
- Next action: Revalidate the existing offline M1B two-leg accounting with strict 1h event-time semantics.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M1B Event-Time Revalidation Started

- Date UTC: 2026-07-09T20:51:34Z
- Task ID: M1B-EVENT-TIME-REVALIDATION
- Phase: M1B event-time revalidation
- Branch: codex/m1b-event-time-revalidation
- Commit: working tree pending initial commit
- PR: pending
- Completed so far: The existing M1B engine now uses next-1h-open entries/exits, excludes triggering funding, credits held funding before exit, derives every event interval from M0 history, uses settlement mark notional, charges actual fill notionals, separates incomplete end positions and OOS carry-in, and joins BTC/ETH by UTC.
- Public run: Local M0 public ZIP fallback covered 2020-01-01 through 2024-12-31. Invalid close-boundary bars and observed gaps remain explicit diagnostics; raw data and DuckDB stay ignored.
- Validation result: M1B remains failed_validation with 13 complete cycles and 2 incomplete end positions. The complete-cycle gate fails; M0 audit status also remains revalidation_required.
- Decision: The historical report remains unchanged. The new report cannot approve M2 even if numerical gates pass.
- Next action: Run full validation, publish the independent PR, and merge only after checks pass.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.
