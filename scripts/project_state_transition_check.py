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
        "Liquid universe V2 qualification independently audited; hypothesis preregistration requires separate task",
        "liquid_universe_v2_qualification_audited_pass_no_hypothesis_no_oos_no_m2",
    ): "U-03F",
    (
        "Liquid universe V2 independent audit blocked",
        "liquid_universe_v2_independent_audit_blocked_no_strategy_no_m2",
    ): "U-03F",
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
    active = [item for item in open_work if item.get("id") in {"U-03D", "U-03E", "U-03F"}]
    if expected_task and not any(item.get("id") == expected_task for item in active):
        failures.append(f"current V2 task missing from open_work: {expected_task}")
    merged = {item.get("number") for item in state.get("latest_merged_prs", [])}
    for item in open_work:
        if isinstance(item.get("pr"), int) and item["pr"] in merged:
            failures.append(f"open_work references merged PR #{item['pr']}")
    if pair in list(ALLOWED)[:2] and any("U-04" == item.get("id") and item.get("status") != "not_authorized" for item in open_work):
        failures.append("U-04 authorized before independent audit")
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
