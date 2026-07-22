#!/usr/bin/env python3
"""Fail-closed validation for the post-runtime original-IS authority.

The ADR-0016 pre-runtime root remains immutable.  This checker validates the
append-only authority layered above it after runtime/causal validation and the
reviewed 92-boundary authority merge.  It never opens market data or results.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = Path("config/external_strategy_original_is_authority_v1.json")
EXPECTED_AUTHORITY_HASH = "32922386a3984ef96e24ed64e96771e81860b2fbf269c3baf5a46739775bf2ae"
EXPECTED_CANDIDATES = [
    "Supertrend",
    "Strategy001",
    "UniversalMACD",
    "Bandtastic",
    "Diamond",
    "Heracles",
]
OOS_START_MS = 1_726_012_800_000


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: dict) -> str:
    clone = {
        key: item
        for key, item in value.items()
        if key not in {"content_hash", "generated_utc", "generated_at_utc"}
    }
    return hashlib.sha256(
        json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def read_json(root: Path, relative: str, failures: list[str]) -> dict:
    try:
        value = json.loads((root / relative).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"cannot read {relative}: {exc}")
        return {}


def semantic_identity(value: dict) -> str | None:
    for field in ("content_hash", "canonical_content_hash"):
        item = value.get(field)
        if isinstance(item, str):
            return item
    return None


def validate_binding(root: Path, binding: object, failures: list[str], label: str) -> dict:
    if not isinstance(binding, dict):
        failures.append(f"binding is not an object: {label}")
        return {}
    path = binding.get("path")
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        failures.append(f"binding path is unsafe: {label}")
        return {}
    value = read_json(root, path, failures)
    try:
        actual_bytes = sha256_bytes(root / path)
    except OSError:
        return value
    if binding.get("byte_sha256") != actual_bytes:
        failures.append(f"binding byte hash drift: {label}")
    if "content_hash" in binding and binding.get("content_hash") != semantic_identity(value):
        failures.append(f"binding semantic hash drift: {label}")
    return value


def utc_ms(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean timestamp")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError("non-finite timestamp")
        return int(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("UTC timestamp required")
    return int(parsed.timestamp() * 1000)


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    authority = read_json(root, str(AUTHORITY_PATH), failures)
    if authority.get("schema_version") != "external-strategy-original-is-authority-v1":
        failures.append("original-IS authority schema changed")
    if authority.get("status") != "authorized_pending_first_original_is_execution":
        failures.append("original-IS authority status changed")
    if authority.get("content_hash") != canonical_hash(authority):
        failures.append("original-IS authority canonical hash mismatch")
    if authority.get("content_hash") != EXPECTED_AUTHORITY_HASH:
        failures.append("original-IS authority exact root hash mismatch")

    bindings = authority.get("bindings")
    if not isinstance(bindings, dict):
        failures.append("authority bindings missing")
        return failures
    adr17 = validate_binding(root, bindings.get("adr0017"), failures, "ADR-0017")
    adr18 = validate_binding(root, bindings.get("adr0018"), failures, "ADR-0018")
    if adr17.get("status") != "adopted_last_pre_runtime_governance_oos_sealed":
        failures.append("ADR-0017 is not adopted")
    permissions17 = adr17.get("permissions", {})
    if permissions17.get("is_after_automated_causal_gate") is not True or permissions17.get("oos") is not False:
        failures.append("ADR-0017 original-IS/OOS permissions drift")
    if adr18.get("generic_rule", {}).get("boundary_row_use") != "forced_exit_lookup_only":
        failures.append("ADR-0018 boundary isolation drift")
    if adr18.get("generic_rule", {}).get("reset_and_rewarm_required_after_any_later_readmission") is not True:
        failures.append("ADR-0018 reset/rewarm rule drift")

    pre_runtime = bindings.get("pre_runtime_contracts")
    if not isinstance(pre_runtime, dict) or set(pre_runtime) != {
        "candidate_freeze",
        "unified_is_protocol",
        "data_authority",
        "benchmark",
        "dsr_reference",
        "oos_guard",
    }:
        failures.append("pre-runtime binding set changed")
        pre_runtime = pre_runtime if isinstance(pre_runtime, dict) else {}
    pre_values = {
        name: validate_binding(root, item, failures, f"pre-runtime:{name}")
        for name, item in pre_runtime.items()
    }
    oos_guard = pre_values.get("oos_guard", {})
    expected_oos = {
        "oos_authorized": False,
        "oos_opened": False,
        "oos_runs": 0,
        "oos_rows_decoded": 0,
        "single_use_token": None,
        "result_materialized": False,
        "rerun_authorized": False,
    }
    if any(oos_guard.get(key) != value for key, value in expected_oos.items()):
        failures.append("OOS guard is not exact sealed zero state")

    route = validate_binding(root, bindings.get("runtime_route"), failures, "runtime route")
    causal = validate_binding(root, bindings.get("causal_summary"), failures, "causal summary")
    boundary = validate_binding(
        root, bindings.get("completed_boundary_authority"), failures, "completed boundary authority"
    )
    review = validate_binding(root, bindings.get("pr119_review"), failures, "PR119 review")

    if route.get("runtime_identity_hash") != "a88f0c591bc40d6acdaa3bb8e4fafe5b0dcda398f076f8f265a339caffb9eed1":
        failures.append("runtime identity drift")
    route_candidates = route.get("candidates")
    authority_candidates = authority.get("runtime_candidates")
    if not isinstance(route_candidates, list) or not isinstance(authority_candidates, list):
        failures.append("runtime candidate lists missing")
        route_candidates, authority_candidates = [], []
    if [item.get("candidate_id") for item in authority_candidates] != EXPECTED_CANDIDATES:
        failures.append("authority candidate order changed")
    if [item.get("candidate_id") for item in route_candidates] != EXPECTED_CANDIDATES:
        failures.append("runtime route candidate order changed")
    route_by_id = {str(item.get("candidate_id")): item for item in route_candidates}
    causal_rows = causal.get("results") if isinstance(causal.get("results"), list) else []
    causal_by_id = {str(item.get("candidate_id")): item for item in causal_rows}
    candidate_fields = {
        "base_adapter_hash",
        "variant_executable_hash",
        "runtime_effective_settings_hash",
        "runtime_resolved_parameters_hash",
    }
    for candidate in authority_candidates:
        candidate_id = str(candidate.get("candidate_id"))
        route_row = route_by_id.get(candidate_id, {})
        causal_row = causal_by_id.get(candidate_id, {})
        if route_row.get("load_status") != "PASS":
            failures.append(f"runtime load is not PASS: {candidate_id}")
        for field in candidate_fields:
            if not candidate.get(field) or candidate.get(field) != route_row.get(field):
                failures.append(f"runtime candidate exact hash drift: {candidate_id}:{field}")
        if causal_row.get("status") != "PASS" or candidate.get("causal_result_hash") != causal_row.get("causal_result_hash"):
            failures.append(f"causal candidate drift: {candidate_id}")
        compatibility = read_json(
            root, f"external_strategies/adapters/{candidate_id}/compatibility_manifest.json", failures
        )
        if candidate.get("compatibility_manifest_hash") != compatibility.get("content_hash"):
            failures.append(f"compatibility manifest drift: {candidate_id}")
        for field in candidate_fields:
            if candidate.get(field) != compatibility.get(field):
                failures.append(f"compatibility runtime identity drift: {candidate_id}:{field}")
        effective = compatibility.get("runtime_effective_settings", {})
        if candidate.get("timeframe") != effective.get("timeframe"):
            failures.append(f"runtime timeframe drift: {candidate_id}")
        if candidate.get("startup_candle_count") != effective.get("startup_candle_count"):
            failures.append(f"runtime startup count drift: {candidate_id}")
        if compatibility.get("observed_external_parameter_file_count") != 0 or compatibility.get("observed_config_override_count") != 0:
            failures.append(f"runtime parameter/config override drift: {candidate_id}")
    if causal.get("status") != "pass" or causal.get("pass_count") != 6 or causal.get("causal_validations") != 6:
        failures.append("causal summary six-pass Gate failed")
    if causal.get("market_or_oos_rows") != 0 or causal.get("oos_rows_decoded") != 0:
        failures.append("causal validation decoded market/OOS rows")

    records = boundary.get("records")
    required_boundary_count = bindings.get("completed_boundary_authority", {}).get("required_boundary_count")
    if not isinstance(records, list) or len(records) != required_boundary_count or len(records) != 92:
        failures.append("completed boundary authority is not exact 92/92")
        records = records if isinstance(records, list) else []
    identities: set[tuple[object, int]] = set()
    for record in records:
        try:
            symbol = record["symbol"]
            row = record["row"]
            open_ms = utc_ms(row["open_time_ms"])
            if row.get("symbol") != symbol or row.get("close_time_ms") != open_ms + 299_999:
                raise ValueError("boundary row identity or close time mismatch")
        except (KeyError, TypeError, ValueError) as exc:
            failures.append(f"invalid boundary record identity: {exc}")
            continue
        if open_ms >= OOS_START_MS:
            failures.append("boundary authority contains OOS timestamp")
        identity = (symbol, open_ms)
        if identity in identities:
            failures.append("duplicate boundary authority identity")
        identities.add(identity)
    consumption = boundary.get("runtime_consumption_contract", {})
    if consumption.get("lookup_use") != "execution_side_forced_exit_only":
        failures.append("completed authority forced-exit use drift")
    if consumption.get("append_to_candidate_ohlcv") is not False:
        failures.append("completed authority permits OHLCV append")
    if consumption.get("append_to_indicator_history") is not False:
        failures.append("completed authority permits indicator append")
    if consumption.get("future_runner_must_segment_active_intervals") is not True:
        failures.append("completed authority does not require active-interval segmentation")
    if consumption.get("inactive_interval_state_carry") is not False:
        failures.append("completed authority permits inactive-interval state carry")
    if boundary.get("completed_authority_nb01_satisfied") is not True:
        failures.append("completed authority independent construction Gate failed")

    if review.get("verdict") != "approve" or review.get("critical_findings") != 0 or review.get("high_findings") != 0:
        failures.append("PR119 independent review not approved 0/0")
    review_binding = bindings.get("pr119_review", {})
    if review.get("reviewed_head") != review_binding.get("reviewed_head"):
        failures.append("PR119 reviewed head drift")
    if review_binding.get("exact_head_gate_conclusion") != "success" or review_binding.get("exact_head_gate_run") != 29881020014:
        failures.append("PR119 exact-head Gate binding drift")
    if review_binding.get("merge_commit") != "7b6a0601588f4387f8816cf6b49bdf5bf94a18f3":
        failures.append("PR119 merge binding drift")

    execution = authority.get("execution_contract", {})
    expected_execution = {
        "candidate_order": EXPECTED_CANDIDATES,
        "required_causal_pass_count": 6,
        "original_trial_per_candidate": 1,
        "cost_scenarios": ["Base", "CostX2", "StressA", "StressB"],
        "active_interval_state": "reset_and_rewarm_per_symbol_interval",
        "boundary_rows_use": "execution_side_forced_exit_lookup_only",
        "boundary_rows_in_ohlcv_or_indicator_history": False,
        "strict_next_eligible_5m_open": True,
        "oos_start_exclusive_gate": "2024-09-11T00:00:00Z",
        "result_bundle_schema": "external-strategy-atomic-trial-bundle-v1",
        "selection_state_path": "reports/m1/evidence/external_strategy_is_state/selection_state_v1.json",
        "runtime_trial_checker": "scripts/external_strategy_original_is_trial_check.py",
        "per_trial_final_dsr_stored": False,
        "final_selection_recomputes_dsr_once": True,
    }
    if execution != expected_execution:
        failures.append("original-IS execution contract drift")
    permissions = authority.get("permissions", {})
    if permissions.get("original_is") is not True:
        failures.append("original IS is not authorized")
    for field in ("oos", "dry_run", "api_private_endpoints", "paper_live", "order_placement", "execution_live", "m2"):
        if permissions.get(field) is not False:
            failures.append(f"prohibited permission enabled: {field}")
    initial = authority.get("initial_state", {})
    if initial != {
        "freqtrade_loads": 6,
        "causal_validations": 6,
        "is_trials": 0,
        "selection_trial_count": 0,
        "oos_authorized": False,
        "oos_opened": False,
        "oos_runs": 0,
        "oos_rows_decoded": 0,
    }:
        failures.append("original-IS initial counter state drift")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("external strategy original-IS authority FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"external strategy original-IS authority PASS: {EXPECTED_AUTHORITY_HASH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
