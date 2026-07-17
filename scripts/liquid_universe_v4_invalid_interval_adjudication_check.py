#!/usr/bin/env python3
"""Validate the frozen U-03F V4 invalid-interval diagnostic evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports/m0/evidence/liquid_universe_v4_invalid_interval_adjudication"
REPORT_PATH = ROOT / "reports/m0/U03F_V4_INVALID_INTERVAL_ADJUDICATION_REPORT.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER = load_module(
    "u03f_v4_invalid_interval_adjudication_runner",
    ROOT / "scripts/liquid_universe_v4_invalid_interval_adjudication.py",
)
PROTOCOL_CHECK = load_module(
    "u03f_v4_invalid_interval_adjudication_protocol_check",
    ROOT / "scripts/u03f_v4_invalid_interval_protocol_check.py",
)

EXPECTED_CONTENT_HASHES = {
    "authorization_matrix": "3188ac4696e74ad8c7bb2b0971b589b8c2d5c569db803fb56c557cdfd281418c",
    "diagnostic_run_manifest": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
    "input_binding_summary": "d07c7b0066976f0581163a3705897e29a12f7c4751cec8d6a74b54e77ad86468",
    "invalid_interval_rows": "d93f1004e082f42dcf13ed57f6b129949d092c7d73b0fc700001ec72c685623c",
    "order_determinism_summary": "1cd7b74215b701783f9879029bb9ecda095b8f7ff1a770f6190191841f02bf2e",
    "policy_gap_assessment": "28ee2769a103d36435a8988fab94860e33833e618e1fb0071adfdf4a45432d26",
    "synchronized_window_summary": "05a531735a326fa5c2472a322a9618559ca76472fb917a9c957ffaae2779ae98",
}

EXPECTED_FILE_HASHES = {
    "authorization_matrix.json": "b7e55b65fc19b43834217d123b7987706bfa183ea6182b248772040e600f2d83",
    "diagnostic_run_manifest.json": "ef768648f8cd8c60d40b617fcad1773e77bc89d318489f09df1ba9e15215c38f",
    "input_binding_summary.json": "85b23d98841e51182830c9141864f754bdd5cd84b6c1d91815bc8fbbae4b4fda",
    "invalid_interval_rows.json": "7dcd57fc0c9ff5fcf6976e21e0374971d919162c620ba21be54f8b6a27e519b9",
    "order_determinism_summary.json": "06eb7c7c6c01949779662249dba2e954dc8daeddb400948d63e262b2d41a630b",
    "policy_gap_assessment.json": "d311bdb03e9c92e339c17c4c2fb6d5818d482a4e3fe0d9ddcb8529e2c7f5543c",
    "synchronized_window_summary.json": "d0ec2a886135ae343507ee8a167d2037a0d10516ed48cb4dd5597952d9f27bdb",
}

EXPECTED_REPORT_SHA256 = "ff2b60c1e6a5d0fb0de8b07f39c0bec185f2818ab26d810559b50e24df1ca29c"
EXPECTED_DIAGNOSTIC_HASH = "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677"
EXPECTED_WINDOW_COUNTS = (15, 15, 15, 15, 15, 15, 14, 15)
EXPECTED_WINDOW_TIMES = (
    "2020-02-19T11:35:00.000Z",
    "2020-03-04T09:20:00.000Z",
    "2020-12-21T14:05:00.000Z",
    "2021-02-11T03:40:00.000Z",
    "2021-04-25T04:00:00.000Z",
    "2021-08-13T01:55:00.000Z",
    "2021-12-24T04:55:00.000Z",
    "2023-03-24T12:35:00.000Z",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_documents() -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for filename in EXPECTED_FILE_HASHES:
        name = filename.removesuffix(".json")
        output[name] = RUNNER.strict_json(EVIDENCE_DIR / filename)
    return output


def validate_wrappers(documents: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for name, document in documents.items():
        if document.get("schema_version") != 1:
            failures.append(f"schema version changed: {name}")
        if document.get("generated_utc") != "2026-07-17T00:00:00Z":
            failures.append(f"generated time changed: {name}")
        actual = RUNNER.content_hash(document.get("content"))
        if actual != document.get("content_hash"):
            failures.append(f"self content hash mismatch: {name}: {actual}")
        if document.get("content_hash") != EXPECTED_CONTENT_HASHES[name]:
            failures.append(f"frozen content hash changed: {name}")
    return failures


def validate_bindings(documents: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    try:
        _, freeze, membership, summary = RUNNER.validate_inputs()
    except RUNNER.DiagnosticMismatch as exc:
        return [f"immutable input mismatch: {exc}"]
    bindings = documents["input_binding_summary"]["content"]
    expected = RUNNER.input_bindings(freeze=freeze, membership=membership)
    if bindings != expected:
        failures.append("input binding summary changed")

    rows = documents["invalid_interval_rows"]["content"]
    known = RUNNER.expected_blockers(summary)
    identities = [(row.get("symbol"), row.get("month")) for row in rows]
    if len(rows) != 119 or set(identities) != known or len(set(identities)) != 119:
        failures.append("119 frozen invalid-row identities changed")

    archives = {
        item["canonical_key"]: item for item in freeze["content"]["archives"]
    }
    for row in rows:
        entry = archives.get(row.get("canonical_key"))
        if entry is None:
            failures.append(f"row archive is not frozen: {row.get('canonical_key')}")
            continue
        if row.get("archive_sha256") != entry.get("sha256"):
            failures.append(f"row archive SHA changed: {row.get('canonical_key')}")
        if row.get("archive_byte_size") != entry.get("byte_size"):
            failures.append(f"row archive size changed: {row.get('canonical_key')}")
        if not isinstance(row.get("line_number"), int) or row["line_number"] < 1:
            failures.append("invalid source line provenance")
        raw_hash = row.get("raw_row_sha256")
        if not isinstance(raw_hash, str) or len(raw_hash) != 64:
            failures.append("invalid raw-row SHA provenance")
    return failures


def validate_diagnostic(documents: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    rows = documents["invalid_interval_rows"]["content"]
    membership = RUNNER.strict_json(RUNNER.MEMBERSHIP_PATH)
    expected_windows = RUNNER.synchronized_windows(
        rows, RUNNER.membership_map(membership)
    )
    windows = documents["synchronized_window_summary"]["content"]
    if windows != expected_windows:
        failures.append("synchronized windows do not derive exactly from rows")
    if tuple(item.get("open_time_utc") for item in windows) != EXPECTED_WINDOW_TIMES:
        failures.append("frozen synchronized window times changed")
    if tuple(item.get("invalid_member_count") for item in windows) != EXPECTED_WINDOW_COUNTS:
        failures.append("frozen synchronized window counts changed")
    if not all(item.get("synchronous_candidate") is True for item in windows):
        failures.append("a frozen window no longer meets the synchronous Gate")

    expected_policy = RUNNER.policy_assessment(rows=rows, windows=windows)
    policy = documents["policy_gap_assessment"]["content"]
    if policy != expected_policy or policy.get("decision") != "new_policy_adr_required":
        failures.append("policy-gap assessment changed")
    if policy.get("direct_existing_gap_policy_adoption_allowed") is not False:
        failures.append("direct existing-policy adoption was enabled")
    if policy.get("per_row_exception_registry_allowed") is not False:
        failures.append("per-row exceptions were enabled")

    authorization = documents["authorization_matrix"]["content"]
    if authorization != RUNNER.authorization_matrix():
        failures.append("authorization matrix changed")

    order = documents["order_determinism_summary"]["content"]
    if order.get("canonical_diagnostic_content_hash") != EXPECTED_DIAGNOSTIC_HASH:
        failures.append("canonical diagnostic content hash changed")
    order_rows = order.get("orders", [])
    if [item.get("name") for item in order_rows] != [
        "normal", "reverse", "deterministic_shuffled"
    ]:
        failures.append("diagnostic orders changed")
    if any(
        item.get("status") != "pass"
        or item.get("content_hash") != EXPECTED_DIAGNOSTIC_HASH
        for item in order_rows
    ):
        failures.append("three-order determinism evidence changed")
    return failures


def validate_run_and_report(documents: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    run = documents["diagnostic_run_manifest"]
    content = run["content"]
    component_hashes = {
        name: documents[name]["content_hash"] for name in RUNNER.OUTPUT_NAMES
    }
    if content.get("component_hashes") != component_hashes:
        failures.append("run component binding changed")
    if content.get("status") != "completed_new_policy_adr_required":
        failures.append("diagnostic run status changed")
    if content.get("decision") != "new_policy_adr_required":
        failures.append("diagnostic run decision changed")
    if content.get("invalid_physical_rows") != 119 or content.get("synchronized_windows") != 8:
        failures.append("diagnostic run counts changed")
    if content.get("diagnostic_content_hash") != EXPECTED_DIAGNOSTIC_HASH:
        failures.append("diagnostic run canonical hash changed")

    render_documents = {
        name: documents[name] for name in RUNNER.OUTPUT_NAMES
    }
    expected_report = RUNNER.render_report(render_documents, run)
    actual_report = REPORT_PATH.read_text(encoding="utf-8")
    if actual_report != expected_report:
        failures.append("Markdown is not the exact machine render")
    if sha256(REPORT_PATH) != EXPECTED_REPORT_SHA256:
        failures.append("frozen diagnostic report SHA changed")
    return failures


def main() -> int:
    failures: list[str] = []
    protocol = PROTOCOL_CHECK.load_protocol()
    failures.extend(PROTOCOL_CHECK.validate_protocol(protocol))
    failures.extend(PROTOCOL_CHECK.validate_immutable_inputs(protocol))
    for filename, expected in EXPECTED_FILE_HASHES.items():
        path = EVIDENCE_DIR / filename
        if not path.is_file():
            failures.append(f"missing evidence file: {filename}")
        elif sha256(path) != expected:
            failures.append(f"frozen evidence file SHA changed: {filename}")
    if failures:
        print("liquid_universe_v4_invalid_interval_adjudication_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    documents = load_documents()
    failures.extend(validate_wrappers(documents))
    failures.extend(validate_bindings(documents))
    failures.extend(validate_diagnostic(documents))
    failures.extend(validate_run_and_report(documents))
    if failures:
        print("liquid_universe_v4_invalid_interval_adjudication_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("liquid_universe_v4_invalid_interval_adjudication_check PASS")
    print(f"diagnostic_content_hash={EXPECTED_DIAGNOSTIC_HASH}")
    print(f"run_content_hash={EXPECTED_CONTENT_HASHES['diagnostic_run_manifest']}")
    print("rows=119 synchronized_windows=8 decision=new_policy_adr_required")
    print("policy=no implementation=no requalification=no audit=no u04=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
