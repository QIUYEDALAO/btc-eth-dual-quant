#!/usr/bin/env python3
"""Print the current project context for task startup."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def main() -> int:
    state_path = ROOT / "PROJECT_STATE.yaml"
    data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("PROJECT_STATE.yaml is invalid")
        return 1

    print("Project Context Summary")
    print(f"- current_phase: {data.get('current_phase')}")
    print(f"- current_status: {data.get('current_status')}")
    print("- completed_milestones:")
    for item in _as_list(data.get("completed_milestones")):
        print(f"  - {item.get('phase')}: {item.get('status')}")
    print("- open_work:")
    for item in _as_list(data.get("open_work")):
        print(f"  - {item.get('id')}: {item.get('status')} ({item.get('blocker')})")
    print("- active_blockers:")
    for item in _as_list(data.get("open_work")):
        blocker = item.get("blocker")
        if blocker:
            print(f"  - {blocker}")
    print("- next_action:")
    for item in _as_list(data.get("allowed_next_work")):
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
