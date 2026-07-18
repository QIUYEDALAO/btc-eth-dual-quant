#!/usr/bin/env python3
"""Validate the independent exact-head review of the U-04 paper protocol."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "reports/expert/evidence/u04_cross_sectional_paper_protocol_review_v1.json"
REPORT_PATH = ROOT / "reports/expert/U04_CROSS_SECTIONAL_PAPER_PROTOCOL_REVIEW.md"
EXPECTED_TARGET = "6523b83d6b6ba93771ec1bad15625eb191fa07be"
EXPECTED_BASE = "ab85814c4f242502681f4a68db750ad565ffeab9"
EXPECTED_PROTOCOL_HASH = "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6"
EXPECTED_REVIEW_HASH = "34fe2efdf4788b20b915f34b3b6442f60ddaa364103ae90b920dc2cacf9646b1"
EXPECTED_FILES = {
    "config/u04_cross_sectional_paper_protocol_v1.json": "6a5551e070d10cf0e159ab684ca03a343c9d7ceb46f61546ebc10be5a3e4439f",
    "reports/m1/U04_CROSS_SECTIONAL_PAPER_PROTOCOL.md": "8b50b3f27cd9836b3e2bf5f8e6f0187cfcd8319b9037477d094f990c40e9b933",
    "scripts/u04_cross_sectional_paper_protocol_check.py": "6dd4afd0cba5d46509d7e6a8dadf74680a09c4889b6b595341178b793e0d08fb",
    "scripts/u04_cross_sectional_paper_protocol_validate.sh": "389d4370d60a4deef325b2d95cc3cc31f9ae6e496558879cf8dc81347a8069c0",
    "tests/test_u04_cross_sectional_paper_protocol.py": "df5546f213e0d779084b0a58642874632c964230242a165726b4672b8c0f6189",
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
    if review.get("target_files") != EXPECTED_FILES:
        failures.append("target file bindings changed")
    dimensions = review.get("review_dimensions", [])
    if len(dimensions) != 13 or [item.get("id") for item in dimensions] != [f"U04-PR-{i:02d}" for i in range(1, 14)]:
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
            protocol = json.loads(git_bytes(EXPECTED_TARGET, "config/u04_cross_sectional_paper_protocol_v1.json"))
        except (ValueError, json.JSONDecodeError) as exc:
            failures.append(f"target protocol unavailable or invalid: {exc}")
        else:
            if protocol.get("content_hash") != EXPECTED_PROTOCOL_HASH:
                failures.append("target protocol content hash is not exact")
            if protocol.get("scope", {}).get("oos_opened") is not False:
                failures.append("target OOS is not sealed")
            enabled = {key for key, value in protocol.get("authorizations", {}).items() if value}
            if enabled != {"paper_protocol_frozen", "exact_head_independent_review"}:
                failures.append("target authorization exceeds protocol freeze/review")
    return failures


def validate_report() -> list[str]:
    report = REPORT_PATH.read_text(encoding="utf-8")
    markers = [
        f"Target: `{EXPECTED_TARGET}`", "Verdict: `approve`",
        "Remaining critical/high findings: `0 / 0`", "Target modified by review: no",
        "authorizes only a separate data-qualification and isolation task",
    ]
    return [f"review report missing: {marker}" for marker in markers if marker not in report]


def main() -> int:
    failures = validate(load(REVIEW_PATH)) + validate_report()
    if failures:
        print("u04_cross_sectional_paper_protocol_review_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u04_cross_sectional_paper_protocol_review_check PASS")
    print(f"target={EXPECTED_TARGET} review_hash={EXPECTED_REVIEW_HASH} verdict=approve critical=0 high=0")
    print("authorized_next=data_qualification events=no paths=no returns=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
