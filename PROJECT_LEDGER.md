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
- Commit: pending
- PR: #65 open
- Result commit: `b348126c38e9b22106e5a499a650781c1f159f86`
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

## 2026-07-10 - T3 Unified Metrics Passed Locally

- Date UTC: 2026-07-10T14:26:00Z
- Task ID: SHORT-HORIZON-T3-UNIFIED-METRICS
- Phase: T3 unified metrics and policy benchmark
- Branch: codex/short-horizon-t3-unified-metrics
- Commit: ecc464f3487fcd04c895592b83a95bae426bfbf1
- PR: #25 open
- Completed: Continuous UTC daily-MTM metrics, Freqtrade completed-trade adapter, fixed weekly policy benchmark, PSR/DSR, cost attribution, frequency/turnover/duration/sleep/order-event percentiles, concentration, and granularity comparisons.
- Regression: Sealed expert CSV SHA256 `842291287ca64967831fb36d1d1af2cbea4c77a80663f283d238f490e0a06bda` reproduced Base Sharpe 0.7882, MaxDD 23.4729%, PSR 0.9024 and Cost x2 Sharpe 0.7528, MaxDD 24.4688%, PSR 0.8920.
- Validation: 157 repository tests passed; T3 Validate `PASS=10 FAIL=0`; isolated expert recompute, secret, no-trading, execution/live, artifact, and diff checks passed.
- Scope: Measurement foundation only. No new strategy, candidate OOS, strategy return, API, or execution behavior was introduced.
- Next action: Commit, open the T3 PR, require clean CI, and merge before T4.
- Guardrails: No M1D feasibility run or strategy code, no OOS opening, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T3 Unified Metrics Merged

- Date UTC: 2026-07-10T14:36:02Z
- Task ID: SHORT-HORIZON-T3-MERGED
- Phase: T3 unified metrics and policy benchmark
- Branch: main
- Commit: e5eae32dedcdf77eb6684548f79ea2f9862ff7f5
- PR: #25 merged
- Completed: Unified daily-MTM metrics, audit trade adaptation, fixed policy benchmark, PSR/DSR, diagnostics, sealed expert regression, tests, report Gate, and CI.
- Result: T3 status `pass`; all PR checks passed. T4 IS-only feasibility harness is the next authorized task, but is not started by this closeout.
- Guardrails: No M1D feasibility run or strategy code, no candidate OOS, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T4 IS-Only Feasibility Harness Passed Locally

- Date UTC: 2026-07-10T16:12:00Z
- Task ID: SHORT-HORIZON-T4-FEASIBILITY-HARNESS
- Phase: T4 IS-only feasibility harness
- Branch: codex/short-horizon-t4-feasibility-harness
- Commit: c24144e5dac5a3a496558ef0f5927fe74756e83a
- PR: #27 open
- Completed: Ledger-locked event references, next-15m-open observation, fixed 1/2/4/8/12/24-bar horizons, four fixed cost scenarios, MAE/MFE, decay, frequency, clustering, path-risk, occupancy, right-censor and sample-budget diagnostics.
- Local evidence: Ignored T2 golden 15m structure smoke passed for BTCUSDT and ETHUSDT with 96,384 rows each and deterministic hashes; no events were selected and no candidate return was computed.
- Validation: 169 repository tests passed; T4 Validate `PASS=10 FAIL=0`; ledger, secret, no-trading, execution/live, artifact, and diff checks passed.
- Scope result: T4 tooling foundation `pass`; candidate evaluated `no`; OOS returns accessed `no`; M1D strategy code remains unauthorized.
- Calendar blocker: The formal 1004-day range provides 302 OOS days, below the fixed 540-day minimum by 238 days. T5 must run this precheck first and stop; earliest projected resolution is `2028-09-03`.
- Next action: Commit, open the T4 PR, require clean CI, squash merge, and complete governance closeout. Do not define or run an M1D event candidate.
- Guardrails: No strategy returns, OOS opening, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T4 IS-Only Feasibility Harness Merged

- Date UTC: 2026-07-10T16:20:02Z
- Task ID: SHORT-HORIZON-T4-MERGED
- Phase: T4 IS-only feasibility harness
- Branch: main
- Commit: b38d242563e3874be7653351973255dfc29a5889
- PR: #27 merged
- Completed: The ledger-locked IS-only observation interfaces, fixed costs and horizons, diagnostic summaries, local golden structure evidence, report Gate, tests, and T4 CI were squash merged.
- Validation: All PR #27 checks passed, including T4 Validate. No candidate was evaluated and no OOS return was accessed.
- Result: T4 status `pass`. T5 is authorized only for a sample-budget precheck and is currently blocked because 302 OOS days are below the fixed 540-day minimum.
- Next action: A T5 precheck may record the fixed calendar failure and stop. Do not define candidate events, read OOS returns, implement strategy code, or proceed to T6.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, execution/live, threshold changes, or candidate OOS access.

## 2026-07-10 - T5 Sample-Budget Precheck Blocked Locally

- Date UTC: 2026-07-10T17:25:35Z
- Task ID: SHORT-HORIZON-T5-SAMPLE-BUDGET
- Phase: T5 M1D sample-budget precheck
- Branch: codex/short-horizon-t5-sample-budget-precheck
- Commit: 69bfca351543dc443cf20cd9e5b8790a32f53f68
- PR: #29 open
- Inputs: Ignored T1/T2 manifest metadata and the sealed M1D trial-ledger identity only; no OHLCV row, event, signal, price, equity, or return was read.
- Result: 1004 full days split into 702 IS and 302 sealed OOS days. The fixed 540-day OOS Gate fails by 238 days; T5 status is `blocked_insufficient_oos_calendar`.
- Earliest resolution: 1800 full days are required; the earliest projected complete day is `2028-09-03`.
- Trial state: candidate evaluated `no`; events selected `no`; OOS opened `no`; trial count incremented `no`; T5 feasibility analysis executed `no`.
- Next action: Commit and merge the truthful failure record, then stop M1D. Continue monthly public-data accrual and M0 audit diagnostics without lowering the Gate.
- Guardrails: No T6, strategy code, OOS access, API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-10 - T5 Sample-Budget Blocker Merged

- Date UTC: 2026-07-10T17:36:17Z
- Task ID: SHORT-HORIZON-T5-MERGED
- Phase: T5 M1D sample-budget precheck
- Branch: main
- Commit: 9362f9a2b0c5bb44bfdec52718c88ea379330494
- PR: #29 merged
- Completed: Immutable 30%/540-day policy validation, metadata-only T1/T2 calendar extraction, sealed-ledger guard, sanitized failure report, tests, report Gate, and T5 CI.
- Validation: 178 repository tests passed; T5 Validate `PASS=10 FAIL=0`; all PR #29 checks passed. No candidate, event, OOS price, or return was evaluated.
- Result: T5 status `blocked_insufficient_oos_calendar`. M1D and T6 are stopped; no strategy is eligible for M2.
- Next action: Continue monthly public-data accrual and M0 audit diagnostics. Any different candidate requires a separately approved design PR and a separately sealed OOS path.
- Guardrails: No threshold reduction, M1D continuation, T6, strategy code, OOS access, API keys, private smoke, M2, dry-run, live, orders, simulated matching, or execution/live.

## 2026-07-11 - M1E 1h Product And Data Contract Started

- Date UTC: 2026-07-10T18:09:31Z
- Task ID: M1E-1H-DATA-ADMISSION
- Phase: M1E product and data contract
- Branch: codex/m1e-1h-product-data-contract
- Commit: e98cd5789e0c7f83b13ed429df7f2e37a2f40879
- PR: #31 merged
- Candidate: `M1E-1H-TREND-BREAKOUT`, registered as a separate sealed trial with `oos_opened=false`.
- Scope: Official Binance spot BTC/ETH 5m/1h/4h data qualification from 2020-01-01, followed only on pass by a metadata-only 1800/540-day calendar Gate.
- Non-reuse: M1E may not reuse M1A's combined SMA200, Donchian 55/20, and ATR20 2x rules.
- Current result: Product/data contract foundation is implemented locally; no strategy rule, candidate return, OOS value, or Freqtrade backtest was created.
- Next action: Validate and merge the contract PR, then begin public-data qualification on a new branch.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-11 - M1E Public-Data Qualification Blocked Locally

- Date UTC: 2026-07-10T18:45:00Z
- Task ID: M1E-1H-PUBLIC-DATA-QUALIFICATION
- Phase: M1E public-data qualification
- Branch: codex/m1e-1h-public-data-qualification
- Commit: 9181fad67a4c8b245871d1397c2e33d145f814a4
- PR: #32 open
- Public evidence: 468 official monthly ZIP payloads for BTCUSDT/ETHUSDT 5m/1h/4h, daily fill-only evidence, 6 public REST sample windows, and deterministic aggregate parity through 2026-06.
- Research start: The first common six-month quality/liquidity window is 2020-01 through 2020-06, fixing the research start at `2020-07-01`.
- Result: blocked. Months 2020-12, 2021-01, 2021-04, 2021-09, 2021-11, and 2022-04 contain official aggregate or monthly/daily source conflicts that the contract forbids ignoring.
- Runtime: Pinned Freqtrade 2026.6 on the VPS read all six jsongz caches with exact ranges and row counts using `list-data` only. No strategy or backtest ran.
- Trial state: candidate evaluated `no`; OOS opened `no`; returns accessed `no`; strategy code authorized `no`.
- Next action: Merge the truthful blocked evidence after CI. Do not create the sample-budget PR or change data tolerances.
- Guardrails: No API keys, private smoke, M2, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-11 - M1E Public-Data Qualification Blocker Merged

- Date UTC: 2026-07-10T18:58:26Z
- Task ID: M1E-1H-PUBLIC-DATA-QUALIFICATION-MERGED
- Phase: post-M1E data qualification review
- Branch: main
- Commit: 9820ef8dbdbbff64ad268fa3b6c3b27112995745
- PR: #32 merged
- Validation: M1E Data Validate `PASS=9 FAIL=0`; all GitHub checks passed; no runtime artifacts or private data were committed.
- Result: Data tooling and public evidence completed, but M1E remains blocked by six official OHLCV aggregate/source-conflict months after its fixed research start.
- Decision: Do not create PR3 sample budget, strategy rules, Freqtrade backtesting, or M2 work. Source diagnostics may continue without weakening the contract.
- Guardrails: No API keys, private smoke, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-11 - M1E Official Source Conflict Diagnostics Completed Locally

- Date UTC: 2026-07-10T19:23:51Z
- Task ID: M1E-OFFICIAL-SOURCE-CONFLICT-DIAGNOSTICS
- Phase: M1E official source conflict diagnostics
- Branch: codex/m1e-official-source-conflict-diagnostics
- Commit: 8a334255089cac8d6f6742577684793ceb21bab3
- PR: #35 merged
- Evidence: 36/36 affected monthly ZIP hashes were unchanged on fresh download; 30 field-level conflict rows were compared with current public REST.
- Classification: 16 monthly/daily conflicts where REST supports daily; 10 higher-timeframe flow revisions confirmed by REST; 2 child aggregates confirmed by REST; 2 unresolved third-version flow revisions.
- Result: Every conflict remains contract-blocking. Source precedence and numeric tolerances were not changed.
- Diagnostic suffix: The first six-month clean suffix starts 2022-11-01 but has only 1338 full and 402 sealed-OOS days through 2026-06-30, below 1800/540.
- Trial state: candidate evaluated `no`; candidate OOS returns accessed `no`; strategy code and PR3 remain unauthorized.
- Next action: Validate and merge the diagnostic record. Do not create strategy, sample-budget, backtest, or M2 work.
- Guardrails: No API keys, private smoke, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-11 - M1E Official Source Diagnostics Merged

- Date UTC: 2026-07-10T19:30:49Z
- Task ID: M1E-OFFICIAL-SOURCE-CONFLICT-DIAGNOSTICS-MERGED
- Phase: post-M1E source diagnostics review
- Branch: main
- Commit: 8a334255089cac8d6f6742577684793ceb21bab3
- PR: #35 merged
- Validation: M1E Conflict Validate `PASS=9 FAIL=0`; all GitHub checks passed; raw ZIP/REST evidence and runtime artifacts remained ignored.
- Result: The source conflict is reproducible and contract-blocking. No data-quality resolution path exists under ADR-0008, and the clean suffix also fails 1800/540 days.
- Decision: M1E stops before PR3. Future work requires source-owner correction, natural data accrual, or a separately approved new candidate; no strategy or M2 work is authorized.
- Guardrails: No API keys, private smoke, backtesting, dry-run, live, orders, cancellation, simulated matching, or execution/live.

## 2026-07-11 - M1E Binance Source-Owner Package Prepared

- Date UTC: 2026-07-10T19:45:00Z
- Task ID: M1E-BINANCE-SOURCE-OWNER-PACKAGE
- Phase: M1E source-owner escalation preparation
- Branch: codex/m1e-binance-source-owner-package
- Commit: 3828194d0c139bc80efe6cdcd7f3514333479ee5
- PR: #37 merged
- Official channel: `binance/binance-public-data` issue #475 already covers the 16 December 2020 overlap rows.
- Package: 14 new cross-timeframe rows, 36/36 stable monthly ZIP hashes, deterministic evidence SHA256, and a ready-to-post issue comment.
- Safety: No raw payload, API key, private data, account data, strategy, backtest, or trading operation is included.
- Status: `ready_not_submitted`; no external comment or issue was created.
- Decision: External publication requires explicit user approval and would not itself unblock M1E.
- Guardrails: No PR3, OOS returns, strategy code, M2, private smoke, dry-run, live, orders, or execution/live.

## 2026-07-11 - M1E Source-Owner Package Merged Not Submitted

- Date UTC: 2026-07-10T19:51:13Z
- Task ID: M1E-BINANCE-SOURCE-OWNER-PACKAGE-MERGED
- Phase: M1E source-owner submission decision
- Branch: main
- Commit: 3828194d0c139bc80efe6cdcd7f3514333479ee5
- PR: #37 merged
- Validation: M1E Source Owner Validate `PASS=8 FAIL=0`; all GitHub checks passed.
- Result: The sanitized issue #475 supplement is committed and ready, but no external submission occurred.
- Next action: Await explicit user approval before posting the prepared comment. M1E remains blocked either way.
- Guardrails: No PR3, OOS returns, strategy code, M2, private smoke, backtesting, dry-run, live, orders, or execution/live.

## 2026-07-11 - M1E Source-Owner Comment Submitted

- Date UTC: 2026-07-10T20:04:37Z
- Task ID: M1E-BINANCE-SOURCE-OWNER-SUBMITTED
- Phase: M1E source-owner response monitoring
- External evidence: https://github.com/binance/binance-public-data/issues/475#issuecomment-4939090508
- Submission: The prepared 14-row supplement was posted by `QIUYEDALAO` after explicit user approval and read back successfully.
- Safety: No raw payload, API key, private data, account data, strategy, backtest, or trading operation was posted.
- Status: `submitted_awaiting_response`; M1E contract remains unresolved and blocked.
- Next action: Monitor for an official maintainer response or archive correction, then rerun the unchanged data Gate.
- Guardrails: No PR3, OOS returns, strategy code, M2, private smoke, dry-run, live, orders, or execution/live.

## 2026-07-11 - M1E Canonical 5m Requalification Passed Locally

- Date UTC: 2026-07-11T04:30:00Z
- Task ID: M1E-CANONICAL-5M-V2
- Phase: M1E canonical 5m requalification
- Branch: `codex/m1e-canonical-5m-contract-v2`
- PR: #75 open
- Head SHA: `f5ce341ed66396f3239171b935047dddaea90d1a`
- Contract: ADR-0009 and machine contract v2 make evidenced official 5m rows canonical; official 1h/4h rows become audit comparators.
- Evidence: 12 daily 5m revisions are independently supported by public REST; unresolved canonical conflicts `0`; unexpected incomplete child buckets `0`; 146 confirmed-outage child buckets isolated.
- Runtime: Fixed Freqtrade 2026.6 container read BTC/ETH 5m, 1h, and 4h caches on the VPS using `list-data` only.
- Result: Data Gate `pass`; fixed research start restored to `2020-07-01`. Binance source-owner response remains provenance follow-up rather than an operational dependency.
- Authorization: Only the metadata-only 1800/540-day sample-budget Gate may follow after merge. Candidate evaluation, OOS returns, strategy code, backtesting, and M2 remain unauthorized.
- Safety: No API key, private data, strategy return, order, paper/live mode, or execution module was used.

## 2026-07-11 - M1E Canonical 5m Requalification Merged

- Date UTC: 2026-07-11T04:45:00Z
- Task ID: M1E-CANONICAL-5M-V2-MERGED
- Phase: post-M1E canonical data requalification
- Branch: main
- Commit: `37a9b17`
- PR: #40 merged
- Validation: M1E Requalification Validate `PASS=8 FAIL=0`; all GitHub checks passed.
- Result: M1E canonical data Gate is `pass`; research start is `2020-07-01`; Binance source-owner response is no longer an operational dependency.
- Next authorization: metadata-only 1800/540-day sample-budget Gate only. No candidate evaluation, OOS returns, strategy code, backtesting, or M2.
- Safety: No raw runtime data, API key, private payload, order, paper/live mode, or execution module was committed or used.

## 2026-07-11 - M1E Metadata-Only Sample Budget Passed Locally

- Date UTC: 2026-07-10T21:12:00Z
- Task ID: M1E-SAMPLE-BUDGET
- Phase: M1E metadata-only sample-budget review
- Branch: `codex/m1e-1h-sample-budget`
- PR: pending
- Evidence: 2191 full calendar days split into 1533 IS and 658 sealed OOS days; OOS starts `2024-09-11` and exceeds the fixed 540-day minimum.
- Status: `sample_budget_pass_design_only`; candidate evaluated `no`, OOS prices/returns accessed `no`, trial count incremented `no`.
- Authorization: After merge, only a separately approved IS-only rule-design review may follow. Strategy code, Freqtrade backtesting, OOS opening, and M2 remain unauthorized.
- Safety: No OHLCV data, API key, private data, order, paper/live mode, or execution module was read or used.

## 2026-07-11 - M1E Metadata-Only Sample Budget Merged

- Date UTC: 2026-07-10T21:20:00Z
- Task ID: M1E-SAMPLE-BUDGET-MERGED
- Phase: M1E IS-only rule-design approval decision
- Branch: main
- Commit: `b19e0ea`
- PR: #42 merged
- Validation: M1E Sample Budget Validate `PASS=8 FAIL=0`; all GitHub checks passed.
- Result: Calendar Gate passed with 2191 full, 1533 IS, and 658 sealed OOS days. OOS remains unopened.
- Next action: Await explicit approval for a separate IS-only rule-design PR. Do not implement strategy code or run Freqtrade backtesting.
- Safety: No OHLCV row, OOS return, API key, private data, order, paper/live mode, or execution module was read or used.

## 2026-07-11 - Candidate Queue And Common Gates Frozen Locally

- Date UTC: 2026-07-11T00:43:41Z
- Task IDs: Q-01, Q-02
- Phase: research candidate governance
- Branch: `codex/candidate-queue-common-gates`
- PR: #44 open
- Commit: `aaab962c09ae53f24b54a438ffc65a4a0216c598`
- Decision: ADR-0010 freezes M1E -> M1G -> M1H; M1H aliases the existing `FUNDING-EXTREME-SPOT-CONTRARIAN` trial and is not duplicated.
- Trial accounting: M1A, M1B, and M1C are the three historical OOS-opened trials used by DSR. M1D, M1E, M1G, daily panic, and M1H remain unopened.
- Common Gates: Base 0.15%, Cost x2 0.30%, Stress A 0.40%, Stress B 0.55% per side; sealed final 30% OOS; 1800/540 calendar minimum; 80/20 completed trades; OOS daily-MTM Sharpe 1.0; PSR 0.95; MaxDD 15%; positive Base/Cost-x2 full and OOS returns; delete-best-three nonnegative; benchmark, bias, and data-quality checks.
- Stop: M1E failure may move only to M1G after separate approval; M1G failure may move only to M1H; three failures stop BTC/ETH two-asset indicator research.
- Authorization: Governance review only. M1E rule design, all strategy code, backtesting, OOS access, M2, API use, paper/live mode, orders, and execution remain unauthorized.

## 2026-07-11 - Candidate Queue And Common Gates Merged

- Date UTC: 2026-07-11T00:49:27Z
- Task IDs: Q-01, Q-02
- Phase: M1E IS-only rule-design approval decision
- Branch: main
- Commit: `8f883d9e3275747745f3c708443a97029bf2517b`
- PR: #44 merged
- Validation: Candidate Queue Validate, Project Validate, M0 Validate, M1A Validate, M1B Validate, and M1F Validate all succeeded on the final head.
- Result: M1E -> M1G -> M1H, the historical DSR count of three, common Gates, failure transitions, and the terminal stop are now canonical.
- Next action: Await separate explicit approval for M1E IS-only rule design. M1G and M1H remain unopened.
- Safety: No OOS access, strategy code, backtest, API key, private data, order, paper/live mode, or execution module was used or authorized.

## 2026-07-11 - M1E-04 Economic Hypothesis Passed Locally

- Date UTC: 2026-07-11T01:00:00Z
- Task ID: M1E-04
- Phase: M1E IS-only economic hypothesis and non-duplication review
- Branch: `codex/m1e-is-only-rule-design`
- PR: #46 open
- Commit: `36e9da6ccf3d79eef35f8dae5d37ec845b5ab89b`
- Approval: The user granted automatic approval for sequential research steps in the current session; dependency and Gate checks remain mandatory.
- Hypothesis: A completed 1h compression state can precede directional expansion driven by delayed repricing, stops and forced liquidity; the candidate is spot long/cash only.
- Non-duplication: M1A's SMA200, Donchian 55/20 and ATR20 x2 bundle, timeframe relabeling and fixed-channel rescue remain prohibited.
- Result: `economic_hypothesis_pass_isolation_only`; no rule parameter, event, trade or return was selected or calculated.
- Authorization: After merge, M1E-05 IS data isolation only. Paper diagnostics, fixed rules, strategy code, backtesting, OOS, M2, API use, paper/live mode, orders and execution remain unauthorized.

## 2026-07-11 - M1E-04 Economic Hypothesis Merged

- Date UTC: 2026-07-11T01:10:31Z
- Task ID: M1E-04
- Phase: M1E IS-only economic hypothesis
- Branch: main
- Commit: `fca037f78a5a7cb8151129e86c3d721a81cc7d31`
- PR: #46 merged
- Result: Economic mechanism and M1A non-duplication are canonical; no strategy parameter or return was selected.
- Next action: M1E-05 IS data isolation only.

## 2026-07-11 - M1E-05 IS Data Isolation Passed Locally

- Date UTC: 2026-07-11T01:14:56Z
- Task ID: M1E-05
- Phase: M1E IS-only data isolation
- Branch: `codex/m1e-is-data-isolator`
- PR: #47 open
- Commit: `7adaf3f60fbcbc8e0e3ef91307b247b68a883564`
- Evidence: BTC/ETH each contain 36,763 isolated 1h bars and 9,181 isolated 4h bars from 2020-07-01 through 2024-09-10. Each dataset has 11 gaps and 12 continuous segments.
- OOS safety: Rows at or after 2024-09-11 are not exposed to the isolator and their OHLC fields are not parsed; candidate evaluated `no`, returns computed `no`, OOS opened `no`.
- Runtime artifacts: IS snapshots and detailed manifest remain ignored under storage/duckdb and storage/logs.
- Authorization: After merge, M1E-06 IS paper diagnostics only. Fixed rule contract, strategy code, backtesting, OOS, M2, APIs, paper/live mode, orders and execution remain unauthorized.

## 2026-07-11 - M1E-05 IS Data Isolation Merged

- Date UTC: 2026-07-11T01:25:17Z
- Task ID: M1E-05
- Phase: M1E-06 IS-only paper-feasibility preparation
- Branch: main
- Commit: `08d40c8e8f3416e81269f3fb3a80d47a786fc88c`
- PR: #47 merged
- Validation: M1E Isolator Validate `PASS=8 FAIL=0`; all GitHub checks succeeded.
- Result: Physically bounded IS snapshots and OOS-rejecting audit interfaces are canonical; runtime snapshots remain ignored.
- Next action: M1E-06 IS-only paper diagnostics. No formal strategy returns or OOS access.

## 2026-07-11 - M1E-06 IS-Only Paper Feasibility Failed

- Date UTC: 2026-07-11T01:40:08Z
- Task ID: M1E-06
- Phase: M1E IS-only paper feasibility
- Branch: `codex/m1e-is-paper-feasibility`
- PR: #49 open
- Commit: `c107190`
- Protocol: Frozen in commits `03b8df8` and `66fd9a7` before outcome access; no parameter search or alternate rule was run.
- Evidence: 177 raw candidates, 139 complete 24h-cluster representatives, projected full/OOS counts 198/59, and no right-censored observation.
- Passed Gates: projected sample counts, both-symbol event counts, three-year repetition, year concentration and quarantine exclusion.
- Failed Gates: combined median 24h MFE 1.4005%, BTC 1.4658%, and ETH 1.4005%, each below the fixed 1.80% requirement.
- Decision: `failed_feasibility`. M1E-07, strategy code and Freqtrade backtesting are blocked. No M1E parameter rescue is allowed.
- OOS safety: OOS remains unopened; no OOS price, event, signal, trade or return was read. No formal strategy return or equity curve was computed.
- Next action: After this failure record is merged, only a separate M1G IS-only design review may follow. M2 and all trading remain prohibited.

## 2026-07-11 - M1E-06 Failure Record Merged

- Date UTC: 2026-07-11T01:53:39Z
- Task ID: M1E-06-MERGED
- Phase: M1G IS-only design preparation
- Branch: main
- Commit: `5bedd60`
- PR: #49 merged
- Validation: M1E Paper Validate, all predecessor M1E validators, Project Validate, M0 Validate, M1A Validate, M1B Validate and M1F Validate succeeded.
- Result: M1E is closed as `failed_feasibility`; M1E-07 and all M1E strategy implementation remain blocked, and its OOS was never opened.
- Next action: M1G may begin only with a separate IS-only economic-hypothesis and non-duplication design review. No fixed rule, strategy code, backtesting or OOS access is authorized.

## 2026-07-11 - M1G IS-Only Design Passed Locally

- Date UTC: 2026-07-11T02:05:00Z
- Task ID: M1G-01
- Phase: M1G IS-only economic hypothesis and non-duplication
- Branch: `codex/m1g-is-only-rule-design`
- PR: pending
- Candidate: `M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION`; registered hypothesis SHA256 remains `288d3c37b577f6523890155b3ab4e31e4150fea876e8c66bf5c0c69403c4f2fc`.
- Mechanism: A completed 1h forced-selling and urgent-liquidity dislocation may partially revert when the move is not permanent information repricing.
- Non-duplication: No M1E inversion or outcome-derived rule, M1D/daily-panic timeframe rescue, M1A bundle, or unauthorized volume field is allowed.
- Result: `economic_hypothesis_pass_paper_protocol_only`; no threshold, event, trade, return or strategy rule was selected.
- OOS safety: OOS remains unopened; existing sealed IS snapshot evidence is reused without duplicating the data pipeline.
- Next action: After merge, only freeze a price-only M1G paper protocol before outcome access. Strategy code, backtesting, M2 and all trading remain prohibited.

## 2026-07-11 - M1G Design Merged And Paper Protocol Frozen Locally

- Date UTC: 2026-07-11T02:13:18Z
- Task IDs: M1G-01-MERGED, M1G-02
- Phase: M1G paper protocol review
- Branch: `codex/m1g-paper-protocol`
- PR: pending
- Design merge: PR #51 merged as `0933779`; no event or return was evaluated.
- Frozen event: completed 1h return <= -2.40%, at least 3x prior-168h median absolute return, at least 2.5x prior-168h median true range, bottom-quartile close, and first event in each connected 24h cluster.
- Frozen Gates: projected full/OOS 120/30; combined and per-symbol median 24h MFE 1.80%; cross-symbol/year distribution and quarantine checks unchanged.
- Outcome safety: Event scan executed `no`; candidate outcomes accessed `no`; OOS opened `no`; formal returns computed `no`.
- Next action: After protocol merge, one exact sealed-IS diagnostic run may follow. Fixed rule contract, strategy code, backtesting, M2 and trading remain prohibited.

## 2026-07-11 - M1G Protocol Merged And Paper Feasibility Passed Locally

- Date UTC: 2026-07-11T02:23:06Z
- Task IDs: M1G-02-MERGED, M1G-03
- Phase: M1G IS-only paper feasibility
- Branch: `codex/m1g-is-paper-feasibility`
- PR: pending
- Protocol merge: PR #52 merged as `9a4e1f1`; the protocol was not changed before the run.
- Evidence: 316 raw candidates, 213 cluster representatives, 210 complete events, 3 right-censored; projected full/OOS events 300/90.
- Passed Gates: combined median 24h MFE 2.6908%, BTC 2.6997%, ETH 2.6409%; sample, symbol, year, concentration and quarantine Gates all pass.
- Tail warning: median 24h MAE -3.3118%, worst MAE -21.5829%, maximum 7 events in rolling 7 days, and median 24h close displacement 0.2268% below Base roundtrip cost.
- Decision: `pass_tail_risk_disclosed` authorizes only fixed-rule contract design after merge. It does not establish positive expectancy or approve strategy code.
- OOS safety: OOS prices/returns accessed `no`; OOS opened `no`; formal strategy returns and equity curve computed `no`.
- Next action: Freeze one target, invalidation stop, holding limit, position cap and cooldown without parameter search. Backtesting, M2 and trading remain prohibited.

## 2026-07-11 - M1G Paper Evidence Merged And Fixed Contract Frozen Locally

- Date UTC: 2026-07-11T02:35:07Z
- Task IDs: M1G-03-MERGED, M1G-04
- Phase: M1G fixed rule contract
- Branch: `codex/m1g-fixed-rule-contract`
- PR: pending
- Paper merge: PR #53 merged as `5221e43`; the frozen event protocol and outcome report remain unchanged.
- Contract: +1.80% target, -4.00% invalidation stop, 24h timeout, 25% equity cap, maximum one trade and 72h global cooldown.
- Conservative semantics: next available 5m open entry; same-5m target/stop resolves to stop; stop gap uses worse open; target gap receives target threshold only.
- Derivation: target equals the fixed paper hurdle; stop rounds median MAE outward; stop times position cap gives 1% planned equity risk; cooldown addresses observed event clustering.
- Search safety: Parameter search `no`; alternatives evaluated `no`; OOS opened `no`; backtest executed `no`.
- Next action: After contract merge, only an exact Freqtrade implementation and causal fixture validation may follow. Performance backtesting, M2 and trading remain prohibited.

## 2026-07-11 - M1G Contract Merged And Freqtrade Capability Reviewed Locally

- Date UTC: 2026-07-11T02:48:23Z
- Task IDs: M1G-04-MERGED, M1G-05A
- Phase: M1G Freqtrade capability review
- Branch: `codex/m1g-freqtrade-capability-review`
- PR: pending
- Contract merge: PR #54 merged as `a160f2c`; no performance backtest or OOS access occurred.
- Native pass: 1h next-open signals, 5m detail, stop-before-ROI, 1.80% ROI, 24h timeout, one slot, 25% capital cap, deterministic pair ranking and all-pair 72h cooldown are implementable.
- Material difference: Native ROI and stoploss gap pricing can be more favorable than the fixed conservative target/stop gap rules.
- Decision: `capability_pass_with_mandatory_execution_audit`. Freqtrade remains signal/trade-lifecycle authority; Python may only reprice exported trades with canonical 5m data and cannot select events or run a second strategy.
- Next action: After merge, implement the exact Freqtrade plugin and audit hook without running performance backtests. OOS, M2 and trading remain prohibited.

## 2026-07-11 - M1G Freqtrade Capability Review Merged

- Date UTC: 2026-07-11T07:11:38Z
- Task ID: M1G-05A-C
- Phase: M1G Freqtrade implementation preparation
- Branch: main
- Commit: `d9e43ddf805bbed8100e0596012acb4a84334cee`
- PR: #55 merged
- Validation: M1G Freqtrade Capability Validate, Project Validate, and all repository checks succeeded.
- Result: `capability_pass_with_mandatory_execution_audit`; exact strategy implementation is authorized, but performance backtesting is not.
- Next action: Implement the frozen Freqtrade plugin, causal/runtime fixtures, and conservative trade-export repricing audit on a new branch.
- Safety: OOS remains unopened. M2, private APIs, dry-run/live, orders, matching and execution/live remain prohibited.

## 2026-07-11 - M1G Freqtrade Implementation Passed Locally

- Date UTC: 2026-07-11T07:45:53Z
- Task IDs: M1G-05, M1G-06, M1G-07
- Phase: M1G Freqtrade implementation and conservative execution audit
- Branch: `codex/m1g-freqtrade-implementation`
- PR: pending
- Strategy: Exact completed-1h event, 5m detail, deterministic BTC/ETH ranking, +1.80% target, -4.00% stop, 24h timeout, 25% cap, one position and 72h all-pair cooldown.
- Runtime: Pinned Freqtrade 2026.6 lookahead passed 20 signals with zero biased entries/exits/indicators; recursive analysis found zero variance and zero indicator lookahead at startup 170/250/340.
- Audit: Python reprices only exported trades using canonical 5m target/stop/gap/timeout rules; it cannot select signals or become a second strategy engine.
- Result: `implementation_pass_no_performance_run`; candidate return computed `no`, OOS opened `no`.
- Next action: After merge, freeze a separate IS validation protocol before any performance run.
- Safety: No API key, private data, dry-run/live, order, matching or execution/live logic was used.

## 2026-07-11 - M1G Implementation Merged And IS Protocol Frozen

- Date UTC: 2026-07-11T08:00:16Z
- Task IDs: M1G-05/06/07-MERGED, M1G-08
- Phase: M1G IS validation protocol review
- Branch: `codex/m1g-is-validation-protocol`
- PR: pending
- Implementation merge: PR #57 merged as `03879c5`; all checks succeeded.
- Protocol: IS `2020-07-01` through `2024-09-11` exclusive, four fixed costs, 56-trade IS minimum, daily-MTM/benchmark Gates and mandatory native plus conservative audit.
- Artifact freeze: Strategy, config, audit, fixed contract, runtime evidence and data-authority report are pinned by SHA256.
- Outcome safety: IS performance run `no`; OOS opened `no`; trial count remains 3.
- Next action: Merge this pre-result protocol before one fixed IS numerical run.
- Safety: API keys, private data, dry-run/live, orders, matching, execution/live and M2 remain prohibited.

## 2026-07-11 - M1G IS Protocol Merged

- Date UTC: 2026-07-11T08:13:06Z
- Task ID: M1G-08-MERGED
- Phase: M1G frozen IS validation
- Branch: main
- Commit: `f7dddd215ef556d4ff7067a70315381d92a44f74`
- PR: #58 merged
- Result: The IS range, four cost scenarios, daily-MTM and benchmark Gates, artifact hashes, and mandatory native/conservative audit were frozen before any performance result was accessed.
- Authorization: One exact IS run only. OOS, parameter changes, M2 and all trading remained prohibited.

## 2026-07-11 - M1G Frozen IS Validation Failed

- Date UTC: 2026-07-11T08:24:06Z
- Task IDs: M1G-09, M1G-10
- Phase: M1G IS numerical validation and independent audit
- Branch: `codex/m1g-is-validation`
- PR: #59 open
- Result commit: `3636a2ad93996f02ab0c629acfc38c5995fc608b`
- Evidence: `reports/m1/M1G_IS_VALIDATION_REPORT.md`
- Freqtrade Base: 179 trades, -22.6272% total return, daily-MTM Sharpe -1.3195, PSR 0.0013, MaxDD 23.9747%.
- Conservative Base: -21.3551% total return with 66 native/audited exit-bar mismatches.
- Freqtrade Cost x2: 177 trades, -28.3540% total return, daily-MTM Sharpe -1.6457, PSR 0.0001, MaxDD 29.5509%.
- Conservative Cost x2: -31.5286% total return with 83 native/audited exit-bar mismatches.
- Decision: `failed_validation`; returns, risk-adjusted metrics, drawdown, delete-best-3, segment, benchmark and execution-audit Gates fail.
- OOS safety: M1G OOS remains unopened and the DSR opened-trial count remains three.
- Next action: Merge the truthful failure record, then allow only a separate M1H design review. No M1G rescue, M2, private API, dry-run/live, order or execution work is authorized.

## 2026-07-11 - M1G Failed IS Validation Merged

- Date UTC: 2026-07-11T08:40:23Z
- Task IDs: M1G-09-MERGED, M1G-10-MERGED
- Phase: M1H independent design-review authorization
- Branch: main
- Commit: `929e3a23f0f78be75a746920a313572d15519910`
- PR: #59 merged
- Validation: All 60 GitHub checks passed; local M1G IS Validate passed 9/0.
- Result: M1G is closed as `failed_validation`; no Gate was lowered, no parameter changed, and OOS was never opened.
- Next action: Only M1H economic-hypothesis and non-duplication design review is authorized. Rule selection, strategy code, return analysis, OOS, M2 and trading remain prohibited.

## 2026-07-11 - M1H Independent Design Review Passed Locally

- Date UTC: 2026-07-11T09:20:00Z
- Task ID: M1H-01
- Phase: M1H economic hypothesis, timing, lineage and non-duplication design
- Branch: `codex/m1h-independent-design-review`
- PR: #61 open
- Result commit: `7cde978acd50291dc6d09f788c5e4301dc767533`
- Candidate: `FUNDING-EXTREME-SPOT-CONTRARIAN`; registered SHA256 remains `f4caf96502aca9272d58faab20a6e2dc07eea4c69e49d9705272c00a46b814ed`.
- Selected route: A settled extreme negative funding observation may represent crowded short positioning whose later unwind can support spot appreciation.
- Structural boundary: Funding is public sentiment information only; M1H uses spot long/cash and has no funding income, perpetual short, basis hedge or two-leg execution.
- Timing: The event is unavailable before `fundingTime`; a future entry must be at a canonical spot open strictly later than settlement and cannot precede the decision.
- Data lineage: M0 public funding history is primary; funding cadence follows fundingInfo, multiple premium schedules, then adjacent historical settlements, with no hardcoded default.
- Representability: No exit selected. Any later implementation requires a separate capability review and zero-mismatch conservative fixtures under Freqtrade-first authority.
- Outcome safety: Event scan `no`, rule parameters selected `no`, formal returns `no`, OOS opened `no`, DSR trial count unchanged at three.
- Next action: Review and merge the design package. Only then may a separate pre-outcome M1H paper protocol be frozen; no diagnostic run is yet authorized.

## 2026-07-11 - M1H Independent Design Review Merged

- Date UTC: 2026-07-11T15:10:06Z
- Task ID: M1H-01-MERGED
- Phase: M1H paper protocol design authorization
- Branch: main
- Commit: `5622a10606f32ed7af04f172ff1c0e919cc035b4`
- PR: #61 merged
- Validation: All 62 GitHub checks passed; local M1H design validation passed 10/0.
- Result: The settlement-aligned negative-funding crowding hypothesis, strict post-settlement timing, public lineage, non-duplication and representability constraints are accepted as design evidence only.
- Outcome safety: M1H remains `declared_unopened`; no event scan, return, OOS value, strategy rule or implementation was produced.
- Next action: Only a separate pre-outcome M1H paper-protocol design is authorized. It must merge before any sealed-IS event scan; strategy code, OOS, M2 and trading remain prohibited.

## 2026-07-11 - M1H Paper Research Protocol Frozen Locally

- Date UTC: 2026-07-11T15:36:43Z
- Task ID: M1H-02
- Phase: M1H paper protocol freeze pending review
- Branch: `codex/m1h-paper-protocol-freeze`
- PR: #63 open
- Result commit: `71d1e38b1f3ff41960f3c663a2070976f0049523`
- Candidate: `FUNDING-EXTREME-SPOT-CONTRARIAN`; registered hash and `declared_unopened` state are unchanged.
- Event contract: Settled negative funding at or below the same-symbol prior-365-day lower 5% percentile, linearly interpolated and annualized with the M0 per-event interval chain.
- Timing contract: The observation reference is the exact next expected canonical 5m open strictly after `fundingTime`; missing references are not shifted forward.
- Evidence contract: Frozen 1/2/4/8/12/24-hour reaction windows; median close displacement is the cost-coverage Gate, while MFE/MAE/recovery are mandatory mechanism diagnostics only.
- Leakage contract: No threshold, interval, horizon, year, symbol, clustering or censoring choice may change from outcomes; changes require a new ADR and protocol identity.
- Outcome safety: Event scan `no`, event count `no`, formal returns `no`, paper feasibility `no`, OOS `no`, strategy code `no`, M2 `no`.
- Next action: Review and merge this protocol. A future separately started M1H-03 task may qualify funding data first and, only if it passes, continue once to sealed-IS paper feasibility without an intermediate approval.

## 2026-07-11 - M1H Paper Research Protocol Merged

- Date UTC: 2026-07-11T16:12:28Z
- Task ID: M1H-02-MERGED
- Phase: M1H-03 authorization, not started
- Branch: main
- Commit: `dd4ae5bb04d9343e83a4a3f05994c7f5edea8617`
- PR: #63 merged
- Validation: Local M1H protocol validation passed 11/0 with 308 tests; all 64 GitHub checks passed.
- Result: The pre-outcome funding-tail identity, exact post-settlement timing, fixed reaction windows, close-displacement Gates and leakage controls are frozen.
- Outcome safety: M1H remains `declared_unopened`; no funding event, event count, path result, return or OOS value was accessed.
- Next action: M1H-03 may be started separately. It must run pure funding-data qualification first and may continue once to sealed-IS paper feasibility only if qualification passes; no intermediate approval is required.

## 2026-07-11 - M1H Funding Qualification Passed And Paper Feasibility Failed

- Date UTC: 2026-07-11T16:45:55Z
- Task IDs: M1H-03A, M1H-03B
- Phase: M1H public funding qualification and one frozen sealed-IS paper observation
- Branch: `codex/m1h-funding-paper-feasibility`
- PR: #65 merged
- Merge commit: `57c2b1c038b949396999c9735b2c06df76cf61aa`
- Qualification: pass; BTCUSDT and ETHUSDT each have 5,145 unique pre-OOS settlements, zero conflicting duplicates, invalid intervals or missing settlements. OOS funding and spot values parsed: no.
- Canonical spot dependency: 441,215 sealed-IS 5m rows per symbol; 11 known gaps remain explicit and were never filled or shifted.
- Paper evidence: 131 independent episodes, projected full 187 and sealed-OOS 56; sample Gates passed without reading OOS events or prices.
- Failure: combined median 24h close displacement was 0.0714%, BTCUSDT 0.0731%, and ETHUSDT 0.0132%, each below the frozen 1.80% Gate. The maximum single-year share was 48.09%, above 45%.
- MFE disclosure: median 24h MFE was 2.3108%, but the frozen protocol makes MFE diagnostic only and forbids it from overriding close-displacement failure.
- Decision: `failed_feasibility`; no protocol parameter changed, no strategy rule or return was created, and OOS remains sealed.
- Next action: Stop the ADR-0010 BTC/ETH two-asset candidate queue. Only M0 audit work or a new broader high-liquidity spot-universe ADR may follow; M2 and all trading remain prohibited.

## 2026-07-11 - BTC/ETH Candidate Queue Closed

- Date UTC: 2026-07-11T17:23:26Z
- Task ID: U-01
- Phase: Candidate-queue terminal governance
- Evidence: PR #65 merged at `57c2b1c`; M1E, M1G and M1H retain their truthful failure records.
- Decision: BTC/ETH two-asset indicator research is exhausted. A fourth indicator candidate, parameter rescue, OOS reuse or threshold reduction is prohibited.
- Safety: M1G and M1H OOS remain sealed; DSR opened-trial count remains three; no strategy is eligible for M2.
- Next action: ADR-0011 may define a historically reconstructable high-liquidity USDT spot universe and asset qualification contract only. Strategy selection, event scanning, returns and OOS remain unauthorized.

## 2026-07-12 - ADR-0011 Liquid Spot Universe Frozen

- Task ID: U-02
- Branch: `codex/adr-0011-liquid-spot-universe-expansion`
- Decision: Monthly point-in-time Top 15 by prior-90-day median daily quote volume, minimum 365 complete days, deterministic symbol tie-break and conservative exclusions.
- Authority: M0 constructs historical membership; Freqtrade may later consume deterministic slices and must not use a current dynamic pairlist as historical truth.
- Safety: No strategy family, event, signal, return, OOS, API, trading or M2 permission is created.
- Next action: Merge after contract and project validation; only then may a separate asset/data qualification task start.

## 2026-07-12 - Liquid Universe Qualification Core Implemented

- Task ID: U-03A
- Branch: `codex/liquid-spot-universe-qualification`
- Result: Deterministic prior-window ranking, monthly/daily precedence, exclusions, delisting-safe historical membership, exact 5m-to-1h aggregation and canonical hashing are fixture-tested.
- Evidence status: `implementation_pass_runtime_qualification_pending`; no real broader-universe monthly membership is claimed.
- Safety: No strategy, event, signal, return, OOS, API or trading logic was added.
- Next action: Execute the official public archive run. Cross-sectional hypothesis design remains blocked until real qualification evidence passes.

## 2026-07-12 - Liquid Universe Public Qualification Blocked

- Task ID: U-03B
- Evidence: 676 historical symbols, 78 effective months, 1,170 membership rows, 1,019 qualified 5m symbol-months and 803,652 derived 1h bars.
- Blocker: 151 selected symbol-months contain at least one incomplete 5m hour. They have not yet been proven as common exchange outages.
- Decision: Qualification remains blocked; no fill, interpolation or strategy authorization is allowed.
- Next action: Use official cross-symbol and archive evidence to classify each incomplete observation. Preserve the frozen universe contract and rankings.

## 2026-07-12 - Liquid Universe Gap Attribution Completed

- Task ID: U-03C
- Branch / PR: `codex/liquid-spot-universe-qualification` / #68
- Scope correction: The original 151 count represented affected symbol-months. Exact timestamp expansion produced 227 contiguous gap runs.
- Global evidence: 225 per-symbol runs collapse to 15 unique windows and meet the frozen >=80% synchronous-member threshold; they are quarantined without synthetic bars.
- Symbol-specific evidence: LUNAUSDT 2022-05 and RNDRUSDT 2024-07 terminate in their official monthly ZIP while 14 peers remain present. Each symbol-month is isolated without replacement.
- Processing/unresolved: zero / zero.
- Decision: Universe data qualification is `pass_with_quarantine` pending PR review. Strategy design, outcomes, backtesting, OOS and M2 remain unauthorized.

## 2026-07-11 - Liquid Universe Qualification Merged

- Task IDs: U-03A, U-03B, U-03C
- PR / merge commit: #68 / `1996ea3e2c891d3ad6a366b5243111950a6968ed`
- Validation: 70/70 GitHub checks passed; local qualification validation passed with 336 full-suite tests.
- Result: Public data qualification and all gap attributions are accepted with quarantine, zero processing errors and zero unresolved gaps.
- Safety: No strategy, event, return, backtest, OOS, API, trading or M2 authorization was created.
- Next action: Await a separate explicit decision to preregister one cross-sectional hypothesis family; do not begin implementation automatically.

## 2026-07-14 - Liquid Universe V2 Correctness Hardening Started

- Task ID: U-03D
- Branch: `codex/liquid-universe-qualification-hardening-v2`
- PR: pending
- Basis: A blocking correctness review found that V1 did not fully machine-enforce asset categories, continuous windows, complete 5m grids, fail-closed gap evidence, quarantine scope, artifact authority, or authorization output.
- Decision: Preserve V1 reports as historical evidence but mark their admission decision `superseded_pending_v2_requalification` under ADR-0012.
- Implementation: Freeze `LIQUID-SPOT-USDT-TOP15-V2`, a versioned exclusion registry, verified archive provenance, deterministic machine manifests, complete-grid validation, fail-closed attribution, and exact state transitions.
- Safety: No hypothesis, event scan, strategy, return, OOS, Freqtrade backtest, API/trading, or M2 work is authorized.
- Next action: Complete U-03D tests and CI, merge it, then perform U-03E public cold/warm requalification before any independent audit.

## 2026-07-15 - Liquid Universe V2 Public Requalification Blocked

- Task IDs: U-03D / U-03E
- U-03D: PR #70 merged at `5ab69e2`; the V2 contract, registry, machine authority and fail-closed validators passed.
- U-03E branch: `codex/liquid-universe-v2-requalification`
- U-03E PR / evidence head: #71 / `9d04ff8e31fb92024aa24922b183203dc4ec4d9a`
- Scope: Official public archives only, `2020-01` through `2026-06`; no event, signal, return, OOS or strategy data was accessed.
- Determinism: Cold build with 16 workers and warm build with 3 workers produced the same artifact-set hash `b7c89f2465f570db0687ed20f81a84d570e8746eb0be95c2767429733c0bdfb7`; deterministic mismatches are zero.
- Result: `blocked_data_conflict`, with 676 discovered symbols, 78 months, 1,170 membership rows, 227 gap records, zero unresolved gaps, zero excluded-category members, zero synthetic fills and zero replacement members.
- Official-source blockers: BTTUSDT 2019-01 and 2019-02 contain negative daily volume; AXSUSDT 2026-02 contains a duplicate official monthly row for 2026-02-10. All source files passed official checksum verification.
- V1/V2 comparison: 78 months compared; 6 changed months, 7 additions, 7 removals and 33 rank changes. V1 Markdown was not used as a qualification input.
- Decision: Keep U-03F and U-04 unauthorized. Do not deduplicate, drop rows, change rankings or continue to strategy research. Resolve source evidence or introduce a separately reviewed data-policy ADR.
- Safety: No API key, private data, trading API, backtest, OOS, execution/live or M2 authorization was used or created.

## 2026-07-15 - Liquid Universe V2 Blocked Evidence Merged

- Date UTC: 2026-07-15T02:39:37Z
- Task ID: U-03E-MERGED
- Phase: Liquid universe V2 public requalification blocked
- Branch: main
- PR / merge commit: #71 / `8c4db86bba3f8910b892e174119eba3a5c5e88c1`
- Result: The deterministic cold/warm public requalification evidence is merged as `blocked_data_conflict`; it is not a qualification pass.
- Blockers: Checksum-verified BTTUSDT 2019-01/02 daily archives contain negative volume and the AXSUSDT 2026-02 daily archive duplicates 2026-02-10.
- Governance: U-03E leaves `open_work` as a closed blocked milestone. U-03F and U-04 remain `not_authorized` until a future V2 public requalification passes under reviewed source evidence or a new data-policy ADR.
- Safety: No strategy, event scan, return, backtest, OOS, API/trading, execution/live or M2 authorization was created.

## 2026-07-15 - Liquid Universe V2 Source Conflicts Adjudicated

- Task ID: U-03E-ADJ
- Branch: `codex/u03e-source-conflict-adjudication`
- PR / evidence commit: #73 / `b9d3a30a94ddaa24a753ba6fb966f8491ba34d69`
- Evidence: `reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json`, content hash `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`.
- BTT result: Current official monthly checksums are unchanged. One January and four February rows have negative `base_volume`; official daily ZIPs and both public REST hosts agree on positive rows, with all other authoritative fields equal. The exact delta has a `2^64 / 1e8` overflow signature, but no algebraic repair is authorized.
- AXS result: The current official monthly checksum is unchanged. Monthly and daily ZIPs each contain two byte-identical 2026-02-10 rows; both public REST hosts return one matching row. The conflict is not parser-created and is not waived by AXS having no V2 Top-15 membership month.
- Decision: `new_policy_adr_required`. The V2 contract remains unchanged and fail closed; no U-03E rerun is authorized.
- Next action: After this evidence merges, create a separate Draft ADR for a general archive-row conflict policy. Do not adopt it or rerun qualification without independent review and explicit approval.
- Safety: U-03F/U-04, strategy, event scan, returns, backtesting, OOS, API/trading, execution/live and M2 remain unauthorized.

## 2026-07-15 - ADR-0013 Independent Review Completed Pending Merge

- Date UTC: 2026-07-15T06:30:00Z
- Task ID: ADR-0013-REVIEW
- Phase: ADR-0013 independent review
- Branch: `codex/adr-0013-independent-review`
- PR: pending
- Base main: `7477c34a403cdbdcf0a7dcc36c4646d32e6d5b83`
- Reviewed PR #74 head: `8dc9ee034fdd172147485f7718117f8a76713cdf`
- ADR evidence commit: `4a95a28142d13aa2f03f271baf660ae95ba67e78`
- Verdict: `approve_with_required_changes`.
- Evidence: `reports/expert/evidence/adr0013_independent_review.json`.
- Mandatory changes: A1-A10 cover frozen comparator evidence, fixed processing order, field semantics, complete duplicate groups, daily-candidate validation, fail-closed registry, quarantine layers, fixed first range, hash bindings and governance SHA meanings.
- Authorization: ADR remains proposed; V3 implementation, U-03E rerun, U-03F, U-04, strategy, outcomes, OOS, API/trading and M2 remain false.

## 2026-07-15 - ADR-0013 Mandatory Changes Completed Pending Merge

- Date UTC: 2026-07-15T07:00:00Z
- Task ID: ADR-0013-ADOPT
- Phase: ADR-0013 conditional adoption
- Branch / PR: `codex/adr-0013-official-archive-row-conflict-policy` / #74
- Independent review: PR #75 merged at `2f925324bd8c0e92d031e96b7fca3a80adb80b6b` with 78/78 checks successful.
- Result: A1-A10 are incorporated; status is `Accepted for V3 implementation and U-03E requalification only` pending PR #74 conformance, CI and merge.
- SHA semantics: `evidence_commit=4a95a28142d13aa2f03f271baf660ae95ba67e78`, `reviewed_head_sha=8dc9ee034fdd172147485f7718117f8a76713cdf`, while current `head_sha` is runtime Git/GitHub metadata.
- Authorization: generic V3 contract/registry implementation and a dependent U-03E V3 rerun only. U-03F, U-04, strategy, events, returns, OOS, API/trading and M2 remain false.
# 2026-07-15 - ADR-0013 Adopted And V3 Generic Implementation Started

- Date UTC: 2026-07-15T06:30:00Z
- Task IDs: ADR-0013-ADOPT, U-03E-V3-IMPL
- ADR PR / merge: #74 / `20e7ceb7f35366da3afe4859a4168ee1954bd5ae`
- Branch: `codex/liquid-universe-v3-row-conflict-policy`
- Decision: ADR-0013 is accepted only for generic V3 implementation and the fixed-range U-03E V3 requalification. U-03F and U-04 remain unauthorized.
- Implementation: complete-key duplicate classification, exact offline registry binding, invalid-monthly daily correction, canonical provenance, two quarantine scopes and fail-closed drift handling are fixture-tested.
- Hashes: contract `f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed`; resolution registry `570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4`; adjudication evidence `8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b`.
- Public run: not executed in this task. V2 remains blocked historical evidence.
- Safety: no strategy, event, return, backtest, OOS, API, trading, U-03F, U-04 or M2 authorization.
