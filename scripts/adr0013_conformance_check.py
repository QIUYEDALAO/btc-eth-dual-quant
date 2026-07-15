#!/usr/bin/env python3
"""Verify ADR-0013 satisfies the merged independent-review conditions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs/decisions/ADR-0013-official-archive-row-conflict-policy.md"
REVIEW = ROOT / "reports/expert/evidence/adr0013_independent_review.json"

EXPECTED_REVIEW_HASH = "c964048091870270344a9139b7656b3f35cb02925fc725a7c03fa0b2c65dd7d3"
EXPECTED_ADJUDICATION_HASH = "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b"


def verify_adr_text(text: str) -> list[str]:
    failures: list[str] = []
    for change_id in range(1, 11):
        if f"## A{change_id}:" not in text:
            failures.append(f"missing mandatory section: A{change_id}")
    required = (
        "Status: Accepted for V3 implementation and U-03E requalification only",
        "config/liquid_spot_source_conflict_resolutions_v3.json",
        "Qualification must never query live REST",
        "group all rows by the canonical row key",
        "symbol, interval, open_time UTC",
        "quote_volume",
        "`ignore` is an authoritative equality field",
        "Two identical rows plus one different row block the entire key",
        "parsed canonical equality",
        "blocked_pending_adjudication",
        "raw_row_quarantine",
        "research_panel_quarantine",
        "canonical_source_resolution",
        "2020-01-01` through `2026-06",
        "conflict resolution registry hash",
        "authorization matrix",
        "evidence_commit",
        "reviewed_head_sha",
        "`head_sha` means the current PR head",
        "V3 contract implementation: true",
        "Conflict resolution registry implementation: true",
        "U-03E V3 rerun: true",
    )
    for marker in required:
        if marker not in text:
            failures.append(f"missing conformance marker: {marker}")
    forbidden_authorizations = (
        "U-03F: true",
        "U-04: true",
        "Hypothesis preregistration: true",
        "Strategy code: true",
        "Event scan: true",
        "Returns/backtesting: true",
        "OOS: true",
        "API/trading: true",
        "M2: true",
    )
    for marker in forbidden_authorizations:
        if marker in text:
            failures.append(f"forbidden authorization: {marker}")
    for marker in (
        "U-03F: false",
        "U-04: false",
        "Hypothesis preregistration: false",
        "Strategy code: false",
        "Event scan: false",
        "Returns/backtesting: false",
        "OOS: false",
        "API/trading: false",
        "M2: false",
    ):
        if marker not in text:
            failures.append(f"missing denied authorization: {marker}")
    return failures


def main() -> int:
    failures = verify_adr_text(ADR.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    if review.get("content_hash") != EXPECTED_REVIEW_HASH:
        failures.append("independent review hash changed")
    if review.get("content", {}).get("verdict") != "approve_with_required_changes":
        failures.append("independent review verdict changed")
    if {item.get("id") for item in review.get("content", {}).get("mandatory_changes", [])} != {
        f"A{index}" for index in range(1, 11)
    }:
        failures.append("independent review mandatory-change set changed")
    if review.get("reviewed_artifacts", {}).get("adjudication_evidence_hash") != EXPECTED_ADJUDICATION_HASH:
        failures.append("adjudication evidence binding changed")
    if failures:
        print("ADR0013_CONFORMANCE_CHECK FAIL")
        for failure in sorted(set(failures)):
            print(f"- {failure}")
        return 1
    print("ADR0013_CONFORMANCE_CHECK PASS")
    print(f"independent_review_hash={EXPECTED_REVIEW_HASH}")
    print(f"adjudication_evidence_hash={EXPECTED_ADJUDICATION_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
