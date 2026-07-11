#!/usr/bin/env python3
"""Validate the immutable strategy trial ledger without network access."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml


REQUIRED_RULES = {
    "candidate_queue_order_is_immutable",
    "dsr_trial_count_equals_opened_oos_candidates",
    "oos_opening_increments_trial_count",
    "oos_opening_is_single_use_per_hash",
    "post_freeze_rule_change_creates_new_candidate",
    "failed_or_rejected_candidates_are_append_only",
}
REQUIRED_CANDIDATE_FIELDS = {
    "id",
    "status",
    "hypothesis",
    "sha256",
    "oos_opened",
}


def validate_ledger(path: Path) -> list[str]:
    """Return deterministic validation failures for a trial ledger."""
    failures: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot read trial ledger: {exc}"]

    if not isinstance(data, dict):
        return ["trial ledger must parse to a mapping"]
    if data.get("version") != 1:
        failures.append("version must be 1")
    if data.get("hash_algorithm") != "sha256":
        failures.append("hash_algorithm must be sha256")

    rules = data.get("rules")
    if not isinstance(rules, dict):
        failures.append("rules must be a mapping")
    else:
        for rule in sorted(REQUIRED_RULES):
            if rules.get(rule) is not True:
                failures.append(f"required rule must be true: {rule}")

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        failures.append("candidates must be a non-empty list")
        return failures

    seen_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        label = f"candidate[{index}]"
        if not isinstance(candidate, dict):
            failures.append(f"{label} must be a mapping")
            continue

        missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
        if missing:
            failures.append(f"{label} missing fields: {', '.join(missing)}")

        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            failures.append(f"{label} id must be a non-empty string")
        elif candidate_id in seen_ids:
            failures.append(f"duplicate candidate id: {candidate_id}")
        else:
            seen_ids.add(candidate_id)

        for field in ("status", "hypothesis"):
            value = candidate.get(field)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{label} {field} must be a non-empty string")

        if not isinstance(candidate.get("oos_opened"), bool):
            failures.append(f"{label} oos_opened must be boolean")

        hypothesis = candidate.get("hypothesis")
        recorded_hash = candidate.get("sha256")
        if isinstance(hypothesis, str) and isinstance(recorded_hash, str):
            calculated = hashlib.sha256(hypothesis.encode("utf-8")).hexdigest()
            if recorded_hash != calculated:
                failures.append(
                    f"{label} sha256 mismatch: recorded={recorded_hash} calculated={calculated}"
                )
        elif "sha256" in candidate:
            failures.append(f"{label} sha256 must be a string")

    return failures


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
    failures = validate_ledger(path)
    if failures:
        print("strategy_trial_ledger_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("strategy_trial_ledger_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
