#!/usr/bin/env python3
"""Validate append-only post-runtime original-IS trial bundles and DSR state."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".deps"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from btc_eth_dual_quant.audit.external_strategy_trial_bundle import (
    KINDS,
    SCENARIOS,
    TrialBundleError,
    byte_hash,
    materialized_trial_ids,
    semantic_hash,
    validate_trial_bundle,
)
from btc_eth_dual_quant.audit.unified_metrics import EquityPoint, metrics_from_equity
from external_strategy_original_is_authority_check import validate as validate_authority


ROOT = Path(__file__).resolve().parents[1]
TRIAL_ROOT = Path("reports/m1/evidence/external_strategy_is_trials")
STATE_PATH = Path("reports/m1/evidence/external_strategy_is_state/selection_state_v1.json")
METRIC_FIELDS = {
    "net_return",
    "daily_mtm_sharpe",
    "psr",
    "max_drawdown",
    "completed_trades",
    "delete_best_3_return",
    "profitable_subperiod_count",
    "equal_weight_benchmark",
    "risk_matched_benchmark",
    "hard_gate_status",
}


def read_json(path: Path, failures: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"cannot read {path}: {exc}")
        return {}


def canonical_hash(value: dict) -> str:
    clone = {
        key: item
        for key, item in value.items()
        if key not in {"content_hash", "generated_utc", "generated_at_utc"}
    }
    return hashlib.sha256(
        json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def parse_utc(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("UTC timestamp required")
    return parsed.astimezone(timezone.utc)


def result_payloads(directory: Path, failures: list[str], trial_id: str) -> dict[tuple[str, str], dict]:
    manifest = read_json(directory / "trial.bundle.json", failures)
    results: dict[tuple[str, str], dict] = {}
    for descriptor in manifest.get("result_files", []):
        if not isinstance(descriptor, dict):
            continue
        scenario, kind = str(descriptor.get("scenario")), str(descriptor.get("kind"))
        path_text = descriptor.get("path")
        if not isinstance(path_text, str):
            continue
        result_path = directory.parent / path_text
        payload = read_json(result_path, failures)
        results[(scenario, kind)] = payload
    expected = {(scenario, kind) for scenario in SCENARIOS for kind in KINDS}
    if set(results) != expected:
        failures.append(f"trial result coverage mismatch: {trial_id}")
    return results


def validate_equity(payload: dict, protocol: dict, failures: list[str], label: str) -> list[EquityPoint] | None:
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        failures.append(f"equity points empty: {label}")
        return None
    curve = protocol.get("equity_curve", {})
    try:
        anchor = date.fromisoformat(str(curve["equity_anchor_day"]))
        final = date.fromisoformat(str(curve["is_final_return_day"]))
        expected_returns = int(curve["is_return_count"])
        days = [date.fromisoformat(str(item["day"])) for item in points]
        values = [item["equity"] for item in points]
    except (KeyError, TypeError, ValueError):
        failures.append(f"equity schema invalid: {label}")
        return None
    if days[0] != anchor or days[-1] != final or len(days) != expected_returns + 1:
        failures.append(f"equity half-open boundary/count mismatch: {label}")
        return None
    if any(current != previous + timedelta(days=1) for previous, current in zip(days, days[1:])):
        failures.append(f"equity UTC days not consecutive: {label}")
        return None
    if any(not finite_number(value) or float(value) <= 0 for value in values):
        failures.append(f"equity values invalid: {label}")
        return None
    return [EquityPoint(day=day_value, equity=float(value)) for day_value, value in zip(days, values)]


def validate_trades(payload: dict, protocol: dict, failures: list[str], label: str) -> int | None:
    trades = payload.get("trades")
    if not isinstance(trades, list):
        failures.append(f"trades list invalid: {label}")
        return None
    try:
        is_start = parse_utc(protocol["calendar"]["is_start"])
        is_end = parse_utc(protocol["calendar"]["is_end_exclusive"])
        fixed_stake = float(protocol["portfolio"]["stake_amount_usdt"])
        maximum = int(protocol["portfolio"]["maximum_open_trades"])
    except (KeyError, TypeError, ValueError):
        failures.append(f"trade protocol authority invalid: {label}")
        return None
    identities: set[str] = set()
    by_pair: dict[str, list[tuple[datetime, datetime]]] = {}
    events: list[tuple[datetime, int, str]] = []
    for trade in trades:
        if not isinstance(trade, dict):
            failures.append(f"trade row invalid: {label}")
            continue
        try:
            trade_id = str(trade["trade_id"])
            pair = str(trade["pair"])
            opened = parse_utc(trade["open_time"])
            closed = parse_utc(trade["close_time"])
        except (KeyError, TypeError, ValueError):
            failures.append(f"trade identity/timestamp invalid: {label}")
            continue
        if not trade_id or trade_id in identities:
            failures.append(f"trade identity duplicated: {label}:{trade_id}")
        identities.add(trade_id)
        if closed < opened or opened < is_start or closed >= is_end:
            failures.append(f"trade outside sealed IS interval: {label}:{trade_id}")
        if not finite_number(trade.get("stake_amount")) or float(trade["stake_amount"]) != fixed_stake:
            failures.append(f"trade fixed stake mismatch: {label}:{trade_id}")
        if trade.get("position_increase") is not False:
            failures.append(f"trade position increase not false: {label}:{trade_id}")
        by_pair.setdefault(pair, []).append((opened, closed))
        if closed > opened:
            events.extend(((opened, 1, pair), (closed, -1, pair)))
    for pair, intervals in by_pair.items():
        intervals.sort()
        if any(current[0] < previous[1] for previous, current in zip(intervals, intervals[1:])):
            failures.append(f"same-pair trade overlap: {label}:{pair}")
    active = 0
    for _, delta, _ in sorted(events, key=lambda item: (item[0], item[1], item[2])):
        active += delta
        if active > maximum or active < 0:
            failures.append(f"trade concurrency invalid: {label}")
            break
    return len(trades)


def validate_metrics(payload: dict, failures: list[str], label: str) -> None:
    missing = sorted(METRIC_FIELDS - set(payload))
    if missing:
        failures.append(f"metrics fields missing: {label}:{missing}")
        return
    numeric = METRIC_FIELDS - {"equal_weight_benchmark", "risk_matched_benchmark", "hard_gate_status"}
    if any(not finite_number(payload.get(field)) for field in numeric):
        failures.append(f"metrics numeric field invalid: {label}")
    if type(payload.get("completed_trades")) is not int or payload.get("completed_trades", -1) < 0:
        failures.append(f"metrics completed trades invalid: {label}")
    if payload.get("hard_gate_status") not in {"pass", "failed"}:
        failures.append(f"metrics hard Gate status invalid: {label}")
    for field in ("equal_weight_benchmark", "risk_matched_benchmark"):
        value = payload.get(field)
        if not isinstance(value, dict) or not value or any(not finite_number(item) for item in value.values()):
            failures.append(f"metrics benchmark invalid: {label}:{field}")
    if "dsr" in payload:
        failures.append(f"per-trial final DSR must not be stored: {label}")
    if "dsr_at_materialization" in payload and not finite_number(payload["dsr_at_materialization"]):
        failures.append(f"DSR-at-materialization invalid: {label}")


def validate_manifest_contract(
    envelope: dict,
    *,
    candidate_freeze: dict,
    runtime_authority: dict,
    protocol: dict,
    data_authority: dict,
    benchmark: dict,
    dsr_reference: dict,
    failures: list[str],
    trial_id: str,
) -> None:
    frozen = {str(item.get("id")): item for item in candidate_freeze.get("frozen_candidates", [])}
    runtime = {str(item.get("candidate_id")): item for item in runtime_authority.get("runtime_candidates", [])}
    candidate_id = str(envelope.get("candidate_id"))
    candidate, runtime_candidate = frozen.get(candidate_id), runtime.get(candidate_id)
    if candidate is None or runtime_candidate is None:
        failures.append(f"unknown candidate: {trial_id}:{candidate_id}")
        return
    exact = {
        "source_hash": candidate.get("source_sha256"),
        "source_declaration_hash": candidate.get("source_declaration_hash"),
        "candidate_freeze_hash": candidate_freeze.get("content_hash"),
        "unified_is_protocol_hash": protocol.get("content_hash"),
        "data_authority_hash": data_authority.get("canonical_content_hash"),
        "benchmark_contract_hash": benchmark.get("canonical_content_hash"),
        "dsr_reference_hash": dsr_reference.get("canonical_content_hash"),
        "original_is_authority_hash": runtime_authority.get("content_hash"),
        "runtime_route_manifest_hash": runtime_authority.get("bindings", {}).get("runtime_route", {}).get("content_hash"),
        "causal_summary_hash": runtime_authority.get("bindings", {}).get("causal_summary", {}).get("content_hash"),
        "boundary_authority_hash": runtime_authority.get("bindings", {}).get("completed_boundary_authority", {}).get("content_hash"),
        "base_adapter_hash": runtime_candidate.get("base_adapter_hash"),
        "variant_executable_hash": runtime_candidate.get("variant_executable_hash"),
        "runtime_effective_settings_hash": runtime_candidate.get("runtime_effective_settings_hash"),
        "runtime_resolved_parameters_hash": runtime_candidate.get("runtime_resolved_parameters_hash"),
    }
    for field, expected in exact.items():
        if not expected or envelope.get(field) != expected:
            failures.append(f"trial exact identity mismatch: {trial_id}:{field}")
    if envelope.get("append_only") is not True:
        failures.append(f"trial is not append-only: {trial_id}")
    try:
        parse_utc(envelope.get("first_materialized_utc"))
    except (TypeError, ValueError):
        failures.append(f"invalid first_materialized_utc: {trial_id}")
    variant_type = envelope.get("variant_type")
    if variant_type == "original":
        if envelope.get("variant_id") != "original-v1":
            failures.append(f"original variant identity drift: {trial_id}")
        if envelope.get("modification_package_id") is not None or envelope.get("modification_package_hash") is not None:
            failures.append(f"original trial has modification package: {trial_id}")
    elif variant_type == "modified":
        package = candidate.get("modification_package", {})
        if not package.get("id") or not package.get("package_hash"):
            failures.append(f"modified trial lacks preregistered package: {trial_id}")
        if envelope.get("modification_package_id") != package.get("id") or envelope.get("modification_package_hash") != package.get("package_hash"):
            failures.append(f"modified trial package mismatch: {trial_id}")
    else:
        failures.append(f"invalid variant type: {trial_id}")


def validate(root: Path = ROOT) -> list[str]:
    failures = list(validate_authority(root))
    trial_root = root / TRIAL_ROOT
    if not trial_root.is_dir():
        return failures + [f"trial directory missing: {TRIAL_ROOT}"]
    authority = read_json(root / "config/external_strategy_original_is_authority_v1.json", failures)
    freeze = read_json(root / "config/external_strategy_candidate_freeze_v1.json", failures)
    protocol = read_json(root / "config/external_strategy_unified_is_protocol_v1.json", failures)
    data_authority = read_json(root / "config/external_strategy_data_authority_v1.json", failures)
    benchmark = read_json(root / "config/external_strategy_benchmark_v1.json", failures)
    dsr_reference = read_json(root / "config/external_strategy_dsr_reference_trials_v1.json", failures)
    state = read_json(root / STATE_PATH, failures)
    if state.get("content_hash") != canonical_hash(state):
        failures.append("selection state canonical hash mismatch")

    try:
        trial_ids = materialized_trial_ids(trial_root)
    except TrialBundleError as exc:
        failures.append(f"invalid materialized trial bundle: {exc}")
        trial_ids = ()
    records: list[dict] = []
    original_by_candidate: dict[str, dict] = {}
    modified_by_candidate: dict[str, dict] = {}
    for trial_id in trial_ids:
        directory = trial_root / trial_id
        try:
            receipt = validate_trial_bundle(trial_root, trial_id)
        except TrialBundleError as exc:
            failures.append(f"invalid trial bundle {trial_id}: {exc}")
            continue
        if not receipt.governance_complete:
            failures.append(f"trial governance marker missing: {trial_id}")
        manifest = read_json(directory / "trial.bundle.json", failures)
        envelope = manifest.get("base_envelope")
        if not isinstance(envelope, dict):
            failures.append(f"trial base envelope missing: {trial_id}")
            continue
        validate_manifest_contract(
            envelope,
            candidate_freeze=freeze,
            runtime_authority=authority,
            protocol=protocol,
            data_authority=data_authority,
            benchmark=benchmark,
            dsr_reference=dsr_reference,
            failures=failures,
            trial_id=trial_id,
        )
        payloads = result_payloads(directory, failures, trial_id)
        sharpes: dict[str, float] = {}
        hard_gates: dict[str, str] = {}
        for scenario in SCENARIOS:
            metrics = payloads.get((scenario, "metrics"), {})
            equity = payloads.get((scenario, "equity"), {})
            trades = payloads.get((scenario, "trades"), {})
            label = f"{trial_id}:{scenario}"
            validate_metrics(metrics, failures, label)
            points = validate_equity(equity, protocol, failures, label)
            count = validate_trades(trades, protocol, failures, label)
            if points is not None and count is not None:
                recomputed = metrics_from_equity(points)
                expected = {
                    "net_return": recomputed.total_return,
                    "daily_mtm_sharpe": recomputed.sharpe,
                    "psr": recomputed.psr,
                    "max_drawdown": recomputed.max_drawdown,
                }
                tolerance = float(protocol.get("result_reconciliation", {}).get("metric_reconciliation_absolute_error_maximum", 0))
                for field, value in expected.items():
                    if not finite_number(metrics.get(field)) or abs(float(metrics[field]) - value) > tolerance:
                        failures.append(f"metrics/equity reconciliation mismatch: {label}:{field}")
                if metrics.get("completed_trades") != count:
                    failures.append(f"metrics/trades count mismatch: {label}")
                if scenario in {"Base", "CostX2"}:
                    sharpes[scenario] = recomputed.sharpe
            hard_gates[scenario] = str(metrics.get("hard_gate_status"))
        try:
            materialized = parse_utc(envelope.get("first_materialized_utc"))
        except (TypeError, ValueError):
            materialized = datetime.max.replace(tzinfo=timezone.utc)
        record = {
            "trial_id": trial_id,
            "candidate_id": str(envelope.get("candidate_id")),
            "variant_type": str(envelope.get("variant_type")),
            "first_materialized_utc": materialized,
            "bundle_content_hash": receipt.bundle_content_hash,
            "sharpes": sharpes,
            "hard_gates": hard_gates,
        }
        records.append(record)
        target = original_by_candidate if record["variant_type"] == "original" else modified_by_candidate
        if record["candidate_id"] in target:
            failures.append(f"more than one {record['variant_type']} trial: {record['candidate_id']}")
        target[record["candidate_id"]] = record

    if len(modified_by_candidate) > 3:
        failures.append("more than three modified candidates")
    for candidate_id, modified in modified_by_candidate.items():
        original = original_by_candidate.get(candidate_id)
        if original is None or original["first_materialized_utc"] >= modified["first_materialized_utc"]:
            failures.append(f"modified trial lacks earlier original: {candidate_id}")
            continue
        if any(original["hard_gates"].get(scenario) != "pass" for scenario in ("Base", "CostX2")):
            failures.append(f"modified trial cannot rescue failed original: {candidate_id}")

    ordered = sorted(records, key=lambda item: (item["first_materialized_utc"], item["trial_id"]))
    derived_order = [item["trial_id"] for item in ordered]
    derived_hashes = {item["trial_id"]: item["bundle_content_hash"] for item in ordered}
    derived_sharpes = {
        scenario: [item["sharpes"][scenario] for item in ordered if scenario in item["sharpes"]]
        for scenario in ("Base", "CostX2")
    }
    incident_hashes: dict[str, str] = {}
    incident_dir = trial_root / ".incidents"
    if incident_dir.is_dir():
        for path in sorted(incident_dir.glob("*.json")):
            payload = read_json(path, failures)
            if payload.get("content_hash") != semantic_hash({key: value for key, value in payload.items() if key != "content_hash"}):
                failures.append(f"incident canonical hash mismatch: {path.name}")
            if payload.get("performance_materialized") is not False or payload.get("result_values_recorded") is not False:
                failures.append(f"incident contains performance materialization: {path.name}")
            incident_hashes[path.name] = byte_hash(path.read_bytes())

    count = len(ordered)
    expected_status = "zero_trials_pending_first_original_is" if count == 0 else "original_is_trials_materialized_append_only"
    expected_state = {
        "schema_version": "external-strategy-selection-state-v1",
        "status": expected_status,
        "original_is_authority_hash": authority.get("content_hash"),
        "frozen_dsr_reference_hash": dsr_reference.get("canonical_content_hash"),
        "historical_opened_oos_trial_count": 3,
        "selection_trial_count": count,
        "required_trial_count": 3 + count,
        "trial_order": derived_order,
        "trial_bundle_hashes": derived_hashes,
        "selection_trial_sharpes": derived_sharpes,
        "incident_hashes": incident_hashes,
        "final_selection_materialized": False,
        "oos_authorized": False,
        "oos_opened": False,
        "oos_runs": 0,
        "oos_rows_decoded": 0,
    }
    for field, value in expected_state.items():
        if state.get(field) != value:
            failures.append(f"selection state drift: {field}")
    if set(state) != set(expected_state) | {"content_hash"}:
        failures.append("selection state fields changed")
    if any(len(derived_sharpes[scenario]) != count for scenario in ("Base", "CostX2")):
        failures.append("DSR selection sequence length mismatch")
    if set(state.get("selection_trial_sharpes", {})) != {"Base", "CostX2"}:
        failures.append("DSR scenarios must be exactly Base and CostX2")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("external strategy original-IS trial accounting FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    state = json.loads((ROOT / STATE_PATH).read_text(encoding="utf-8"))
    print(
        "external strategy original-IS trial accounting PASS: "
        f"selection_trial_count={state['selection_trial_count']} oos_rows=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
