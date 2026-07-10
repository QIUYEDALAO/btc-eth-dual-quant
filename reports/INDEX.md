# Reports Index

| Report | Phase | Status | Meaning | Approves Trading |
| --- | --- | --- | --- | --- |
| `reports/m0/M0_FINAL_ACCEPTANCE.md` | M0 | accepted / audit_revalidation_required | Read-only infrastructure remains accepted; funding cadence fallback and ZIP/REST evidence require revalidation before new strategy approval. | no |
| `reports/m0/M0_AUDIT_REVALIDATION_REPORT.md` | M0 | blocked / audit_revalidation_required | Decision-facing exact audit summary. Approved proxy transport completed official futures REST; remaining blockers are official spot/UM source revisions and a 2026-06-29 reference-price archive omission with daily ZIP HTTP 404. | no |
| `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md` | M0 | blocked / audit_revalidation_required | Field-level direct/proxy evidence with payload hashes and daily ZIP outcomes. Official daily ZIPs recover monthly omissions when exact, but never replace conflicting monthly rows. | no |
| `reports/m1/M1A_REVIEW_DECISION.md` | M1A | failed_validation | Trend leg failed validation and is not eligible for M2; affected numerical evidence is superseded by the revalidation notice. | no |
| `reports/m1/M1A_REVALIDATION_NOTICE.md` | M1A | superseded_pending_revalidation | UTC alignment and delete-best-three methodology defects make affected historical metrics ineligible for future approval. | no |
| `reports/m1/M1F_FINAL_ACCEPTANCE.md` | M1F | accepted_as_feasibility_lab | Freqtrade Lab accepted only as research/backtest/WebUI candidate. | no |
| `reports/m1/FREQTRADE_PRIMARY_FRAMEWORK_HARDENING.md` | Freqtrade | pass | Official 2026.6 image is pinned by digest; approved research commands and VPS public smoke passed. This is framework acceptance only. | no |
| `reports/m1/FREQTRADE_M0_DATA_PROVENANCE.md` | Freqtrade/M0 | pass | BTC/ETH 1d Freqtrade JSON cache matches canonical M0 public rows over the recorded range. | no |
| `reports/m1/M1B_FUNDING_ARBITRAGE_BACKTEST_REPORT.md` | M1B | failed_validation / numerical evidence invalidated | Historical decision remains failed; numerical evidence contains event-time lookahead and cannot support future approval. | no |
| `reports/m1/M1B_DECISION.md` | M1B | failed_validation | Records suitability conclusion B accepted and corrected numerical report failed validation. | no |
| `reports/m1/M1B_FREQTRADE_FUNDING_BACKTEST_SUITABILITY.md` | M1B | conclusion_b_accepted | Freqtrade is partial support only and external accounting is required. | no |
| `reports/m1/M1B_DATA_RUN_PROVENANCE.md` | M1B | public_data_provenance | Records local public-data run provenance and corrected time-indexed metrics methodology; no raw data, DuckDB, API keys, or private payloads are committed. | no |
| `reports/m1/M1B_FINAL_DECISION.md` | M1B | failed_validation | Final M1B decision; not eligible for M2. | no |
| `reports/m1/M1B_REVALIDATION_NOTICE.md` | M1B | invalidated_pending_event_time_revalidation | Records the daily-close lookahead and entry-funding timing defects without rewriting history. | no |
| `reports/m1/M1B_EVENT_TIME_REVALIDATION_REPORT.md` | M1B | failed_validation | Strict 1h event-time rerun excludes entry-trigger funding, uses settlement mark notional, separates incomplete/carry-in positions, and still fails the complete-cycle gate. | no |
| `reports/m1/POST_M1B_REVIEW.md` | post-M1B | under_review | Reviews project after M1A and M1B failed validations. | no |
| `reports/m1/STRATEGY_FAILURE_DIAGNOSTICS.md` | post-M1B | diagnostics_complete_no_strategy_approved | Diagnoses M1A structural signal scarcity and M1B complete-cycle scarcity; recommends a new Freqtrade single-leg hypothesis design review without approving code or M2. | no |
| `docs/superpowers/specs/2026-07-10-quant-system-end-to-end-roadmap-design.md` | governance | approved | Defines the P0-P8 Freqtrade-first lifecycle, fixed M1C hypothesis, gates, ownership, and authorization boundaries. | no |
| `docs/superpowers/plans/2026-07-10-quant-system-end-to-end-implementation-plan.md` | governance | approved | Defines sequential branches, deliverables, validation, and rollback for P0-P8. | no |
| `docs/superpowers/specs/2026-07-10-m1c-btc-eth-rotation-design.md` | M1C P1 | design_pass | Fixes the BTC/ETH/cash rotation rules, time semantics, capital limits, numerical gates, and framework-failure behavior. | no |
| `reports/m1/M1C_FREQTRADE_CAPABILITY_REVIEW.md` | M1C P1 | design_pass | Pinned Freqtrade source supports informative-pair ranking, next-open signals, one slot, and same-open different-pair rotation; P2 runtime confirmation remains mandatory. | no |
| `reports/m1/M1C_IMPLEMENTATION_STATUS.md` | M1C P2 | pass | Fixed Freqtrade strategy, guarded research commands, UTC timing checks, same-open runtime fixture, lookahead, and recursive analysis passed; performance is not evaluated here. | no |
| `reports/m1/M1C_BTC_ETH_ROTATION_BACKTEST_REPORT.md` | M1C P3 | failed_validation | Freqtrade full/OOS/base/cost-x2 validation failed complete-trade, OOS Sharpe, and maximum-drawdown gates. P4 and M2 are blocked; no parameter rescue is allowed. | no |
| `reports/expert/2026-07-10-FABLE5-EXPERT-REVIEW.md` | post-M1C expert review | expert_review_complete | Reproduces Freqtrade risk fields, corrects M1C daily-MTM Sharpe/MaxDD/PSR, and keeps every failed decision frozen. | no |
| `reports/expert/m1c_recompute.py` | post-M1C expert review | deterministic_recompute_evidence | Standalone numpy recompute and integrity assertions for the expert review. | no |
| `reports/expert/m1c_oos_daily_equity.csv` | post-M1C expert review | deterministic_recompute_evidence | Auditable OOS daily-MTM Base and Cost x2 equity series. | no |
| `docs/superpowers/specs/2026-07-10-btc-eth-short-horizon-event-quant-design.md` | short-horizon governance | approved | Locks discrete 15m events, 1m detail, unified metrics, data authority, benchmark, and risk Gates. | no |
| `docs/superpowers/plans/2026-07-10-btc-eth-short-horizon-event-quant-implementation-plan.md` | short-horizon governance | approved | Defines dependency-ordered T0-T9 implementation and failure stops. | no |
| `docs/decisions/ADR-0007-btc-eth-short-horizon-product-conditions.md` | short-horizon governance | accepted | Records the capital-owner-approved product conditions and keeps automation prohibited. | no |
| `STRATEGY_TRIAL_LEDGER.yaml` | research governance | initialized | Stores exact hypotheses, hashes, OOS-open state, and append-only trial rules. | no |
| `PROJECT_EXECUTION_CHECKLIST.md` | governance | active | T0 is complete; T1 is the next authorized task while later work remains dependency-gated. | no |
| `docs/decisions/ADR-0005-post-m1b-no-strategy-eligible-for-m2.md` | post-M1B | accepted | No strategy is eligible for M2. | no |
| `docs/decisions/ADR-0006-freqtrade-first-with-audit-sidecar.md` | architecture | accepted | Freqtrade owns single-leg research; M0 and Python remain independent audit/offline accounting sidecars. | no |

No report in this repository currently approves live trading, paper trading with real API, execution/live, order placement, or API trading permissions.
