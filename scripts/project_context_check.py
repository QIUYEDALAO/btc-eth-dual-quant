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

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").exists() else ""
    if "PROJECT_STATE.yaml" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_STATE.yaml")
    if "PROJECT_LEDGER.md" not in agents_text:
        failures.append("AGENTS.md must mention PROJECT_LEDGER.md")

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
