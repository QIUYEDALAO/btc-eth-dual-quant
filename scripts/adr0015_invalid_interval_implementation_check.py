#!/usr/bin/env python3
"""Validate the fixture-only ADR-0015 generic policy implementation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from btc_eth_dual_quant.data.invalid_interval_quarantine import (
    ADR0015_FAULT_IDS,
    ADR0015_MANIFEST_TYPES,
    EXPECTED_AUTHORIZATIONS,
    InvalidIntervalPolicy,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/liquid_spot_invalid_interval_policy_v1.json"
CORE_PATH = ROOT / "src/btc_eth_dual_quant/data/invalid_interval_quarantine.py"
PUBLIC_RUN_PATH = ROOT / "scripts/liquid_universe_v4_public_run.py"
REPORT_PATH = ROOT / "reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS.md"

EXPECTED = {
    "policy_hash": "0ac074cf6849918065569fe6fb77eb8bd68f30d416325a70d4f55eef02262d04",
    "algorithm_hash": "8f8a36681f35c64a244a7fc0e7155fdcdeb8fb6e5ace2054d261ef8daadea4ff",
    "adr_file_sha256": "c87288449b1c96db74b5f4c68100e4313fbfc19917b29818ae2fd0dfeb535dc5",
    "adoption_hash": "d9b220657d3867941f4f42fd112339c4058e7bc734aa9db72a5b7f81ac78fc19",
    "review_hash": "893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3",
    "protocol_hash": "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190",
    "diagnostic_hash": "ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677",
    "run_hash": "df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33",
    "source_freeze_hash": "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c",
    "membership_hash": "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5",
    "lifecycle_hash": "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d",
    "v2_gap_hash": "051894e89b713f541caa601efab51be22f83461a4e624e1d51d7f576ed8cda51",
}


def _json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_bindings() -> list[str]:
    failures: list[str] = []
    try:
        policy = InvalidIntervalPolicy.from_path(POLICY_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"runtime policy invalid: {exc}"]
    if policy.canonical_hash != EXPECTED["policy_hash"]:
        failures.append("runtime policy hash changed")
    if policy.algorithm_hash != EXPECTED["algorithm_hash"]:
        failures.append("algorithm hash changed")
    if policy.document.get("authorizations") != EXPECTED_AUTHORIZATIONS:
        failures.append("runtime authorization matrix changed")
    bindings = policy.document.get("bindings", {})
    expected_bindings = {
        "adopted_adr_file_sha256": EXPECTED["adr_file_sha256"],
        "adoption_content_hash": EXPECTED["adoption_hash"],
        "review_content_hash": EXPECTED["review_hash"],
        "protocol_content_hash": EXPECTED["protocol_hash"],
        "diagnostic_content_hash": EXPECTED["diagnostic_hash"],
        "diagnostic_run_content_hash": EXPECTED["run_hash"],
        "source_freeze_content_hash": EXPECTED["source_freeze_hash"],
        "membership_manifest_content_hash": EXPECTED["membership_hash"],
        "lifecycle_registry_hash": EXPECTED["lifecycle_hash"],
        "v2_gap_policy_contract_hash": EXPECTED["v2_gap_hash"],
    }
    for key, value in expected_bindings.items():
        if bindings.get(key) != value:
            failures.append(f"runtime binding changed: {key}")
    if _sha256(ROOT / bindings.get("adopted_adr_path", "missing")) != EXPECTED["adr_file_sha256"]:
        failures.append("adopted ADR bytes changed")

    documents = {
        "adoption": _json("reports/expert/evidence/adr0015_adoption_manifest.json").get("content_hash"),
        "review": _json("reports/expert/evidence/adr0015_independent_review.json").get("review_content_sha256"),
        "source_freeze": _json("reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json").get("content_hash"),
        "membership": _json("reports/m0/evidence/liquid_universe_v4_repair_requalification/membership_manifest.json").get("content_hash"),
        "lifecycle": _json("config/liquid_spot_lifecycle_event_resolutions_v4.json").get("canonical_hash"),
        "v2_gap": _json("config/liquid_spot_universe_contract_v2.json").get("canonical_hash"),
    }
    for name, expected_key in (
        ("adoption", "adoption_hash"), ("review", "review_hash"),
        ("source_freeze", "source_freeze_hash"), ("membership", "membership_hash"),
        ("lifecycle", "lifecycle_hash"), ("v2_gap", "v2_gap_hash"),
    ):
        if documents[name] != EXPECTED[expected_key]:
            failures.append(f"frozen {name} evidence changed")
    return failures


def validate_implementation_shape() -> list[str]:
    failures: list[str] = []
    core = CORE_PATH.read_text(encoding="utf-8")
    public = PUBLIC_RUN_PATH.read_text(encoding="utf-8")
    required_core = (
        "class VerifiedFiveMinuteRow", "class ActiveMembershipAuthority",
        "def read_verified_monthly_five_minute_archive", "def evaluate_invalid_interval_policy",
        "def apply_invalid_interval_mask", "def build_invalid_interval_manifests",
    )
    for marker in required_core:
        if marker not in core:
            failures.append(f"core implementation missing: {marker}")
    if len(ADR0015_MANIFEST_TYPES) != 4 or len(ADR0015_FAULT_IDS) != 16:
        failures.append("manifest or fault identity count changed")
    for forbidden in ('if symbol == "', "if open_time_ms == ", "docs/decisions", "storage/raw"):
        if forbidden in core:
            failures.append(f"production core contains forbidden special input: {forbidden}")
    required_public = (
        "read_verified_monthly_five_minute_archive(",
        "evaluate_invalid_interval_policy(",
        "apply_invalid_interval_mask(",
        "_with_invalid_interval_mask(",
        "_apply_invalid_interval_artifact_overlay(",
        "build_invalid_interval_manifests(",
    )
    for marker in required_public:
        if marker not in public:
            failures.append(f"public-run integration missing: {marker}")
    positions = [public.index(marker) for marker in required_public[:3]] if all(marker in public for marker in required_public[:3]) else []
    if positions and positions != sorted(positions):
        failures.append("physical verification/evaluation/mask order changed")
    return failures


def validate_report_and_context() -> list[str]:
    failures: list[str] = []
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.exists() else ""
    for marker in (
        "- Status: `implementation_pass_fixture_only_pending_exact_head_review`",
        "- Public data read or executed: no",
        "- Fixed-range requalification authorized: no",
        "- Exact-head independent implementation review required: yes",
        f"- Runtime policy hash: `{EXPECTED['policy_hash']}`",
    ):
        if marker not in report:
            failures.append(f"implementation report marker missing: {marker}")
    state = (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    for marker in (
        "current_phase: ADR-0015 generic invalid-interval policy implementation pending exact-head review",
        "adr0015_invalid_interval_policy_implementation:",
        "public_data_run_executed: false",
        "fixed_range_public_requalification_authorized: false",
    ):
        if marker not in state:
            failures.append(f"project state marker missing: {marker}")
    return failures


def validate() -> list[str]:
    failures: list[str] = []
    for check in (validate_bindings, validate_implementation_shape, validate_report_and_context):
        try:
            failures.extend(check())
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            failures.append(f"{check.__name__} failed closed: {exc}")
    return sorted(set(failures))


def main() -> int:
    failures = validate()
    if failures:
        print("adr0015_invalid_interval_implementation_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("adr0015_invalid_interval_implementation_check PASS")
    print(f"policy_hash={EXPECTED['policy_hash']}")
    print(f"algorithm_hash={EXPECTED['algorithm_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
