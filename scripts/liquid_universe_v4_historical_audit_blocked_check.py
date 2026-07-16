#!/usr/bin/env python3
"""Verify the exact immutable V4 evidence whose report binding failed audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = {
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md": "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a",
    "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md": "b43a365a906c9b2689d3853d3478762c25df64bc7193dbf54dd697e6e172cb06",
    "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json": "77df052ce642231af1357a8c61848408f516421a83bd467bca39d5c9deb317ad",
    "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json": "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb",
}
HISTORICAL_RECORDED_REPORT_HASH = "dec61cf9d0cdd2a1182b5622e85cfdf9dbc6043e7342ba4f2400fa66245bc2b3"
HISTORICAL_COMMITTED_REPORT_HASH = "ad414f760655645e20c6bc20c49c0f25bf3aea1d5f47b373fc254364aab91e2a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    state = (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    if "current_status: liquid_universe_v4_independent_audit_failed_no_strategy_no_m2" not in state:
        raise ValueError("historical audit-blocked check requires failed-audit project state")
    for relative, expected in EXPECTED_FILES.items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"historical audit-blocked evidence drift: {relative}")
    run = json.loads(
        (ROOT / "reports/m0/evidence/liquid_universe_v4/requalification_run_manifest.json").read_text()
    )
    bindings = {
        record.get("qualification_report_sha256")
        for record in run.get("content", {}).get("builds", {}).values()
    }
    if bindings != {HISTORICAL_RECORDED_REPORT_HASH}:
        raise ValueError("historical run-recorded report hash changed")
    if sha256(ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md") != HISTORICAL_COMMITTED_REPORT_HASH:
        raise ValueError("historical committed report hash changed")
    if HISTORICAL_RECORDED_REPORT_HASH == HISTORICAL_COMMITTED_REPORT_HASH:
        raise ValueError("historical failed binding was reinterpreted as a pass")
    print("V4 historical audit-blocked evidence check PASS")
    print("report_binding_status=known_failed_immutable_historical_evidence")
    print("qualification_authority=audit_blocked revalidation_required=yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
