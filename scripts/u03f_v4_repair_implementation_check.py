#!/usr/bin/env python3
"""Validate the fixture-only U-03F V4 repair implementation."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import scan_float_timestamp_paths


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/m0/U03F_V4_REPAIR_IMPLEMENTATION_STATUS.md"
PROTOCOL_HASH = "9b771317d8257b397addefc262a1ffd48ded57ec1d79542372fe3c95cf8180c1"
AUDITOR_HASH = "7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1"
IMPLEMENTATION_HASH = "882b0149d99b30f35118ce85b9db72083a2093428e0e0fa4e19603f0f458af5d"
IMPLEMENTATION_FILES = (
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    "scripts/liquid_universe_v4_public_run.py",
    "scripts/liquid_universe_v4_requalification.py",
    "scripts/liquid_universe_v4_requalification_check.py",
)
AUDITOR_FILES = (
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
    "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
    "scripts/u03f_v4_independent_audit.py",
)
EXPECTED_FILE_HASHES = {
    "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py": "54487fb676df99e5f761a96caf988f6d30a62878c4334a201761a95726337e4a",
    "scripts/liquid_universe_v4_public_run.py": "e6da1d1cd1204ab98f2882eb8aeb4acf7421c6933d379afc06ef48285b0dd1b5",
    "scripts/liquid_universe_v4_requalification.py": "8303bcad64e758308ac3cc9186e4ca668156f84a8fda42c12aca57d5f4448f5a",
    "scripts/liquid_universe_v4_requalification_check.py": "f902e4f90b2a3380c00ecc43468003256a5626523220402de1cabbd28f25e874",
}
IMMUTABLE_EVIDENCE = {
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md": "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a",
    "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md": "b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06",
    "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json": "77df052ce642231af1357a8c61848408f516421a83bd467bca39d5c9deb317ad",
    "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json": "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb",
    "reports/expert/U03F_V4_INDEPENDENT_AUDIT_REPORT.md": "dab79b1224e1c1f8be4c6f6e018b9ce6f40e751af58d380fd4d872d3f442045c",
    "reports/expert/evidence/liquid_universe_v4_independent_audit/audit_summary.json": "d11af8c2fdc54cac699909b0b418dd90a5f1c87e6a5e91e892770924c2184003",
}
FAULT_TEST_METHODS = {
    "FT-INT-PRECISION": "test_ft_int_precision_retains_integer_millisecond_identity",
    "FT-STATIC-FLOAT-PATH": "test_ft_static_float_path_fails_closed_on_reintroduction",
    "FT-ADA-INVALID-INTERVAL": "test_ft_ada_invalid_interval_counts_8269_valid_physical_rows",
    "FT-INVALID-CLOSE-BOUNDARY": "test_ft_invalid_close_boundary_is_excluded_and_reported",
    "FT-REPORT-BYTE-DRIFT": "test_ft_report_byte_drift_invalidates_manifest_binding",
    "FT-RUN-MANIFEST-BINDING": "test_ft_run_manifest_binds_exact_final_report_bytes",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_set_hash(paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((ROOT / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def protocol_hash() -> str:
    protocol = json.loads(
        (ROOT / "config/liquid_universe_v4_repair_requalification_protocol.json").read_text()
    )
    canonical = copy.deepcopy(protocol)
    canonical.pop("generated_utc", None)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def implementation_hash() -> str:
    return content_set_hash(IMPLEMENTATION_FILES)


def validate() -> list[str]:
    failures: list[str] = []
    if protocol_hash() != PROTOCOL_HASH:
        failures.append("repair protocol hash drift")
    if content_set_hash(AUDITOR_FILES) != AUDITOR_HASH:
        failures.append("independent auditor algorithm hash drift")
    if implementation_hash() != IMPLEMENTATION_HASH:
        failures.append("repair implementation hash drift")
    for relative, expected in EXPECTED_FILE_HASHES.items():
        if sha256(ROOT / relative) != expected:
            failures.append(f"repair implementation file drift: {relative}")
    for relative, expected in IMMUTABLE_EVIDENCE.items():
        if sha256(ROOT / relative) != expected:
            failures.append(f"historical evidence changed: {relative}")

    freeze = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json").read_text())
    if freeze.get("content", {}).get("archive_count") != 27_736:
        failures.append("frozen source archive count changed")
    if freeze.get("content_hash") != "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c":
        failures.append("source freeze content hash drift")

    for relative in IMPLEMENTATION_FILES[:2]:
        for finding in scan_float_timestamp_paths((ROOT / relative).read_text(encoding="utf-8")):
            failures.append(f"integer-time violation: {relative}:{finding}")

    tests = (ROOT / "tests/test_u03f_v4_repair_implementation.py").read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for fault_id, method in FAULT_TEST_METHODS.items():
        if method not in tests:
            failures.append(f"missing frozen fault test: {fault_id}")
        if fault_id not in report:
            failures.append(f"implementation report missing fault result: {fault_id}")
    for marker in (
        "- Status: `implementation_fixture_pass_pending_exact_head_review`",
        "- Real public requalification run: `not run`",
        "- Historical evidence modified: `no`",
        "- U-04 authorized: `no`",
        f"- Repair implementation hash: `{IMPLEMENTATION_HASH}`",
    ):
        if marker not in report:
            failures.append(f"implementation report missing: {marker}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("u03f_v4_repair_implementation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u03f_v4_repair_implementation_check PASS")
    print(f"protocol_content_hash={PROTOCOL_HASH}")
    print(f"repair_implementation_hash={IMPLEMENTATION_HASH}")
    print(f"auditor_algorithm_hash={AUDITOR_HASH}")
    print("fault_tests=6/6 public_requalification=no audit=no u04=no strategy=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
