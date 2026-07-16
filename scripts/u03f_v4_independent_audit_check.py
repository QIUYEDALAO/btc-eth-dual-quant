#!/usr/bin/env python3
"""Validate the exact stage-B U-03F independent auditor implementation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import (
    scan_files,
    scan_float_timestamp_paths,
)


ROOT = Path(__file__).resolve().parents[1]
AUDITOR_FILES = [
    ROOT / "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
    ROOT / "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
    ROOT / "scripts/u03f_v4_independent_audit.py",
]
PRODUCTION_TIME_PATHS = [
    ROOT / "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
    ROOT / "src/btc_eth_dual_quant/data/lifecycle_availability.py",
    ROOT / "scripts/liquid_universe_v4_public_run.py",
]
PROTOCOL = ROOT / "config/liquid_universe_v4_independent_audit_protocol.json"


def algorithm_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(AUDITOR_FILES):
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate() -> tuple[list[str], list[str]]:
    failures = scan_files(AUDITOR_FILES)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol.get("status") != "frozen_before_independent_audit_result":
        failures.append("frozen protocol status changed")
    if any(protocol.get("authorization", {}).values()):
        failures.append("protocol downstream authorization changed")
    risk_findings: list[str] = []
    for path in PRODUCTION_TIME_PATHS:
        for finding in scan_float_timestamp_paths(path.read_text(encoding="utf-8")):
            risk_findings.append(f"{path.relative_to(ROOT)}:{finding}")
    if not risk_findings:
        failures.append("production integer-time conformance must be explicitly evaluated")
    return failures, risk_findings


def main() -> int:
    failures, risks = validate()
    if failures:
        print("u03f_v4_independent_audit_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("u03f_v4_independent_audit_check PASS")
    print(f"audit_algorithm_hash={algorithm_hash()}")
    print(f"production_integer_time_risk_findings={len(risks)}")
    for item in risks:
        print(f"- pending_D_gate: {item}")
    print("full_public_audit_executed=no u04=no strategy=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
