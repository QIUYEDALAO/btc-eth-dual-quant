#!/usr/bin/env python3
"""Validate repository-level context recovery files.

This script is intentionally local-only: no network calls, no API keys, and no
private-smoke access.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml


REQUIRED_FIELDS = {
    "project",
    "last_updated_utc",
    "current_phase",
    "current_status",
    "completed_milestones",
    "open_work",
    "active_decisions",
    "allowed_next_work",
    "prohibited",
    "latest_reports",
    "latest_tags",
    "latest_merged_prs",
    "required_context_files",
    "validation_commands",
}

REQUIRED_PROHIBITED = {
    "live trading",
    "paper trading with real API",
    "execution/live",
    "order placement",
    "API trading permissions",
    "API keys",
}


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("PROJECT_STATE.yaml must parse to a mapping")
    return data


def main() -> int:
    failures: list[str] = []
    state_path = ROOT / "PROJECT_STATE.yaml"

    try:
        state = _load_state(state_path)
    except Exception as exc:
        print(f"FAIL PROJECT_STATE.yaml: {exc}")
        return 1

    missing_fields = sorted(REQUIRED_FIELDS - set(state))
    if missing_fields:
        failures.append(f"PROJECT_STATE.yaml missing fields: {', '.join(missing_fields)}")

    for rel_path in state.get("required_context_files", []):
        if not (ROOT / str(rel_path)).exists():
            failures.append(f"required context file missing: {rel_path}")

    latest_reports = state.get("latest_reports", [])
    if not isinstance(latest_reports, list):
        failures.append("PROJECT_STATE.yaml latest_reports must be a list")
        latest_reports = []
    report_paths: list[str] = []
    for item in latest_reports:
        if not isinstance(item, dict):
            failures.append("PROJECT_STATE.yaml latest_reports items must be mappings")
            continue
        rel_path = str(item.get("path", ""))
        status = str(item.get("status", ""))
        marker = str(item.get("status_marker", ""))
        report_paths.append(rel_path)
        target = ROOT / rel_path
        if not rel_path or not target.is_file():
            failures.append(f"latest report missing: {rel_path or '<empty>'}")
            continue
        if not status:
            failures.append(f"latest report status missing: {rel_path}")
        if not marker:
            failures.append(f"latest report status_marker missing: {rel_path}")
        elif marker not in target.read_text(encoding="utf-8"):
            failures.append(f"latest report status_marker not found in {rel_path}: {marker}")
    if len(report_paths) != len(set(report_paths)):
        failures.append("PROJECT_STATE.yaml latest_reports contains duplicate paths")

    latest_tags = [str(item) for item in state.get("latest_tags", [])]
    if len(latest_tags) != len(set(latest_tags)):
        failures.append("PROJECT_STATE.yaml latest_tags contains duplicates")
    for required_tag in (
        "project-context-system-v0.4.0",
        "m1b-funding-failed-validation-v0.5.0",
        "post-m1b-review-no-m2-v0.6.0",
    ):
        if required_tag not in latest_tags:
            failures.append(f"PROJECT_STATE.yaml latest_tags missing: {required_tag}")

    merged_prs = state.get("latest_merged_prs", [])
    if not isinstance(merged_prs, list):
        failures.append("PROJECT_STATE.yaml latest_merged_prs must be a list")
        merged_prs = []
    merged_numbers = {
        int(item["number"])
        for item in merged_prs
        if isinstance(item, dict) and str(item.get("number", "")).isdigit()
    }
    if len(merged_numbers) != len(merged_prs):
        failures.append("PROJECT_STATE.yaml latest_merged_prs contains invalid or duplicate PR numbers")
    for required_pr in (6, 7):
        if required_pr not in merged_numbers:
            failures.append(f"PROJECT_STATE.yaml latest_merged_prs missing PR #{required_pr}")

    open_work = state.get("open_work", [])
    if not isinstance(open_work, list):
        failures.append("PROJECT_STATE.yaml open_work must be a list")
        open_work = []
    for item in open_work:
        if not isinstance(item, dict):
            failures.append("PROJECT_STATE.yaml open_work items must be mappings")
            continue
        pr_value = item.get("pr")
        if isinstance(pr_value, int) and pr_value in merged_numbers:
            failures.append(f"open_work references already merged PR #{pr_value}: {item.get('id')}")

    for rel_path in ("PROJECT_LEDGER.md", "NEXT_ACTION.md", "reports/INDEX.md", "AGENTS.md"):
        if not (ROOT / rel_path).exists():
            failures.append(f"required file missing: {rel_path}")

    next_action_text = (ROOT / "NEXT_ACTION.md").read_text(encoding="utf-8") if (ROOT / "NEXT_ACTION.md").exists() else ""
    for required in ("No strategy is eligible for M2", "Do not enter M2", "Freqtrade-first"):
        if required not in next_action_text:
            failures.append(f"NEXT_ACTION.md must contain: {required}")

    ledger_text = (ROOT / "PROJECT_LEDGER.md").read_text(encoding="utf-8") if (ROOT / "PROJECT_LEDGER.md").exists() else ""
    for required in (
        "M1B Failed Validation Merged",
        "Post-M1B Review Started",
        "Freqtrade-First Architecture Hardening Started",
    ):
        if required not in ledger_text:
            failures.append(f"PROJECT_LEDGER.md must contain: {required}")

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").exists() else ""
    if "PROJECT_STATE.yaml" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_STATE.yaml")
    if "PROJECT_LEDGER.md" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_LEDGER.md")

    allowed_next_work = [str(item) for item in state.get("allowed_next_work", [])]
    if not any("diagnostics" in item.casefold() for item in allowed_next_work):
        failures.append("PROJECT_STATE.yaml allowed_next_work must include diagnostics")
    if not any("design review" in item.casefold() for item in allowed_next_work):
        failures.append("PROJECT_STATE.yaml allowed_next_work must include design review")

    current_status = str(state.get("current_status", ""))
    if not (
        "pr5_suitability_conclusion_b_accepted" in current_status
        or "m1b_numerical_failed_validation_pending_review" in current_status
        or "m1b_failed_validation_recorded" in current_status
        or "no_strategy_eligible_for_m2" in current_status
        or "freqtrade_first_revalidation_required_no_m2" in current_status
    ):
        failures.append("PROJECT_STATE.yaml current_status must include PR #5 M1B numerical review status")
    if "m2" not in current_status and "m1b" not in current_status:
        failures.append("PROJECT_STATE.yaml current_status must include m1b or m2")

    prohibited = {str(item) for item in state.get("prohibited", [])}
    missing_prohibited = sorted(REQUIRED_PROHIBITED - prohibited)
    if missing_prohibited:
        failures.append(f"PROJECT_STATE.yaml prohibited missing: {', '.join(missing_prohibited)}")

    if failures:
        print("project_context_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("project_context_check PASS")
    print(f"current_phase={state.get('current_phase')}")
    print(f"current_status={state.get('current_status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
