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
- Commit: 795724d
- PR: #11 open
- Completed so far: The existing M1B engine now uses next-1h-open entries/exits, excludes triggering funding, credits held funding before exit, derives every event interval from M0 history, uses settlement mark notional, charges actual fill notionals, separates incomplete end positions and OOS carry-in, and joins BTC/ETH by UTC.
- Public run: Local M0 public ZIP fallback covered 2020-01-01 through 2024-12-31. Invalid close-boundary bars and observed gaps remain explicit diagnostics; raw data and DuckDB stay ignored.
- Validation result: M1B remains failed_validation with 13 complete cycles and 2 incomplete end positions. The complete-cycle gate fails; M0 audit status also remains revalidation_required.
- Freqtrade cross-check: Futures probe schema validation passed after replacing an invalid empty placeholder, but GitHub run 29049892500 was blocked by Binance `exchangeInfo` HTTP 451 before data download/backtest. No futures result is claimed.
- Freqtrade primary smoke: GitHub run 29050078339 passed after the blocked futures probe was separated into its own manual workflow.
- Decision: The historical report remains unchanged. The new report cannot approve M2 even if numerical gates pass.
- Next action: Run full validation, publish the independent PR, and merge only after checks pass.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M1B Event-Time Revalidation Merged

- Date UTC: 2026-07-09T21:06:52Z
- Task ID: M1B-EVENT-TIME-REVALIDATION-MERGED
- Phase: M1B event-time revalidation
- Branch: main
- Commit: 6e0d9ba74dd7c5490de496ba1dbd722cb50eebf7
- PR: #11 merged
- Completed: Strict next-1h-open timing, per-event funding intervals, settlement-mark funding income, actual-notional costs, incomplete-position handling, OOS carry-in separation, UTC portfolio alignment, and public-data diagnostics were merged.
- Validation: 84 repository tests passed in the final branch cycle; M0/M1A/M1B/M1F/Project checks passed; Freqtrade Public Smoke run 29050078339 passed.
- Result: M1B remains failed_validation with 13 complete cycles and 2 incomplete end positions. Complete cycles remain below the unchanged gate of 20.
- Freqtrade futures probe: blocked_network; run 29049892500 reached Binance public market metadata and received HTTP 451. No futures backtest output is claimed.
- Decision: The four Freqtrade-first hardening PRs are complete. No strategy is eligible for M2.
- Blockers: M0 public dual-source audit remains blocked by spot differences and futures REST HTTP 451.
- Next action: Public-data audit diagnostics or design review only; no strategy rescue and no execution work.
- Guardrails: No API key, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Dual-Source Audit Unblock Design Approved

- Date UTC: 2026-07-09T21:25:09Z
- Task ID: M0-DUAL-SOURCE-AUDIT-UNBLOCK-DESIGN
- Phase: M0 audit revalidation
- Branch: codex/m0-dual-source-audit-unblock
- Commit: recorded in the branch history for this specification
- PR: not opened
- Request summary: Design a multi-network, evidence-first public audit to explain spot ZIP/REST differences and obtain compliant futures dual-source evidence.
- Completed: Architecture, difference classifications, strict gate, VPS safety rules, reporting, error handling, and fixture test requirements were approved in conversation and written as a specification.
- Not completed: User review of the written specification, implementation plan, audit implementation, real local/VPS evidence run, M0 audit pass, M2, or any trading work.
- Decision: Official REST plus official ZIP is mandatory. ZIP-only or third-party evidence cannot satisfy the gate. HTTP 451 and unresolved source differences remain blocking outcomes.
- Blockers: The real 1h audit still has unexplained spot differences and unavailable hosted futures REST evidence.
- Next action: User reviews the written specification; after approval, create the implementation plan without weakening validation thresholds.
- Guardrails: Public unauthenticated data only; no API keys, private smoke, VPN/proxy bypass, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Multi-Network Dual-Source Evidence Completed Blocked

- Date UTC: 2026-07-09T22:13:36Z
- Task ID: M0-DUAL-SOURCE-AUDIT-EVIDENCE
- Phase: M0 audit revalidation
- Branch: codex/m0-dual-source-audit-unblock
- Commit: recorded in the branch history for this implementation
- PR: not opened at evidence-record time
- Request summary: Implement and run the approved multi-network, evidence-first official public REST/ZIP audit locally and on the approved remote node.
- Completed: Strict Decimal/timestamp comparison, append-only ignored raw evidence, sanitized JSON/Markdown evidence, fixture tests, manual public workflow, local full-history audit, remote futures audit, and multi-node aggregation.
- Validation: 95 repository tests passed; M0 validation PASS=6 FAIL=0 before final project-context update.
- Evidence: `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md` and `reports/m0/M0_AUDIT_REVALIDATION_REPORT.md`.
- Spot result: BTCUSDT had 14 field revisions and one timestamp mismatch across two blocked scopes; ETHUSDT had the same counts. The affected UTC windows are 2020-12-21T13:00Z/14:00Z and 2021-04-23T01:00Z. All other selected spot scopes passed exact comparison.
- Futures result: Both compliant execution nodes could read official ZIP profiles, but official futures REST remained network blocked; no ZIP-only result was treated as pass.
- Decision: M0 infrastructure remains accepted, while M0 audit remains `audit_revalidation_required`. M1A and M1B remain `failed_validation`; M2 remains prohibited.
- Not completed: No official source-owner resolution for historical spot revisions and no compliant node with working official futures REST evidence.
- Next action: Seek official source clarification or another compliant public network. Do not use third-party substitution, VPN/proxy bypass, threshold reduction, or ZIP-only acceptance.
- Guardrails: No API keys, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Dual-Source Audit PR Opened

- Date UTC: 2026-07-09T22:15:56Z
- Task ID: M0-DUAL-SOURCE-AUDIT-PR
- Phase: M0 audit revalidation
- Branch: codex/m0-dual-source-audit-unblock
- Commit: 27f5032831b3cfbe8311ee019a71e89a92f7f455
- PR: #13 open
- Completed: Implementation, multi-network evidence, truthful blocked reports, validation, branch push, and PR creation.
- Decision: PR #13 records a completed diagnostic implementation with a blocked audit result; it does not restore M0 audit pass or authorize M2.
- Blockers: Historical spot source revisions remain, and official futures REST is unavailable from both compliant execution nodes.
- Next action: Review PR #13 checks and evidence. Any future unblock requires official source clarification or a compliant public network, not weaker validation.
- Guardrails: No API keys, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Proxy-Assisted Official Audit Evidence Completed

- Date UTC: 2026-07-09T23:12:00Z
- Task ID: M0-DUAL-SOURCE-PROXY-EVIDENCE
- Phase: M0 audit revalidation
- Branch: codex/m0-dual-source-audit-unblock
- Commit: ce6b226f8ffb06cc9cc11e1a515cade74603d6ad
- PR: #13 open
- Transport: official REST through an explicit unauthenticated loopback HTTPS proxy; official Binance Vision monthly/daily ZIP direct; proxy disclosed as transport, not a data source.
- Completed: Futures REST connectivity, full BTCUSDT/ETHUSDT 1h comparison for UM/mark/index/premium, supplemental official daily ZIP recovery, payload-bundle hashes, daily HTTP outcomes, strict classification, and regenerated sanitized reports.
- Archive result: 936 monthly-archive omissions were recovered exactly from 41 successful official daily ZIP requests. Six required `2026-06-29` mark/index/premium daily ZIP requests returned HTTP 404 and remain timestamp mismatches.
- Source-revision result: BTCUSDT/ETHUSDT UM monthly and daily ZIPs agree with each other but differ from REST at `2024-10-28T20:00Z` and `2024-10-28T21:00Z`. Historical spot revisions and ZIP-only timestamps remain unchanged.
- Validation: 101 tests passed; M0 validation PASS=6 FAIL=0; Project validation PASS=7 FAIL=0; secret, no-trading, execution/live, artifact, and diff checks passed.
- Decision: Connectivity is no longer the active futures blocker, but M0 audit remains `audit_revalidation_required` because official-source differences and unavailable daily archives remain. No result is reclassified or hidden.
- Next action: Seek Binance source-owner clarification and recheck the missing daily archives after official publication; do not weaken the dual-source gate.
- Guardrails: No API keys, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - M0 Dual-Source Audit Evidence Merged

- Date UTC: 2026-07-09T23:23:15Z
- Task ID: M0-DUAL-SOURCE-AUDIT-MERGED
- Phase: M0 audit revalidation
- Branch: main
- Commit: 8f0eb2c0f3c6ad4f780f4936ad54a77ffe46d3df
- PR: #13 merged
- Completed: The strict public REST/monthly ZIP/daily ZIP audit implementation, sanitized blocked evidence, approved proxy transport disclosure, and project context updates were squash merged.
- Decision: M0 audit remains `audit_revalidation_required`; merging truthful diagnostic evidence does not turn its gate into pass.
- Next action: Strategy diagnostics or M0 source-owner/archive follow-up only.
- Guardrails: No API keys, private smoke, M2, live/paper trading, order operations, simulated matching, or execution/live.

## 2026-07-09 - Strategy Failure Diagnostics Completed

- Date UTC: 2026-07-09T23:27:14Z
- Task ID: STRATEGY-FAILURE-DIAGNOSTICS
- Phase: strategy failure diagnostics
- Branch: codex/strategy-failure-diagnostics
- Commit: 9bcbb9047d7d13c20459afb12ce79cb677843839
- PR: #14 open
- Completed: Evidence-validity review, M1A structural scarcity diagnosis, M1B complete-cycle scarcity diagnosis, comparative priority, and next-work recommendation.
- M1A finding: 35 trades over 8.89 years; all 81 fixed-neighborhood combinations remain below 80 trades and full-sample Sharpe 1.0, while the separate fixed-rule OOS evidence also fails. The frozen historical engine must not be tuned or extended.
- M1B finding: 13 complete cycles over five years, two OOS complete cycles, long holding periods, and a 713-day sleep period. Cost and drawdown gates pass, but sample scarcity remains blocking.
- Decision: No strategy is eligible for M2. The next primary task is a design review for one genuinely new fixed Freqtrade single-leg strategy hypothesis; no strategy code is approved yet.
- Evidence: `reports/m1/STRATEGY_FAILURE_DIAGNOSTICS.md`.
- Guardrails: No API keys, private smoke, M2, live/paper trading, order operations, parameter rescue, simulated matching, or execution/live.

## 2026-07-10 - End-to-End Roadmap P0 Started

- Date UTC: 2026-07-10T00:05:00Z
- Task ID: END-TO-END-P0
- Phase: P0 end-to-end governance
- Branch: codex/strategy-failure-diagnostics
- Commit: 162b62ad12122e5cc720ad0e47323521efb8a581
- PR: #14 open
- Request summary: Establish the complete Freqtrade-first P0-P8 lifecycle and execute all authorized work in strict dependency order.
- Completed so far: Approved master roadmap, implementation plan, and canonical `PROJECT_EXECUTION_CHECKLIST.md` created; M1C candidate and conservative gates fixed.
- Current task: P0-05 local validation, GitHub checks, and merge.
- Decision: P0-P4 are authorized sequentially. P5-P8 require future explicit approvals and remain blocked.
- Next action: Validate, update PR #14, wait for CI, and merge P0 before creating the P1 branch.
- Guardrails: No M1C strategy code before P0 merge; no API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-09 - End-to-End Roadmap P0 Merged

- Date UTC: 2026-07-09T23:45:27Z
- Task ID: END-TO-END-P0-MERGED
- Phase: P0 end-to-end governance
- Branch: main
- Commit: d3532b611bd0da4d5d20128979c3c93e17e2eb90
- PR: #14 merged
- Completed: The P0-P8 roadmap, implementation plan, canonical execution checklist, strategy diagnostics, and context updates were squash merged.
- Decision: P0-P4 are authorized only in dependency order. P5-P8 remain not authorized.
- Next action: Complete P1 fixed M1C design before creating strategy code.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-09 - M1C Rotation P1 Design Started

- Date UTC: 2026-07-09T23:53:01Z
- Task ID: M1C-P1-DESIGN
- Phase: P1 M1C rotation design
- Branch: codex/m1c-btc-eth-rotation-design
- PR: #15 open
- Commit: 62aa9e00d96eab8fc1aa1e6102d1c70dc17da967
- Completed so far: Fixed strategy specification, machine-readable contract, pinned Freqtrade 2026.6 source capability evidence, design validator, fixture-level tests, and capability report.
- Design result: `design_pass`. Informative-pair ranking and same-open different-pair rotation are representable in the pinned source; P2 runtime confirmation remains mandatory.
- Not completed: P1 PR/CI/merge, strategy implementation, historical backtest, independent audit, M2, dry-run, live/API/trading.
- Decision: If the P2 pinned-runtime same-open fixture fails, record `blocked_framework_capability` and stop; do not create a parallel single-leg backtester.
- Next action: Validate and merge P1 before creating `BTCETHRelativeStrengthRotation`.
- Guardrails: No strategy code on P1; no API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-09 - M1C Rotation P1 Design Merged

- Date UTC: 2026-07-09T23:57:24Z
- Task ID: M1C-P1-DESIGN-MERGED
- Phase: P1 M1C rotation design
- Branch: main
- Commit: 810d7332154a5bd00ad631ac98e268bfbdc157a5
- PR: #15 merged
- Completed: Fixed strategy specification, machine-readable contract, pinned Freqtrade source capability evidence, design validation, and context updates.
- Result: `design_pass`. This permits P2 implementation only and does not approve performance, M2, dry-run, or live trading.
- Next action: Implement the fixed strategy in Freqtrade and run the mandatory pinned-runtime capability checks.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P2 Implementation Started

- Date UTC: 2026-07-10T00:03:50Z
- Task ID: M1C-P2-IMPLEMENTATION
- Phase: P2 M1C Freqtrade implementation
- Branch: codex/m1c-btc-eth-rotation-validation
- PR: #16 open
- Commit: 89271afeda71284487623e37bcde1b229251b84a
- Completed so far: Fixed Freqtrade strategy, no-key public research config, guarded download/backtest/lookahead/recursive commands, independent event-time validator, and deterministic unit fixtures.
- Validation so far: Nine strategy/time tests pass. Full validation awaits the context transition and pinned Freqtrade runtime checks.
- Runtime attempt: GitHub run 29059348880 completed the pinned image, public download, M1A smoke, M1C backtest, lookahead-analysis, and recursive-analysis. The job failed only because host `tee` could not create a log inside the Docker-owned result directory; the log target was moved to the runner temporary directory for a full retry.
- Blocker: Same-open cross-pair rotation, lookahead-analysis, and recursive-analysis must pass in the pinned Freqtrade 2026.6 runtime.
- Decision: Runtime disagreement becomes `blocked_framework_capability`; no parallel single-leg engine is allowed.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P2 Runtime Gate Passed

- Date UTC: 2026-07-10T00:16:26Z
- Task ID: M1C-P2-RUNTIME-PASS
- Phase: P2 M1C Freqtrade implementation
- Branch: codex/m1c-btc-eth-rotation-validation
- PR: #16 open
- Commit: e5989a23b6de102e43c426afb10e6646d14712e5
- Workflow: Freqtrade Public Smoke run 29059474678
- Completed: Official pinned Freqtrade 2026.6 image, public spot data download, M1C backtest, same-open rotation check, one-position check, Monday-open check, lookahead-analysis, recursive-analysis, and artifact boundary.
- Validation: lookahead checked 20 signals with zero biased entries/exits; recursive analysis reported zero indicator variance and no indicator lookahead; runtime evidence parser passed.
- Result: P2 implementation Gate passed pending PR checks and merge. This is not a performance or trading approval.
- Next action: Merge PR #16 after all checks pass, then start P3 immutable historical validation.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P2 Merged

- Date UTC: 2026-07-10T00:19:23Z
- Task ID: M1C-P2-MERGED
- Phase: P2 M1C Freqtrade implementation
- Branch: main
- Commit: 1564df8c22e717d850091a2e6ade3e1f2aa0e1e2
- PR: #16 merged
- Completed: Fixed Freqtrade strategy, public research config and commands, independent event-time checks, runtime output validator, public runtime evidence, and implementation status report.
- Result: P2 passed. This permits immutable P3 historical validation only.
- Next action: Run P3 without changing strategy parameters or gates.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P3 Validation Started

- Date UTC: 2026-07-10T00:20:41Z
- Task ID: M1C-P3-VALIDATION
- Phase: P3 M1C historical validation
- Branch: codex/m1c-btc-eth-rotation-backtest
- PR: pending
- Commit: pending
- Scope: Freqtrade full history, sealed last-30% OOS, four fixed IS segments, base and cost-x2, concentration, lookahead, recursive, and data-gap evidence.
- Runtime attempt: GitHub run 29060046050 downloaded the complete public range and calculated the first full backtest, but Freqtrade could not create a nonexistent export subdirectory. No numerical Gate result was claimed. The retry uses unique export filename prefixes in the existing ignored result directory; ranges and thresholds are unchanged.
- Runtime attempt: GitHub run 29060187324 completed all eight Freqtrade matrix runs and full-range bias checks, but Freqtrade 2026.6 ignored custom export filename prefixes, so the report loader found no labeled archive. No numerical Gate result was claimed. The retry uses official `--notes` metadata for exact run selection; ranges and thresholds remain unchanged.
- Runtime attempt: GitHub run 29060403128 completed and note-matched all eight numerical runs plus bias checks. Report rendering then found that Freqtrade 2026.6 annual breakdown rows expose `profit_abs`, not `profit_total`. No partial Gate result was published. Annual return is now derived from Freqtrade annual absolute profit divided by Freqtrade starting balance; strategy inputs and gates remain unchanged.
- Decision: Any failed Gate records `failed_validation` and stops the candidate; no parameter tuning or P4 follows a failure.
- Next action: Generate the numerical report from Freqtrade public-data exports.
- Guardrails: No API keys, private smoke, M2, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P3 Failed Validation Recorded

- Date UTC: 2026-07-10T00:46:33Z
- Task ID: M1C-P3-FAILED-VALIDATION
- Phase: P3 M1C historical validation
- Branch: codex/m1c-btc-eth-rotation-backtest
- PR: #17 open
- Commit: 45f8b86319a0c5c7b63110b989e0b14d6f86691e
- Workflow: Freqtrade Public Smoke run 29060604088 passed
- Data: BTC/ETH public spot daily JSON, 3,249 rows per symbol from 2017-08-17 through 2026-07-09, zero missing daily bars.
- Passed: base and cost-x2 full/OOS returns, delete-best-three, 3/4 IS segments, lookahead, recursive, and data-gap gates.
- Failed: complete trades 31 < 80; OOS complete trades 15 < 20; OOS Sharpe 0.1146 < 1.0; worst cost-scenario drawdown 16.6528% > 15%.
- Result: `failed_validation`. M1C is not eligible for P4 or M2 and must not be tuned or rescued.
- Next action: Merge PR #17 as truthful evidence, then stop this candidate. A future candidate requires a new approved P1 design.
- Guardrails: No API keys, private smoke, M2, P4, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - M1C Rotation P3 Failed Validation Merged

- Date UTC: 2026-07-10T00:50:37Z
- Task ID: M1C-P3-FAILED-VALIDATION-MERGED
- Phase: post-M1C review
- Branch: main
- Commit: bccb01c8d50733a0aaa5637c4ff4da55c5f7e418
- PR: #17 merged
- Completed: Immutable Freqtrade matrix, sanitized numerical report, truthful Gate failures, CI, and no-rescue decision were squash merged.
- Result: M1C remains `failed_validation`. P4 was not started because its P3 dependency failed. No strategy is eligible for M2.
- Next action: No active implementation. Future work requires a new approved P1 design or M0 audit diagnostics.
- Guardrails: No API keys, private smoke, M2, P4 for M1C, dry-run, live trading, orders, simulated matching, or execution/live.

## 2026-07-10 - Short-Horizon Product Governance Started

- Date UTC: 2026-07-10T02:46:20Z
- Task ID: SHORT-HORIZON-T0-GOVERNANCE
- Phase: short-horizon product governance
- Branch: codex/short-horizon-product-governance
- Commit: 9eaf1161b69687e118717808720ce10473847d26
- PR: #19 open
- Request summary: Record the capital-owner-approved BTC/ETH 15m short-horizon event product and its dependency-complete T0-T9 delivery chain.
- Completed so far: Approved specification, ADR-0007, implementation plan, expert evidence intake, immutable candidate hashes, automated ledger validation, and isolated expert recomputation.
- Validation: The standalone expert script reproduced its committed OOS CSV byte-for-byte; 124 repository tests passed; Project Validate PASS=8 FAIL=0; secret, no-trading, execution/live, and diff checks passed.
- Not completed: Governance PR checks/merge, public 1m golden data, unified MTM engine, M1D feasibility, strategy code, historical validation, audit, M2, dry-run, live, or API trading.
- Decision: Discrete completed-15m events only; 1m is authoritative detail, 5m is sensitivity, holding/frequency are strategy outputs, and daily-MTM MaxDD remains 15%.
- Next action: Require clean PR #19 CI and merge T0 before T1.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, execution/live, OOS tuning, raw commits, or runtime artifacts.

## 2026-07-10 - Short-Horizon Product Governance Merged

- Date UTC: 2026-07-10T03:19:29Z
- Task ID: SHORT-HORIZON-T0-MERGED
- Phase: short-horizon product governance
- Branch: main
- Commit: 82d4718efb3f15fb851ab93c16a74c099270e1e8
- PR: #19 merged
- Completed: The approved product specification, ADR-0007, T0-T9 plan, expert recomputation evidence, immutable strategy trial ledger, and automated ledger validator were squash merged.
- Validation: All PR #19 M0, M1A, M1B, M1C, M1F, and Project Validate checks passed. Local validation recorded 124 tests and Project Validate PASS=8 FAIL=0.
- Decision: T0 is complete. T1 canonical public spot 1m data work is the next authorized task; T2-T9 remain dependency-gated and no M1D strategy code is authorized.
- Not completed: T1 minute data, golden derivatives, unified metrics, M1D feasibility, strategy implementation, historical validation, independent audit, M2, dry-run, live, or API trading.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, execution/live, OOS tuning, raw commits, or runtime artifacts.

## 2026-07-10 - Short-Horizon T0 Context Closed

- Date UTC: 2026-07-10T03:24:46Z
- Task ID: SHORT-HORIZON-T0-CLOSEOUT
- Phase: short-horizon product governance
- Branch: main
- Commit: 6b9ca8e2f774c4c4450cd6827a0af5209b6eb9fc
- PR: #20 merged
- Completed: T0 was removed from open work, ADR-0007 became active, and T1 became the only newly authorized task.
- Guardrails: T2-T9 remain dependency-gated; no API keys, M2, dry-run, live, orders, simulated matching, or execution/live.

## 2026-07-10 - T1 Canonical Public Minute Data Passed Locally

- Date UTC: 2026-07-10T03:50:22Z
- Task ID: SHORT-HORIZON-T1-MINUTE-DATA
- Phase: T1 canonical public minute data
- Branch: codex/short-horizon-t1-minute-data
- Commit: 97799efe447a2485e79e176750d86d290d180cf3
- PR: #21 open
- Data: Official Binance public BTCUSDT/ETHUSDT spot 1m monthly ZIPs from actual first open `2017-08-17T04:00:00Z` through `2026-06-30T23:59:00Z`; official daily ZIPs supplement missing timestamps; 20 deterministic REST windows provide comparison evidence.
- Result: T1 report status `pass`; all REST windows matched with zero field differences; no relevant blocker exists on or after the fixed research start `2023-10-01`.
- Quarantine: 50 pre-start symbol-months remain explicitly registered. The official 2017-12 monthly archives contain 20,401 off-grid rows per symbol and are not rewritten or hidden.
- Artifacts: Raw ZIP/REST data and the detailed manifest remain ignored; only the sanitized report, public-data code, tests, and validation workflow are eligible for commit.
- Next action: Require clean PR #21 CI and merge T1. T2 remains blocked until then.
- Guardrails: No strategy returns, M1D code, OOS access, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T1 Canonical Public Minute Data Merged

- Date UTC: 2026-07-10T03:57:53Z
- Task ID: SHORT-HORIZON-T1-MERGED
- Phase: T1 canonical public minute data
- Branch: main
- Commit: f802868ecb2f0d39913074d009bea8e780d6147e
- PR: #21 merged
- Completed: Public 1m archive acquisition, daily supplement logic, deterministic REST evidence, liquidity qualification, report guard, unit tests, and T1 CI were squash merged.
- Result: T1 status `pass`; fixed research start `2023-10-01`; T2 golden data and quarantine is the next authorized task.
- Not completed: T2 derivatives/quarantine, unified metrics, M1D feasibility, strategy code, historical validation, M2, dry-run, live, or API trading.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, execution/live, OOS tuning, raw commits, or runtime artifacts.

## 2026-07-10 - T2 Golden Data and Quarantine Passed Locally

- Date UTC: 2026-07-10T13:20:00Z
- Task ID: SHORT-HORIZON-T2-GOLDEN-DATA
- Phase: T2 golden data and quarantine
- Branch: codex/short-horizon-t2-golden-data
- Commit: b89f637d0086bde3197b62f5b6942a49ec6c0d80
- PR: #23 open
- Data: BTCUSDT and ETHUSDT golden spot 1m from `2023-10-01T00:00:00Z` through `2026-06-30T23:59:00Z`, derived from the append-only T1 run with monthly ZIP precedence and daily ZIP fill-only semantics.
- Result: 1,445,760 golden 1m rows per symbol; 289,152 deterministic 5m rows and 96,384 deterministic 15m rows per symbol; zero incomplete research buckets.
- Official parity: 66 symbol-month official 15m ZIP comparisons, 192,768 overlapping rows, and zero numeric, timestamp, ordering, derived-only, or official-only differences.
- Quarantine: 60,485 traceable records from 50 pre-start symbol-months remain outside the formal research range and are hash-addressed in ignored storage.
- Runtime: Pinned Freqtrade 2026.6 container read all six BTC/ETH 1m/5m/15m jsongz caches with exact time ranges and row counts.
- Validation: 146 repository tests passed; T2 Validate `PASS=9 FAIL=0`; secret, no-trading, execution/live, artifact, and diff checks passed.
- Artifacts: Raw archives, golden files, detailed manifests, logs, and Freqtrade caches remain ignored and uncommitted.
- Next action: Commit, open the T2 PR, require clean CI, and merge before T3. Do not implement M1D strategy code.
- Guardrails: No strategy returns, OOS access, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T2 Golden Data and Quarantine Merged

- Date UTC: 2026-07-10T13:48:14Z
- Task ID: SHORT-HORIZON-T2-MERGED
- Phase: T2 golden data and quarantine
- Branch: main
- Commit: da7874c4e2f6d391e898a36bbc819a9634d600f9
- PR: #23 merged
- Completed: Golden 1m construction, pre-start quarantine, deterministic 5m/15m derivation, official 15m payload and field parity, Freqtrade jsongz export, pinned runtime evidence, tests, report Gate, and CI.
- Result: T2 status `pass`; all PR checks passed. T3 unified metrics is the next authorized task, but is not started by this closeout.
- Artifacts: Raw archives, golden data, detailed manifests, logs, and Freqtrade runtime caches remain ignored and uncommitted.
- Guardrails: No M1D strategy code, strategy returns, OOS access, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.
