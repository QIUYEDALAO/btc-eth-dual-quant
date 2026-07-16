#!/usr/bin/env python3
"""Validate the frozen U-03F V4 invalid-interval adjudication protocol."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "config/liquid_universe_v4_invalid_interval_adjudication_protocol.json"
REPORT_PATH = ROOT / "reports/m0/U03F_V4_INVALID_INTERVAL_ADJUDICATION_PROTOCOL.md"
DESIGN_PATH = ROOT / "docs/superpowers/specs/2026-07-17-u03f-v4-invalid-interval-adjudication-design.md"
EXPECTED_PROTOCOL_CONTENT_HASH = "9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190"

IMMUTABLE_FILES = {
    "reports/m0/evidence/liquid_universe_v4_repair_requalification/source_freeze_manifest.json": "71ef8d900ceca6618d0557ce62db0b63814793502789bc8346ba02abc3bb96fb",
    "reports/m0/evidence/liquid_universe_v4_repair_requalification/requalification_run_manifest.json": "16fc8162e254462ef9444833bbe21262445b8fbfc75864ef00f22a142f110313",
    "reports/m0/evidence/liquid_universe_v4_repair_requalification/qualification_summary.json": "b2afe36cd8a7c8e91cb628ecf3ce479b6860701bc073a114fdec443212b84b19",
    "reports/m0/evidence/liquid_universe_v4_repair_requalification/expected_grid_manifest.json": "9901fd07c00734be352674d7af62152e458109643c65e15df0a31af9798159fa",
    "reports/m0/evidence/liquid_universe_v4_repair_requalification/membership_manifest.json": "d3dbf7508b1cd8373834a70cf7ee307937de754643687bd9ad9928f082aea72f",
    "reports/m0/LIQUID_SPOT_UNIVERSE_V4_REPAIR_REQUALIFICATION_REPORT.md": "0085e32766bc7b0b261c158aecef5d022154f396533712a957a4b97b1a3c1eb2",
    "config/liquid_spot_universe_contract_v2.json": "a728462f52cdc7a53ed5574b4db4d2acb0f48f772acda0165a48a165f0a9ec4d",
    "config/liquid_spot_universe_contract_v4.json": "b882bdb8a10b266d504bebb5406613624332497c9b84a7c4364b4c6b1dfd86ee",
}

FALSE_AUTHORIZATIONS = {
    "draft_policy_adr_before_diagnostic_merge",
    "policy_adoption",
    "repair_implementation",
    "public_requalification",
    "new_independent_audit",
    "u04",
    "hypothesis",
    "strategy",
    "event_scan",
    "returns",
    "backtesting",
    "oos",
    "api_trading",
    "execution_live",
    "m2",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol must be an object")
    return value


def protocol_content_hash(protocol: dict[str, Any]) -> str:
    value = copy.deepcopy(protocol)
    value.pop("generated_utc", None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if protocol_content_hash(protocol) != EXPECTED_PROTOCOL_CONTENT_HASH:
        failures.append("protocol content hash changed")
    if protocol.get("schema_version") != 1:
        failures.append("schema version changed")
    if protocol.get("protocol_id") != "U03F-V4-INVALID-INTERVAL-ADJUDICATION-V1":
        failures.append("protocol id changed")
    if protocol.get("status") != "frozen_before_diagnostic_run":
        failures.append("protocol is not frozen before diagnostics")

    binding = protocol.get("repository_binding", {})
    if binding != {
        "repository": "QIUYEDALAO/btc-eth-dual-quant",
        "starting_main_sha": "3ba411d28563526a5357e3882a1e5759311f6179",
        "repair_requalification_pr": 100,
        "repair_requalification_head_sha": "a0e680fbfb4415bb25871aa0cb3ed8b873d6c810",
        "repair_requalification_merge_sha": "927f121651d6e1e07f174410a39595f6d09e9a5d",
        "repair_closeout_pr": 101,
        "repair_closeout_merge_sha": "3ba411d28563526a5357e3882a1e5759311f6179",
    }:
        failures.append("repository binding changed")

    known = protocol.get("known_blocked_input", {})
    expected_known = {
        "source_mode": "frozen_local_only",
        "source_archive_count": 27736,
        "range_start": "2020-01",
        "range_end": "2026-06",
        "repair_requalification_status": "blocked",
        "processing_errors": 119,
        "stop_reason_count": 119,
        "stop_reason_suffix": "5m interval boundary is invalid",
        "warm_worker_status": "not_run_due_fail_closed_cold_block",
    }
    if known != expected_known:
        failures.append("known blocked input changed")

    scope = protocol.get("diagnostic_scope", {})
    for key in ("physical_source_rows_must_remain_unchanged", "integer_time_only"):
        if scope.get(key) is not True:
            failures.append(f"diagnostic scope must require {key}")
    for key in (
        "network_access_allowed",
        "source_download_or_replacement_allowed",
        "daily_or_rest_substitution_allowed",
        "historical_evidence_mutation_allowed",
        "production_pipeline_change_allowed",
        "policy_adoption_allowed",
        "validation_gate_reduction_allowed",
    ):
        if scope.get(key) is not False:
            failures.append(f"diagnostic scope must forbid {key}")

    algorithm = protocol.get("diagnostic_algorithm", {})
    if algorithm.get("orders") != ["normal", "reverse", "deterministic_shuffled"]:
        failures.append("diagnostic traversal orders changed")
    if algorithm.get("open_time_grid_ms") != 300000 or algorithm.get("valid_close_delta_ms") != 299999:
        failures.append("strict 5m integer boundary changed")
    if algorithm.get("synchronous_minimum_symbols") != 2 or algorithm.get("synchronous_minimum_fraction") != 0.8:
        failures.append("synchronous evidence threshold changed")
    for key in (
        "archive_binding_required_before_parse",
        "zip_crc_required",
        "one_csv_member_required",
        "raw_row_hash_required",
        "verified_archive_required_for_synchronous_candidate",
        "non_member_row_is_blocking",
        "duplicate_or_missing_expected_row_is_blocking",
    ):
        if algorithm.get(key) is not True:
            failures.append(f"diagnostic algorithm must require {key}")
    for key in ("raw_field_repair_allowed", "synthetic_fill_allowed"):
        if algorithm.get(key) is not False:
            failures.append(f"diagnostic algorithm must forbid {key}")

    decision = protocol.get("decision_gate", {})
    if decision.get("allowed_decisions") != [
        "new_policy_adr_required",
        "official_source_followup_required",
        "blocked_evidence_mismatch",
    ]:
        failures.append("allowed diagnostic decisions changed")
    for key in ("direct_existing_gap_policy_adoption_allowed", "per_row_exception_registry_allowed"):
        if decision.get(key) is not False:
            failures.append(f"decision Gate must forbid {key}")
    for key in (
        "new_policy_adr_required_if_all_rows_are_exact_and_synchronous",
        "any_binding_or_order_mismatch_must_fail_closed",
        "normal_reverse_shuffled_content_hashes_must_match",
        "markdown_must_be_exact_machine_render",
    ):
        if decision.get(key) is not True:
            failures.append(f"decision Gate must require {key}")

    authorization = protocol.get("authorization", {})
    if authorization.get("diagnostic_run_after_protocol_merge") is not True:
        failures.append("diagnostic run is not authorized after protocol merge")
    for key in FALSE_AUTHORIZATIONS:
        if authorization.get(key) is not False:
            failures.append(f"unauthorized scope enabled: {key}")
    return failures


def validate_immutable_inputs(protocol: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for relative, expected in IMMUTABLE_FILES.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            failures.append(f"immutable input changed: {relative}: {actual}")

    bindings = protocol.get("immutable_input_bindings", {})
    run = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/requalification_run_manifest.json").read_text())
    summary = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/qualification_summary.json").read_text())
    freeze = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/source_freeze_manifest.json").read_text())
    membership = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v4_repair_requalification/membership_manifest.json").read_text())
    exact = {
        "source_freeze_content_hash": freeze.get("content_hash"),
        "repair_run_manifest_content_hash": run.get("content_hash"),
        "repair_qualification_summary_content_hash": summary.get("content_hash"),
        "repair_membership_content_hash": membership.get("content_hash"),
    }
    for key, actual in exact.items():
        if bindings.get(key) != actual:
            failures.append(f"immutable content binding changed: {key}: {actual}")
    if run.get("content", {}).get("status") != "blocked":
        failures.append("repair run is no longer blocked")
    if run.get("content", {}).get("processing_errors") != 119:
        failures.append("repair processing-error count changed")
    if len(run.get("content", {}).get("stop_reasons", [])) != 119:
        failures.append("repair stop-reason count changed")
    return failures


def validate_docs() -> list[str]:
    failures: list[str] = []
    report = REPORT_PATH.read_text(encoding="utf-8")
    design = DESIGN_PATH.read_text(encoding="utf-8")
    for item in (
        "- Status: frozen_before_diagnostic_run",
        "- Diagnostic run executed: no",
        "- Production pipeline modified: no",
        "- U-04 authorized: no",
        "new_policy_adr_required",
    ):
        if item not in report:
            failures.append(f"protocol report missing: {item}")
    for item in (
        "Design status: approved_by_explicit_follow_on",
        "protocol-first, evidence-second",
        "new_policy_adr_required",
        "never auto-enters U-04",
    ):
        if item not in design:
            failures.append(f"design missing: {item}")
    return failures


def main() -> int:
    protocol = load_protocol()
    failures = validate_protocol(protocol) + validate_immutable_inputs(protocol) + validate_docs()
    if failures:
        print("u03f_v4_invalid_interval_protocol_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u03f_v4_invalid_interval_protocol_check PASS")
    print(f"protocol_content_hash={EXPECTED_PROTOCOL_CONTENT_HASH}")
    print("diagnostic=no policy=no implementation=no requalification=no audit=no u04=no oos=no m2=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
