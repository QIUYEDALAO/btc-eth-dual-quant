#!/usr/bin/env python3
"""Validate the independent exact-head review of the U-05 Paper protocol."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "reports/expert/evidence/u05_cross_sectional_paper_protocol_review_v1.json"
REPORT_PATH = ROOT / "reports/expert/U05_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
EXPECTED_TARGET = "8d8652796e22a15285ba682b4524baa0218ca5a6"
EXPECTED_BASE = "f66dcbdf5ad48b35e7bba2f112257e446563288c"
EXPECTED_PROTOCOL_HASH = "c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214"
EXPECTED_REVIEW_HASH = "8602f209c3e80ea31b4b1175967acfba2bb20252254d3fbdf5cc72ea128d914f"
EXPECTED_FILES = {
    "config/u05_cross_sectional_paper_protocol_v1.json": "7a6c5e5ef9bc4d61d2da9712d3801d0438dff299cece3836f34de4661e9ed9e0",
    "reports/m1/U05_CROSS_SECTIONAL_PAPER_PROTOCOL.md": "f926c75c0e662a3cbe1b01686ac7573cb513263c3a5ca4b92be115ccc5c33617",
    "scripts/u05_cross_sectional_paper_protocol_check.py": "e699ef06be85049e2aa81a4fdb714032c02cece9858d07548875f723cdabdf05",
    "scripts/u05_cross_sectional_paper_protocol_validate.sh": "218e33a8c9d3c42bfa2489dff314a877779427946c5f63331634bd10981480d7",
    "tests/test_u05_cross_sectional_paper_protocol.py": "16094f3476db30714fdfce8a63d146a141669695ec4b144ece397248978acfa5",
}
EXPECTED_AUTHORIZATIONS = {
    "data_qualification": True, "event_scan": False, "path_observation": False,
    "formal_returns": False, "fixed_rule_contract": False,
    "freqtrade_strategy_code": False, "backtesting": False, "oos": False,
    "api_trading": False, "execution_live": False, "m2": False,
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    return value


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def git_bytes(commit: str, rel_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{rel_path}"], cwd=ROOT,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"exact target file unavailable: {rel_path}")
    return result.stdout


def validate(review: Mapping[str, Any], *, verify_git: bool = True) -> list[str]:
    failures: list[str] = []
    identity = {key: value for key, value in review.items() if key not in {"review_content_hash", "generated_utc"}}
    if review.get("review_content_hash") != EXPECTED_REVIEW_HASH or canonical_hash(identity) != EXPECTED_REVIEW_HASH:
        failures.append("review content identity changed")
    target = review.get("target", {})
    if target.get("head_commit") != EXPECTED_TARGET or target.get("base_commit") != EXPECTED_BASE:
        failures.append("exact target or base changed")
    if target.get("protocol_content_hash") != EXPECTED_PROTOCOL_HASH:
        failures.append("target protocol hash changed")
    if target.get("candidate_id") != "U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE":
        failures.append("candidate identity changed")
    if review.get("target_files") != EXPECTED_FILES:
        failures.append("target file bindings changed")
    dimensions = review.get("review_dimensions", [])
    if len(dimensions) != 13 or [item.get("id") for item in dimensions] != [f"U05-PR-{i:02d}" for i in range(1, 14)]:
        failures.append("review dimensions changed or are incomplete")
    if any(item.get("result") != "pass" for item in dimensions):
        failures.append("not every review dimension passes")
    if review.get("findings") != [] or review.get("verdict") != "approve":
        failures.append("review verdict or findings changed")
    if review.get("remaining_critical_findings") != 0 or review.get("remaining_high_findings") != 0:
        failures.append("approve requires zero critical and high findings")
    if review.get("target_modified_by_review") is not False:
        failures.append("review must not modify target")
    if review.get("authorizations") != EXPECTED_AUTHORIZATIONS:
        failures.append("only data qualification may be authorized")

    if verify_git:
        parent = subprocess.run(
            ["git", "rev-parse", f"{EXPECTED_TARGET}^"], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        if parent.returncode or parent.stdout.strip() != EXPECTED_BASE:
            failures.append("target parent is unavailable or changed")
        for rel_path, digest in EXPECTED_FILES.items():
            try:
                actual = hashlib.sha256(git_bytes(EXPECTED_TARGET, rel_path)).hexdigest()
            except ValueError as exc:
                failures.append(str(exc))
                continue
            if actual != digest:
                failures.append(f"exact target file drifted: {rel_path}")
        try:
            protocol = json.loads(git_bytes(EXPECTED_TARGET, "config/u05_cross_sectional_paper_protocol_v1.json"))
        except (ValueError, json.JSONDecodeError) as exc:
            failures.append(f"target protocol unavailable or invalid: {exc}")
        else:
            if protocol.get("content_hash") != EXPECTED_PROTOCOL_HASH:
                failures.append("target protocol content hash is not exact")
            if protocol.get("scope", {}).get("oos_opened") is not False:
                failures.append("target OOS is not sealed")
            if protocol.get("breadth_event", {}).get("breadth_integer_gate") != "positive_member_count_times_5_greater_than_or_equal_to_active_member_count_times_4":
                failures.append("target integer breadth Gate drifted")
            if protocol.get("breadth_event", {}).get("common_move_minimum") != "0.0120":
                failures.append("target common-move threshold drifted")
            enabled = {key for key, value in protocol.get("authorizations", {}).items() if value}
            if enabled != {"paper_protocol_frozen", "exact_head_independent_review"}:
                failures.append("target authorization exceeds protocol freeze/review")
    return failures


def validate_report() -> list[str]:
    report = REPORT_PATH.read_text(encoding="utf-8")
    markers = [
        f"Target: `{EXPECTED_TARGET}`", "Verdict: `approve`",
        "Remaining critical/high findings: `0 / 0`", "Target modified by review: no",
        "authorizes only a separate frozen-source data-qualification",
    ]
    return [f"review report missing: {marker}" for marker in markers if marker not in report]


def main() -> int:
    failures = validate(load(REVIEW_PATH)) + validate_report()
    if failures:
        print("u05_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u05_cross_sectional_paper_protocol_review_check PASS")
    print(f"target={EXPECTED_TARGET} review_hash={EXPECTED_REVIEW_HASH} verdict=approve critical=0 high=0")
    print("authorized_next=data_qualification events=no paths=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
