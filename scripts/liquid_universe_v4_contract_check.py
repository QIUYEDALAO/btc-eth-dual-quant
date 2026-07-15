#!/usr/bin/env python3
"""Fail-closed validation for the fixture-only V4 lifecycle authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry
from btc_eth_dual_quant.data.liquid_universe import canonical_hash, content_hash


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/liquid_spot_universe_contract_v4.json"
POLICY = ROOT / "config/liquid_spot_lifecycle_policy_v4.json"
REGISTRY = ROOT / "config/liquid_spot_lifecycle_event_resolutions_v4.json"

EXPECTED = {
    "adr0011_adr_sha256": "5e05543cc7019fe7aaa6c90ebf78fb26adf084e33cb78aeccf6089202a1b94df",
    "adopted_adr_sha256": "2de88986f6123a0d0ddaa2756b6c665a2fc0d3960f24dba1966bd51332becad9",
    "adoption_manifest_hash": "9c3572bee81edbf1efcc3ca523c9fdd10003adc5f3c3ac5a7211ad673405394a",
    "reviewed_semantic_hash": "5c2113edbb7a69b52c1e78e3a6c3f223dac36d21769a9e1c5b815894945f8e99",
    "policy_model_hash": "bce56a1070ef0690b13cba492bf9619a456af2618be94eb2ecbe03ea7e709d97",
    "fault_matrix_hash": "90beb680e568ab5bc045556ef728e34cd2827d5bf6005ebb524b6e38ed6a199f",
    "mc_conformance_hash": "303e4d28ea27575ed7fa46e9d9da459e5c237a0390f36f9c9de9cfcd7c9821d2",
    "klay_evidence_hash": "6d31fa1f6fe01d16d3a7f00ae67ce114faa370ddb269b57406ea98af7c416f0a",
    "v3_contract_hash": "f41f5fedf6002487c9d576a39927ade4409d55e1bc0442aa097e6b2ed054b3ed",
    "v3_registry_hash": "570b66e32c3a7ac910ba5ef6688eff966304e65a9519f4f8a902b60fbe4957a4",
    "v3_blocked_artifact_set_hash": "f661d7abd99adc4067d354afba0c5421e7d1f33c54f768b89c8011ec01eab4f3",
    "asset_registry_hash": "d8c7fc6b034f1b0c82dc2e41f7b4f2c67122311246b33505f22ad694a3d0b091",
}

EXPECTED_ORDER = [
    "verify_checksum_crc_schema",
    "collect_raw_rows_and_classify_defects",
    "load_adr0013_row_registry",
    "load_adr0014_lifecycle_policy_and_registry",
    "reject_policy_overlap",
    "resolve_registered_row_conflicts",
    "build_lifecycle_availability_epochs",
    "quarantine_registered_lifecycle_rows",
    "apply_availability_mask",
    "build_expected_grid",
    "detect_gaps",
    "aggregate_timeframes",
    "build_complete_day_mask",
    "compute_eligibility_and_ranking",
    "freeze_monthly_membership",
    "build_timestamped_active_universe",
    "emit_hash_bound_artifacts",
]

DOWNSTREAM_KEYS = {
    "u03f", "u04", "hypothesis", "strategy", "events", "signals", "returns",
    "backtesting", "oos", "api_trading", "execution_live", "m2",
}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(
    contract: dict[str, Any],
    policy: dict[str, Any],
    registry_document: dict[str, Any],
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    _require(contract.get("canonical_hash") == content_hash(contract), "contract canonical hash mismatch")
    _require(policy.get("canonical_hash") == content_hash(policy), "policy canonical hash mismatch")
    registry = LifecycleEventRegistry.from_document(registry_document)

    bindings = contract.get("bindings", {})
    _require(bindings.get("adr0011_adr_sha256") == EXPECTED["adr0011_adr_sha256"], "ADR-0011 binding changed")
    _require(bindings.get("v3_contract_hash") == EXPECTED["v3_contract_hash"], "V3 contract binding changed")
    _require(bindings.get("v3_row_conflict_registry_hash") == EXPECTED["v3_registry_hash"], "V3 registry binding changed")
    _require(bindings.get("v3_blocked_cold_artifact_set_hash") == EXPECTED["v3_blocked_artifact_set_hash"], "V3 artifact binding changed")
    _require(bindings.get("asset_eligibility_registry_hash") == EXPECTED["asset_registry_hash"], "asset registry binding changed")
    _require(bindings.get("adopted_adr0014_sha256") == EXPECTED["adopted_adr_sha256"], "adopted ADR binding changed")
    _require(bindings.get("adr0014_adoption_manifest_hash") == EXPECTED["adoption_manifest_hash"], "adoption manifest binding changed")
    _require(bindings.get("lifecycle_policy_model_hash") == EXPECTED["policy_model_hash"], "reviewed policy model changed")
    _require(bindings.get("fault_matrix_hash") == EXPECTED["fault_matrix_hash"], "reviewed fault matrix changed")
    _require(bindings.get("mc_conformance_hash") == EXPECTED["mc_conformance_hash"], "reviewed MC conformance changed")
    _require(bindings.get("klay_adjudication_evidence_hash") == EXPECTED["klay_evidence_hash"], "lifecycle evidence binding changed")
    _require(bindings.get("lifecycle_policy_config_hash") == policy["canonical_hash"], "contract/policy hash mismatch")
    _require(bindings.get("lifecycle_event_registry_hash") == registry.canonical_hash, "contract/registry hash mismatch")

    _require(policy.get("processing_order") == EXPECTED_ORDER, "normative processing order mismatch")
    _require(policy["adopted_adr"]["sha256"] == EXPECTED["adopted_adr_sha256"], "policy ADR hash mismatch")
    _require(policy["adopted_adr"]["reviewed_semantic_body_sha256"] == EXPECTED["reviewed_semantic_hash"], "reviewed semantic body mismatch")
    _require(policy["adopted_adr"]["adoption_manifest_content_hash"] == EXPECTED["adoption_manifest_hash"], "policy adoption manifest mismatch")
    _require(policy["reviewed_models"]["policy_model_sha256"] == EXPECTED["policy_model_hash"], "policy model hash mismatch")
    _require(policy["reviewed_models"]["fault_matrix_sha256"] == EXPECTED["fault_matrix_hash"], "fault matrix hash mismatch")
    _require(policy["reviewed_models"]["mc_conformance_sha256"] == EXPECTED["mc_conformance_hash"], "MC conformance hash mismatch")

    _require(hashlib.sha256((root / "docs/decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md").read_bytes()).hexdigest() == EXPECTED["adopted_adr_sha256"], "adopted ADR file changed")
    _require(hashlib.sha256((root / "docs/decisions/ADR-0011-liquid-spot-universe-expansion.md").read_bytes()).hexdigest() == EXPECTED["adr0011_adr_sha256"], "ADR-0011 file changed")
    for path, expected in (
        ("docs/decisions/proposals/adr0014_lifecycle_policy_model.json", EXPECTED["policy_model_hash"]),
        ("docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json", EXPECTED["fault_matrix_hash"]),
        ("docs/decisions/proposals/adr0014_mc_conformance.json", EXPECTED["mc_conformance_hash"]),
    ):
        _require(canonical_hash(_read(root / path)) == expected, f"reviewed model changed: {path}")
    _require(_read(root / "reports/expert/evidence/adr0014_adoption_manifest.json").get("content_hash") == EXPECTED["adoption_manifest_hash"], "adoption evidence changed")
    _require(_read(root / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json").get("content_hash") == EXPECTED["klay_evidence_hash"], "KLAY adjudication evidence changed")
    _require(content_hash(_read(root / "config/liquid_spot_universe_contract_v3.json")) == EXPECTED["v3_contract_hash"], "V3 contract changed")
    _require(content_hash(_read(root / "config/liquid_spot_source_conflict_resolutions_v3.json")) == EXPECTED["v3_registry_hash"], "V3 row registry changed")
    _require(content_hash(_read(root / "config/liquid_spot_asset_eligibility_v2.json")) == EXPECTED["asset_registry_hash"], "asset eligibility registry changed")
    run = _read(root / "reports/m0/evidence/liquid_universe_v3/requalification_run_manifest.json")
    _require(
        run["content"]["builds"]["cold"]["artifact_set_hash"] == EXPECTED["v3_blocked_artifact_set_hash"],
        "V3 qualification artifacts changed",
    )

    downstream = {key: contract["authorizations"].get(key) for key in sorted(DOWNSTREAM_KEYS)}
    _require(not any(downstream.values()), "downstream authorization enabled")
    _require(not any(policy["authorizations"].get(key) for key in DOWNSTREAM_KEYS), "policy downstream authorization enabled")
    return {
        "contract_hash": contract["canonical_hash"],
        "policy_hash": policy["canonical_hash"],
        "registry_hash": registry.canonical_hash,
        "downstream_authorizations": downstream,
    }


def main() -> int:
    try:
        result = validate(_read(CONTRACT), _read(POLICY), _read(REGISTRY))
    except (KeyError, TypeError, ValueError) as exc:
        print(f"Liquid universe V4 contract check: FAIL - {exc}")
        return 1
    print("Liquid universe V4 contract check: PASS")
    for key in ("contract_hash", "policy_hash", "registry_hash"):
        print(f"{key}={result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
