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

    for rel_path in ("PROJECT_LEDGER.md", "NEXT_ACTION.md", "reports/INDEX.md", "AGENTS.md"):
        if not (ROOT / rel_path).exists():
            failures.append(f"required file missing: {rel_path}")

    next_action_text = (ROOT / "NEXT_ACTION.md").read_text(encoding="utf-8") if (ROOT / "NEXT_ACTION.md").exists() else ""
    for required in ("M1B numerical", "public data", "Do not enter M2"):
        if required not in next_action_text:
            failures.append(f"NEXT_ACTION.md must contain: {required}")

    ledger_text = (ROOT / "PROJECT_LEDGER.md").read_text(encoding="utf-8") if (ROOT / "PROJECT_LEDGER.md").exists() else ""
    for required in ("PR #5 Suitability Conclusion B Accepted", "Conclusion B accepted"):
        if required not in ledger_text:
            failures.append(f"PROJECT_LEDGER.md must contain: {required}")

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").exists() else ""
    if "PROJECT_STATE.yaml" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_STATE.yaml")
    if "PROJECT_LEDGER.md" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_LEDGER.md")

    allowed_next_work = [str(item) for item in state.get("allowed_next_work", [])]
    if not any("M1B numerical" in item for item in allowed_next_work):
        failures.append("PROJECT_STATE.yaml allowed_next_work must include M1B numerical")

    current_status = str(state.get("current_status", ""))
    if "pr5_suitability_conclusion_b_accepted" not in current_status:
        failures.append("PROJECT_STATE.yaml current_status must include pr5_suitability_conclusion_b_accepted")

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
