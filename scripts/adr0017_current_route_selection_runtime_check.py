#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/adr0017_current_route_selection_runtime_v1.json"
EXPECTED = "8a4b1d6d859c683bf3a61fd55784083bc04c8169a9cd1cab2362273177b48cdd"


def digest(value: Mapping[str, Any]) -> str:
    identity = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        contract = json.loads((root / "config/adr0017_current_route_selection_runtime_v1.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"contract unreadable: {exc}"]

    if contract.get("content_hash") != EXPECTED or digest(contract) != EXPECTED:
        failures.append("ADR-0017 canonical identity mismatch")

    bindings = contract.get("bindings", {})
    for relative, expected in bindings.get("contract_byte_hashes", {}).items():
        try:
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        except OSError as exc:
            failures.append(f"bound file unreadable: {relative}: {exc}")
            continue
        if actual != expected:
            failures.append(f"bound file hash drift: {relative}")

    try:
        freeze = json.loads((root / "config/external_strategy_candidate_freeze_v1.json").read_text())
        protocol = json.loads((root / "config/external_strategy_unified_is_protocol_v1.json").read_text())
        oos = json.loads((root / "config/external_strategy_oos_guard_v1.json").read_text())
        dsr = json.loads((root / "config/external_strategy_dsr_reference_trials_v1.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return failures + [f"bound contract unreadable: {exc}"]

    candidates = [item.get("id") for item in freeze.get("frozen_candidates", [])]
    if candidates != bindings.get("frozen_candidates"):
        failures.append("frozen candidate identity or order changed")
    if freeze.get("selection_trial_count") != 0 or freeze.get("is_rows_materialized") != 0:
        failures.append("ADR-0017 must be adopted before current-route results")
    if protocol.get("execution_counters") != {"freqtrade_loads": 0, "causal_validations": 0, "is_trials": 0}:
        failures.append("pre-adoption runtime counters are not zero")

    historical = contract.get("statistical_selection", {}).get("historical_m1a_m1b_m1c", {})
    expected_historical = {
        "retained_in_historical_trial_ledger": True,
        "reported": True,
        "deleted": False,
        "current_route_same_distribution_reference": False,
        "reason": "heterogeneous instrument / scope / window / return process",
    }
    if historical != expected_historical or dsr.get("historical_opened_oos_trial_count") != 3:
        failures.append("historical DSR scope decision changed")

    selection = contract.get("statistical_selection", {})
    dsr_policy = selection.get("dsr", {})
    if dsr_policy != {
        "mandatory_to_compute": True,
        "mandatory_to_report": True,
        "primary_selection_rank": True,
        "absolute_is_hard_gate": False,
        "base_and_costx2_separate": True,
    }:
        failures.append("DSR policy changed")
    if selection.get("all_hard_gates_pass_excludes_absolute_dsr_threshold") is not True:
        failures.append("absolute DSR was restored as a hard Gate")
    if selection.get("selection_order") != [
        "all_non_dsr_hard_gates_pass", "base_dsr_desc", "costx2_dsr_desc",
        "costx2_daily_mtm_sharpe_desc", "costx2_max_drawdown_asc",
        "turnover_asc", "candidate_id_asc",
    ]:
        failures.append("selection order changed")
    if selection.get("per_trial_final_dsr_stored") is not False:
        failures.append("mutable final DSR cannot be stored per trial")

    final = contract.get("final_selection", {})
    if final.get("path") != "reports/m1/evidence/external_strategy_selection/final_is_selection.json":
        failures.append("final selection path changed")
    if final.get("generate_once_after_all_original_and_allowed_modified_trials_close") is not True:
        failures.append("final selection is not single generation")
    if final.get("maximum_selected_candidates") != 1 or final.get("terminal_success_status") != "pending_explicit_unique_oos_authorization":
        failures.append("final selection or terminal state changed")

    permissions = contract.get("permissions", {})
    expected_true = {"runtime_load", "causal_validation", "is_after_automated_causal_gate", "limited_modification_after_original_hard_gate"}
    if {key for key, value in permissions.items() if value is True} != expected_true:
        failures.append("authorization matrix changed")
    for key in ("oos", "dry_run", "api", "paper_live", "order_placement", "execution_live", "m2"):
        if permissions.get(key) is not False:
            failures.append(f"forbidden permission enabled: {key}")

    zero = contract.get("zero_state_at_adoption", {})
    if zero != {
        "freqtrade_loads": 0, "causal_validations": 0, "is_trials": 0, "selection_trial_count": 0,
        "oos_authorized": False, "oos_opened": False, "oos_runs": 0, "oos_rows_decoded": 0,
    }:
        failures.append("zero adoption state changed")
    if oos.get("oos_authorized") is not False or oos.get("oos_opened") is not False or oos.get("oos_runs") != 0 or oos.get("oos_rows_decoded") != 0:
        failures.append("OOS guard is not sealed")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"ADR-0017 current-route selection/runtime PASS: {EXPECTED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
