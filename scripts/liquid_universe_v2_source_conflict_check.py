#!/usr/bin/env python3
"""Verify committed U-03E adjudication evidence without network access."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.liquid_universe_source_conflicts import (  # noqa: E402
    scan_forbidden_repairs,
    verify_adjudication_document,
)
from liquid_universe_v2_source_conflict_probe import render_report  # noqa: E402

EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json"
REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_SOURCE_CONFLICT_ADJUDICATION_REPORT.md"
EXPECTED_BINDINGS = {
    "contract_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
    "source_manifest_hash": "928c3520028ddf5bfc1c03fe3185d5af4b9ad8fea0f327469d60f388a3f638cf",
    "qualification_summary_hash": "80cd0a88b6253f06aeb40bfe4123aa55f874ce31a40d2e94a46859b2aba8380c",
}
EXPECTED_EVIDENCE_HASH = "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b"
EXPECTED_CONFLICTS = {
    "U03E-BTTUSDT-1D-2019-01-NEGATIVE-BASE-VOLUME": {
        "classification": "official_monthly_daily_conflict",
        "sha256": "304382601fa91cd11ecdda83442850b35dd8c072875ef96d9871808179c4c724",
        "affected_rows": 1,
    },
    "U03E-BTTUSDT-1D-2019-02-NEGATIVE-BASE-VOLUME": {
        "classification": "official_monthly_daily_conflict",
        "sha256": "9d396d4bc1995456cf2f37a286c637c623420170e03a9c5c02db32f7c28907a5",
        "affected_rows": 4,
    },
    "U03E-AXSUSDT-1D-2026-02-10-DUPLICATE": {
        "classification": "exact_identical_duplicate",
        "sha256": "7f18d5a29f2e767389efce407d47a247dac3e0e309cef4a3b377040bddf001bf",
        "affected_rows": 2,
    },
}


def _check_conflict(conflict: dict) -> list[str]:
    failures: list[str] = []
    conflict_id = conflict.get("conflict_id")
    expected = EXPECTED_CONFLICTS.get(conflict_id)
    if expected is None:
        return [f"unexpected conflict: {conflict_id}"]
    if conflict.get("classification") != expected["classification"]:
        failures.append(f"{conflict_id}: classification changed")
    if conflict.get("monthly_archive", {}).get("zip_sha256") != expected["sha256"]:
        failures.append(f"{conflict_id}: official monthly SHA changed")
    if len(conflict.get("affected_rows", [])) != expected["affected_rows"]:
        failures.append(f"{conflict_id}: affected-row count changed")
    if conflict.get("current_remote_checksum_changed") is not False:
        failures.append(f"{conflict_id}: current archive is not the frozen archive")
    if conflict.get("same_contract_rerun_allowed") is not False:
        failures.append(f"{conflict_id}: same-contract rerun was enabled")
    if conflict.get("qualification_decision") != "blocked":
        failures.append(f"{conflict_id}: qualification no longer fails closed")

    findings = conflict.get("findings", {})
    if conflict.get("symbol") == "BTTUSDT":
        if conflict.get("duplicate_type") != "not_duplicate":
            failures.append(f"{conflict_id}: unexpected duplicate classification")
        if findings.get("negative_field") != "base_volume":
            failures.append(f"{conflict_id}: negative field changed")
        if findings.get("daily_and_two_rest_hosts_agree_on_positive_volume") is not True:
            failures.append(f"{conflict_id}: cross-source agreement missing")
        if findings.get("unsigned_64bit_eight_decimal_overflow_signature_all_rows") is not True:
            failures.append(f"{conflict_id}: overflow signature missing")
        if findings.get("parser_schema_bug_found") is not False:
            failures.append(f"{conflict_id}: unsupported parser-bug claim")
        if findings.get("same_month_schema_matches") is not True:
            failures.append(f"{conflict_id}: same-month schema comparator mismatch")
        if findings.get("affected_timestamp_duplicate_count") != 1:
            failures.append(f"{conflict_id}: negative row also has a duplicate timestamp")
        if findings.get("legal_same_timestamp_alternative_found") is not False:
            failures.append(f"{conflict_id}: unsupported legal alternative claim")
    else:
        if conflict.get("duplicate_type") != "byte_identical_duplicate":
            failures.append(f"{conflict_id}: top-level duplicate type changed")
        if findings.get("monthly_duplicate_type") != "byte_identical_duplicate":
            failures.append(f"{conflict_id}: monthly duplicate type changed")
        if findings.get("daily_duplicate_type") != "byte_identical_duplicate":
            failures.append(f"{conflict_id}: daily duplicate type changed")
        if findings.get("parser_created_duplicate") is not False:
            failures.append(f"{conflict_id}: duplicate misclassified as parser-created")
        if findings.get("rest_hosts_return_one_matching_row") is not True:
            failures.append(f"{conflict_id}: REST comparator evidence missing")
        if findings.get("ignored_because_not_top15") is not False:
            failures.append(f"{conflict_id}: non-membership incorrectly waived conflict")
    return failures


def _scan_sources() -> list[str]:
    failures: list[str] = []
    evidence_scripts = {
        "scripts/liquid_universe_v2_source_conflict_probe.py",
        "scripts/liquid_universe_v2_source_conflict_check.py",
    }
    for root_name in ("src", "scripts"):
        for path in sorted((ROOT / root_name).rglob("*.py")):
            relative = str(path.relative_to(ROOT))
            if relative in evidence_scripts:
                continue
            source = path.read_text(encoding="utf-8")
            failures.extend(
                scan_forbidden_repairs(
                    ast.parse(source),
                    source_name=relative,
                )
            )
    return failures


def main() -> int:
    failures: list[str] = []
    document = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    failures.extend(verify_adjudication_document(document))
    if document.get("content_hash") != EXPECTED_EVIDENCE_HASH:
        failures.append("adjudication evidence hash changed")
    for key, value in EXPECTED_BINDINGS.items():
        if document.get(key) != value:
            failures.append(f"binding changed: {key}")
    conflicts = document.get("content", {}).get("conflicts", [])
    if {item.get("conflict_id") for item in conflicts} != set(EXPECTED_CONFLICTS):
        failures.append("frozen conflict set changed")
    for conflict in conflicts:
        failures.extend(_check_conflict(conflict))
    content = document.get("content", {})
    if content.get("overall_decision") != "new_policy_adr_required":
        failures.append("overall decision is not new_policy_adr_required")
    if content.get("same_contract_rerun_authorized") is not False:
        failures.append("same-contract rerun was authorized")
    if any(content.get("authorizations", {}).values()):
        failures.append("research authorization matrix is not all false")
    if REPORT.read_text(encoding="utf-8") != render_report(document):
        failures.append("Markdown report does not exactly regenerate from evidence")
    failures.extend(_scan_sources())
    if (ROOT / "docs/decisions/ADR-0013-official-archive-row-conflict-policy.md").exists():
        failures.append("PR-A must not adopt or include ADR-0013")

    if failures:
        print("liquid_universe_v2_source_conflict_check FAIL")
        for failure in sorted(set(failures)):
            print(f"- {failure}")
        return 1
    print("liquid_universe_v2_source_conflict_check PASS")
    print(f"evidence_hash={document['content_hash']}")
    print("decision=new_policy_adr_required")
    print("same_contract_rerun_authorized=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
