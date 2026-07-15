#!/usr/bin/env python3
"""Fail-closed static validation for the adopted V3 qualification contract."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry
from btc_eth_dual_quant.data.liquid_universe import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/liquid_spot_universe_contract_v3.json"
REGISTRY = ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"
ADR = ROOT / "docs/decisions/ADR-0013-official-archive-row-conflict-policy.md"
IMPLEMENTATION = (
    ROOT / "src/btc_eth_dual_quant/data/kline_row_conflicts.py",
    ROOT / "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v3.py",
)

EXPECTED_ORDER = [
    "verify_archive", "retain_raw", "group_complete_key", "classify_group",
    "collapse_byte_identical_only", "block_heterogeneous_group", "validate_candidate",
    "lookup_offline_registry", "validate_daily_candidate", "emit_canonical_provenance",
    "monthly_primary_daily_fill_merge", "build_qualification",
]
PROHIBITED_AUTHORIZATIONS = {
    "hypothesis_preregistration", "strategy_selection", "event_scan", "signals",
    "returns", "oos_access", "freqtrade_backtesting", "u03f", "u04", "m2",
    "api_or_trading",
}


def check() -> list[str]:
    failures: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    registry = ResolutionRegistry.from_path(REGISTRY)
    adr = ADR.read_text(encoding="utf-8")
    if "Status: Accepted for V3 implementation and U-03E requalification only" not in adr:
        failures.append("ADR-0013 adoption status mismatch")
    unsigned = {key: value for key, value in contract.items() if key != "canonical_hash"}
    if contract.get("canonical_hash") != canonical_hash(unsigned):
        failures.append("V3 contract canonical hash mismatch")
    if contract.get("universe_id") != "LIQUID-SPOT-USDT-TOP15-V3":
        failures.append("V3 contract identity mismatch")
    policy = contract.get("conflict_resolution_policy", {})
    if policy.get("resolution_registry_hash") != registry.canonical_hash:
        failures.append("contract/registry hash mismatch")
    if policy.get("adjudication_evidence_hash") != registry.adjudication_evidence_hash:
        failures.append("contract/evidence hash mismatch")
    if policy.get("adr_sha256") != hashlib.sha256(ADR.read_bytes()).hexdigest():
        failures.append("contract/ADR hash mismatch")
    if policy.get("processing_order") != EXPECTED_ORDER:
        failures.append("normative processing order mismatch")
    membership = contract.get("membership", {})
    expected_membership = {
        "target_size": 15,
        "ranking_window_complete_days": 90,
        "minimum_complete_history_days": 365,
        "tie_break": "symbol_ascending",
        "replacement_allowed": False,
    }
    for key, expected in expected_membership.items():
        if membership.get(key) != expected:
            failures.append(f"frozen membership policy changed: {key}")
    authorizations = contract.get("authorizations", {})
    for key in PROHIBITED_AUTHORIZATIONS:
        if authorizations.get(key) is not False:
            failures.append(f"prohibited authorization enabled: {key}")
    if authorizations.get("u03e_v3_requalification") is not True:
        failures.append("fixed-range U-03E V3 requalification is not authorized")
    for path in IMPLEMENTATION:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for forbidden in ("BTTUSDT", "AXSUSDT", "2019-01-31", "2026-02-10", "drop_duplicates", "keep=", "urlopen", "requests"):
            if forbidden in source:
                failures.append(f"special-case or runtime repair token in {path.name}: {forbidden}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "abs":
                failures.append(f"absolute-value repair in {path.name}:{node.lineno}")
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Liquid universe V3 contract check: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    print("Liquid universe V3 contract check: PASS")
    print(f"contract_hash={contract['canonical_hash']}")
    print(f"resolution_registry_hash={registry['canonical_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
