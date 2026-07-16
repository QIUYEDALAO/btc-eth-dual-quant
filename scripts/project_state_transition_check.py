#!/usr/bin/env python3
"""Validate exact V2 qualification phases and authorization transitions."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
import yaml

ALLOWED = {
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

CLOSED_TASK_PAIRS = {
    FAILED_U03F_CLOSEOUT_PAIR,
    REPAIR_CHAIN_CLOSED_PAIR,
}

AUDIT_BLOCKED_PAIRS = {
    FAILED_U03F_CLOSEOUT_PAIR,
    REPAIR_REQUALIFICATION_BLOCKED_PAIR,
    REPAIR_CHAIN_CLOSED_PAIR,
    INVALID_INTERVAL_PROTOCOL_PAIR,
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


def validate(state: dict) -> list[str]:
    failures = []
    pair = (state.get("current_phase"), state.get("current_status"))
    expected_task = ALLOWED.get(pair)
    if expected_task is None:
        failures.append(f"unsupported V2 phase/status pair: {pair}")
    if state.get("research_authorizations") != EXPECTED_AUTH:
        failures.append("research authorization matrix changed")
    open_work = state.get("open_work", [])
    active = [
        item
        for item in open_work
        if item.get("id") in {"U-03D", "U-03E", "U-03E-ADJ", "ADR-0013-REVIEW", "ADR-0013-ADOPT", "U-03E-V3-IMPL", "U-03E-V3-RUN", "U-03E-V3-ADJ", "ADR-0014-DRAFT", "ADR-0014-REVIEW", "ADR-0014-ADOPT", "U-03E-V4-IMPL", "U-03E-V4-RUN", "U-03F", "U-03F-REPAIR-REQUALIFICATION", "U-03F-R2-PROTOCOL"}
    ]
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
    if pair[0] in {
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
    if pair[0] in {
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
            if item.get("protocol_content_hash") != "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190":
                failures.append("invalid-interval protocol hash changed")
            if item.get("diagnostic_executed") is not False:
                failures.append("invalid-interval diagnostic ran before protocol merge")
            if item.get("production_pipeline_modified") is not False:
                failures.append("production pipeline changed in protocol task")
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
    if pair[0] in {
        "Liquid universe V4 public requalification passed; U-03F independent audit is the only authorized next task",
        "U-03F V4 independent audit protocol frozen pending review",
        "U-03F V4 independent auditor implementation pending independent review",
        "U-03F V4 independent auditor approved and merged; real offline audit authorized not started",
        "U-03F V4 independent audit failed pending truthful result review",
        "Liquid universe V4 independent audit failed or blocked",
        "U-03F V4 repair public requalification blocked",
        "U-03F V4 repair chain closed blocked",
        "U-03F V4 invalid-interval adjudication protocol frozen pending review",
    }:
        milestones = [
            item
            for item in state.get("completed_milestones", [])
            if item.get("phase") == "Liquid universe V4 fixed-range public requalification"
        ]
        expected_milestone = {
            "status": (
                "pass_revalidation_required_after_failed_independent_audit"
                if pair in AUDIT_BLOCKED_PAIRS
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
        if pair not in AUDIT_BLOCKED_PAIRS:
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
    if pair in AUDIT_BLOCKED_PAIRS:
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
    if any("U-04" == item.get("id") and item.get("status") != "not_authorized" for item in open_work):
        failures.append("U-04 authorized without a separate post-audit task")
    if pair == INVALID_INTERVAL_PROTOCOL_PAIR:
        protocol = state.get("u03f_v4_invalid_interval_adjudication_protocol", {})
        expected_protocol = {
            "status": "frozen_before_diagnostic_run_pending_review",
            "starting_main_sha": "3ba411d28563526a5357e3882a1e5759311f6179",
            "branch": "codex/u03f-v4-invalid-interval-protocol",
            "pr": "pending",
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
