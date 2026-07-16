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

- Current phase: U-03F V4 independent audit failed pending truthful result review. Three offline runs are deterministic, but only 10/15 production manifests match and the result has 1 critical / 7 high findings.
- The implementation algorithm hash remains `7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1`; production V4 authority code and evidence were not modified by the audit.
- U-03F V4 independent-audit protocol merged in PR #91 and remains frozen. Its content hash is `0f4127ceb4f57f78c6fead022f9c71cb07d0f10c55d4a91f3f9cde57005a8157`.
- Stage D processed all 27,736 frozen archives in normal, reverse and deterministic shuffled order. The truthful verdict is `failed_audit`.
- Only the audit-result review and subsequent separate failed-audit governance closeout may follow. U-04, strategy, outcomes, OOS and M2 remain unauthorized.
- V4 is the active qualification authority. Cold/warm/worker all produced artifact set `4cfca060...65fde6`; the run manifest is `f55f2829...76b127`.
- PR #81 is closed as superseded. Its exact reviewed head `31c967c`, semantic hash and three docs-only models remain immutable historical evidence.
- The reviewed Draft models KLAYUSDT 2024-10-28 partial lifecycle, 2024-10-29 normal-duration post-cessation placeholder and 2024-10-30 malformed placeholder as one versioned availability event instead of one row signature.
- PR #76 merged the generic V3 implementation at `b3496fe` after 82/82 checks passed.
- PR #77 merged at `c6d44d9` after 84/84 checks passed. The cold V3 build resolved the six frozen BTT/AXS cases, then blocked on KLAYUSDT 2024-10-30; warm/worker were not run after the stop. U-03F and U-04 remain unauthorized.
- ADR-0012 supersedes the V1 qualification admission decision pending V2 public requalification and independent audit. V1 reports remain historical evidence.
- V3 machine JSON manifests supersede V2 only after a V3 pass. The current cold V3 evidence is blocked and cannot authorize U-03F.
- U-03D passed and merged in PR #70 at `5ab69e2`. U-03E cold/warm public builds match exactly but qualification is blocked by BTTUSDT negative daily volume in 2019-01/02 and a duplicate AXSUSDT row on 2026-02-10.
- U-03E truthful blocked evidence merged in PR #71 at `8c4db86`. It is a closed blocked milestone, not a qualification pass or active implementation task.
- U-03F is `completed_failed_audit_pending_review`. Do not fix production logic in the result PR; U-04 remains unauthorized.
- V3 machine JSON manifests become active qualification authority only after a V3 pass. V1 is superseded, V2 is blocked historical evidence, and Markdown reports must never be qualification inputs.
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
- P2 static and pinned-runtime checks passed in run 29059474678 and merged in PR #16.
- P2 merged in PR #16. P3 must use fixed parameters and gates; any failure stops the candidate without tuning or P4.
- M1C P3 failed fixed trade-count, OOS Sharpe, and drawdown gates in run 29060604088. PR #17 is a failure record; P4 is blocked.
- PR #17 merged. M1C is closed as `failed_validation`; there is no active strategy implementation task.
- Expert measurement review independently reproduced M1C and kept it failed; corrected daily-MTM metrics are the future regression authority.
- ADR-0007 locks the product to discrete completed-15m events, authoritative 1m backtest detail, and 5m sensitivity only.
- Holding time and trade frequency are strategy outputs. Do not add a fixed holding duration or daily trade quota.
- T0 governance merged in PR #19; T1 data work merged in PR #21.
- T1 passed and merged in PR #21 with research start `2023-10-01`.
- T2 golden-data and quarantine passed and merged in PR #23.
- T3 unified metrics and policy benchmark passed and merged in PR #25.
- T4 IS-only feasibility harness passed and merged in PR #27 with no candidate evaluation and no OOS-return access.
- T5 was authorized only for its sample-budget precheck. The current sealed OOS calendar is 302 days versus the fixed 540-day minimum, so T5 stopped without lowering the gate.
- The earliest projected full-history end that can satisfy the calendar requirement is `2028-09-03`.
- T5 metadata-only precheck merged in PR #29 as `blocked_insufficient_oos_calendar`; it evaluated no candidate, selected no events, and accessed no OOS prices or returns.
- T6 and M1D strategy implementation are blocked. Only monthly public-data accrual, M0 audit diagnostics, or a separately approved new-candidate design may follow.
- M1E is that separately approved new trial. ADR-0008 and its machine contract authorize only official spot 5m/1h/4h data qualification, then a conditional metadata-only 1800/540-day calendar check.
- M1E is not an M1A rescue. Reuse of the combined SMA200, Donchian 55/20, and ATR20 2x rule bundle is prohibited.
- M1E OOS remains sealed. No M1E strategy rule, Freqtrade backtest, candidate return, or opened trial is authorized.
- ADR-0009 canonical-5m requalification passed and merged in PR #40 with research start `2020-07-01`, zero unresolved canonical conflicts, and pinned Freqtrade 2026.6 `list-data` pass.
- M1E metadata-only sample budgeting passed and merged in PR #42 with 2191 full, 1533 IS, and 658 sealed OOS days. It authorizes design review only after explicit approval.
- ADR-0010 froze the research order as M1E, M1G, then M1H. All three have now failed their applicable frozen Gates without opening M1G/M1H OOS, so BTC/ETH two-asset indicator research is stopped.
- The DSR ledger counts three historically opened OOS trials: M1A, M1B, and M1C. No current candidate OOS is open.
- Q-01/Q-02 governance merged in PR #44. M1E-04 design approval is now granted, while strategy code, Freqtrade backtesting and OOS access remain unauthorized.
- The user granted current-session automatic approval for sequential research approvals. This removes confirmation pauses only; dependencies, machine Gates, OOS sealing and safety prohibitions remain mandatory.
- M1E-04 selects no strategy parameter. It defines only the compression-to-expansion economic mechanism, failure regimes, IS boundary and M1A non-duplication; only M1E-05 isolation may follow after merge.
- M1E-04 merged in PR #46. M1E-05 produced ignored IS-only 1h/4h snapshots with no OOS OHLC parsing, gap segmentation and deferred rewarm thresholds; only M1E-06 paper diagnostics may follow after merge.
- M1E-05 merged in PR #47. M1E-06 used only sealed IS snapshots and failed the fixed combined/BTC/ETH 24h MFE Gates. M1E-07 and all M1E strategy work are blocked; no formal strategy returns or OOS data were accessed.
- M1E-06 failed-feasibility evidence merged in PR #49. The next queue item is M1G one-hour panic-dislocation mean reversion, but only an independent IS-only design review may start. No M1G strategy code or OOS access is authorized.
- M1G design defines only a completed-1h forced-selling dislocation and short-horizon reversion hypothesis. It reuses the existing sealed canonical IS snapshots, selects no event threshold or strategy rule, and may authorize only a separate paper-protocol commit after merge.
- M1G design merged in PR #51. The M1G paper protocol is frozen before outcomes: completed 1h decline <= -2.40%, prior-168h median-relative return/range filters, bottom-quartile close, 24h clustering and unchanged 120/30 and 1.80% Gates. No event scan is authorized before protocol merge.
- M1G protocol merged in PR #52. Its exact sealed-IS run passed all paper Gates with 210 events and 2.69% median MFE, but median MAE is -3.31%, worst MAE is -21.58%, and median 24h close displacement is below Base cost. This is not a profitability pass; only a fixed-rule contract may follow after review.
- M1G paper evidence merged in PR #53. The fixed pre-implementation contract uses +1.80% target, -4.00% stop, 24h timeout, 25% equity cap, one open trade and 72h global cooldown. It contains no parameter alternatives and authorizes no backtest until separately merged and implemented.
- M1G fixed contract merged in PR #54. Freqtrade 2026.6 supports the signal/lifecycle core and all-pair cooldown through `confirm_trade_entry`, but native ROI/stop gap pricing differs materially; every future result must also pass a conservative trade-export execution audit without creating a second strategy engine.
- M1G capability review merged in PR #55 as `d9e43dd`. Only exact strategy implementation, causal/runtime fixtures, and the mandatory conservative trade-export audit are authorized next; performance backtesting and OOS remain blocked.
- M1G exact strategy, causal fixtures, conservative repricing audit, pinned lookahead and recursive checks pass on `codex/m1g-freqtrade-implementation`. No performance report was generated; only a separately frozen IS protocol may follow after merge.
- M1G implementation merged in PR #57. The IS protocol is frozen before outcomes on `codex/m1g-is-validation-protocol`; no performance run is allowed before that protocol merges.
- M1G IS protocol merged in PR #58 before any performance result was accessed.
- The one frozen IS run is now `failed_validation`: Base and Cost x2 lose money, daily-MTM Sharpe/PSR/MaxDD and benchmark Gates fail, and conservative repricing finds non-zero exit-bar mismatches.
- M1G OOS remains sealed and its trial does not increment the DSR opened count.
- M1G failed-IS evidence merged in PR #59 as `929e3a2`; all 60 GitHub checks passed. M1G is closed without opening OOS or changing its frozen contract.
- M1H independent design is historical evidence only. Rule selection, strategy code, returns and OOS access remain unauthorized.
- M1H design selects only the settlement-aligned negative-funding crowding hypothesis route. Funding is a public sentiment input for spot long/cash; no futures position, funding cashflow or two-leg execution is allowed.
- M1H timing requires decisions no earlier than settlement and any future entry strictly after `fundingTime`. The extreme threshold, lookback, spot condition, timeframe, entry, exit, risk and position rules remain unresolved.
- M1H implementation requires a future zero-mismatch execution-representability Gate. The current design selects no exit family and authorizes only a separate paper-protocol design after merge.
- M1H independent design merged in PR #61 at `5622a10`. Only a separate pre-outcome paper-protocol design is authorized; event scanning, returns, strategy code and OOS access remain prohibited.
- M1H paper protocol freezes the prior-365-day lower 5% settled-funding event identity, exact post-settlement 5m timing, fixed reaction windows, close-displacement Gates and leakage controls without reading any outcome.
- MFE is a mandatory path diagnostic only and cannot prove edge or override a failed median 24h close-displacement Gate.
- This protocol PR authorizes no data qualification, event scan or paper feasibility. After merge, a separately started M1H-03 task may qualify data first and continue to one sealed-IS paper run only if qualification passes.
- M1H paper protocol merged in PR #63 at `dd4ae5b` after local 11/0 and GitHub 64/64 validation. M1H-03 may now be started as one two-stage task, but qualification must pass before any event scan.
- M1H-03A passed public funding lineage, per-event interval, settlement-continuity, canonical 5m and sealed-OOS qualification.
- The only frozen M1H-03B sealed-IS observation failed: combined/BTC/ETH median 24h close displacement was far below 1.80%, and the maximum single-year episode share exceeded 45%. MFE cannot rescue these failures.
- M1H remains `declared_unopened`; no strategy return, Freqtrade backtest or OOS value was accessed. M1H fixed rules and implementation are blocked.
- PR #65 merged the M1H truthful failure record at `57c2b1c`; M1H remains `declared_unopened`, failed feasibility, and closed without strategy or OOS access.
- Future research requires ADR-0011 for a broader point-in-time high-liquidity spot universe. Do not add a fourth BTC/ETH indicator candidate or modify the M1H protocol.
- ADR-0011 may define universe membership and data qualification only. It cannot select a strategy, scan outcomes, calculate returns, open OOS or authorize M2.
- ADR-0011 fixes monthly Top 15 by prior-90-complete-day median daily quote volume, 365 complete history days and deterministic symbol tie-break. Current dynamic pairlists are not historical authority.
- The public run discovered 676 historical symbols and 78 monthly Top-15 snapshots. All 151 affected symbol-months are attributed with 15 synchronized global windows, two isolated symbol-months, zero processing errors and zero unresolved gaps.
- Gap isolation never fills bars or replaces an excluded symbol. PR #68 merged at `1996ea3` after 70/70 checks passed; cross-sectional design still requires a separate explicit task.
- The original PR #32 blocked report remains historical evidence; PR #40 supersedes only its admission decision under the versioned authority contract.
- M1E conflict diagnostics found 30 reproducible rows: 16 monthly/daily conflicts, 10 REST-confirmed higher-timeframe revisions, 2 REST-confirmed child aggregates, and 2 third-version REST revisions. All remain contract-blocking.
- The diagnostic clean suffix starts `2022-11-01` but has only 1338 full and 402 sealed-OOS days, so it cannot satisfy the fixed 1800/540-day Gate even under a future contract review.
- M1E source diagnostics merged in PR #35. M1E is stopped before PR3; there is no active strategy or data-admission implementation branch.
- The sanitized 14-row supplement was posted with explicit user approval to Binance public-data issue #475 and is `submitted_awaiting_response`.
- Source-owner response remains provenance follow-up and is not an operational dependency for canonical M1E OHLC.
- No new strategy code is authorized.
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
