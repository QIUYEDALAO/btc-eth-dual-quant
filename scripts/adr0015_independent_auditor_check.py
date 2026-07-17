#!/usr/bin/env python3
"""Validate the fixture-only ADR-0015 independent auditor implementation."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import (
    scan_copied_production_functions,
    scan_independence,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/liquid_universe_v4_adr0015_independent_auditor_implementation.json"
PROTOCOL_HASH = "9a1768f01e7891f8c76f74293fb3836339e75fafa039fe12ebf3a7ddfdbb970b"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate() -> list[str]:
    failures: list[str] = []
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in document.items() if key not in {"content_hash", "generated_utc"}}
    if _canonical(unsigned) != document.get("content_hash"):
        failures.append("implementation manifest content hash changed")
    if document.get("protocol_content_hash") != PROTOCOL_HASH:
        failures.append("protocol binding changed")
    files = document.get("files", {})
    actual = {name: _hash(ROOT / name) for name in files}
    if actual != files:
        failures.append("implementation file hash changed")
    identity = {"protocol_content_hash": PROTOCOL_HASH, "files": actual}
    if _canonical(identity) != document.get("implementation_content_hash"):
        failures.append("implementation content identity changed")
    fault_ids = document.get("fault_injection_ids", [])
    if fault_ids != [f"ADR0015-AUD-FI-{number:03d}" for number in range(1, 17)]:
        failures.append("16-case fault inventory changed")
    expected_authorizations = {
        "synthetic_fixture_validation": True, "fault_injection": True, "exact_head_review": True,
        "full_independent_audit_run": False, "u04": False, "strategy": False,
        "returns": False, "backtesting": False, "oos": False, "api_trading": False,
        "execution_live": False, "m2": False,
    }
    if document.get("authorizations") != expected_authorizations:
        failures.append("implementation authorization matrix changed")
    auditor_paths = [
        ROOT / "src/btc_eth_dual_quant/audit/liquid_universe_v4_adr0015.py",
        ROOT / "src/btc_eth_dual_quant/audit/liquid_universe_v4_adr0015_audit_run.py",
    ]
    auditor_source = "\n".join(path.read_text(encoding="utf-8") for path in auditor_paths)
    for finding in scan_independence(auditor_source):
        failures.append(f"independence:{finding}")
    production_sources = [
        (ROOT / "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py").read_text(encoding="utf-8"),
        (ROOT / "scripts/liquid_universe_v4_public_run.py").read_text(encoding="utf-8"),
    ]
    failures.extend(scan_copied_production_functions(auditor_source, production_sources))
    forbidden = (
        "from btc_eth_dual_quant.data.invalid_interval_quarantine",
        "import btc_eth_dual_quant.data.invalid_interval_quarantine",
        "storage/raw",
        "create" + "_order", "cancel" + "_order", "place" + "_order",
    )
    failures.extend(f"forbidden auditor text: {item}" for item in forbidden if item in auditor_source)
    historical = subprocess.run(
        ["git", "diff", "--exit-code", "--",
         "src/btc_eth_dual_quant/audit/liquid_universe_v4_independent.py",
         "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_artifacts.py",
         "src/btc_eth_dual_quant/audit/liquid_universe_v4_audit_run.py"],
        cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if historical.returncode:
        failures.append("historical frozen independent auditor changed")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("adr0015_independent_auditor_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print("adr0015_independent_auditor_check PASS")
    print(f"implementation_content_hash={document['implementation_content_hash']}")
    print("real_audit=no u04=no strategy=no oos=no trading=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
