#!/usr/bin/env python3
"""Fail closed unless ADR-0015 integration preserves the reviewed implementation."""
from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REVIEWED_HEAD = "67e7d29eaed63a3edb903dd618184bc9f02c5748"
REVIEW_MERGE = "a02d4dfbe752bb7e26e8a7b41971a9f089ddc57f"
EXACT_FILES = (
    "config/liquid_spot_invalid_interval_policy_v1.json",
    "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md",
    "scripts/adr0015_invalid_interval_implementation_check.py",
    "scripts/adr0015_invalid_interval_implementation_validate.sh",
    "scripts/liquid_universe_v4_public_run.py",
    "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py",
    "tests/test_adr0015_invalid_interval_policy.py",
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def validate() -> list[str]:
    failures: list[str] = []
    for commit, label in ((REVIEWED_HEAD, "reviewed head"), (REVIEW_MERGE, "review merge")):
        if git("cat-file", "-e", f"{commit}^{{commit}}", check=False).returncode:
            failures.append(f"{label} is unavailable: {commit}")
            continue
        if git("merge-base", "--is-ancestor", commit, "HEAD", check=False).returncode:
            failures.append(f"{label} is not an ancestor of HEAD: {commit}")

    parents = git("rev-list", "--parents", "HEAD").stdout.splitlines()
    if not any(REVIEWED_HEAD in line.split()[1:] for line in parents):
        failures.append("no integration ancestor records the exact reviewed head as a parent")

    for path in EXACT_FILES:
        reviewed = git("rev-parse", f"{REVIEWED_HEAD}:{path}", check=False)
        current = git("rev-parse", f"HEAD:{path}", check=False)
        if reviewed.returncode or current.returncode:
            failures.append(f"required exact file is unavailable: {path}")
        elif reviewed.stdout.strip() != current.stdout.strip():
            failures.append(f"reviewed implementation blob drifted: {path}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("adr0015_invalid_interval_controlled_integration_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
