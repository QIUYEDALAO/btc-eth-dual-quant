#!/usr/bin/env python3
"""Fail closed when the frozen U-03F protocol or its repository bindings drift."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/liquid_universe_v4_independent_audit_protocol.json"
REPORT_PATH = ROOT / "reports/m0/U03F_V4_INDEPENDENT_AUDIT_PROTOCOL.md"
EVIDENCE_DIR = ROOT / "reports/m0/evidence/liquid_universe_v4"

EXPECTED_MANIFEST_HASHES = {
    "V3_V4_diff": "32a944d4dbc5232e4a4ec91187722004e4db7ed4b434fde35662351145dc8d48",
    "active_universe_manifest": "416941b6c8f50472c4ec6fe0edf5070982f508bc68d803e03b7f94995898379d",
    "candidate_eligibility_manifest": "2d116eb8c22419f124a6865937b3a3e5adad4c6c3fefd4f81a3f93719b389d06",
    "complete_day_mask": "c7c497147ce5d00081dae5c4e5dd993447507ffe596fbfea10dc28880595a95f",
    "expected_grid_manifest": "38c1c703a80025307c83d5fe5bcdb1ce933ef8061bf61f96dd36d6b9ee8513ff",
    "lifecycle_event_quarantine_manifest": "c4930bb769c70e2f26cdd2cff25c80391fa254afc0d26d5dd1eca939d27f20a4",
    "lifecycle_policy_manifest": "9ba2dfdd310319475a719291c81eaf93930273732db169d997c9c8252a107f13",
    "lifecycle_resolution_registry": "adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef",
    "membership_manifest": "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5",
    "qualification_summary": "1c989a0d14ea7cbf461de6fb178f3b7238a5cd508972d518eef8610d14bd839b",
    "qualified_panel_manifest": "cc5299a52f11678ddbcee895b54ca20b3eba6079d814c802823c2a2843270ab5",
    "raw_row_quarantine_manifest": "ce97b4826e8305b7d28a27b6693dc120b5b1a8ce5a5cc8462581ace8f68bb4e3",
    "row_conflict_resolution_manifest": "0ed070e44351864473f13e1b127a3ab04464be13477776ec32abbedaf2beac15",
    "source_manifest": "b4dd05d6cb1375c3a6ec3781060e1179845155d3e7e91525921de5f0b9499b39",
    "symbol_availability_manifest": "1bf3eb5bfb403fbddb12970a2ea4c53963219766a49f0737e5f113023ef39f19",
}

EXPECTED_AUTHORITY = {
    "v4_contract_hash": "816a354a1fe20ebab4c162ecaefbde47a90d61567f40873e2b477a983d06ee83",
    "lifecycle_policy_hash": "7dc02e719f6e41839a1aff8002befd117b2daa7b426edeed9ebb4bd42c303977",
    "lifecycle_event_registry_hash": "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d",
    "klay_adjudication_evidence_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
    "v3_row_conflict_registry_hash": "570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4",
    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "production_artifact_set_hash": "4cfca060b423f4071c831c9ce52556a3a66837fb7326f689245253e13165fde6",
    "production_run_manifest_hash": "f55f2829be39445a8489a0863ee5e013c481351d64797251bd79bc199376b127",
    "committed_qualification_report_sha256": "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a",
    "run_recorded_qualification_report_sha256": "dec61cf9d0cdd2a1182b5622e85cfdf9dbc6043e7342ba4f2400fa66245bc2b3",
    "v3_v4_diff_report_sha256": "b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06",
}

FROZEN_BINDING_PATHS = tuple(
    [("authority_bindings", key) for key in EXPECTED_AUTHORITY]
    + [("production_manifest_hashes", key) for key in EXPECTED_MANIFEST_HASHES]
)


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol must be a JSON object")
    return value


def _identity_content(protocol: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(protocol)
    value.pop("generated_utc", None)
    return value


def protocol_content_hash(protocol: dict[str, Any]) -> str:
    encoded = json.dumps(
        _identity_content(protocol), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if protocol.get("schema_version") != 1:
        failures.append("schema version changed")
    if protocol.get("protocol_id") != "U03F-LIQUID-UNIVERSE-V4-INDEPENDENT-AUDIT-V1":
        failures.append("protocol identity changed")
    if protocol.get("status") != "frozen_before_independent_audit_result":
        failures.append("protocol is not frozen before result")
    if protocol.get("repository_binding") != {
        "repository": "QIUYEDALAO/btc-eth-dual-quant",
        "starting_main_sha": "1b6026499cb247f02f0a471eb5a33370769376d9",
        "v4_requalification_pr": 89,
        "v4_requalification_merge_sha": "77cb0969980978e65f3560f38f50924c73dfee6e",
        "v4_governance_closeout_pr": 90,
    }:
        failures.append("repository binding changed")
    if protocol.get("audit_scope") != {
        "range_start": "2020-01", "range_end": "2026-06",
        "months_expected": 78, "membership_rows_expected": 1170,
        "offline_only": True, "production_evidence_mutation_allowed": False,
        "production_requalification_rerun_allowed": False,
    }:
        failures.append("audit scope changed")
    if protocol.get("authority_bindings") != EXPECTED_AUTHORITY:
        failures.append("authority binding changed")
    if protocol.get("production_manifest_hashes") != EXPECTED_MANIFEST_HASHES:
        failures.append("production manifest binding changed")
    if protocol.get("allowed_verdicts") != [
        "pass", "failed_audit", "blocked_missing_evidence", "blocked_protocol_violation"
    ]:
        failures.append("allowed verdicts changed")
    comparison = protocol.get("independence_and_comparison")
    if comparison != {
        "freeze_before_result": True,
        "production_builder_as_audit_result_allowed": False,
        "production_markdown_as_computation_input_allowed": False,
        "exact_mismatch_must_be_reported": True,
        "semantic_mismatch_must_be_reported": True,
        "economic_materiality_exception_allowed": False,
        "tolerance_membership_rank_timestamp_status_allowed": False,
        "wrapper_generated_time_uses_frozen_canonical_identity": True,
        "method_or_gate_change_requires_new_protocol_version_or_adr": True,
    }:
        failures.append("independence/comparison Gate changed")
    authorization = protocol.get("authorization", {})
    if not authorization or any(value is not False for value in authorization.values()):
        failures.append("downstream authorization must remain entirely false")
    if len(protocol.get("required_recomputations", [])) != 17:
        failures.append("required recalculation scope changed")
    return failures


def validate_repository_bindings(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    file_map = {name: EVIDENCE_DIR / f"{name}.json" for name in EXPECTED_MANIFEST_HASHES}
    for name, path in file_map.items():
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{name} unreadable: {exc}")
            continue
        if wrapper.get("content_hash") != protocol["production_manifest_hashes"][name]:
            failures.append(f"{name} wrapper content_hash changed")
    direct = {
        ROOT / "config/liquid_spot_universe_contract_v4.json": ("canonical_hash", EXPECTED_AUTHORITY["v4_contract_hash"]),
        ROOT / "config/liquid_spot_lifecycle_policy_v4.json": ("canonical_hash", EXPECTED_AUTHORITY["lifecycle_policy_hash"]),
        ROOT / "config/liquid_spot_lifecycle_event_resolutions_v4.json": ("canonical_hash", EXPECTED_AUTHORITY["lifecycle_event_registry_hash"]),
        ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json": ("canonical_hash", EXPECTED_AUTHORITY["v3_row_conflict_registry_hash"]),
        EVIDENCE_DIR / "source_freeze_manifest.json": ("content_hash", EXPECTED_AUTHORITY["source_freeze_hash"]),
        EVIDENCE_DIR / "requalification_run_manifest.json": ("content_hash", EXPECTED_AUTHORITY["production_run_manifest_hash"]),
    }
    for path, (key, expected) in direct.items():
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get(key) != expected:
            failures.append(f"{path.relative_to(ROOT)} {key} changed")
    report_hashes = {
        ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md": EXPECTED_AUTHORITY["committed_qualification_report_sha256"],
        ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md": EXPECTED_AUTHORITY["v3_v4_diff_report_sha256"],
    }
    for path, expected in report_hashes.items():
        if _sha256(path) != expected:
            failures.append(f"{path.relative_to(ROOT)} SHA256 changed")
    return failures


def validate_report(path: Path = REPORT_PATH) -> list[str]:
    text = path.read_text(encoding="utf-8")
    required = [
        "- Status: frozen_before_independent_audit_result",
        "- U-04 authorized: no",
        "- Strategy/events/returns/backtesting/OOS: no",
        "Production builders and production Markdown are not computation inputs.",
        "The only verdicts are `pass`, `failed_audit`, `blocked_missing_evidence` and",
    ]
    return [f"protocol report missing: {item}" for item in required if item not in text]


def main() -> int:
    protocol = load_protocol()
    failures = validate_protocol(protocol) + validate_repository_bindings(protocol) + validate_report()
    if failures:
        print("u03f_v4_audit_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u03f_v4_audit_protocol_check PASS")
    print(f"protocol_content_hash={protocol_content_hash(protocol)}")
    print("audit_result_generated=no u04=no strategy=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
