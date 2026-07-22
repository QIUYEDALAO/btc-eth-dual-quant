#!/usr/bin/env python3
"""Offline preflight for the first external-strategy original-IS execution.

This command never opens SSH, Docker, Freqtrade, market rows, or result files.
It validates committed authorities and reports whether the separately pinned
remote execution environment has been explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from external_strategy_original_is_authority_check import validate as validate_authority
from external_strategy_original_is_trial_check import validate as validate_trials


def preflight(*, identity_file: Path | None, require_environment: bool) -> tuple[dict, int]:
    failures = [f"authority: {item}" for item in validate_authority(ROOT)]
    failures.extend(f"trial-accounting: {item}" for item in validate_trials(ROOT))
    state_path = ROOT / "reports/m1/evidence/external_strategy_is_state/selection_state_v1.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    boundary_snapshot = ROOT / "storage/raw/external_strategy_boundary_authority"
    raw_root = ROOT / "storage/raw/liquid_universe"

    environment_blockers: list[str] = []
    host = os.environ.get("VPS_HOST", "").strip()
    if not host:
        environment_blockers.append("VPS_HOST is not configured")
    if identity_file is None:
        environment_blockers.append("an explicit SSH identity file was not supplied")
    elif not identity_file.is_file():
        environment_blockers.append("the explicit SSH identity file does not exist")
    if shutil.which("ssh") is None:
        environment_blockers.append("ssh executable is unavailable")
    if shutil.which("rsync") is None:
        environment_blockers.append("rsync executable is unavailable")
    if not raw_root.is_dir():
        environment_blockers.append("frozen liquid-universe raw root is unavailable")
    boundary_file_count = 0
    if boundary_snapshot.is_dir():
        boundary_file_count = sum(1 for path in boundary_snapshot.rglob("*.zip") if path.is_file())
    if boundary_file_count != 92:
        environment_blockers.append(f"read-only boundary snapshot count is {boundary_file_count}, expected 92")

    result = {
        "schema_version": "external-strategy-original-is-offline-preflight-v1",
        "contracts_valid": not failures,
        "contract_failures": failures,
        "execution_environment_ready": not environment_blockers,
        "environment_blockers": environment_blockers,
        "vps_host_configured": bool(host),
        "explicit_identity_supplied": identity_file is not None,
        "ssh_connection_attempted": False,
        "docker_or_freqtrade_started": False,
        "market_rows_decoded": 0,
        "result_rows_read": 0,
        "selection_trial_count": state.get("selection_trial_count"),
        "oos_authorized": state.get("oos_authorized"),
        "oos_opened": state.get("oos_opened"),
        "oos_runs": state.get("oos_runs"),
        "oos_rows_decoded": state.get("oos_rows_decoded"),
        "boundary_snapshot_file_count": boundary_file_count,
        "next_candidate": "Supertrend" if state.get("selection_trial_count") == 0 else None,
    }
    if failures:
        return result, 1
    if require_environment and environment_blockers:
        return result, 2
    return result, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-file", type=Path)
    parser.add_argument("--require-environment", action="store_true")
    args = parser.parse_args()
    payload, code = preflight(
        identity_file=args.identity_file,
        require_environment=args.require_environment,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
