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
        if item.get("id") in {"U-03D", "U-03E", "U-03E-ADJ", "ADR-0013-REVIEW", "ADR-0013-ADOPT", "U-03E-V3-IMPL", "U-03E-V3-RUN", "U-03E-V3-ADJ", "ADR-0014-DRAFT", "U-03F"}
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
    elif expected_task and not any(item.get("id") == expected_task for item in active):
        failures.append(f"current V2 task missing from open_work: {expected_task}")
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
    if any("U-04" == item.get("id") and item.get("status") != "not_authorized" for item in open_work):
        failures.append("U-04 authorized without a separate post-audit task")
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
