#!/usr/bin/env python3
"""Fail closed on ADR-0015 independent-audit protocol or binding drift."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/liquid_universe_v4_adr0015_independent_audit_protocol.json"
REPORT_PATH = ROOT / "reports/m0/ADR_0015_INVALID_INTERVAL_INDEPENDENT_AUDIT_PROTOCOL.md"
EVIDENCE_DIR = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
RUN_PATH = EVIDENCE_DIR / "requalification_run_manifest.json"

EXPECTED_REPOSITORY_BINDING = {
    "repository": "QIUYEDALAO/btc-eth-dual-quant",
    "starting_local_commit": "a16b844",
    "controlled_integration_merge": "e2112a31908f1587eb657a4123f1f114cf2016fe",
    "reviewed_implementation_head": "67e7d29eaed63a3edb903dd618184bc9f02c5748",
    "implementation_review_merge": "a02d4dfbe752bb7e26e8a7b41971a9f089ddc57f",
}
EXPECTED_AUTHORITY = {
    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "production_artifact_set_hash": "8784b564e8ce21c88b54045b3236021a16344998356a7a15a332188a441348c3",
    "production_run_manifest_hash": "a2f122244e34408071c49f457b96f90b6eba219c6b1304bcdcd9ab7d7d89cdf9",
    "runtime_policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
    "runtime_policy_file_sha256": "a54ec2cca0769439039311c826c328a248e2097b62ef5565291e95965e740cab",
    "algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
    "implementation_content_hash": "7cc4f9a3343de1f81ea7ac38e7c77efdd9fdb6bcbe3f8eeec099ddfca1dd020f",
    "implementation_review_hash": "9a0736431f4df6e27ce0b8e35d28e90d22838aef684e78fbd4c76bd79efe5af1",
    "requalification_report_sha256": "3c1a2b1450a269d1ed2a8abefac0c5e2e44cca7b67adf873832cc26d3012a16d",
    "v3_v4_diff_report_sha256": "b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06",
}
EXPECTED_MANIFEST_HASHES = {
    "V3_V4_diff": "32a944d4dbc5232e4a4ec91187722004e4db7ed4b434fde35662351145dc8d48",
    "active_universe_manifest": "416941b6c8f50472c4ec6fe0edf5070982f508bc68d803e03b7f94995898379d",
    "candidate_eligibility_manifest": "2d116eb8c22419f124a6865937b3a3e5adad4c6c3fefd4f81a3f93719b389d06",
    "complete_day_mask": "1cd6b17593aed5b29e85cb80175b9f51565939f361a9309f9ccd3975daa710be",
    "expected_grid_manifest": "aacea2d14948714c07c188d1774536c7e47530527fc979db5936f940246ce328",
    "invalid_interval_accounting_manifest": "77789efb7535dd487abdd5d575b341e1699a46bfd46a1d5fa874f6431d45d65d",
    "invalid_interval_event_manifest": "8a4e022a9c837b1fb9d4fe7539b7e9c45605660d605e2dcdf71fff0ac34103a6",
    "invalid_interval_policy_manifest": "8c2efd2f2598d851523cfc54ad361d7ab3639558b821fcec2e04fbb4a83fabc7",
    "invalid_interval_slot_mask_manifest": "23e78e15a4484af9167b03e29bf9d499a39ff1e1c8195a056fae72b984285487",
    "lifecycle_event_quarantine_manifest": "c4930bb769c70e2f26cdd2cff25c80391fa254afc0d26d5dd1eca939d27f20a4",
    "lifecycle_policy_manifest": "9ba2dfdd310319475a719291c81eaf93930273732db169d997c9c8252a107f13",
    "lifecycle_resolution_registry": "adccc1f752c171096e6906057225710dd58632744d80927f53f7a1e4a587fbef",
    "membership_manifest": "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5",
    "qualification_summary": "491f4249cb804033d688750b005bdaff9cd830f2715d3b14bd5566bf4d9f4ba3",
    "qualified_panel_manifest": "712bf111b093c80a088fd9685aa9d1faacc49d875c3da7ce550a76c1798480cc",
    "raw_row_quarantine_manifest": "ce97b4826e8305b7d28a27b6693dc120b5b1a8ce5a5cc8462581ace8f68bb4e3",
    "row_conflict_resolution_manifest": "0ed070e44351864473f13e1b127a3ab04464be13477776ec32abbedaf2beac15",
    "source_manifest": "2d7df8798445964cf68c99d7635c18c01ec5d6de264a7facdcea4adb958d405c",
    "symbol_availability_manifest": "1bf3eb5bfb403fbddb12970a2ea4c53963219766a49f0737e5f113023ef39f19",
}


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol must be an object")
    return value


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def protocol_content_hash(protocol: dict[str, Any]) -> str:
    value = copy.deepcopy(protocol)
    value.pop("generated_utc", None)
    return _canonical_hash(value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if protocol.get("schema_version") != 1:
        failures.append("schema version changed")
    if protocol.get("protocol_id") != "ADR0015-LIQUID-UNIVERSE-V4-INDEPENDENT-AUDIT-V1":
        failures.append("protocol identity changed")
    if protocol.get("status") != "frozen_before_independent_auditor_implementation_or_result":
        failures.append("protocol is not frozen before implementation/result")
    if protocol.get("repository_binding") != EXPECTED_REPOSITORY_BINDING:
        failures.append("repository binding changed")
    if protocol.get("authority_bindings") != EXPECTED_AUTHORITY:
        failures.append("authority binding changed")
    if protocol.get("production_manifest_hashes") != EXPECTED_MANIFEST_HASHES:
        failures.append("19-manifest binding changed")
    scope = protocol.get("audit_scope", {})
    if scope != {
        "range_start": "2020-01", "range_end": "2026-06",
        "months_expected": 78, "membership_rows_expected": 1170,
        "source_archive_count": 27736, "source_mode": "frozen_local_only",
        "traversal_orders": ["normal", "reverse", "deterministic_shuffled"],
        "production_evidence_mutation_allowed": False,
        "production_requalification_rerun_allowed": False,
        "audit_result_execution_allowed_in_protocol_stage": False,
    }:
        failures.append("audit scope changed")
    comparison = protocol.get("comparison_gate", {})
    if comparison != {
        "production_manifests_total": 19,
        "production_manifests_exact_required": 19,
        "semantic_mismatches_allowed": 0,
        "traversal_content_mismatches_allowed": 0,
        "critical_findings_allowed_for_pass": 0,
        "high_findings_allowed_for_pass": 0,
        "expected_invalid_interval_events": 8,
        "expected_invalid_physical_rows": 119,
        "expected_valid_minority_rows": 1,
        "expected_total_active_slots_masked": 120,
    }:
        failures.append("comparison Gate changed")
    independence = protocol.get("independence_and_comparison", {})
    required_true = {
        "freeze_before_result", "independent_archive_and_raw_row_verification_required",
        "independent_membership_and_lifecycle_recomputation_required",
        "independent_invalid_interval_event_mask_accounting_required",
        "exact_manifest_comparison_required", "semantic_manifest_comparison_required",
        "order_result_identity_required", "wrapper_generated_time_uses_frozen_canonical_identity",
        "method_or_gate_change_requires_new_protocol_version",
    }
    required_false = {
        "production_builder_as_audit_result_allowed",
        "production_policy_module_as_audit_algorithm_allowed",
        "production_markdown_as_computation_input_allowed",
        "economic_materiality_exception_allowed", "timestamp_repair_fill_or_replacement_allowed",
        "date_symbol_or_row_exception_allowed",
    }
    if set(independence) != required_true | required_false:
        failures.append("independence rule inventory changed")
    elif any(independence[key] is not True for key in required_true) or any(
        independence[key] is not False for key in required_false
    ):
        failures.append("independence rule weakened")
    if len(protocol.get("required_recomputations", [])) != 19:
        failures.append("required recomputation scope changed")
    severity = protocol.get("severity_rules", {})
    if len(severity.get("critical", [])) != 6 or len(severity.get("high", [])) != 4:
        failures.append("severity matrix changed")
    if protocol.get("allowed_verdicts") != [
        "pass", "failed_audit", "blocked_missing_evidence", "blocked_protocol_violation"
    ]:
        failures.append("allowed verdicts changed")
    authorization = protocol.get("authorization", {})
    allowed_true = {
        "independent_auditor_fixture_implementation_after_protocol_freeze",
        "independent_auditor_fault_injection_after_protocol_freeze",
        "independent_auditor_exact_head_review_after_implementation",
    }
    if set(authorization) != allowed_true | {
        "full_independent_audit_run", "u04", "hypothesis", "strategy", "event_scan",
        "returns", "backtesting", "oos", "api_trading", "execution_live", "m2",
    }:
        failures.append("authorization inventory changed")
    elif any(authorization[key] is not True for key in allowed_true) or any(
        value is not False for key, value in authorization.items() if key not in allowed_true
    ):
        failures.append("authorization boundary changed")
    return failures


def validate_repository_bindings(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for name, expected in EXPECTED_MANIFEST_HASHES.items():
        path = EVIDENCE_DIR / f"{name}.json"
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{name} unreadable: {exc}")
            continue
        if document.get("content_hash") != expected:
            failures.append(f"{name} content hash changed")
    try:
        run = json.loads(RUN_PATH.read_text(encoding="utf-8"))
        content = run["content"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return failures + [f"run manifest unreadable: {exc}"]
    if run.get("content_hash") != EXPECTED_AUTHORITY["production_run_manifest_hash"]:
        failures.append("run manifest hash changed")
    if content.get("source_freeze_hash") != EXPECTED_AUTHORITY["source_freeze_hash"]:
        failures.append("run source freeze changed")
    if {item.get("artifact_set_hash") for item in content.get("builds", {}).values()} != {
        EXPECTED_AUTHORITY["production_artifact_set_hash"]
    }:
        failures.append("run artifact set changed")
    if any(item.get("manifest_hashes") != EXPECTED_MANIFEST_HASHES for item in content.get("builds", {}).values()):
        failures.append("run manifest inventory changed")
    freeze = json.loads((EVIDENCE_DIR / "source_freeze_manifest.json").read_text(encoding="utf-8"))
    if freeze.get("content_hash") != EXPECTED_AUTHORITY["source_freeze_hash"]:
        failures.append("source-freeze evidence changed")
    policy_path = ROOT / "config/liquid_spot_invalid_interval_policy_v1.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("canonical_hash") != EXPECTED_AUTHORITY["runtime_policy_hash"]:
        failures.append("runtime policy canonical hash changed")
    if policy.get("algorithm_hash") != EXPECTED_AUTHORITY["algorithm_hash"]:
        failures.append("runtime algorithm hash changed")
    if _sha256(policy_path) != EXPECTED_AUTHORITY["runtime_policy_file_sha256"]:
        failures.append("runtime policy bytes changed")
    report_hashes = {
        ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_ADR0015_REQUALIFICATION_REPORT.md": EXPECTED_AUTHORITY["requalification_report_sha256"],
        ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_ADR0015_V3_V4_DIFF_REPORT.md": EXPECTED_AUTHORITY["v3_v4_diff_report_sha256"],
    }
    for path, expected in report_hashes.items():
        if _sha256(path) != expected:
            failures.append(f"{path.name} bytes changed")
    commit = subprocess.run(
        ["git", "rev-parse", EXPECTED_REPOSITORY_BINDING["starting_local_commit"]],
        cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if commit.returncode or not commit.stdout.strip().startswith("a16b844"):
        failures.append("starting local requalification commit unavailable")
    return failures


def validate_report(path: Path = REPORT_PATH) -> list[str]:
    text = path.read_text(encoding="utf-8")
    required = [
        "frozen_before_independent_auditor_implementation_or_result",
        "Protocol stage executed the real audit: no",
        "Production builders, the production invalid-interval module and production",
        "`pass` requires 19/19 exact manifest comparisons",
        "The real audit remains disabled",
        "Nothing in this protocol authorizes U-04",
    ]
    return [f"protocol report missing: {item}" for item in required if item not in text]


def main() -> int:
    protocol = load_protocol()
    failures = validate_protocol(protocol) + validate_repository_bindings(protocol) + validate_report()
    if failures:
        print("adr0015_invalid_interval_audit_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("adr0015_invalid_interval_audit_protocol_check PASS")
    print(f"protocol_content_hash={protocol_content_hash(protocol)}")
    print("real_audit=no u04=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
