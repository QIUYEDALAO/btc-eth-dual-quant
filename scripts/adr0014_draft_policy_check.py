#!/usr/bin/env python3
"""Fail-closed static validation for the proposed ADR-0014 draft."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))

import yaml

from scripts.liquid_universe_v3_klay_conflict_check import validate as validate_klay_evidence


ADR = ROOT / "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md"
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json"
EXPECTED_KLAY_EVIDENCE_HASH = "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a"

REQUIRED_CONDITIONS = (
    "monthly and daily official archives are checksum verified and CRC valid",
    "monthly and daily raw rows and semantic rows are identical",
    "two frozen public REST comparators each return exactly one row identical to the archive row",
    "open = high = low = close",
    "base volume, quote volume, both taker volumes and trade count are all zero",
    "close_time is less than open_time",
    "affected open_time is not earlier than official cessation_time",
    "close_time equals official cessation_time minus exactly 1 millisecond",
    "the affected UTC day has no official intraday trading bars",
    "the final intraday close equals official cessation_time minus exactly 1 millisecond",
    "official lifecycle evidence is checksum/hash bound",
    "the row is not a parser bug, duplicate or archive republication",
    "similar-scope scan finds no broader unexplained schema defect",
)

REQUIRED_SHORTCUT_PROHIBITIONS = (
    "Do not rewrite close_time as open_time plus one day minus 1 millisecond.",
    "Do not construct a normal zero-volume candle.",
    "Do not replace the daily row with an intraday aggregation.",
    "Do not replace the archive row with REST data.",
    "Do not delete the raw row.",
    "Do not splice KLAY history into KAIA automatically.",
    "Do not add a symbol/date special case.",
    "Do not ignore the conflict because Top-15 membership is unchanged.",
    "Do not add the sixteenth-ranked asset after a mid-month cessation.",
    "Do not rewrite historical ranks or membership.",
    "Do not mutate a registry before policy adoption.",
    "Do not treat a lifecycle announcement as canonical data override authority.",
)

DENIED_AUTHORIZATIONS = (
    "Policy adopted: false",
    "Policy implemented: false",
    "Contract modified: false",
    "Registry modified: false",
    "V3/V4 requalification run: false",
    "U-03F: false",
    "U-04: false",
    "Hypothesis preregistration: false",
    "Strategy code: false",
    "Event scan: false",
    "Returns/backtesting: false",
    "OOS: false",
    "API/trading: false",
    "M2: false",
)


def verify_adr_text(text: str) -> list[str]:
    failures: list[str] = []
    for section in range(1, 7):
        if f"## B{section}:" not in text:
            failures.append(f"missing mandatory section: B{section}")
    if "Status: Proposed draft; not adopted" not in text:
        failures.append("ADR status is not proposed draft; not adopted")
    if EXPECTED_KLAY_EVIDENCE_HASH not in text:
        failures.append("KLAY adjudication evidence hash missing or changed")
    for marker in REQUIRED_CONDITIONS:
        if marker not in text:
            failures.append(f"missing eligibility condition: {marker}")
    for marker in REQUIRED_SHORTCUT_PROHIBITIONS:
        if marker not in text:
            failures.append(f"missing prohibited shortcut: {marker}")
    for marker in DENIED_AUTHORIZATIONS:
        if marker not in text:
            failures.append(f"missing denied authorization: {marker}")
        enabled = marker.replace(": false", ": true")
        if enabled in text:
            failures.append(f"forbidden authorization: {enabled}")
    for marker in (
        "official_lifecycle_boundary_placeholder",
        "raw_row_quarantine",
        "symbol_availability_boundary",
        "lifecycle_terminated",
        "no automatic KLAY/KAIA history splice",
        "versioned lifecycle resolution registry",
        "LIQUID-SPOT-USDT-TOP15-V4",
        "2020-01 through 2026-06",
        "cold, warm-cache and worker-variant",
        "V4 requalification PASS before U-03F",
        "U-03F PASS and separate authorization before U-04",
        "Any missing, unavailable, changed or contradictory condition remains blocked",
    ):
        if marker not in text:
            failures.append(f"missing draft policy marker: {marker}")
    for step in range(1, 11):
        if f"{step}. " not in text:
            failures.append(f"missing independent-review sequence step: {step}")
    return sorted(set(failures))


def verify_repository() -> list[str]:
    failures = verify_adr_text(ADR.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("content_hash") != EXPECTED_KLAY_EVIDENCE_HASH:
        failures.append("frozen KLAY evidence content hash changed")
    if evidence.get("classification") != "symbol_lifecycle_boundary_artifact":
        failures.append("frozen KLAY classification changed")
    if evidence.get("overall_decision") != "new_policy_adr_required":
        failures.append("frozen KLAY decision changed")
    failures.extend(validate_klay_evidence())

    state = yaml.safe_load((ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8"))
    expected_pair = (
        "ADR-0014 lifecycle-boundary placeholder policy draft pending independent review",
        "adr0014_proposed_draft_not_adopted_no_requalification_no_strategy_no_m2",
    )
    if (state.get("current_phase"), state.get("current_status")) != expected_pair:
        failures.append("PROJECT_STATE does not identify the proposed ADR-0014 review state")
    work = next((item for item in state.get("open_work", []) if item.get("id") == "ADR-0014-DRAFT"), None)
    if not work:
        failures.append("ADR-0014-DRAFT is missing from open_work")
    else:
        expected = {
            "status": "proposed_draft_pending_independent_review",
            "adopted": False,
            "implemented": False,
            "registry_change": False,
            "v3_rerun": False,
        }
        for key, value in expected.items():
            if work.get(key) != value:
                failures.append(f"ADR-0014 open_work {key} must be {value!r}")
    if any(state.get("research_authorizations", {}).values()):
        failures.append("research authorization matrix must remain all false")
    if list((ROOT / "config").glob("*adr0014*")):
        failures.append("ADR-0014 Draft created a config/implementation artifact")
    return sorted(set(failures))


def main() -> int:
    failures = verify_repository()
    if failures:
        print("ADR0014_DRAFT_POLICY_CHECK FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ADR0014_DRAFT_POLICY_CHECK PASS")
    print(f"klay_evidence_hash={EXPECTED_KLAY_EVIDENCE_HASH}")
    print("policy_adopted=false")
    print("requalification_run=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
