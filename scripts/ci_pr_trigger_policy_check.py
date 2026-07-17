#!/usr/bin/env python3
"""Validate selective PR CI and main/manual historical workflow routing."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
PR_WORKFLOW = WORKFLOWS / "pr-selective-validate.yml"
MAIN_WORKFLOW = WORKFLOWS / "main-regression.yml"


def validate() -> list[str]:
    failures: list[str] = []
    files = sorted(WORKFLOWS.glob("*.yml"))
    pull_request_files: list[str] = []
    push_files: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(ROOT))
        if "pull_request:" in text or "pull_request," in text or ", pull_request" in text:
            pull_request_files.append(relative)
        if "push:" in text:
            push_files.append(relative)
        if path not in {PR_WORKFLOW, MAIN_WORKFLOW}:
            if "pull_request:" in text or "push:" in text:
                failures.append(f"historical workflow is not manual-only: {relative}")
            if "workflow_dispatch:" not in text:
                failures.append(f"historical workflow lacks manual trigger: {relative}")

    expected = [str(PR_WORKFLOW.relative_to(ROOT))]
    if pull_request_files != expected:
        failures.append(f"pull_request routing must be selective-only: {pull_request_files}")
    expected_push = [str(MAIN_WORKFLOW.relative_to(ROOT))]
    if push_files != expected_push:
        failures.append(f"push routing must be main-regression-only: {push_files}")

    pr_text = PR_WORKFLOW.read_text(encoding="utf-8") if PR_WORKFLOW.exists() else ""
    for marker in (
        "cancel-in-progress: true",
        "PR_BASE_SHA:",
        "bash scripts/pr_ci_selective_validate.sh",
    ):
        if marker not in pr_text:
            failures.append(f"selective PR workflow missing marker: {marker}")

    main_text = MAIN_WORKFLOW.read_text(encoding="utf-8") if MAIN_WORKFLOW.exists() else ""
    for marker in (
        "branches: [main]",
        "cancel-in-progress: true",
        "github.event.before",
        "bash scripts/pr_ci_selective_validate.sh",
    ):
        if marker not in main_text:
            failures.append(f"main regression workflow missing marker: {marker}")

    selector = (ROOT / "scripts/pr_ci_selective_validate.sh").read_text(encoding="utf-8")
    for marker in (
        "bash scripts/project_validate.sh",
        "scripts/m0_secret_scan.py",
        "scripts/*_validate.sh",
        "workflow_body_changed",
        '"$validator" != scripts/pr_ci_selective_validate.sh',
        "ci_pr_trigger_policy_check.py",
        "git diff --check",
    ):
        if marker not in selector:
            failures.append(f"selective PR script missing marker: {marker}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("ci_pr_trigger_policy_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ci_pr_trigger_policy_check PASS")
    print("pull_request_workflows=1 main_push_workflows=1 historical_automatic_workflows=0 cancel_in_progress=yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
