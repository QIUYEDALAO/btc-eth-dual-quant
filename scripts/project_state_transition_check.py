#!/usr/bin/env python3
"""Validate exact V2 qualification phases and authorization transitions."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import yaml

ALLOWED = {
    (
        "U-20 negative-coskewness risk-premium design completed; outcome-blind Paper protocol design is the only next task",
        "u20_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-20",
    (
        "U-20 independent outcome-blind hypothesis design authorized",
        "u20_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2",
    ): "U-20",
    (
        "U-19 closed after unique sealed-IS Paper observation failed feasibility; no successor is authorized",
        "u19_failed_feasibility_closed_no_second_run_no_oos_no_trading_no_m2",
    ): "U-19-PAPER-OBSERVATION",
    (
        "U-19 data qualification and complexity preflight passed; one sealed-IS Paper observation is the only next task",
        "u19_qualification_pass_one_paper_observation_only_no_returns_no_oos_no_trading_no_m2",
    ): "U-19-DATA-QUALIFICATION",
    (
        "U-19 Paper protocol exact-head review approved; data qualification, complexity and preflight are the only next task",
        "u19_protocol_review_approve_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-19-PROTOCOL-REVIEW",
    (
        "U-19 volatility-of-volatility Paper protocol frozen; exact-head independent review is the only next task",
        "u19_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-19-PROTOCOL",
    (
        "U-19 volatility-of-volatility risk-premium design completed; outcome-blind Paper protocol design is the only next task",
        "u19_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-19",
    (
        "U-19 independent outcome-blind hypothesis design authorized",
        "u19_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2",
    ): "U-19",
    (
        "U-18 closed after unique sealed-IS Paper observation failed feasibility; no successor is authorized",
        "u18_failed_feasibility_closed_no_second_run_no_oos_no_trading_no_m2",
    ): "U-18-PAPER-OBSERVATION",
    (
        "U-18 data qualification and complexity preflight passed; one sealed-IS Paper observation is the only next task",
        "u18_qualification_pass_one_paper_observation_only_no_returns_no_oos_no_trading_no_m2",
    ): "U-18-DATA-QUALIFICATION",
    (
        "U-18 Paper protocol exact-head review approved; data qualification, complexity and preflight are the only next task",
        "u18_protocol_review_approve_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-18-PROTOCOL-REVIEW",
    (
        "U-18 downside-tail-risk-premium Paper protocol frozen; exact-head independent review is the only next task",
        "u18_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-18-PROTOCOL",
    (
        "U-18 downside-tail-risk-premium design completed; outcome-blind Paper protocol design is the only next task",
        "u18_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-18",
    (
        "U-18 independent outcome-blind hypothesis design authorized",
        "u18_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2",
    ): "U-18",
    (
        "U-17 closed on failed pre-result structural sample ceiling; no successor is authorized",
        "u17_failed_pre_result_sample_ceiling_closed_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-17-DATA-QUALIFICATION",
    (
        "U-17 Paper protocol exact-head review approved; data qualification, complexity and preflight are the only next task",
        "u17_protocol_review_approve_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-17-PROTOCOL-REVIEW",
    (
        "U-17 liquidity-risk-premium Paper protocol frozen; exact-head independent review is the only next task",
        "u17_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-17-PROTOCOL",
    (
        "U-17 liquidity-risk-premium design completed; outcome-blind Paper protocol design is the only next task",
        "u17_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-17",
    (
        "U-17 independent outcome-blind hypothesis design authorized",
        "u17_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2",
    ): "U-17",
    (
        "U-16 closed failed feasibility; no successor is authorized",
        "u16_failed_feasibility_closed_no_returns_no_oos_no_trading_no_m2",
    ): "U-16-PAPER-OBSERVATION",
    (
        "U-16 data qualification and complexity preflight passed; one frozen sealed-IS Paper observation is the only next task",
        "u16_qualification_pass_one_paper_observation_only_no_returns_no_oos_no_trading_no_m2",
    ): "U-16-PAPER-OBSERVATION",
    (
        "U-16 Paper protocol exact-head review approved; data qualification, complexity and preflight are the only next task",
        "u16_protocol_review_approve_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-16-DATA-QUALIFICATION",
    (
        "U-16 correlation-breakdown Paper protocol frozen; exact-head independent review is the only next task",
        "u16_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-16-PROTOCOL-REVIEW",
    (
        "U-16 correlation-breakdown information-persistence design completed; outcome-blind Paper protocol design is the only next task",
        "u16_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-16-PROTOCOL",
    (
        "U-16 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u16_one_independent_hypothesis_design_authorized_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-16",
    (
        "U-15 closed on failed pre-result taker-buy field qualification; no successor is authorized",
        "u15_failed_pre_result_field_qualification_closed_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-15-DATA-QUALIFICATION",
    (
        "U-15 Paper protocol exact-head review approved; field/data qualification, complexity and preflight are the only next task",
        "u15_protocol_review_approve_field_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-15-DATA-QUALIFICATION",
    (
        "U-15 taker-buy absorption Paper protocol frozen; exact-head independent review is the only next task",
        "u15_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-15-PROTOCOL-REVIEW",
    (
        "U-15 taker-buy absorption persistence design completed; outcome-blind Paper protocol design is the only next task",
        "u15_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-15-PROTOCOL",
    (
        "U-15 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u15_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-15",
    (
        "U-14 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u14_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-15-DECISION",
    (
        "U-14 data qualification and complexity preflight passed; one frozen sealed-IS Paper observation is the only next task",
        "u14_data_qualification_complexity_preflight_pass_one_sealed_is_paper_observation_authorized_no_returns_no_oos_no_trading_no_m2",
    ): "U-14-PAPER-OBSERVATION",
    (
        "U-14 Paper protocol exact-head review approved; qualification, complexity benchmark and preflight are the only next task",
        "u14_paper_protocol_review_approve_qualification_complexity_preflight_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-14-DATA-QUALIFICATION",
    (
        "U-14 downside-rejection persistence design completed; outcome-blind Paper protocol design is the only next task",
        "u14_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-14-PROTOCOL",
    (
        "U-14 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u14_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-14",
    (
        "U-13 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u13_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-14-DECISION",
    (
        "U-13 data qualification passed; one frozen sealed-IS Paper observation is the only next task",
        "u13_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-13-PAPER-OBSERVATION",
    (
        "U-13 Paper protocol exact-head review approved; frozen-source qualification and preflight are the only next task",
        "u13_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-13-DATA-QUALIFICATION",
    (
        "Liquid universe V2 correctness hardening pending review",
        "liquid_universe_v1_superseded_v2_hardening_pending_requalification_no_strategy_no_m2",
    ): "U-03D",
    (
        "Liquid universe V2 public requalification pending independent audit",
        "liquid_universe_v2_requalification_pass_pending_independent_audit_no_strategy_no_m2",
    ): "U-03E",
    (
        "Liquid universe V2 public requalification blocked",
        "liquid_universe_v2_requalification_blocked_data_conflict_no_strategy_no_m2",
    ): "U-03E",
    (
        "Liquid universe V2 source conflict adjudication pending review",
        "liquid_universe_v2_source_conflict_adjudication_new_policy_adr_required_no_strategy_no_m2",
    ): "U-03E-ADJ",
    (
        "ADR-0013 independent review pending merge",
        "adr0013_approve_with_required_changes_v2_blocked_no_strategy_no_m2",
    ): "ADR-0013-REVIEW",
    (
        "ADR-0013 conditional adoption pending merge",
        "adr0013_accepted_for_v3_implementation_u03e_requalification_only_no_strategy_no_m2",
    ): "ADR-0013-ADOPT",
    (
        "Liquid universe V3 generic row-conflict implementation pending review",
        "liquid_universe_v3_implementation_pass_fixture_only_public_requalification_not_run_no_strategy_no_m2",
    ): "U-03E-V3-IMPL",
    (
        "Liquid universe V3 public requalification blocked by unregistered official row conflict",
        "liquid_universe_v3_requalification_blocked_unknown_conflict_no_strategy_no_m2",
    ): "U-03E-V3-RUN",
    (
        "Liquid universe V3 public requalification blocked; independent source adjudication is the only authorized next task",
        "liquid_universe_v3_requalification_blocked_no_strategy_no_m2",
    ): "U-03E-V3-ADJ",
    (
        "Liquid universe V3 KLAY official-source conflict adjudication pending review",
        "liquid_universe_v3_klay_source_adjudication_new_policy_adr_required_no_strategy_no_m2",
    ): "U-03E-V3-ADJ",
    (
        "ADR-0014 lifecycle-boundary placeholder policy draft authorized",
        "klay_adjudication_merged_adr0014_draft_authorized_no_strategy_no_m2",
    ): "ADR-0014-DRAFT",
    (
        "ADR-0014 independent policy review completed pending review",
        "adr0014_review_approve_with_required_changes_pr81_draft_unmodified_no_requalification_no_strategy_no_m2",
    ): "ADR-0014-REVIEW",
    (
        "ADR-0014 required-changes Draft revision authorized",
        "adr0014_required_changes_revision_authorized_draft_not_adopted_no_requalification_no_strategy_no_m2",
    ): "ADR-0014-DRAFT",
    (
        "ADR-0014 required-changes independent conformance review completed",
        "adr0014_required_changes_review_approve_pr81_draft_unadopted_no_requalification_no_strategy_no_m2",
    ): "ADR-0014-DRAFT",
    (
        "ADR-0014 conditional adoption pending merge",
        "adr0014_adopted_for_v4_implementation_requalification_only_no_strategy_no_m2",
    ): "ADR-0014-ADOPT",
    (
        "Liquid universe V4 lifecycle availability implementation pending independent review",
        "liquid_universe_v4_implementation_pass_fixture_only_public_requalification_not_run_no_strategy_no_m2",
    ): "U-03E-V4-IMPL",
    (
        "Liquid universe V4 implementation approved and merged; fixed-range public requalification authorized not started",
        "liquid_universe_v4_implementation_merged_requalification_authorized_not_started_no_strategy_no_m2",
    ): "U-03E-V4-RUN",
    (
        "Liquid universe V4 public requalification passed pending review and merge",
        "liquid_universe_v4_requalification_pass_pending_review_u03f_not_authorized_no_strategy_no_m2",
    ): "U-03E-V4-RUN",
    (
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
        "liquid_universe_v4_requalification_pass_u03f_authorized_not_started_no_strategy_no_m2",
    ): "U-03F",
    (
        "U-03F V4 independent audit protocol frozen pending review",
        "u03f_v4_audit_protocol_frozen_before_result_no_strategy_no_m2",
    ): "U-03F",
    (
        "U-03F V4 independent auditor implementation pending independent review",
        "u03f_v4_auditor_fixture_implementation_pending_review_no_full_audit_no_m2",
    ): "U-03F",
    (
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "u03f_v4_auditor_approved_real_audit_authorized_not_started_no_m2",
    ): "U-03F",
    (
        "U-03F V4 independent audit failed pending truthful result review",
        "u03f_v4_independent_audit_failed_pending_review_no_strategy_no_m2",
    ): "U-03F",
    (
        "Liquid universe V4 independent audit failed or blocked",
        "liquid_universe_v4_independent_audit_failed_no_strategy_no_m2",
    ): "U-03F",
    (
        "U-03F V4 repair public requalification blocked",
        "liquid_universe_v4_repair_requalification_blocked_no_new_audit_no_u04_no_m2",
    ): "U-03F-REPAIR-REQUALIFICATION",
    (
        "U-03F V4 repair chain closed blocked",
        "u03f_v4_repair_chain_closed_requalification_blocked_no_new_audit_no_u04_no_m2",
    ): "U-03F-RC",
    (
        "U-03F V4 invalid-interval adjudication protocol frozen pending review",
        "u03f_v4_invalid_interval_protocol_frozen_diagnostic_not_run_no_u04_no_m2",
    ): "U-03F-R2-PROTOCOL",
    (
        "U-03F V4 invalid-interval diagnostic completed pending review",
        "u03f_v4_invalid_interval_diagnostic_new_policy_adr_required_pending_review_no_u04_no_m2",
    ): "U-03F-R2-DIAGNOSTIC",
    (
        "U-03F V4 invalid-interval diagnostic merged; Draft policy ADR is the only authorized next task",
        "u03f_v4_invalid_interval_diagnostic_merged_new_policy_adr_draft_authorized_no_u04_no_m2",
    ): "ADR-0015-DRAFT",
    (
        "ADR-0015 synchronized invalid-interval quarantine policy Draft pending independent review",
        "adr0015_draft_pending_independent_policy_review_unadopted_no_implementation_no_u04_no_m2",
    ): "ADR-0015-DRAFT",
    (
        "ADR-0015 exact-head independent policy review pending PR validation",
        "adr0015_independent_policy_review_approve_pending_ci_unadopted_no_implementation_no_u04_no_m2",
    ): "ADR-0015-REVIEW",
    (
        "ADR-0015 conditional adoption pending PR validation",
        "adr0015_adopted_for_generic_implementation_review_only_pending_ci_no_requalification_no_u04_no_m2",
    ): "ADR-0015-ADOPT",
    (
        "ADR-0015 generic invalid-interval policy implementation pending exact-head review",
        "adr0015_generic_policy_implementation_fixture_pass_pending_exact_head_review_no_requalification_no_u04_no_m2",
    ): "ADR-0015-IMPL",
    (
        "ADR-0015 invalid-interval implementation controlled integration pending PR validation",
        "adr0015_generic_policy_controlled_integration_pending_ci_no_requalification_no_u04_no_m2",
    ): "ADR-0015-IMPL",
    (
        "ADR-0015 fixed-range requalification passed; new independent audit protocol is the only authorized next task",
        "adr0015_requalification_pass_new_audit_protocol_authorized_no_audit_no_u04_no_m2",
    ): "ADR-0015-AUDIT-PROTOCOL",
    (
        "ADR-0015 independent audit protocol frozen; independent auditor implementation is the only authorized next task",
        "adr0015_audit_protocol_frozen_auditor_fixture_implementation_authorized_no_real_audit_no_u04_no_m2",
    ): "ADR-0015-AUDITOR",
    (
        "ADR-0015 independent auditor fixture implementation complete; exact-head review is the only authorized next task",
        "adr0015_independent_auditor_fixture_complete_pending_exact_head_review_no_real_audit_no_u04_no_m2",
    ): "ADR-0015-AUDITOR-REVIEW",
    (
        "ADR-0015 independent auditor exact-head review approved; real independent audit is the only authorized next task",
        "adr0015_independent_auditor_review_approve_real_audit_authorized_no_u04_no_m2",
    ): "ADR-0015-AUDIT",
    (
        "ADR-0015 independent auditor microsecond normalization fixed; replacement exact-head review is the only authorized next task",
        "adr0015_independent_auditor_microsecond_fix_pending_re_review_no_real_audit_no_u04_no_m2",
    ): "ADR-0015-AUDITOR-REVIEW",
    (
        "ADR-0015 independent auditor envelope reconciliation fixed; replacement exact-head review is the only authorized next task",
        "adr0015_independent_auditor_envelope_fix_pending_re_review_no_real_audit_no_u04_no_m2",
    ): "ADR-0015-AUDITOR-REVIEW",
    (
        "ADR-0015 independent audit passed; separate U-04 authorization decision is the only authorized next task",
        "adr0015_independent_audit_pass_pending_separate_u04_decision_no_strategy_no_oos_no_trading_no_m2",
    ): "U-04-DECISION",
    (
        "U-04 cross-sectional hypothesis design authorized; outcome-blind preregistration is the only authorized next task",
        "u04_one_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-04",
    (
        "U-04 cross-sectional residual-reversal design complete; outcome-blind paper protocol design is the only authorized next task",
        "u04_residual_reversal_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-04-PROTOCOL",
    (
        "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "u04_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-04-DATA-QUALIFICATION",
    (
        "U-04 data qualification passed; one frozen sealed-IS paper observation is the only authorized next task",
        "u04_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-04-PAPER-OBSERVATION",
    (
        "U-04 paper feasibility failed; candidate closed without OOS",
        "u04_failed_feasibility_negative_24h_recovery_candidate_closed_no_strategy_no_oos_no_trading_no_m2",
    ): "U-04-CLOSED",
    (
        "U-05 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u05_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-05",
    (
        "U-05 breadth-demand persistence design complete; outcome-blind paper protocol design is the only next task",
        "u05_breadth_demand_persistence_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-05-PROTOCOL",
    (
        "U-05 Paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "u05_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-05-DATA-QUALIFICATION",
    (
        "U-05 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u05_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-05-PAPER-OBSERVATION",
    (
        "U-05 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u05_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-06-DECISION",
    (
        "U-06 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u06_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-06",
    (
        "U-06 volume-share absorption design complete; outcome-blind Paper protocol design is the only next task",
        "u06_volume_share_absorption_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-06-PROTOCOL",
    (
        "U-06 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u06_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-06-DATA-QUALIFICATION",
    (
        "U-06 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u06_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-06-PAPER-OBSERVATION",
    (
        "U-06 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u06_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-07-DECISION",
    (
        "U-07 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u07_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-07",
    (
        "U-07 market-stress relative-strength design complete; outcome-blind Paper protocol design is the only next task",
        "u07_market_stress_relative_strength_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-07-PROTOCOL",
    (
        "U-07 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u07_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-07-DATA-QUALIFICATION",
    (
        "U-07 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u07_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-07-PAPER-OBSERVATION",
    (
        "U-07 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u07_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-08-DECISION",
    (
        "U-08 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u08_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-08",
    (
        "U-08 liquidity-rank entry demand-persistence design complete; outcome-blind Paper protocol design is the only next task",
        "u08_liquidity_rank_entry_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-08-PROTOCOL",
    (
        "U-08 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u08_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-08-DATA-QUALIFICATION",
    (
        "U-08 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u08_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-08-PAPER-OBSERVATION",
    (
        "U-08 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u08_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ): "U-09-DECISION",
    (
        "U-09 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u09_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-09",
    (
        "U-09 idiosyncratic-volatility quality-persistence design complete; outcome-blind Paper protocol design is the only next task",
        "u09_idiosyncratic_volatility_quality_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-09-PROTOCOL",
    (
        "U-09 Paper protocol frozen; exact-head independent review is the only authorized next task",
        "u09_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-09-PROTOCOL-REVIEW",
    (
        "U-09 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u09_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-09-DATA-QUALIFICATION",
    (
        "U-09 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u09_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-09-PAPER-OBSERVATION",
    (
        "U-09 closed before observation on deterministic sample ceiling; only a separate independent-candidate authorization decision may follow",
        "u09_failed_pre_observation_sample_ceiling_closed_no_result_no_strategy_no_oos_no_trading_no_m2",
    ): "U-10-DECISION",
    (
        "U-10 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u10_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ): "U-10",
    (
        "U-10 volume-confirmed relative-trend design complete; outcome-blind Paper protocol design is the only next task",
        "u10_volume_confirmed_relative_trend_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ): "U-10-PROTOCOL",
    (
        "U-10 Paper protocol frozen; exact-head independent review is the only authorized next task",
        "u10_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-10-PROTOCOL-REVIEW",
    (
        "U-10 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u10_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-10-DATA-QUALIFICATION",
    (
        "U-10 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u10_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-10-PAPER-OBSERVATION",
    (
        "U-10 Paper observation failed feasibility; separate U-11 independent-candidate authorization decision is the only next task",
        "u10_paper_failed_feasibility_candidate_closed_u11_decision_only_no_strategy_no_oos_no_trading_no_m2",
    ): "U-11-DECISION",
    (
        "U-11 independent design authorized; one outcome-blind hypothesis design is the only next task",
        "u11_design_authorized_one_hypothesis_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-11",
    (
        "U-11 asymmetric market-capture quality design completed; outcome-blind Paper protocol design is the only next task",
        "u11_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-11-PROTOCOL",
    (
        "U-11 Paper protocol frozen before results; exact-head independent review is the only next task",
        "u11_paper_protocol_frozen_pending_exact_head_review_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-11-PROTOCOL-REVIEW",
    (
        "U-11 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u11_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-11-DATA-QUALIFICATION",
    (
        "U-11 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u11_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-11-PAPER-OBSERVATION",
    (
        "U-11 Paper observation invalid due execution defect; separate U-12 independent-candidate authorization decision is the only next task",
        "u11_failed_execution_invalid_observation_candidate_closed_u12_decision_only_no_strategy_no_oos_no_trading_no_m2",
    ): "U-12-DECISION",
    (
        "U-12 independent design authorized; one outcome-blind hypothesis design is the only next task",
        "u12_design_authorized_one_hypothesis_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-12",
    (
        "U-12 recurring calendar-flow seasonality design completed; outcome-blind Paper protocol design is the only next task",
        "u12_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-12-PROTOCOL",
    (
        "U-12 Paper protocol exact-head review approved; data qualification and same-reader preflight are the only next task",
        "u12_paper_protocol_review_approve_data_qualification_preflight_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-12-DATA-QUALIFICATION",
    (
        "U-12 data qualification and same-reader preflight passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u12_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ): "U-12-PAPER-OBSERVATION",
    (
        "U-12 Paper observation failed feasibility; separate U-13 independent-candidate authorization decision is the only next task",
        "u12_failed_feasibility_candidate_closed_u13_decision_only_no_strategy_no_oos_no_trading_no_m2",
    ): "U-13-DECISION",
    (
        "U-13 independent design authorized; one outcome-blind hypothesis design is the only next task",
        "u13_design_authorized_one_hypothesis_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-13",
    (
        "U-13 common-shock lagged-diffusion design completed; outcome-blind Paper protocol design is the only next task",
        "u13_hypothesis_design_pass_paper_protocol_only_no_data_no_events_no_returns_no_oos_no_trading_no_m2",
    ): "U-13-PROTOCOL",
    (
        "Liquid universe V2 qualification independently audited; hypothesis preregistration requires separate task",
        "liquid_universe_v2_qualification_audited_pass_no_hypothesis_no_oos_no_m2",
    ): "U-03F",
    (
        "Liquid universe V2 independent audit blocked",
        "liquid_universe_v2_independent_audit_blocked_no_strategy_no_m2",
    ): "U-03F",
}

BLOCKED_REQUALIFICATION_PAIR = (
    "Liquid universe V2 public requalification blocked",
    "liquid_universe_v2_requalification_blocked_data_conflict_no_strategy_no_m2",
)

FAILED_U03F_CLOSEOUT_PAIR = (
    "Liquid universe V4 independent audit failed or blocked",
    "liquid_universe_v4_independent_audit_failed_no_strategy_no_m2",
)

REPAIR_REQUALIFICATION_BLOCKED_PAIR = (
    "U-03F V4 repair public requalification blocked",
    "liquid_universe_v4_repair_requalification_blocked_no_new_audit_no_u04_no_m2",
)

REPAIR_CHAIN_CLOSED_PAIR = (
    "U-03F V4 repair chain closed blocked",
    "u03f_v4_repair_chain_closed_requalification_blocked_no_new_audit_no_u04_no_m2",
)

INVALID_INTERVAL_PROTOCOL_PAIR = (
    "U-03F V4 invalid-interval adjudication protocol frozen pending review",
    "u03f_v4_invalid_interval_protocol_frozen_diagnostic_not_run_no_u04_no_m2",
)

INVALID_INTERVAL_DIAGNOSTIC_PAIR = (
    "U-03F V4 invalid-interval diagnostic completed pending review",
    "u03f_v4_invalid_interval_diagnostic_new_policy_adr_required_pending_review_no_u04_no_m2",
)

INVALID_INTERVAL_DIAGNOSTIC_MERGED_PAIR = (
    "U-03F V4 invalid-interval diagnostic merged; Draft policy ADR is the only authorized next task",
    "u03f_v4_invalid_interval_diagnostic_merged_new_policy_adr_draft_authorized_no_u04_no_m2",
)

ADR0015_DRAFT_PAIR = (
    "ADR-0015 synchronized invalid-interval quarantine policy Draft pending independent review",
    "adr0015_draft_pending_independent_policy_review_unadopted_no_implementation_no_u04_no_m2",
)

ADR0015_REVIEW_PAIR = (
    "ADR-0015 exact-head independent policy review pending PR validation",
    "adr0015_independent_policy_review_approve_pending_ci_unadopted_no_implementation_no_u04_no_m2",
)

ADR0015_ADOPTION_PAIR = (
    "ADR-0015 conditional adoption pending PR validation",
    "adr0015_adopted_for_generic_implementation_review_only_pending_ci_no_requalification_no_u04_no_m2",
)

ADR0015_IMPLEMENTATION_PAIR = (
    "ADR-0015 generic invalid-interval policy implementation pending exact-head review",
    "adr0015_generic_policy_implementation_fixture_pass_pending_exact_head_review_no_requalification_no_u04_no_m2",
)

ADR0015_CONTROLLED_INTEGRATION_PAIR = (
    "ADR-0015 invalid-interval implementation controlled integration pending PR validation",
    "adr0015_generic_policy_controlled_integration_pending_ci_no_requalification_no_u04_no_m2",
)

ADR0015_REQUALIFICATION_PASS_PAIR = (
    "ADR-0015 fixed-range requalification passed; new independent audit protocol is the only authorized next task",
    "adr0015_requalification_pass_new_audit_protocol_authorized_no_audit_no_u04_no_m2",
)

ADR0015_AUDIT_PROTOCOL_PAIR = (
    "ADR-0015 independent audit protocol frozen; independent auditor implementation is the only authorized next task",
    "adr0015_audit_protocol_frozen_auditor_fixture_implementation_authorized_no_real_audit_no_u04_no_m2",
)

ADR0015_AUDITOR_REVIEW_PAIR = (
    "U-04 cross-sectional hypothesis design authorized; outcome-blind preregistration is the only authorized next task",
    "u04_one_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

ADR0015_REVIEWED_IMPLEMENTATION_HEAD = "67e7d29eaed63a3edb903dd618184bc9f02c5748"
ADR0015_IMPLEMENTATION_REVIEW_MERGE = "a02d4dfbe752bb7e26e8a7b41971a9f089ddc57f"
ADR0015_EXACT_IMPLEMENTATION_FILES = (
    "config/liquid_spot_invalid_interval_policy_v1.json",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md",
    "scripts/adr0015_invalid_interval_implementation_check.py",
    "scripts/adr0015_invalid_interval_implementation_validate.sh",
    "scripts/liquid_universe_v4_public_run.py",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py",
    "tests/test_adr0015_invalid_interval_policy.py",
)

CLOSED_TASK_PAIRS = {
    FAILED_U03F_CLOSEOUT_PAIR,
    REPAIR_CHAIN_CLOSED_PAIR,
    (
        "U-04 paper feasibility failed; candidate closed without OOS",
        "u04_failed_feasibility_negative_24h_recovery_candidate_closed_no_strategy_no_oos_no_trading_no_m2",
    ),
}

AUDIT_BLOCKED_PAIRS = {
    FAILED_U03F_CLOSEOUT_PAIR,
    REPAIR_REQUALIFICATION_BLOCKED_PAIR,
    REPAIR_CHAIN_CLOSED_PAIR,
    INVALID_INTERVAL_PROTOCOL_PAIR,
    INVALID_INTERVAL_DIAGNOSTIC_PAIR,
    INVALID_INTERVAL_DIAGNOSTIC_MERGED_PAIR,
    ADR0015_DRAFT_PAIR,
    ADR0015_REVIEW_PAIR,
    ADR0015_ADOPTION_PAIR,
    ADR0015_IMPLEMENTATION_PAIR,
    ADR0015_CONTROLLED_INTEGRATION_PAIR,
    ADR0015_REQUALIFICATION_PASS_PAIR,
    ADR0015_AUDIT_PROTOCOL_PAIR,
    ADR0015_AUDITOR_REVIEW_PAIR,
    (
        "U-04 cross-sectional residual-reversal design complete; outcome-blind paper protocol design is the only authorized next task",
        "u04_residual_reversal_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "u04_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-04 data qualification passed; one frozen sealed-IS paper observation is the only authorized next task",
        "u04_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-04 paper feasibility failed; candidate closed without OOS",
        "u04_failed_feasibility_negative_24h_recovery_candidate_closed_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-05 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u05_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-05 breadth-demand persistence design complete; outcome-blind paper protocol design is the only next task",
        "u05_breadth_demand_persistence_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-05 Paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "u05_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-05 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u05_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-05 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u05_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-06 independent design authorized; outcome-blind hypothesis design is the only next task",
        "u06_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-06 volume-share absorption design complete; outcome-blind Paper protocol design is the only next task",
        "u06_volume_share_absorption_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-06 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "u06_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
    ),
    (
        "U-06 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "u06_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
    ),
    (
        "U-06 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "u06_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
    ),
}

EXPECTED_AUTH = {
    "hypothesis_preregistration": False,
    "strategy_code": False,
    "event_scan": False,
    "returns": False,
    "backtesting": False,
    "oos_opened": False,
    "m2": False,
    "api_or_trading": False,
}

U04_DESIGN_PAIR = (
    "U-04 cross-sectional hypothesis design authorized; outcome-blind preregistration is the only authorized next task",
    "u04_one_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U04_PROTOCOL_PAIR = (
    "U-04 cross-sectional residual-reversal design complete; outcome-blind paper protocol design is the only authorized next task",
    "u04_residual_reversal_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
)

U04_PROTOCOL_REVIEW_APPROVED_PAIR = (
    "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
    "u04_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
)

U04_DATA_QUALIFICATION_PASS_PAIR = (
    "U-04 data qualification passed; one frozen sealed-IS paper observation is the only authorized next task",
    "u04_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
)

U04_FAILED_FEASIBILITY_PAIR = (
    "U-04 paper feasibility failed; candidate closed without OOS",
    "u04_failed_feasibility_negative_24h_recovery_candidate_closed_no_strategy_no_oos_no_trading_no_m2",
)

U05_DESIGN_PAIR = (
    "U-05 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u05_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U05_PROTOCOL_PAIR = (
    "U-05 breadth-demand persistence design complete; outcome-blind paper protocol design is the only next task",
    "u05_breadth_demand_persistence_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
)

U05_PROTOCOL_REVIEW_APPROVED_PAIR = (
    "U-05 Paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
    "u05_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
)

U05_DATA_QUALIFICATION_PASS_PAIR = (
    "U-05 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
    "u05_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
)

U05_CLOSED_PAIR = (
    "U-05 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
    "u05_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
)

U06_DESIGN_PAIR = (
    "U-06 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u06_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U07_DESIGN_PAIR = (
    "U-07 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u07_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U07_PROTOCOL_PAIR = (
    "U-07 market-stress relative-strength design complete; outcome-blind Paper protocol design is the only next task",
    "u07_market_stress_relative_strength_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
)

U07_PROTOCOL_REVIEW_APPROVED_PAIR = (
    "U-07 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
    "u07_paper_protocol_review_approve_data_qualification_only_no_events_no_returns_no_oos_no_trading_no_m2",
)

U07_DATA_QUALIFICATION_PASS_PAIR = (
    "U-07 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
    "u07_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
)

U07_FAILED_FEASIBILITY_PAIR = (
    "U-07 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
    "u07_failed_feasibility_closed_no_rerun_no_strategy_no_oos_no_trading_no_m2",
)

U08_DESIGN_PAIR = (
    "U-08 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u08_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U09_DESIGN_PAIR = (
    "U-09 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u09_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U10_DESIGN_PAIR = (
    "U-10 independent design authorized; outcome-blind hypothesis design is the only next task",
    "u10_one_independent_hypothesis_design_authorized_no_event_scan_no_strategy_no_oos_no_trading_no_m2",
)

U08_PROTOCOL_DESIGN_PAIR = (
    "U-08 liquidity-rank entry demand-persistence design complete; outcome-blind Paper protocol design is the only next task",
    "u08_liquidity_rank_entry_design_complete_protocol_design_only_no_event_scan_no_returns_no_oos_no_trading_no_m2",
)

U06_DATA_QUALIFICATION_PASS_PAIR = (
    "U-06 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
    "u06_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2",
)


def validate(state: dict) -> list[str]:
    failures = []
    pair = (state.get("current_phase"), state.get("current_status"))
    expected_task = ALLOWED.get(pair)
    if expected_task is None:
        failures.append(f"unsupported V2 phase/status pair: {pair}")
    expected_auth = dict(EXPECTED_AUTH)
    if pair in {U04_DESIGN_PAIR, U05_DESIGN_PAIR, U06_DESIGN_PAIR, U07_DESIGN_PAIR, U08_DESIGN_PAIR, U09_DESIGN_PAIR, U10_DESIGN_PAIR, ("U-11 independent design authorized; one outcome-blind hypothesis design is the only next task", "u11_design_authorized_one_hypothesis_only_no_events_no_returns_no_oos_no_trading_no_m2"), ("U-12 independent design authorized; one outcome-blind hypothesis design is the only next task", "u12_design_authorized_one_hypothesis_only_no_events_no_returns_no_oos_no_trading_no_m2"), ("U-17 independent outcome-blind hypothesis design authorized", "u17_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2"), ("U-18 independent outcome-blind hypothesis design authorized", "u18_design_only_authorized_no_data_no_results_no_oos_no_trading_no_m2")}:
        expected_auth["hypothesis_preregistration"] = True
    if pair in {U04_DATA_QUALIFICATION_PASS_PAIR, U05_DATA_QUALIFICATION_PASS_PAIR, U06_DATA_QUALIFICATION_PASS_PAIR, U07_DATA_QUALIFICATION_PASS_PAIR} or pair in {("U-08 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task", "u08_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2"), ("U-09 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task", "u09_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2"), ("U-10 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task", "u10_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2"), ("U-11 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task", "u11_data_qualification_pass_one_sealed_is_paper_observation_authorized_no_strategy_no_oos_no_trading_no_m2")}:
        expected_auth["event_scan"] = True
    if state.get("research_authorizations") != expected_auth:
        failures.append("research authorization matrix changed")
    if pair in {ADR0015_CONTROLLED_INTEGRATION_PAIR, ADR0015_REQUALIFICATION_PASS_PAIR, ADR0015_AUDIT_PROTOCOL_PAIR, ADR0015_AUDITOR_REVIEW_PAIR}:
        for commit, label in (
            (ADR0015_REVIEWED_IMPLEMENTATION_HEAD, "reviewed implementation head"),
            (ADR0015_IMPLEMENTATION_REVIEW_MERGE, "implementation review merge"),
        ):
            available = subprocess.run(
                ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode == 0
            ancestor = available and subprocess.run(
                ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode == 0
            if not ancestor:
                failures.append(f"{label} is unavailable or not an ancestor of HEAD")
        parents = subprocess.check_output(
            ["git", "rev-list", "--parents", "HEAD"], cwd=ROOT, text=True
        ).splitlines()
        if not any(
            ADR0015_REVIEWED_IMPLEMENTATION_HEAD in line.split()[1:]
            for line in parents
        ):
            failures.append("no integration ancestor records the reviewed head as a parent")
        for path in ADR0015_EXACT_IMPLEMENTATION_FILES:
            reviewed = subprocess.run(
                ["git", "rev-parse", f"{ADR0015_REVIEWED_IMPLEMENTATION_HEAD}:{path}"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            current = subprocess.run(
                ["git", "rev-parse", f"HEAD:{path}"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            if (
                reviewed.returncode
                or current.returncode
                or reviewed.stdout.strip() != current.stdout.strip()
            ):
                failures.append(f"reviewed implementation blob drifted: {path}")
    open_work = state.get("open_work", [])
    active = [
        item
        for item in open_work
        if item.get("id") in {"U-03D", "U-03E", "U-03E-ADJ", "ADR-0013-REVIEW", "ADR-0013-ADOPT", "U-03E-V3-IMPL", "U-03E-V3-RUN", "U-03E-V3-ADJ", "ADR-0014-DRAFT", "ADR-0014-REVIEW", "ADR-0014-ADOPT", "U-03E-V4-IMPL", "U-03E-V4-RUN", "U-03F", "U-03F-REPAIR-REQUALIFICATION", "U-03F-R2-PROTOCOL", "U-03F-R2-DIAGNOSTIC", "ADR-0015-DRAFT", "ADR-0015-REVIEW", "ADR-0015-ADOPT", "ADR-0015-IMPL", "ADR-0015-AUDIT-PROTOCOL", "ADR-0015-AUDITOR", "ADR-0015-AUDITOR-REVIEW", "ADR-0015-AUDIT", "U-04-DECISION", "U-04", "U-04-PROTOCOL", "U-04-DATA-QUALIFICATION", "U-04-PAPER-OBSERVATION", "U-05", "U-05-PROTOCOL", "U-05-DATA-QUALIFICATION", "U-05-PAPER-OBSERVATION", "U-06-DECISION", "U-06", "U-06-PROTOCOL", "U-06-DATA-QUALIFICATION", "U-06-PAPER-OBSERVATION", "U-07-DECISION", "U-07", "U-07-PROTOCOL", "U-07-DATA-QUALIFICATION", "U-07-PAPER-OBSERVATION", "U-08-DECISION", "U-08", "U-08-PROTOCOL", "U-08-DATA-QUALIFICATION", "U-08-PAPER-OBSERVATION", "U-09-DECISION", "U-09", "U-09-PROTOCOL", "U-09-PROTOCOL-REVIEW", "U-09-DATA-QUALIFICATION", "U-09-PAPER-OBSERVATION", "U-10-DECISION", "U-10", "U-10-PROTOCOL", "U-10-PROTOCOL-REVIEW", "U-10-DATA-QUALIFICATION", "U-10-PAPER-OBSERVATION", "U-11-DECISION", "U-11", "U-11-PROTOCOL", "U-11-PROTOCOL-REVIEW", "U-11-DATA-QUALIFICATION", "U-11-PAPER-OBSERVATION", "U-12-DECISION", "U-12", "U-12-PROTOCOL", "U-12-DATA-QUALIFICATION", "U-12-PAPER-OBSERVATION", "U-13-DECISION", "U-13", "U-13-PROTOCOL", "U-13-DATA-QUALIFICATION", "U-13-PAPER-OBSERVATION", "U-14-DECISION", "U-14", "U-14-PROTOCOL"}
    ]
    active.extend(item for item in open_work if item.get("id") in {"U-14-DATA-QUALIFICATION", "U-14-PAPER-OBSERVATION", "U-15-DECISION", "U-15", "U-15-PROTOCOL", "U-15-PROTOCOL-REVIEW", "U-15-DATA-QUALIFICATION", "U-16", "U-16-PROTOCOL", "U-16-PROTOCOL-REVIEW", "U-16-DATA-QUALIFICATION", "U-16-PAPER-OBSERVATION", "U-17", "U-17-PROTOCOL", "U-17-PROTOCOL-REVIEW", "U-17-DATA-QUALIFICATION", "U-18", "U-18-PROTOCOL", "U-18-PROTOCOL-REVIEW", "U-18-DATA-QUALIFICATION", "U-18-PAPER-OBSERVATION", "U-19", "U-19-PROTOCOL", "U-19-PROTOCOL-REVIEW", "U-19-DATA-QUALIFICATION", "U-19-PAPER-OBSERVATION", "U-20"})
    if pair == BLOCKED_REQUALIFICATION_PAIR:
        completed = state.get("completed_milestones", [])
        merged_prs = {item.get("number") for item in state.get("latest_merged_prs", [])}
        merged_blocked = any(
            item.get("phase") == "Liquid universe V2 public requalification"
            and item.get("status") == "blocked_data_conflict"
            and isinstance(item.get("merged_pr"), int)
            and item.get("merged_pr") in merged_prs
            for item in completed
        )
        if not merged_blocked:
            failures.append("merged blocked U-03E milestone missing")
        if any(item.get("id") == "U-03E" for item in active):
            failures.append("merged blocked U-03E must not remain in open_work")
    elif (
        expected_task
        and pair not in CLOSED_TASK_PAIRS
        and not any(item.get("id") == expected_task for item in active)
    ):
        failures.append(f"current V2 task missing from open_work: {expected_task}")
    if any(
        item.get("phase") == "ADR-0014 required-changes independent conformance review"
        for item in state.get("completed_milestones", [])
    ) or pair[0] in {
        "ADR-0014 required-changes independent conformance review completed",
        "ADR-0014 conditional adoption pending merge",
        "Liquid universe V4 lifecycle availability implementation pending independent review",
        "Liquid universe V4 implementation approved and merged; fixed-range public requalification authorized not started",
        "Liquid universe V4 public requalification passed pending review and merge",
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
        "U-03F V4 independent audit protocol frozen pending review",
        "U-03F V4 independent auditor implementation pending independent review",
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
        "U-03F V4 independent audit protocol frozen pending review",
        "U-03F V4 independent auditor implementation pending independent review",
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
        "Liquid universe V4 independent audit failed or blocked",
        "U-03F V4 repair public requalification blocked",
        "U-03F V4 repair chain closed blocked",
        "U-03F V4 invalid-interval adjudication protocol frozen pending review",
        "U-03F V4 invalid-interval diagnostic completed pending review",
        "U-03F V4 invalid-interval diagnostic merged; Draft policy ADR is the only authorized next task",
        "ADR-0015 synchronized invalid-interval quarantine policy Draft pending independent review",
        "ADR-0015 exact-head independent policy review pending PR validation",
        "ADR-0015 conditional adoption pending PR validation",
        "ADR-0015 generic invalid-interval policy implementation pending exact-head review",
        "ADR-0015 invalid-interval implementation controlled integration pending PR validation",
        "ADR-0015 fixed-range requalification passed; new independent audit protocol is the only authorized next task",
        "ADR-0015 independent audit protocol frozen; independent auditor implementation is the only authorized next task",
        "ADR-0015 independent auditor fixture implementation complete; exact-head review is the only authorized next task",
        "ADR-0015 independent auditor exact-head review approved; real independent audit is the only authorized next task",
        "ADR-0015 independent auditor microsecond normalization fixed; replacement exact-head review is the only authorized next task",
        "ADR-0015 independent auditor envelope reconciliation fixed; replacement exact-head review is the only authorized next task",
        "ADR-0015 independent audit passed; separate U-04 authorization decision is the only authorized next task",
        "U-04 cross-sectional hypothesis design authorized; outcome-blind preregistration is the only authorized next task",
        "U-04 cross-sectional residual-reversal design complete; outcome-blind paper protocol design is the only authorized next task",
        "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "U-04 data qualification passed; one frozen sealed-IS paper observation is the only authorized next task",
        "U-04 paper feasibility failed; candidate closed without OOS",
        "U-05 independent design authorized; outcome-blind hypothesis design is the only next task",
        "U-05 breadth-demand persistence design complete; outcome-blind paper protocol design is the only next task",
        "U-05 Paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "U-05 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "U-05 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "U-06 independent design authorized; outcome-blind hypothesis design is the only next task",
        "U-06 volume-share absorption design complete; outcome-blind Paper protocol design is the only next task",
        "U-06 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "U-06 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "U-06 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "U-07 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
    }:
        milestones = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "ADR-0014 required-changes independent conformance review"
        ]
        expected_milestone = {
            "reviewed_pr": 81,
            "reviewed_head_sha": "31c967c785128671769eb713baed265da8ae0f2a",
            "reviewed_base_sha": "ab45ba4f12badab8a00faa0181b48c948643e223",
            "verdict": "approve",
            "critical_findings": 0,
            "high_findings": 0,
            "evidence_content_hash": "d2b0dfa7fdd9c8cc5bef2c716600f6e79ec6272651fa067dc23a3d0915271bc7",
        }
        if len(milestones) != 1 or any(
            milestones[0].get(key) != value for key, value in expected_milestone.items()
        ):
            failures.append("ADR-0014 conformance milestone binding changed")
    historical_failed_u03f_audit = any(
        item.get("phase") == "U-03F V4 independent audit" and item.get("status") == "failed_audit"
        for item in state.get("completed_milestones", [])
    )
    if historical_failed_u03f_audit or pair[0] in {
        "Liquid universe V4 lifecycle availability implementation pending independent review",
        "Liquid universe V4 implementation approved and merged; fixed-range public requalification authorized not started",
        "Liquid universe V4 public requalification passed pending review and merge",
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
        "U-03F V4 independent audit protocol frozen pending review",
        "U-03F V4 independent auditor implementation pending independent review",
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
    }:
        adoption = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "ADR-0014 conditional adoption"
        ]
        expected_adoption = {
            "merged_pr": 85,
            "merge_commit": "0f5f76f86973316ac66b8e3f9d6e65419b310ec9",
            "evidence_content_hash": "9c3572bee81edbf1efcc3ca523c9fdd10003adc5f3c3ac5a7211ad673405394a",
        }
        if len(adoption) != 1 or any(
            adoption[0].get(key) != value for key, value in expected_adoption.items()
        ):
            failures.append("ADR-0014 adoption milestone binding changed")
    if pair[0] in {
        "Liquid universe V4 implementation approved and merged; fixed-range public requalification authorized not started",
        "Liquid universe V4 public requalification passed pending review and merge",
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
    }:
        implementation = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "Liquid universe V4 lifecycle availability implementation"
        ]
        implementation_review = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "Liquid universe V4 implementation independent review"
        ]
        expected_implementation = {
            "merged_pr": 86,
            "merge_commit": "fccc9972502732319d38eb36775d007396df25db",
            "reviewed_head_sha": "2a745586bff5112d69af45c9a0dd8585f2adab50",
        }
        expected_review = {
            "merged_pr": 87,
            "merge_commit": "f250975e3f95cafc3066f0344727f575922dbe9c",
            "reviewed_pr": 86,
            "reviewed_head_sha": "2a745586bff5112d69af45c9a0dd8585f2adab50",
            "verdict": "approve",
            "critical_findings": 0,
            "high_findings": 0,
        }
        if len(implementation) != 1 or any(
            implementation[0].get(key) != value
            for key, value in expected_implementation.items()
        ):
            failures.append("V4 implementation milestone binding changed")
        if len(implementation_review) != 1 or any(
            implementation_review[0].get(key) != value
            for key, value in expected_review.items()
        ):
            failures.append("V4 implementation review milestone binding changed")
    merged = {item.get("number") for item in state.get("latest_merged_prs", [])}
    for item in open_work:
        if isinstance(item.get("pr"), int) and item["pr"] in merged:
            failures.append(f"open_work references merged PR #{item['pr']}")
        if item.get("id") == "ADR-0013-ADOPT":
            if item.get("head_sha") != "runtime_current_pr_head":
                failures.append("ADR-0013 head_sha must be runtime current PR metadata")
            if item.get("reviewed_head_sha") != "8dc9ee034fdd172147485f7718117f8a76713cdf":
                failures.append("ADR-0013 reviewed_head_sha changed")
            if item.get("evidence_commit") != "4a95a28142d13aa2f03f271baf660ae95ba67e78":
                failures.append("ADR-0013 evidence_commit changed")
        if item.get("id") == "ADR-0014-REVIEW":
            if item.get("head_sha") != "runtime_current_pr_head":
                failures.append("ADR-0014 review head_sha must be runtime current PR metadata")
            if item.get("reviewed_pr") != 81:
                failures.append("ADR-0014 reviewed PR changed")
            if item.get("reviewed_head_sha") != "cd4a1d8fb53870cdf8a3a683a4942a2c81b58f44":
                failures.append("ADR-0014 reviewed_head_sha changed")
            if item.get("verdict") != "approve_with_required_changes":
                failures.append("ADR-0014 review verdict changed")
        if item.get("id") == "ADR-0014-DRAFT" and expected_task == "ADR-0014-DRAFT":
            if pair[0] == "ADR-0014 required-changes independent conformance review completed":
                if item.get("status") != "independent_conformance_review_approve_draft_unadopted":
                    failures.append("ADR-0014 conformance review status changed")
                if item.get("head_sha") != "31c967c785128671769eb713baed265da8ae0f2a":
                    failures.append("ADR-0014 conformance reviewed head changed")
                if item.get("conformance_review_verdict") != "approve":
                    failures.append("ADR-0014 conformance verdict changed")
                if item.get("remaining_critical") != 0 or item.get("remaining_high") != 0:
                    failures.append("ADR-0014 conformance severity changed")
            elif item.get("status") != "draft_revision_authorized_not_started":
                failures.append("ADR-0014 Draft revision status changed")
            if item.get("prior_review_pr") != 82:
                failures.append("ADR-0014 prior review PR changed")
            if item.get("prior_review_merge_sha") != "d507684564fc31812c8e7d4adb06d7ab61c7dab7":
                failures.append("ADR-0014 prior review merge changed")
            if item.get("adopted") or item.get("implemented") or item.get("registry_change") or item.get("requalification"):
                failures.append("ADR-0014 Draft gained authority")
        if item.get("id") == "ADR-0014-ADOPT":
            if item.get("head_sha") != "runtime_current_pr_head":
                failures.append("ADR-0014 adoption head_sha must be runtime current PR metadata")
            if item.get("reviewed_pr") != 81 or item.get("reviewed_head_sha") != "31c967c785128671769eb713baed265da8ae0f2a":
                failures.append("ADR-0014 adoption reviewed target changed")
            if item.get("conformance_review_pr") != 84 or item.get("conformance_review_verdict") != "approve":
                failures.append("ADR-0014 adoption conformance evidence changed")
            if item.get("adoption_content_hash") != "9c3572bee81edbf1efcc3ca523c9fdd10003adc5f3c3ac5a7211ad673405394a":
                failures.append("ADR-0014 adoption manifest hash changed")
            if item.get("adopted") is not True or item.get("implemented") or item.get("registry_change") or item.get("requalification"):
                failures.append("ADR-0014 adoption authority widened beyond Stage A")
        if item.get("id") == "U-03F-R2-PROTOCOL":
            if item.get("status") != "protocol_frozen_pending_review":
                failures.append("invalid-interval protocol status changed")
            if item.get("pr") != 102:
                failures.append("invalid-interval protocol PR binding changed")
            if item.get("protocol_content_hash") != "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190":
                failures.append("invalid-interval protocol hash changed")
            if item.get("diagnostic_executed") is not False:
                failures.append("invalid-interval diagnostic ran before protocol merge")
            if item.get("production_pipeline_modified") is not False:
                failures.append("production pipeline changed in protocol task")
        if item.get("id") == "U-03F-R2-DIAGNOSTIC":
            if item.get("status") != "completed_new_policy_adr_required_pending_review":
                failures.append("invalid-interval diagnostic status changed")
            if item.get("diagnostic_content_hash") != "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677":
                failures.append("invalid-interval diagnostic content hash changed")
            if item.get("run_manifest_hash") != "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33":
                failures.append("invalid-interval diagnostic run hash changed")
            if item.get("decision") != "new_policy_adr_required":
                failures.append("invalid-interval diagnostic decision changed")
            if item.get("invalid_physical_rows") != 119 or item.get("synchronized_windows") != 8:
                failures.append("invalid-interval diagnostic counts changed")
            if item.get("production_pipeline_modified") is not False:
                failures.append("production pipeline changed in diagnostic task")
        if item.get("id") == "ADR-0015-DRAFT":
            expected_status = (
                "draft_pending_independent_review"
                if pair == ADR0015_DRAFT_PAIR
                else "authorized_not_started"
            )
            if item.get("status") != expected_status:
                failures.append("ADR-0015 Draft status changed")
            if item.get("diagnostic_content_hash") != "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677":
                failures.append("ADR-0015 diagnostic binding changed")
            if item.get("run_manifest_hash") != "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33":
                failures.append("ADR-0015 run binding changed")
            if item.get("draft_only") is not True or item.get("independent_review_required_before_adoption") is not True:
                failures.append("ADR-0015 Draft/review Gate changed")
            if pair == ADR0015_DRAFT_PAIR:
                if item.get("branch") != "codex/adr-0015-invalid-interval-policy-draft":
                    failures.append("ADR-0015 Draft branch changed")
                if item.get("head_sha") != "runtime_current_pr_head":
                    failures.append("ADR-0015 Draft head must be runtime current PR metadata")
                if item.get("policy_model_content_hash") != "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c":
                    failures.append("ADR-0015 policy model hash changed")
                if item.get("exact_head_review_required") is not True:
                    failures.append("ADR-0015 exact-head review Gate changed")
                if item.get("maximum_critical_findings") != 0 or item.get("maximum_high_findings") != 0:
                    failures.append("ADR-0015 review severity Gate lowered")
            if item.get("adopted") or item.get("implementation_authorized") or item.get("production_pipeline_modified"):
                failures.append("ADR-0015 gained authority before Draft review")
        if item.get("id") == "ADR-0015-REVIEW":
            expected_review = {
                "status": "approve_pending_pr_validation",
                "branch": "codex/adr-0015-independent-policy-review",
                "pr": "runtime_current_pr",
                "head_sha": "runtime_current_pr_head",
                "reviewed_pr": 105,
                "reviewed_base_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
                "reviewed_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
                "draft_merge_sha": "e1783090dfb0a4560475b97a021ef1e77aebc399",
                "policy_model_content_hash": "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c",
                "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
                "verdict": "approve",
                "critical_findings": 0,
                "high_findings": 0,
                "adopted": False,
                "implementation_authorized": False,
                "production_pipeline_modified": False,
            }
            if any(item.get(key) != value for key, value in expected_review.items()):
                failures.append("ADR-0015 independent review binding changed")
        if item.get("id") == "ADR-0015-ADOPT":
            expected_adoption = {
                "status": "adoption_pending_pr_validation",
                "branch": "codex/adr-0015-conditional-adoption",
                "pr": "runtime_current_pr",
                "head_sha": "runtime_current_pr_head",
                "reviewed_pr": 105,
                "reviewed_base_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
                "reviewed_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
                "draft_merge_sha": "e1783090dfb0a4560475b97a021ef1e77aebc399",
                "review_pr": 107,
                "review_head_sha": "f3cf2131798f8bf3bd319b21480dca196517f3fe",
                "review_merge_sha": "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6",
                "policy_model_content_hash": "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c",
                "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
                "adoption_content_hash": "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19",
                "adopted_pending_merge": True,
                "generic_implementation_authorized_after_merge": True,
                "exact_head_implementation_review_required": True,
                "fixed_range_public_requalification_authorized": False,
                "new_independent_audit_authorized": False,
                "u04_authorized": False,
                "m2_authorized": False,
                "production_pipeline_modified": False,
            }
            if any(item.get(key) != value for key, value in expected_adoption.items()):
                failures.append("ADR-0015 conditional adoption binding changed")
        if item.get("id") == "ADR-0015-IMPL":
            integration = pair == ADR0015_CONTROLLED_INTEGRATION_PAIR
            expected_implementation = {
                "status": (
                    "implementation_exact_head_approved_controlled_integration_pending_gate"
                    if integration
                    else "implementation_pass_fixture_only_pending_exact_head_review"
                ),
                "branch": (
                    "codex/adr-0015-invalid-interval-controlled-integration"
                    if integration
                    else "codex/adr-0015-invalid-interval-implementation"
                ),
                "pr": "runtime_current_pr",
                "head_sha": "runtime_current_pr_head",
                "base_main_sha": "141481fa445bdc03b453844a666dbd2639c3cdf7",
                "policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
                "algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
                "adoption_content_hash": "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19",
                "generic_policy_implemented": True,
                "fixture_validation_complete": True,
                "fault_injection_complete": True,
                "exact_head_implementation_review_required": not integration,
                "public_data_run_executed": False,
                "fixed_range_public_requalification_authorized": False,
                "new_independent_audit_authorized": False,
                "u04_authorized": False,
                "m2_authorized": False,
            }
            if any(item.get(key) != value for key, value in expected_implementation.items()):
                failures.append("ADR-0015 implementation binding changed")
        if item.get("id") == "U-03E-V4-IMPL":
            if item.get("head_sha") != "runtime_current_pr_head":
                failures.append("V4 implementation head_sha must be runtime current PR metadata")
            if item.get("contract_hash") != "816a354a1fe20ebab4c162ecaefbde47a90d61567f40873e2b477a983d06ee83":
                failures.append("V4 contract hash changed")
            if item.get("policy_hash") != "7dc02e719f6e41839a1aff8002befd117b2daa7b426edeed9ebb4bd42c303977":
                failures.append("V4 policy hash changed")
            if item.get("lifecycle_registry_hash") != "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d":
                failures.append("V4 lifecycle registry hash changed")
            if item.get("implemented") is not True or item.get("independent_review_approved") or item.get("public_requalification"):
                failures.append("V4 implementation authority widened before independent review")
        if item.get("id") == "U-03E-V4-RUN":
            pending_review = pair[0] == "Liquid universe V4 public requalification passed pending review and merge"
            expected_status = "completed_pass_pending_review" if pending_review else "authorized_not_started"
            expected_base = (
                "c52a5d1bd9564ad471c38a631fa3897b01801547"
                if pending_review else "fccc9972502732319d38eb36775d007396df25db"
            )
            if item.get("status") != expected_status:
                failures.append("V4 public requalification status mismatch")
            if item.get("base_sha") != expected_base:
                failures.append("V4 public requalification base changed")
            if item.get("contract_hash") != "816a354a1fe20ebab4c162ecaefbde47a90d61567f40873e2b477a983d06ee83":
                failures.append("V4 contract hash changed")
            if item.get("policy_hash") != "7dc02e719f6e41839a1aff8002befd117b2daa7b426edeed9ebb4bd42c303977":
                failures.append("V4 policy hash changed")
            if item.get("lifecycle_registry_hash") != "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d":
                failures.append("V4 lifecycle registry hash changed")
            if item.get("implementation_merged") is not True or item.get("independent_review_approved") is not True:
                failures.append("V4 public requalification lacks merged implementation review authority")
            if item.get("public_requalification") is not pending_review:
                failures.append("V4 public requalification evidence state mismatch")
            if pending_review:
                expected_evidence = {
                    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
                    "artifact_set_hash": "4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6",
                    "run_manifest_hash": "f55f2829be39445a8489a0863ee5e013c481351d64797251bd79bc199376b127",
                    "result": "pass",
                }
                if any(item.get(key) != value for key, value in expected_evidence.items()):
                    failures.append("V4 public requalification evidence binding changed")
    if historical_failed_u03f_audit or pair[0] in {
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
        "U-03F V4 independent audit protocol frozen pending review",
        "U-03F V4 independent auditor implementation pending independent review",
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
        "Liquid universe V4 independent audit failed or blocked",
        "U-03F V4 repair public requalification blocked",
        "U-03F V4 repair chain closed blocked",
        "U-03F V4 invalid-interval adjudication protocol frozen pending review",
        "U-03F V4 invalid-interval diagnostic completed pending review",
        "U-03F V4 invalid-interval diagnostic merged; Draft policy ADR is the only authorized next task",
        "ADR-0015 synchronized invalid-interval quarantine policy Draft pending independent review",
        "ADR-0015 exact-head independent policy review pending PR validation",
        "ADR-0015 conditional adoption pending PR validation",
        "ADR-0015 generic invalid-interval policy implementation pending exact-head review",
        "ADR-0015 invalid-interval implementation controlled integration pending PR validation",
        "ADR-0015 fixed-range requalification passed; new independent audit protocol is the only authorized next task",
        "ADR-0015 independent audit protocol frozen; independent auditor implementation is the only authorized next task",
        "ADR-0015 independent auditor fixture implementation complete; exact-head review is the only authorized next task",
        "ADR-0015 independent auditor exact-head review approved; real independent audit is the only authorized next task",
        "ADR-0015 independent auditor microsecond normalization fixed; replacement exact-head review is the only authorized next task",
        "ADR-0015 independent auditor envelope reconciliation fixed; replacement exact-head review is the only authorized next task",
        "ADR-0015 independent audit passed; separate U-04 authorization decision is the only authorized next task",
        "U-04 cross-sectional hypothesis design authorized; outcome-blind preregistration is the only authorized next task",
        "U-04 cross-sectional residual-reversal design complete; outcome-blind paper protocol design is the only authorized next task",
        "U-04 paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "U-04 data qualification passed; one frozen sealed-IS paper observation is the only authorized next task",
        "U-04 paper feasibility failed; candidate closed without OOS",
        "U-05 independent design authorized; outcome-blind hypothesis design is the only next task",
        "U-05 breadth-demand persistence design complete; outcome-blind paper protocol design is the only next task",
        "U-05 Paper protocol exact-head review approved; data qualification and isolation are the only authorized next task",
        "U-05 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "U-05 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "U-06 independent design authorized; outcome-blind hypothesis design is the only next task",
        "U-06 volume-share absorption design complete; outcome-blind Paper protocol design is the only next task",
        "U-06 Paper protocol exact-head review approved; data qualification and isolation are the only next task",
        "U-06 data qualification passed; one frozen sealed-IS Paper observation is the only authorized next task",
        "U-06 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
        "U-07 closed failed feasibility; only a separate independent-candidate authorization decision may follow",
    }:
        milestones = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "Liquid universe V4 fixed-range public requalification"
        ]
        expected_milestone = {
            "status": (
                "pass_revalidation_required_after_failed_independent_audit"
                if pair in AUDIT_BLOCKED_PAIRS or historical_failed_u03f_audit
                else "pass_active_qualification_authority"
            ),
            "merged_pr": 89,
            "merge_commit": "77cb0969980978e65f3560f38f50924c73dfee6e",
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "artifact_set_hash": "4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6",
            "run_manifest_hash": "f55f2829be39445a8489a0863ee5e013c481351d64797251bd79bc199376b127",
        }
        if len(milestones) != 1 or any(
            milestones[0].get(key) != value for key, value in expected_milestone.items()
        ):
            failures.append("merged V4 requalification milestone binding changed")
        if any(item.get("id") == "U-03E-V4-RUN" for item in open_work):
            failures.append("merged V4 requalification must not remain in open_work")
        if pair not in AUDIT_BLOCKED_PAIRS and not historical_failed_u03f_audit:
            audit = [item for item in open_work if item.get("id") == "U-03F"]
            expected_audit_status = {
                "U-03F V4 independent audit protocol frozen pending review": "protocol_frozen_pending_review",
                "U-03F V4 independent auditor implementation pending independent review": "auditor_implementation_pending_independent_review",
                "U-03F V4 independent auditor approved and merged; real offline audit authorized not started": "real_offline_audit_authorized_not_started",
                "U-03F V4 independent audit failed pending truthful result review": "completed_failed_audit_pending_review",
            }.get(pair[0], "authorized_not_started")
            if len(audit) != 1 or audit[0].get("status") != expected_audit_status:
                failures.append("U-03F state does not match the frozen transition")
            expected_evidence = (
                "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md"
                if pair[0] == "U-03F V4 independent audit failed pending truthful result review"
                else "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json"
            )
            if not audit or audit[0].get("evidence") != expected_evidence:
                failures.append("U-03F must audit the V4 machine authority")
    if pair in AUDIT_BLOCKED_PAIRS or any(
        item.get("phase") == "U-03F V4 independent audit" and item.get("status") == "failed_audit"
        for item in state.get("completed_milestones", [])
    ):
        if any(item.get("id") == "U-03F" for item in open_work):
            failures.append("merged failed U-03F must not remain in open_work")
        audit_milestones = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "U-03F V4 independent audit"
        ]
        expected_failed_audit = {
            "status": "failed_audit",
            "merged_pr": 95,
            "merge_commit": "36b81649fbdaf4f54aea7027f3e9325b0ea80de0",
            "result_head_sha": "fed6aa929d952a9d4744728d398dfa51fe399df1",
            "verdict": "failed_audit",
            "critical_findings": 1,
            "high_findings": 7,
            "production_manifests_exact": 10,
            "production_manifests_total": 15,
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "independent_artifact_set_hash": "c7c8e564db713c9268fcd907f8b28cf3f5f595fa08d0755d96c40d91fe237236",
        }
        if len(audit_milestones) != 1 or any(
            audit_milestones[0].get(key) != value
            for key, value in expected_failed_audit.items()
        ):
            failures.append("merged failed U-03F milestone binding changed")
        if pair == REPAIR_CHAIN_CLOSED_PAIR:
            repair_milestones = [
                item
                for item in state.get("completed_milestones", [])
                if item.get("phase") == "U-03F V4 repair public requalification"
            ]
            expected_repair_closeout = {
                "status": "blocked_invalid_5m_interval_boundaries_merged_closed",
                "source_mode": "frozen_local_only",
                "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
                "cold_artifact_set_hash": "b7cac049c6ab339f52fc29c7f31d275db09b3a4c47e2f62b38175cea219b2f83",
                "run_manifest_hash": "0792ec7b52dbabb6057f0c238d963ed774c1e9e838b42cb21a03bc7e334f68cf",
                "determinism_status": "not_run_due_fail_closed_cold_block",
                "processing_errors": 119,
                "new_independent_audit_executed": False,
                "merged_pr": 100,
                "result_head_sha": "a0e680fbfb4415bb25871aa0cb3ed8b873d6c810",
                "merge_commit": "927f121651d6e1e07f174410a39595f6d09e9a5d",
                "github_checks_success": 114,
            }
            if len(repair_milestones) != 1 or any(
                repair_milestones[0].get(key) != value
                for key, value in expected_repair_closeout.items()
            ):
                failures.append("merged blocked repair requalification binding changed")
            if any(
                item.get("id") == "U-03F-REPAIR-REQUALIFICATION"
                for item in open_work
            ):
                failures.append("closed repair requalification must not remain in open_work")
        v4_milestones = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "Liquid universe V4 fixed-range public requalification"
        ]
        if (
            len(v4_milestones) != 1
            or v4_milestones[0].get("qualification_authority") != "audit_blocked"
            or v4_milestones[0].get("audit_status") != "failed_audit"
        ):
            failures.append("V4 authority is not audit_blocked after failed U-03F")
    if pair[0] in {
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
        "Liquid universe V4 independent audit failed or blocked",
        "U-03F V4 repair public requalification blocked",
        "U-03F V4 repair chain closed blocked",
        "U-03F V4 invalid-interval adjudication protocol frozen pending review",
        "U-03F V4 invalid-interval diagnostic completed pending review",
        "U-03F V4 invalid-interval diagnostic merged; Draft policy ADR is the only authorized next task",
        "ADR-0015 synchronized invalid-interval quarantine policy Draft pending independent review",
        "ADR-0015 exact-head independent policy review pending PR validation",
        "ADR-0015 conditional adoption pending PR validation",
        "ADR-0015 generic invalid-interval policy implementation pending exact-head review",
        "ADR-0015 invalid-interval implementation controlled integration pending PR validation",
        "ADR-0015 fixed-range requalification passed; new independent audit protocol is the only authorized next task",
    }:
        reviews = [
            item for item in state.get("completed_milestones", [])
            if item.get("phase") == "U-03F V4 independent auditor implementation review"
        ]
        implementations = [
            item for item in state.get("completed_milestones", [])
            if item.get("phase") == "U-03F V4 independent auditor implementation"
        ]
        expected_review = {
            "merged_pr": 93,
            "merge_commit": "80f603b341a638a9f20475218582e4c7575c42e3",
            "reviewed_pr": 92,
            "reviewed_head_sha": "d055efc1e46fb90b60a4553b9c5e2d1589bd7f9e",
            "verdict": "approve",
            "critical_findings": 0,
            "high_findings": 0,
        }
        expected_implementation = {
            "status": "implementation_fixture_only_approved_and_merged",
            "merged_pr": 92,
            "merge_commit": "d107894f393de01b2a046a8ffd2ee937a07bdc2b",
            "reviewed_head_sha": "d055efc1e46fb90b60a4553b9c5e2d1589bd7f9e",
            "audit_algorithm_hash": "7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1",
            "full_public_audit_executed": False,
        }
        if len(reviews) != 1 or any(reviews[0].get(key) != value for key, value in expected_review.items()):
            failures.append("U-03F auditor review milestone binding changed")
        if len(implementations) != 1 or any(implementations[0].get(key) != value for key, value in expected_implementation.items()):
            failures.append("U-03F auditor implementation milestone binding changed")
    u04_items = [item for item in open_work if item.get("id") == "U-04"]
    if any(item.get("status") != "not_authorized" for item in u04_items):
        if pair != U04_DESIGN_PAIR:
            failures.append("U-04 authorized without a separate post-audit task")
        elif len(u04_items) != 1 or any(
            u04_items[0].get(key) != value
            for key, value in {
                "status": "authorized_ready",
                "maximum_hypotheses": 1,
                "outcome_blind_preregistration_required": True,
                "event_scan_authorized": False,
                "strategy_authorized": False,
                "oos_authorized": False,
                "trading_authorized": False,
                "m2_authorized": False,
            }.items()
        ):
            failures.append("U-04 narrow design authorization binding changed")
    u04_protocol_items = [item for item in open_work if item.get("id") == "U-04-PROTOCOL"]
    if pair == U04_PROTOCOL_PAIR:
        if len(u04_protocol_items) != 1 or any(
            u04_protocol_items[0].get(key) != value
            for key, value in {
                "status": "authorized_ready",
                "candidate_id": "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL",
                "outcome_blind_protocol_required": True,
                "event_scan_authorized": False,
                "strategy_authorized": False,
                "oos_authorized": False,
                "trading_authorized": False,
                "m2_authorized": False,
            }.items()
        ):
            failures.append("U-04 paper-protocol design authorization binding changed")
    u04_data_items = [item for item in open_work if item.get("id") == "U-04-DATA-QUALIFICATION"]
    if pair == U04_PROTOCOL_REVIEW_APPROVED_PAIR:
        if len(u04_data_items) != 1 or any(
            u04_data_items[0].get(key) != value
            for key, value in {
                "status": "authorized_ready",
                "candidate_id": "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL",
                "protocol_content_hash": "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6",
                "review_content_hash": "34fe2efdf4788b20b915f34b3b6442f60ddaa364103ae90b920dc2cacf9646b1",
                "source_mode": "frozen_local_only",
                "data_qualification_authorized": True,
                "event_scan_authorized": False,
                "strategy_authorized": False,
                "oos_authorized": False,
                "trading_authorized": False,
                "m2_authorized": False,
            }.items()
        ):
            failures.append("U-04 data-qualification authorization binding changed")
    u04_observation_items = [item for item in open_work if item.get("id") == "U-04-PAPER-OBSERVATION"]
    if pair == U04_DATA_QUALIFICATION_PASS_PAIR:
        if len(u04_observation_items) != 1 or any(
            u04_observation_items[0].get(key) != value
            for key, value in {
                "status": "authorized_ready",
                "candidate_id": "U04-CROSS-SECTIONAL-RESIDUAL-REVERSAL",
                "protocol_content_hash": "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6",
                "review_content_hash": "34fe2efdf4788b20b915f34b3b6442f60ddaa364103ae90b920dc2cacf9646b1",
                "qualification_content_hash": "4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c",
                "source_mode": "frozen_local_is_only",
                "paper_observation_authorized": True,
                "event_scan_authorized": True,
                "path_observation_authorized": True,
                "formal_returns_authorized": False,
                "second_run_authorized": False,
                "strategy_authorized": False,
                "oos_authorized": False,
                "trading_authorized": False,
                "m2_authorized": False,
            }.items()
        ):
            failures.append("U-04 sealed-IS paper-observation authorization binding changed")
    if pair == U04_FAILED_FEASIBILITY_PAIR:
        if any(item.get("id", "").startswith("U-04") for item in open_work):
            failures.append("failed U-04 candidate must not remain in open_work")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-04 unique sealed-IS paper observation"]
        expected_failure = {
            "status": "failed_feasibility",
            "run_content_hash": "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2",
            "three_order_identity_hash": "4c512f5900b15969cf13c1481317e388d94d3ac6c2b26dc576914863b5201b42",
            "complete_is_independent_episodes": 397,
            "failed_gates": ["median_24h_relative_recovery", "median_24h_absolute_close_displacement"],
            "oos_opened": False,
            "second_run_executed": False,
            "candidate_closed": True,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_failure.items()):
            failures.append("U-04 failed-feasibility milestone binding changed")
    if pair == U05_DESIGN_PAIR:
        u05_items = [item for item in open_work if item.get("id") == "U-05"]
        expected_u05 = {
            "status": "authorized_ready",
            "maximum_hypotheses": 1,
            "independent_economic_rationale_required": True,
            "u04_outcome_derived_rule_prohibited": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(u05_items) != 1 or any(u05_items[0].get(key) != value for key, value in expected_u05.items()):
            failures.append("U-05 narrow design authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 design authorization decision"]
        expected_decision = {
            "status": "authorized_for_one_independent_outcome_blind_hypothesis_design_only",
            "decision_content_hash": "48482a1d72b34d4925e3b0ed8ab218df202d560af7d8057c4fa8be403c46dc2c",
            "prior_run_content_hash": "9182c9e3fb2aad6959d98ccbe18c77e411a3d5ce5adc6fdf352da76cd53eebc2",
            "maximum_hypotheses": 1,
            "u04_outcome_derived_rule_prohibited": True,
            "event_scan_authorized": False,
            "oos_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-05 design authorization milestone binding changed")
    if pair == U05_PROTOCOL_PAIR:
        protocol_items = [item for item in open_work if item.get("id") == "U-05-PROTOCOL"]
        expected_protocol = {
            "status": "authorized_ready",
            "candidate_id": "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE",
            "design_content_hash": "ae12172aeea45c8447cb40d39dc7d83c4cd85852138a3ee994bf977112b8c2bb",
            "outcome_blind_protocol_required": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(protocol_items) != 1 or any(protocol_items[0].get(key) != value for key, value in expected_protocol.items()):
            failures.append("U-05 paper-protocol design authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 cross-sectional breadth-demand persistence hypothesis design"]
        expected_design = {
            "status": "economic_hypothesis_pass_protocol_design_only",
            "candidate_id": "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE",
            "hypothesis_sha256": "ad164b1d9a94d9d61145bf7431a805cfa795a77a6c8aef2cdc488f6bd9e7349b",
            "design_content_hash": "ae12172aeea45c8447cb40d39dc7d83c4cd85852138a3ee994bf977112b8c2bb",
            "events_evaluated": False,
            "returns_computed": False,
            "oos_opened": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-05 design milestone binding changed")
    if pair == U05_PROTOCOL_REVIEW_APPROVED_PAIR:
        data_items = [item for item in open_work if item.get("id") == "U-05-DATA-QUALIFICATION"]
        expected_data = {
            "status": "authorized_ready",
            "candidate_id": "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE",
            "target_commit": "8d8652796e22a15285ba682b4524baa0218ca5a6",
            "protocol_content_hash": "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214",
            "review_content_hash": "8602f209c3e80ea31b4b1175967acfba2bb20252254d3fbdf5cc72ea128d914f",
            "frozen_source_only": True,
            "three_traversal_orders_required": True,
            "oos_ohlc_decode_authorized": False,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(data_items) != 1 or any(data_items[0].get(key) != value for key, value in expected_data.items()):
            failures.append("U-05 data-qualification-only authorization binding changed")
        reviews = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 Paper-protocol exact-head independent review"]
        expected_review = {
            "status": "approve_local_complete",
            "target_commit": "8d8652796e22a15285ba682b4524baa0218ca5a6",
            "target_base_commit": "f66dcbdf5ad48b35e7bba2f112257e446563288c",
            "protocol_content_hash": "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214",
            "review_content_hash": "8602f209c3e80ea31b4b1175967acfba2bb20252254d3fbdf5cc72ea128d914f",
            "verdict": "approve",
            "remaining_critical_findings": 0,
            "remaining_high_findings": 0,
            "target_modified": False,
            "data_qualification_authorized": True,
            "event_scan_authorized": False,
            "oos_authorized": False,
        }
        if len(reviews) != 1 or any(reviews[0].get(key) != value for key, value in expected_review.items()):
            failures.append("U-05 protocol review milestone binding changed")
        protocols = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 outcome-blind breadth-demand Paper protocol"]
        expected_protocol = {
            "status": "frozen_before_result_exact_head_approved",
            "target_commit": "8d8652796e22a15285ba682b4524baa0218ca5a6",
            "protocol_content_hash": "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214",
            "public_data_read": False,
            "events_evaluated": False,
            "paths_observed": False,
            "returns_computed": False,
            "oos_opened": False,
        }
        if len(protocols) != 1 or any(protocols[0].get(key) != value for key, value in expected_protocol.items()):
            failures.append("U-05 reviewed protocol milestone binding changed")
    if pair == U05_DATA_QUALIFICATION_PASS_PAIR:
        observations = [item for item in open_work if item.get("id") == "U-05-PAPER-OBSERVATION"]
        expected_observation = {
            "status": "authorized_once_not_started",
            "candidate_id": "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE",
            "target_commit": "8d8652796e22a15285ba682b4524baa0218ca5a6",
            "protocol_content_hash": "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214",
            "review_content_hash": "8602f209c3e80ea31b4b1175967acfba2bb20252254d3fbdf5cc72ea128d914f",
            "qualification_content_hash": "348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f",
            "maximum_runs": 1,
            "sealed_is_only": True,
            "three_traversal_orders_required": True,
            "oos_ohlc_decode_authorized": False,
            "event_scan_authorized": True,
            "path_observation_authorized": True,
            "formal_returns_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(observations) != 1 or any(observations[0].get(key) != value for key, value in expected_observation.items()):
            failures.append("U-05 sealed-IS Paper observation authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 frozen-source data qualification and IS/OOS isolation"]
        expected_qualification = {
            "status": "pass_local_complete",
            "protocol_target_commit": "8d8652796e22a15285ba682b4524baa0218ca5a6",
            "contract_content_hash": "f1374b5c7bf7a103be7dacf3985d45cd332388afe601bd849271b30d63f562c3",
            "qualification_content_hash": "348e80291ced6f7cbbb929c0b88c6bbce0b86e23cdbed33718b884810df7cb4f",
            "source_archive_count": 27736,
            "manifests_exact": 19,
            "traversal_identity_hash": "ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa",
            "expected_4h_member_blocks": 213570,
            "oos_ohlc_values_decoded": 0,
            "breadth_rows_generated": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "return_rows_generated": 0,
            "one_sealed_is_paper_observation_authorized": True,
            "strategy_authorized": False,
            "oos_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_qualification.items()):
            failures.append("U-05 data qualification milestone binding changed")
    if pair == U05_CLOSED_PAIR:
        observations = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-05 unique sealed-IS Paper observation"]
        expected_observation = {
            "status": "failed_feasibility",
            "run_content_hash": "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a",
            "three_order_identity_hash": "ac4b36ac2c04d55c25f9db62f9d59598bac8bb1861b97d4e01f701be398267b0",
            "complete_is_independent_episodes": 490,
            "median_24h_common_demand_close_displacement": "0.0007591260524623880214213314285",
            "median_24h_positive_member_fraction": "0.5333333333333333333333333335",
            "oos_opened": False,
            "formal_returns_computed": False,
            "second_run_executed": False,
            "candidate_closed": True,
            "strategy_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(observations) != 1 or any(observations[0].get(key) != value for key, value in expected_observation.items()):
            failures.append("U-05 failed observation milestone binding changed")
        if any(item.get("id") == "U-05-PAPER-OBSERVATION" for item in open_work):
            failures.append("closed U-05 observation remains open")
    if pair == U06_DESIGN_PAIR:
        designs = [item for item in open_work if item.get("id") == "U-06"]
        expected_design = {
            "status": "authorized_ready",
            "authorization_content_hash": "596eacbcf2caec7dd1da27bb66ee8bb5859c5b6992c067f22d40e5305cb74662",
            "maximum_hypotheses": 1,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(designs) != 1 or any(designs[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-06 hypothesis-design-only authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-06 design authorization decision"]
        expected_decision = {
            "status": "authorized_for_one_independent_outcome_blind_hypothesis_design_only",
            "decision_content_hash": "596eacbcf2caec7dd1da27bb66ee8bb5859c5b6992c067f22d40e5305cb74662",
            "prior_run_content_hash": "874cdac32b63535f4b5636420dc55719e8dc795a66e5eca2be96f88ca3737e4a",
            "maximum_hypotheses": 1,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-06 design decision milestone binding changed")
    if pair == U07_DESIGN_PAIR:
        designs = [item for item in open_work if item.get("id") == "U-07"]
        expected_design = {
            "status": "authorized_ready",
            "authorization_content_hash": "58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5",
            "maximum_hypotheses": 1,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(designs) != 1 or any(designs[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-07 hypothesis-design-only authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 design authorization decision"]
        expected_decision = {
            "status": "authorized_for_one_independent_outcome_blind_hypothesis_design_only",
            "decision_content_hash": "58f8301035e593b0621add93cfa876a11a5af52df0a3afae38d7b41f095e37d5",
            "prior_run_content_hash": "2f715394411ca260f9889304ddc84da926d37ec1dfc9d4316493f23f6881382a",
            "maximum_hypotheses": 1,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-07 design decision milestone binding changed")
    if pair == U07_PROTOCOL_PAIR:
        protocols = [item for item in open_work if item.get("id") == "U-07-PROTOCOL"]
        expected_protocol = {
            "status": "authorized_ready",
            "candidate_id": "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION",
            "design_content_hash": "272eabd4ab1737566698309b98cc13b952a8d39b86c457674d58ff56de021795",
            "outcome_blind_required": True,
            "exact_head_review_required": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(protocols) != 1 or any(protocols[0].get(key) != value for key, value in expected_protocol.items()):
            failures.append("U-07 Paper-protocol-design-only authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 cross-sectional market-stress relative-strength continuation hypothesis design"]
        expected_design = {
            "status": "economic_hypothesis_pass_protocol_design_only",
            "candidate_id": "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION",
            "hypothesis_sha256": "3130450cd7bd7cddab4bce0c89b274ae93e50bed278379011cc4d09e15fb3de3",
            "design_content_hash": "272eabd4ab1737566698309b98cc13b952a8d39b86c457674d58ff56de021795",
            "public_data_read": False,
            "events_evaluated": False,
            "returns_computed": False,
            "oos_opened": False,
            "strategy_authorized": False,
            "paper_protocol_design_authorized": True,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-07 hypothesis design milestone binding changed")
    if pair == U07_PROTOCOL_REVIEW_APPROVED_PAIR:
        data_items = [item for item in open_work if item.get("id") == "U-07-DATA-QUALIFICATION"]
        expected_data = {
            "status": "authorized_ready",
            "candidate_id": "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION",
            "target_commit": "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "protocol_content_hash": "d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195",
            "review_content_hash": "fa9d90f7ebb30d4072662a9d8a733760a703eb04031abda23f3b6b0846bc70b6",
            "frozen_source_only": True,
            "three_traversal_orders_required": True,
            "oos_ohlc_decode_authorized": False,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(data_items) != 1 or any(data_items[0].get(key) != value for key, value in expected_data.items()):
            failures.append("U-07 data-qualification-only authorization binding changed")
        reviews = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 Paper-protocol exact-head independent review"]
        expected_review = {
            "status": "approve_local_complete",
            "target_commit": "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "target_base_commit": "f282f45229dbab3fd20767b2097a07a481e50d09",
            "protocol_content_hash": "d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195",
            "review_content_hash": "fa9d90f7ebb30d4072662a9d8a733760a703eb04031abda23f3b6b0846bc70b6",
            "verdict": "approve",
            "remaining_critical_findings": 0,
            "remaining_high_findings": 0,
            "target_modified": False,
            "data_qualification_authorized": True,
            "event_scan_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(reviews) != 1 or any(reviews[0].get(key) != value for key, value in expected_review.items()):
            failures.append("U-07 protocol review milestone binding changed")
        protocols = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 outcome-blind market-stress relative-strength Paper protocol"]
        expected_protocol = {
            "status": "frozen_before_result_exact_head_approved",
            "target_commit": "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "protocol_content_hash": "d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195",
            "public_data_read": False,
            "events_evaluated": False,
            "paths_observed": False,
            "returns_computed": False,
            "oos_opened": False,
        }
        if len(protocols) != 1 or any(protocols[0].get(key) != value for key, value in expected_protocol.items()):
            failures.append("U-07 reviewed protocol milestone binding changed")
    if pair == U07_DATA_QUALIFICATION_PASS_PAIR:
        observations = [item for item in open_work if item.get("id") == "U-07-PAPER-OBSERVATION"]
        expected_observation = {
            "status": "authorized_once_not_started",
            "candidate_id": "U07-CROSS-SECTIONAL-MARKET-STRESS-RELATIVE-STRENGTH-CONTINUATION",
            "target_commit": "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "protocol_content_hash": "d62dd323a01507eeb5a78afe646cec196e417faeddd7d84129b2bd8834250195",
            "review_content_hash": "fa9d90f7ebb30d4072662a9d8a733760a703eb04031abda23f3b6b0846bc70b6",
            "qualification_content_hash": "fa65f34089854cd5faf950234b3488eb64b3058d1ab47f3dab500bbfb395e123",
            "maximum_runs": 1,
            "sealed_is_only": True,
            "three_traversal_orders_required": True,
            "oos_ohlc_decode_authorized": False,
            "event_scan_authorized": True,
            "path_observation_authorized": True,
            "formal_returns_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(observations) != 1 or any(observations[0].get(key) != value for key, value in expected_observation.items()):
            failures.append("U-07 sealed-IS Paper observation authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 frozen-source data qualification and IS/OOS isolation"]
        expected_qualification = {
            "status": "pass_local_complete",
            "protocol_target_commit": "3aed4c337ff984b3e07ad9a4c7cda898425b3791",
            "contract_content_hash": "0dd9a159382f1d515fed0269c9122adcd042a1fd726431bc36a9e4f6e01d5fb8",
            "qualification_content_hash": "fa65f34089854cd5faf950234b3488eb64b3058d1ab47f3dab500bbfb395e123",
            "source_archive_count": 27736,
            "manifests_exact": 19,
            "traversal_identity_hash": "ca7d59b32a4c0a187e6692a0e0f84015780f6f7400217edac130d1abf3f044aa",
            "expected_4h_member_blocks": 213570,
            "constituent_1h_rows": 854280,
            "oos_ohlc_values_decoded": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "return_rows_generated": 0,
            "one_sealed_is_paper_observation_authorized": True,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_qualification.items()):
            failures.append("U-07 data qualification milestone binding changed")
    if pair == U07_FAILED_FEASIBILITY_PAIR:
        decisions = [item for item in open_work if item.get("id") == "U-08-DECISION"]
        expected_decision = {
            "status": "authorized_ready",
            "predecessor_run_content_hash": "8c637a3f13dad4410beb446094af011582ab2cde0ac449e32d044cbaa709352c",
            "maximum_new_hypotheses": 1,
            "independent_economic_rationale_required": True,
            "outcome_inversion_prohibited": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(decisions) != 1 or any(decisions[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-08 independent-candidate decision authorization changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-07 unique sealed-IS Paper observation"]
        expected_result = {
            "status": "failed_feasibility",
            "run_content_hash": "8c637a3f13dad4410beb446094af011582ab2cde0ac449e32d044cbaa709352c",
            "three_order_identity_hash": "2714c2bf0fee08ddd9531eeac2ef531904c7c416eb4c809a666f5f75e4cf00ee",
            "complete_is_independent_episodes": 82,
            "median_24h_relative_continuation": "0.004287821384236292564275564571",
            "median_24h_candidate_absolute_close_displacement": "0.01160736483333721153810826070",
            "fraction_positive_24h_relative_continuation": "0.5243902439024390243902439024",
            "oos_opened": False,
            "formal_returns_computed": False,
            "second_run_executed": False,
            "candidate_closed": True,
            "strategy_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_result.items()):
            failures.append("U-07 failed Paper result binding changed")
    if pair == U08_DESIGN_PAIR:
        designs = [item for item in open_work if item.get("id") == "U-08"]
        expected_design = {
            "status": "authorized_ready",
            "decision_content_hash": "813267f29fd2f019b7d856d95a5eaaa7927a3f072327cc643e6a1ecd51af1cf9",
            "maximum_hypotheses": 1,
            "independent_economic_rationale_required": True,
            "outcome_inversion_prohibited": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(designs) != 1 or any(designs[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-08 design-only authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-08 design authorization decision"]
        expected_decision = {
            "status": "authorized_for_one_independent_outcome_blind_hypothesis_design_only",
            "decision_content_hash": "813267f29fd2f019b7d856d95a5eaaa7927a3f072327cc643e6a1ecd51af1cf9",
            "prior_run_content_hash": "8c637a3f13dad4410beb446094af011582ab2cde0ac449e32d044cbaa709352c",
            "maximum_hypotheses": 1,
            "independent_economic_rationale_required": True,
            "prior_outcome_derived_rule_prohibited": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-08 authorization milestone binding changed")
    if pair == U09_DESIGN_PAIR:
        designs = [item for item in open_work if item.get("id") == "U-09"]
        expected_design = {
            "status": "authorized_not_started",
            "decision_content_hash": "2d643678e00575c93dad0331fff089fd620b214f658ca8d174dfe9bbcc06e477",
            "maximum_hypotheses": 1,
            "event_scan_authorized": False,
            "parameter_selection_authorized": False,
            "formal_returns_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(designs) != 1 or any(designs[0].get(key) != value for key, value in expected_design.items()):
            failures.append("U-09 design-only authorization binding changed")
        milestones = [item for item in state.get("completed_milestones", []) if item.get("phase") == "U-09 design authorization decision"]
        expected_decision = {
            "status": "authorized_for_one_independent_outcome_blind_hypothesis_design_only",
            "decision_content_hash": "2d643678e00575c93dad0331fff089fd620b214f658ca8d174dfe9bbcc06e477",
            "prior_run_content_hash": "f6fbcdee846b855883a5e356ea49e6a98901bfcc6a9dbd5a2cbb07ebed9eca3e",
            "maximum_hypotheses": 1,
            "independent_economic_rationale_required": True,
            "prior_outcome_derived_rule_prohibited": True,
            "event_scan_authorized": False,
            "strategy_authorized": False,
            "oos_authorized": False,
            "trading_authorized": False,
            "m2_authorized": False,
        }
        if len(milestones) != 1 or any(milestones[0].get(key) != value for key, value in expected_decision.items()):
            failures.append("U-09 authorization milestone binding changed")
    if pair == INVALID_INTERVAL_PROTOCOL_PAIR:
        protocol = state.get("u03f_v4_invalid_interval_adjudication_protocol", {})
        expected_protocol = {
            "status": "frozen_before_diagnostic_run_pending_review",
            "starting_main_sha": "3ba411d28563526a5357e3882a1e5759311f6179",
            "branch": "codex/u03f-v4-invalid-interval-protocol",
            "pr": 102,
            "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
            "source_mode": "frozen_local_only",
            "source_archive_count": 27736,
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "blocked_input_processing_errors": 119,
            "diagnostic_orders": ["normal", "reverse", "deterministic_shuffled"],
            "diagnostic_executed": False,
            "policy_adopted": False,
            "production_pipeline_modified": False,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if protocol != expected_protocol:
            failures.append("invalid-interval protocol state binding changed")
    if pair == INVALID_INTERVAL_DIAGNOSTIC_PAIR:
        protocol = state.get("u03f_v4_invalid_interval_adjudication_protocol", {})
        expected_protocol = {
            "status": "frozen_before_diagnostic_run_merged",
            "starting_main_sha": "3ba411d28563526a5357e3882a1e5759311f6179",
            "branch": "codex/u03f-v4-invalid-interval-protocol",
            "pr": 102,
            "result_head_sha": "07e4fc13d4a6d027e4881863b9224906be776e9a",
            "merge_commit": "70c784b1573de8437e189672c89e9c00b6505978",
            "github_checks_success": 116,
            "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
            "source_mode": "frozen_local_only",
            "source_archive_count": 27736,
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "blocked_input_processing_errors": 119,
            "diagnostic_orders": ["normal", "reverse", "deterministic_shuffled"],
            "diagnostic_executed": True,
            "policy_adopted": False,
            "production_pipeline_modified": False,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if protocol != expected_protocol:
            failures.append("merged invalid-interval protocol state binding changed")
        diagnostic = state.get("u03f_v4_invalid_interval_adjudication_diagnostic", {})
        expected_diagnostic = {
            "status": "completed_new_policy_adr_required_pending_review",
            "base_main_sha": "70c784b1573de8437e189672c89e9c00b6505978",
            "branch": "codex/u03f-v4-invalid-interval-diagnostic",
            "source_mode": "frozen_local_only",
            "source_archive_count_per_order": 27736,
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "diagnostic_orders": ["normal", "reverse", "deterministic_shuffled"],
            "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
            "run_manifest_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
            "invalid_physical_rows": 119,
            "synchronized_windows": 8,
            "decision": "new_policy_adr_required",
            "policy_adopted": False,
            "production_pipeline_modified": False,
            "draft_policy_adr_authorized_before_evidence_merge": False,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if diagnostic != expected_diagnostic:
            failures.append("invalid-interval diagnostic state binding changed")
        milestones = [
            item for item in state.get("completed_milestones", [])
            if item.get("phase") == "U-03F V4 invalid-interval adjudication protocol"
        ]
        expected_milestone = {
            "status": "frozen_before_diagnostic_run_merged",
            "merged_pr": 102,
            "result_head_sha": "07e4fc13d4a6d027e4881863b9224906be776e9a",
            "merge_commit": "70c784b1573de8437e189672c89e9c00b6505978",
            "github_checks_success": 116,
            "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
            "diagnostic_executed_before_merge": False,
            "policy_adopted": False,
            "production_pipeline_modified": False,
        }
        if len(milestones) != 1 or any(
            milestones[0].get(key) != value for key, value in expected_milestone.items()
        ):
            failures.append("merged invalid-interval protocol milestone changed")
    if pair in {INVALID_INTERVAL_DIAGNOSTIC_MERGED_PAIR, ADR0015_DRAFT_PAIR, ADR0015_REVIEW_PAIR, ADR0015_ADOPTION_PAIR, ADR0015_IMPLEMENTATION_PAIR, ADR0015_CONTROLLED_INTEGRATION_PAIR}:
        diagnostic = state.get("u03f_v4_invalid_interval_adjudication_diagnostic", {})
        expected = {
            "status": "completed_new_policy_adr_required_merged",
            "base_main_sha": "70c784b1573de8437e189672c89e9c00b6505978",
            "branch": "codex/u03f-v4-invalid-interval-diagnostic",
            "source_mode": "frozen_local_only",
            "source_archive_count_per_order": 27736,
            "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
            "diagnostic_orders": ["normal", "reverse", "deterministic_shuffled"],
            "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
            "run_manifest_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
            "invalid_physical_rows": 119,
            "synchronized_windows": 8,
            "decision": "new_policy_adr_required",
            "evidence_pr": 103,
            "evidence_head_sha": "e4b6f6e70bf6df2b10dbd7acc71a734f107d5076",
            "evidence_merge_commit": "49e028712695cf2a946aae9abf14c5668a5343f2",
            "evidence_pr_checks_success": 118,
            "policy_adopted": False,
            "production_pipeline_modified": False,
            "draft_policy_adr_authorized_before_evidence_merge": False,
            "draft_policy_adr_authorized_after_evidence_merge": True,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if diagnostic != expected:
            failures.append("merged invalid-interval diagnostic state binding changed")
        milestones = [
            item for item in state.get("completed_milestones", [])
            if item.get("phase") == "U-03F V4 invalid-interval deterministic diagnostic"
        ]
        expected_milestone = {
            "status": "completed_new_policy_adr_required_merged",
            "merged_pr": 103,
            "result_head_sha": "e4b6f6e70bf6df2b10dbd7acc71a734f107d5076",
            "merge_commit": "49e028712695cf2a946aae9abf14c5668a5343f2",
            "github_checks_success": 118,
            "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
            "run_manifest_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
            "invalid_physical_rows": 119,
            "synchronized_windows": 8,
            "decision": "new_policy_adr_required",
            "policy_adopted": False,
            "production_pipeline_modified": False,
        }
        if len(milestones) != 1 or any(
            milestones[0].get(key) != value for key, value in expected_milestone.items()
        ):
            failures.append("merged invalid-interval diagnostic milestone changed")
    if pair in {ADR0015_DRAFT_PAIR, ADR0015_REVIEW_PAIR, ADR0015_ADOPTION_PAIR, ADR0015_IMPLEMENTATION_PAIR, ADR0015_CONTROLLED_INTEGRATION_PAIR}:
        draft = state.get("adr0015_policy_draft", {})
        expected_draft = {
            "status": (
                "proposed_draft_non_authoritative_pending_independent_review"
                if pair == ADR0015_DRAFT_PAIR
                else (
                    "proposed_draft_non_authoritative_merged_pending_independent_review"
                    if pair == ADR0015_REVIEW_PAIR
                    else "proposed_draft_non_authoritative_merged_review_approved_historical_source"
                )
            ),
            "base_main_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
            "branch": "codex/adr-0015-invalid-interval-policy-draft",
            "pr": 105,
            **({
                "exact_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
                "merge_commit": "e1783090dfb0a4560475b97a021ef1e77aebc399",
                "github_checks_success": 120,
            } if pair in {ADR0015_REVIEW_PAIR, ADR0015_ADOPTION_PAIR, ADR0015_IMPLEMENTATION_PAIR, ADR0015_CONTROLLED_INTEGRATION_PAIR} else {}),
            "adr": "docs/decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md",
            "model": "docs/decisions/proposals/adr0015_invalid_interval_policy_model.json",
            "model_content_hash": "7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c",
            "protocol_content_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
            "diagnostic_content_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
            "diagnostic_run_content_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
            "policy_family": "synchronized_official_invalid_interval_quarantine",
            "minimum_invalid_active_members": 2,
            "minimum_invalid_active_fraction": 0.8,
            "full_active_slot_quarantine": True,
            "date_or_symbol_exceptions": False,
            "v2_gap_policy_direct_reuse": False,
            "policy_adopted": False,
            "implementation_authorized": False,
            "production_pipeline_modified": False,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if draft != expected_draft:
            failures.append("ADR-0015 Draft state binding changed")
    if pair in {ADR0015_REVIEW_PAIR, ADR0015_ADOPTION_PAIR, ADR0015_IMPLEMENTATION_PAIR, ADR0015_CONTROLLED_INTEGRATION_PAIR}:
        review = state.get("adr0015_independent_policy_review", {})
        expected_review = {
            "status": "approve_pending_pr_validation" if pair == ADR0015_REVIEW_PAIR else "approve_merged",
            "branch": "codex/adr-0015-independent-policy-review",
            "pr": "runtime_current_pr" if pair == ADR0015_REVIEW_PAIR else 107,
            "reviewed_pr": 105,
            "reviewed_base_sha": "6df4aa3aa355f986e5533a51e223d69e3bf16e84",
            "reviewed_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
            "draft_merge_commit": "e1783090dfb0a4560475b97a021ef1e77aebc399",
            "evidence": "reports/expert/ADR_0015_INDEPENDENT_REVIEW.md",
            "machine_evidence": "reports/expert/evidence/adr0015_independent_review.json",
            "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
            "verdict": "approve",
            "critical_findings": 0,
            "high_findings": 0,
            "public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if pair == ADR0015_REVIEW_PAIR:
            expected_review.update({
                "policy_adopted": False,
                "implementation_authorized": False,
            })
        else:
            expected_review.update({
                "review_head_sha": "f3cf2131798f8bf3bd319b21480dca196517f3fe",
                "review_merge_commit": "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6",
                "policy_adopted_by_review": False,
                "implementation_authorized_by_review": False,
            })
        if review != expected_review:
            failures.append("ADR-0015 independent review state binding changed")
    if pair == ADR0015_ADOPTION_PAIR:
        adoption = state.get("adr0015_conditional_adoption", {})
        expected_adoption = {
            "status": "accepted_for_generic_policy_implementation_and_exact_head_implementation_review_only_pending_pr_validation",
            "branch": "codex/adr-0015-conditional-adoption",
            "pr": "runtime_current_pr",
            "head_sha": "runtime_current_pr_head",
            "adopted_semantic_body_hash": "c3d5f605ec26161f1bedc6961ac6f326d00582f9c3dcaa9de68c226961a34149",
            "adoption_content_hash": "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19",
            "reviewed_draft_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
            "review_pr": 107,
            "review_head_sha": "f3cf2131798f8bf3bd319b21480dca196517f3fe",
            "review_merge_commit": "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6",
            "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
            "generic_policy_implementation_authorized_after_merge": True,
            "fixture_validation_authorized_after_merge": True,
            "fault_injection_authorized_after_merge": True,
            "exact_head_implementation_review_required": True,
            "production_pipeline_modified": False,
            "public_data_run_executed": False,
            "fixed_range_public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if adoption != expected_adoption:
            failures.append("ADR-0015 conditional adoption state binding changed")
        review_milestones = [
            item for item in state.get("completed_milestones", [])
            if item.get("phase") == "ADR-0015 exact-head independent policy review"
        ]
        expected_review_milestone = {
            "status": "approve_merged",
            "reviewed_pr": 105,
            "reviewed_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
            "review_pr": 107,
            "review_head_sha": "f3cf2131798f8bf3bd319b21480dca196517f3fe",
            "review_merge_commit": "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6",
            "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
            "verdict": "approve",
            "critical_findings": 0,
            "high_findings": 0,
            "policy_adopted_by_review": False,
        }
        if len(review_milestones) != 1 or any(
            review_milestones[0].get(key) != value for key, value in expected_review_milestone.items()
        ):
            failures.append("ADR-0015 merged review milestone binding changed")
    if pair in {ADR0015_IMPLEMENTATION_PAIR, ADR0015_CONTROLLED_INTEGRATION_PAIR}:
        integration = pair == ADR0015_CONTROLLED_INTEGRATION_PAIR
        adoption = state.get("adr0015_conditional_adoption", {})
        expected_adoption = {
            "status": "accepted_for_generic_policy_implementation_and_exact_head_implementation_review_only_merged",
            "branch": "codex/adr-0015-conditional-adoption",
            "pr": 108,
            "head_sha": "01d98b60ce8a9a0b33082777c946cec70d380fc7",
            "merge_commit": "141481fa445bdc03b453844a666dbd2639c3cdf7",
            "main_validation_run": 29554620941,
            "main_validation_conclusion": "success",
            "adopted_semantic_body_hash": "c3d5f605ec26161f1bedc6961ac6f326d00582f9c3dcaa9de68c226961a34149",
            "adoption_content_hash": "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19",
            "reviewed_draft_head_sha": "03d2b8736abab277e60db1153ba73f0899d7696f",
            "review_pr": 107,
            "review_head_sha": "f3cf2131798f8bf3bd319b21480dca196517f3fe",
            "review_merge_commit": "1573abf2bef7d02df6c3b0624ee25cd3557ff2c6",
            "review_content_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
            "generic_policy_implementation_authorized_after_merge": True,
            "fixture_validation_authorized_after_merge": True,
            "fault_injection_authorized_after_merge": True,
            "exact_head_implementation_review_required": True,
            "production_pipeline_modified_in_adoption": False,
            "public_data_run_executed": False,
            "fixed_range_public_requalification_authorized": False,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if adoption != expected_adoption:
            failures.append("merged ADR-0015 adoption state binding changed")
        implementation = state.get("adr0015_invalid_interval_policy_implementation", {})
        expected_implementation = {
            "status": (
                "implementation_exact_head_approved_controlled_integration_pending_gate"
                if integration
                else "implementation_pass_fixture_only_pending_exact_head_review"
            ),
            "branch": (
                "codex/adr-0015-invalid-interval-controlled-integration"
                if integration
                else "codex/adr-0015-invalid-interval-implementation"
            ),
            "pr": "runtime_current_pr",
            "head_sha": "runtime_current_pr_head",
            "base_main_sha": "141481fa445bdc03b453844a666dbd2639c3cdf7",
            "report": "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md",
            "policy_config": "config/liquid_spot_invalid_interval_policy_v1.json",
            "policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
            "algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
            "fixture_only": True,
            "fault_cases": 16,
            "full_active_slot_mask": True,
            "valid_minority_masked": True,
            "production_pipeline_code_modified": True,
            "public_data_run_executed": False,
            "fixed_range_public_requalification_authorized": False,
            "exact_head_implementation_review_required": not integration,
            "new_independent_audit_authorized": False,
            "u04_authorized": False,
            "m2_authorized": False,
        }
        if integration:
            expected_implementation.update({
                "reviewed_target_pr": 109,
                "reviewed_target_head_sha": "67e7d29eaed63a3edb903dd618184bc9f02c5748",
                "review_pr": 110,
                "review_merge_commit": "a02d4dfbe752bb7e26e8a7b41971a9f089ddc57f",
                "review_content_hash": "9a0736431f4df6e27ce0b8e35d28e90d22838aef684e78fbd4c76bd79efe5af1",
                "exact_head_implementation_review_complete": True,
            })
        if implementation != expected_implementation:
            failures.append("ADR-0015 implementation state binding changed")
    return failures


def main() -> int:
    state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8"))
    failures = validate(state)
    if failures:
        print("project_state_transition_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("project_state_transition_check PASS")
    print(f"current_phase={state['current_phase']}")
    print(f"current_status={state['current_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
