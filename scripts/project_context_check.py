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
    for required_pr in (6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 23, 25):
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

    for rel_path in (
        "PROJECT_LEDGER.md",
        "NEXT_ACTION.md",
        "reports/INDEX.md",
        "AGENTS.md",
        "PROJECT_EXECUTION_CHECKLIST.md",
    ):
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
        "Freqtrade-First Architecture Governance Merged",
        "M0 Audit Correctness Hardening Merged",
        "Freqtrade Primary Framework Hardening Started",
        "Freqtrade Primary Framework Hardening Merged",
        "M1B Event-Time Revalidation Started",
        "M1B Event-Time Revalidation Merged",
        "End-to-End Roadmap P0 Merged",
        "M1C Rotation P1 Design Started",
        "M1C Rotation P1 Design Merged",
        "M1C Rotation P2 Implementation Started",
        "M1C Rotation P2 Merged",
        "M1C Rotation P3 Validation Started",
        "M1C Rotation P3 Failed Validation Recorded",
        "M1C Rotation P3 Failed Validation Merged",
    ):
        if required not in ledger_text:
            failures.append(f"PROJECT_LEDGER.md must contain: {required}")

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").exists() else ""
    if "PROJECT_STATE.yaml" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_STATE.yaml")
    if "PROJECT_LEDGER.md" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_LEDGER.md")

    raw_allowed_next_work = state.get("allowed_next_work", [])
    if not isinstance(raw_allowed_next_work, list) or any(not isinstance(item, str) for item in raw_allowed_next_work):
        failures.append("PROJECT_STATE.yaml allowed_next_work must contain strings only")
        raw_allowed_next_work = []
    allowed_next_work = [str(item) for item in raw_allowed_next_work]
    current_phase = str(state.get("current_phase", ""))
    hypothesis_design_phase = current_phase.startswith(("U-04 ", "U-05 ", "U-06 ", "U-07 ", "U-08 ", "U-09 ", "U-10 ", "U-11 ", "U-12 ", "U-13 ", "U-14 ", "U-15 ", "U-16 ", "U-17 ", "U-18 "))
    if not hypothesis_design_phase and not any("diagnostic" in item.casefold() for item in allowed_next_work):
        failures.append("PROJECT_STATE.yaml allowed_next_work must include diagnostic scope")
    if not any(
        "design review" in item.casefold()
        or "draft policy adr" in item.casefold()
        or "hypothesis design" in item.casefold()
        or "protocol design" in item.casefold()
        or "exact-head independent review" in item.casefold()
        or "data qualification" in item.casefold()
        or "paper observation" in item.casefold()
        for item in allowed_next_work
    ):
        failures.append("PROJECT_STATE.yaml allowed_next_work must include design or Draft policy ADR scope")

    current_status = str(state.get("current_status", ""))
    m1b_history = [
        item
        for item in state.get("completed_milestones", [])
        if isinstance(item, dict) and item.get("phase") == "M1B funding-rate-arbitrage research validation"
    ]
    if not m1b_history or m1b_history[-1].get("status") != "failed_validation":
        failures.append("PROJECT_STATE.yaml must preserve the M1B failed_validation milestone")
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
