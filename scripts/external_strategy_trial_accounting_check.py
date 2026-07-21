#!/usr/bin/env python3
"""Fail-closed ADR-0016 selection-trial accounting from append-only manifests."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".deps"))
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.unified_metrics import (
    EquityPoint,
    daily_returns,
    deflated_sharpe_ratio,
    metrics_from_equity,
)

TRIAL_DIR = Path("reports/m1/evidence/external_strategy_is_trials")
REQUIRED_COSTS = ["Base", "CostX2", "StressA", "StressB"]
REQUIRED_KINDS = ["trades", "equity", "metrics"]
ENVELOPE_FIELDS = {
    "schema_version", "trial_id", "candidate_id", "variant_id", "variant_type",
    "scenario", "kind", "candidate_freeze_hash", "unified_is_protocol_hash",
    "data_authority_hash", "benchmark_contract_hash", "dsr_reference_hash",
    "base_adapter_hash", "variant_executable_hash",
}
METRIC_FIELDS = {
    "net_return", "daily_mtm_sharpe", "psr", "dsr", "max_drawdown",
    "completed_trades", "delete_best_3_return", "profitable_subperiod_count",
    "equal_weight_benchmark", "risk_matched_benchmark", "hard_gate_status",
}


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_hash(value: object) -> str:
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in {"generated_at_utc", "content_hash"}}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def read_json(path: Path, failures: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"cannot read {path}: {exc}")
        return {}


def safe_result_path(directory: Path, relative: object, failures: list[str], trial_id: str) -> Path | None:
    text = str(relative)
    pure = PurePosixPath(text)
    if pure.is_absolute() or ".." in pure.parts or pure.name != text or not text:
        failures.append(f"unsafe trial result path: {trial_id}:{text}")
        return None
    candidate = directory / text
    try:
        if candidate.resolve().parent != directory.resolve():
            raise ValueError
    except (OSError, ValueError):
        failures.append(f"unsafe trial result path: {trial_id}:{text}")
        return None
    return candidate


def parse_utc(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("UTC timestamp required")
    return parsed.astimezone(timezone.utc)


def finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_envelope(payload: dict, manifest: dict, scenario: str, kind: str, failures: list[str]) -> None:
    trial_id = str(manifest.get("trial_id"))
    missing = sorted(ENVELOPE_FIELDS - set(payload))
    if missing:
        failures.append(f"result envelope fields missing: {trial_id}:{scenario}:{kind}:{missing}")
        return
    expected = {
        "schema_version": "external-strategy-is-result-v1", "trial_id": trial_id,
        "candidate_id": manifest.get("candidate_id"), "variant_id": manifest.get("variant_id"),
        "variant_type": manifest.get("variant_type"), "scenario": scenario, "kind": kind,
        **{field: manifest.get(field) for field in (
            "candidate_freeze_hash", "unified_is_protocol_hash", "data_authority_hash",
            "benchmark_contract_hash", "dsr_reference_hash", "base_adapter_hash",
            "variant_executable_hash",
        )},
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            failures.append(f"result envelope mismatch: {trial_id}:{scenario}:{kind}:{field}")


def validate_metrics(payload: dict, failures: list[str]) -> None:
    label = f"{payload.get('trial_id')}:{payload.get('scenario')}:metrics"
    missing = sorted(METRIC_FIELDS - set(payload))
    if missing:
        failures.append(f"metrics fields missing: {label}:{missing}")
        return
    numeric = METRIC_FIELDS - {"equal_weight_benchmark", "risk_matched_benchmark", "hard_gate_status"}
    if any(not finite_number(payload.get(field)) for field in numeric):
        failures.append(f"metrics numeric field invalid: {label}")
    if type(payload.get("completed_trades")) is not int or payload["completed_trades"] < 0:
        failures.append(f"metrics completed_trades invalid: {label}")
    for field in ("equal_weight_benchmark", "risk_matched_benchmark"):
        value = payload.get(field)
        if not isinstance(value, dict) or not value or any(not finite_number(item) for item in value.values()):
            failures.append(f"metrics benchmark invalid: {label}:{field}")
    if payload.get("hard_gate_status") not in {"pass", "failed"}:
        failures.append(f"metrics hard gate status invalid: {label}")


def validate_equity(payload: dict, protocol: dict, failures: list[str]) -> list[EquityPoint] | None:
    label = f"{payload.get('trial_id')}:{payload.get('scenario')}:equity"
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        failures.append(f"equity points empty or invalid: {label}")
        return None
    curve = protocol.get("equity_curve", {})
    try:
        anchor = date.fromisoformat(str(curve["equity_anchor_day"]))
        final = date.fromisoformat(str(curve["is_final_return_day"]))
        expected_returns = int(curve["is_return_count"])
        days = [date.fromisoformat(str(point["day"])) for point in points]
        values = [point["equity"] for point in points]
    except (KeyError, TypeError, ValueError):
        failures.append(f"equity schema invalid: {label}")
        return None
    if days[0] != anchor or days[-1] != final or len(days) != expected_returns + 1:
        failures.append(f"equity boundary/count mismatch: {label}")
    if any(current != previous + timedelta(days=1) for previous, current in zip(days, days[1:])):
        failures.append(f"equity UTC days not consecutive: {label}")
    if any(not finite_number(value) or float(value) <= 0 for value in values):
        failures.append(f"equity value invalid: {label}")
        return None
    if days[0] != anchor or days[-1] != final or len(days) != expected_returns + 1:
        return None
    if any(current != previous + timedelta(days=1) for previous, current in zip(days, days[1:])):
        return None
    return [EquityPoint(day=day_value, equity=float(equity)) for day_value, equity in zip(days, values)]


def validate_trades(payload: dict, manifest: dict, protocol: dict, failures: list[str]) -> int | None:
    label = f"{payload.get('trial_id')}:{payload.get('scenario')}:trades"
    trades = payload.get("trades")
    if not isinstance(trades, list):
        failures.append(f"trades list invalid: {label}")
        return None
    identities: set[str] = set()
    intervals: dict[str, list[tuple[datetime, datetime]]] = {}
    events: list[tuple[datetime, int, str]] = []
    stake = float(protocol.get("portfolio", {}).get("stake_amount_usdt", 0))
    calendar = protocol.get("calendar", {})
    try:
        is_start = parse_utc(calendar["is_start"])
        is_end = parse_utc(calendar["is_end_exclusive"])
        if is_end != parse_utc(calendar["sealed_oos_start"]):
            raise ValueError("IS/OOS boundary mismatch")
    except (KeyError, TypeError, ValueError):
        failures.append(f"trade calendar authority invalid: {label}")
        return None
    for item in trades:
        if not isinstance(item, dict):
            failures.append(f"trade row invalid: {label}")
            continue
        try:
            identity = str(item["trade_id"])
            pair = str(item["pair"])
            opened, closed = parse_utc(item["open_time"]), parse_utc(item["close_time"])
        except (KeyError, TypeError, ValueError):
            failures.append(f"trade identity/timestamp invalid: {label}")
            continue
        if not identity or identity in identities:
            failures.append(f"trade identity duplicated: {label}:{identity}")
        identities.add(identity)
        if closed < opened:
            failures.append(f"trade close precedes open: {label}:{identity}")
        if opened < is_start or closed >= is_end:
            failures.append(f"trade outside sealed IS interval: {label}:{identity}")
        if not finite_number(item.get("stake_amount")) or float(item["stake_amount"]) != stake:
            failures.append(f"trade fixed stake mismatch: {label}:{identity}")
        if item.get("position_increase") is not False:
            failures.append(f"trade position increase not false: {label}:{identity}")
        intervals.setdefault(pair, []).append((opened, closed))
        if closed > opened:
            events.extend(((opened, 1, pair), (closed, -1, pair)))
    for pair, rows in intervals.items():
        rows.sort()
        if any(current[0] < previous[1] for previous, current in zip(rows, rows[1:])):
            failures.append(f"same-pair trade overlap: {label}:{pair}")
    active = 0
    for _, delta, _ in sorted(events, key=lambda value: (value[0], value[1], value[2])):
        active += delta
        if active > 5:
            failures.append(f"more than five concurrent trades: {label}")
            break
    return len(trades)


def reconcile_metrics(
    metrics: dict,
    points: list[EquityPoint],
    completed_trades: int,
    tolerance: float,
    failures: list[str],
) -> float:
    label = f"{metrics.get('trial_id')}:{metrics.get('scenario')}"
    recomputed = metrics_from_equity(points)
    expected = {
        "net_return": recomputed.total_return,
        "daily_mtm_sharpe": recomputed.sharpe,
        "psr": recomputed.psr,
        "max_drawdown": recomputed.max_drawdown,
    }
    for field, value in expected.items():
        declared = metrics.get(field)
        if not finite_number(declared) or abs(float(declared) - value) > tolerance:
            failures.append(f"metrics/equity reconciliation mismatch: {label}:{field}")
    if metrics.get("completed_trades") != completed_trades:
        failures.append(f"metrics/trades completed count mismatch: {label}")
    return recomputed.sharpe


def modification_package_hash(package: dict) -> str:
    payload = {key: package.get(key) for key in ("id", "before_hash", "after_hash", "atomic_changes")}
    return semantic_hash(payload)


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    directory = root / TRIAL_DIR
    if not directory.is_dir():
        return [f"trial directory missing: {TRIAL_DIR}"]
    protocol = read_json(root / "config/external_strategy_unified_is_protocol_v1.json", failures)
    freeze = read_json(root / "config/external_strategy_candidate_freeze_v1.json", failures)
    authority = read_json(root / "config/external_strategy_data_authority_v1.json", failures)
    benchmark = read_json(root / "config/external_strategy_benchmark_v1.json", failures)
    dsr = read_json(root / "config/external_strategy_dsr_reference_trials_v1.json", failures)
    frozen = {str(item.get("id")): item for item in freeze.get("frozen_candidates", [])}
    exact_contracts = {
        "candidate_freeze_hash": freeze.get("content_hash"),
        "unified_is_protocol_hash": protocol.get("content_hash"),
        "data_authority_hash": authority.get("canonical_content_hash"),
        "benchmark_contract_hash": benchmark.get("canonical_content_hash"),
        "dsr_reference_hash": dsr.get("canonical_content_hash"),
    }

    manifest_paths = sorted(directory.glob("*.trial.json"))
    manifests = [read_json(path, failures) for path in manifest_paths]
    trial_ids: set[str] = set()
    variants: set[tuple[str, str]] = set()
    referenced: dict[str, str] = {}
    materialized = 0
    manifest_hashes: dict[str, str] = {}
    original_status: dict[str, str] = {}
    modified_candidates: list[str] = []
    modified_packages: list[tuple[object, object]] = []
    original_counts: dict[str, int] = {}
    modified_counts: dict[str, int] = {}
    trial_records: list[dict] = []
    original_records: dict[str, dict] = {}
    modified_records: list[dict] = []
    tolerance_value = protocol.get("result_reconciliation", {}).get("metric_reconciliation_absolute_error_maximum")
    try:
        tolerance = float(tolerance_value)
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError
    except (TypeError, ValueError):
        failures.append("metric reconciliation tolerance invalid")
        tolerance = 0.0
    for path, manifest in zip(manifest_paths, manifests):
        trial_failure_start = len(failures)
        required = {
            "trial_id", "candidate_id", "variant_id", "variant_type", "source_hash", "source_declaration_hash",
            "adapter_hash", "base_adapter_hash", "variant_executable_hash",
            "runtime_effective_settings_hash", "runtime_resolved_parameters_hash",
            *exact_contracts.keys(), "modification_package_id", "modification_package_hash",
            "first_materialized_utc", "performance_materialized", "cost_scenarios", "status", "append_only", "result_files",
        }
        missing = sorted(required - set(manifest))
        if missing:
            failures.append(f"trial manifest fields missing {path.name}: {missing}")
            continue
        if any(field in manifest for field in ("daily_mtm_sharpe", "base_daily_mtm_sharpe", "costx2_daily_mtm_sharpe", "selection_trial_sharpes")):
            failures.append(f"Sharpe declared outside hash-bound metrics result: {path.name}")
        trial_id = str(manifest["trial_id"])
        candidate_id = str(manifest["candidate_id"])
        variant_type = str(manifest["variant_type"])
        try:
            materialized_utc = parse_utc(manifest["first_materialized_utc"])
        except (TypeError, ValueError):
            failures.append(f"invalid first_materialized_utc: {trial_id}")
            materialized_utc = datetime.max.replace(tzinfo=timezone.utc)
        key = (candidate_id, str(manifest["variant_id"]))
        if trial_id in trial_ids:
            failures.append(f"duplicate trial_id: {trial_id}")
        if key in variants:
            failures.append(f"duplicate candidate/variant: {key}")
        trial_ids.add(trial_id)
        variants.add(key)
        candidate = frozen.get(candidate_id)
        if candidate is None:
            failures.append(f"unknown frozen candidate: {trial_id}:{candidate_id}")
        else:
            if candidate.get("adapter_hash") != candidate.get("base_adapter_hash"):
                failures.append(f"candidate base adapter identity mismatch: {trial_id}")
            expected = {
                "source_hash": candidate.get("source_sha256"),
                "source_declaration_hash": candidate.get("source_declaration_hash"),
                "adapter_hash": candidate.get("adapter_hash"),
                "base_adapter_hash": candidate.get("base_adapter_hash"),
                "runtime_effective_settings_hash": candidate.get("runtime_effective_settings_hash"),
                "runtime_resolved_parameters_hash": candidate.get("runtime_resolved_parameters_hash"),
            }
            for field, value in expected.items():
                if manifest.get(field) != value:
                    failures.append(f"trial exact hash mismatch: {trial_id}:{field}")
        for field, value in exact_contracts.items():
            if manifest.get(field) != value:
                failures.append(f"trial exact hash mismatch: {trial_id}:{field}")
        if variant_type not in {"original", "modified"}:
            failures.append(f"invalid variant_type: {trial_id}")
        if manifest["status"] not in {"pass", "failed"}:
            failures.append(f"invalid trial status: {trial_id}")
        if manifest["append_only"] is not True:
            failures.append(f"trial not append-only: {trial_id}")
        if manifest["cost_scenarios"] != REQUIRED_COSTS:
            failures.append(f"cost scenarios not one four-cost trial: {trial_id}")
        if type(manifest["performance_materialized"]) is not bool:
            failures.append(f"performance_materialized is not strict boolean: {trial_id}")
        performance_materialized = manifest["performance_materialized"] is True
        if variant_type == "original":
            original_counts[candidate_id] = original_counts.get(candidate_id, 0) + 1
            if manifest["modification_package_id"] is not None or manifest["modification_package_hash"] is not None:
                failures.append(f"original trial has modification package: {trial_id}")
            if manifest.get("variant_executable_hash") != manifest.get("base_adapter_hash"):
                failures.append(f"original executable identity mismatch: {trial_id}")
        elif variant_type == "modified":
            modified_counts[candidate_id] = modified_counts.get(candidate_id, 0) + 1
            modified_candidates.append(candidate_id)
            package = candidate.get("modification_package", {}) if candidate else {}
            package_fields = {"id", "before_hash", "after_hash", "atomic_changes", "package_hash"}
            if set(package) != package_fields or package.get("id") is None or package.get("package_hash") is None:
                failures.append(f"modified trial lacks preregistered package: {trial_id}")
            if manifest["modification_package_id"] != package.get("id") or manifest["modification_package_hash"] != package.get("package_hash"):
                failures.append(f"modified trial package mismatch: {trial_id}")
            if package.get("before_hash") != manifest.get("base_adapter_hash") or package.get("after_hash") == package.get("before_hash"):
                failures.append(f"modified package executable transition invalid: {trial_id}")
            changes = package.get("atomic_changes")
            if not isinstance(changes, list) or not 1 <= len(changes) <= 2:
                failures.append(f"modified package atomic change count invalid: {trial_id}")
            if package.get("package_hash") != modification_package_hash(package):
                failures.append(f"modified package hash mismatch: {trial_id}")
            if manifest.get("variant_executable_hash") != package.get("after_hash"):
                failures.append(f"modified executable identity mismatch: {trial_id}")
            modified_packages.append((manifest["modification_package_id"], manifest["modification_package_hash"]))

        result_files = manifest["result_files"]
        if not isinstance(result_files, list):
            failures.append(f"result_files not a list: {trial_id}")
            result_files = []
        metrics_by_scenario: dict[str, dict] = {}
        equity_by_scenario: dict[str, list[EquityPoint]] = {}
        trade_counts: dict[str, int] = {}
        trial_sharpes: dict[str, float] = {}
        if performance_materialized:
            materialized += 1
            for name in ("adapter_hash", "base_adapter_hash", "variant_executable_hash", "runtime_effective_settings_hash", "runtime_resolved_parameters_hash"):
                if not manifest.get(name):
                    failures.append(f"runtime hash missing for materialized trial: {trial_id}:{name}")
            expected_pairs = {(scenario, kind) for scenario in REQUIRED_COSTS for kind in REQUIRED_KINDS}
            actual_pairs: set[tuple[str, str]] = set()
            for result in result_files:
                if not isinstance(result, dict):
                    failures.append(f"invalid result descriptor: {trial_id}")
                    continue
                if set(result) != {"path", "kind", "scenario", "byte_sha256", "semantic_hash"}:
                    failures.append(f"result descriptor fields changed: {trial_id}")
                    continue
                pair = (str(result["scenario"]), str(result["kind"]))
                if pair in actual_pairs:
                    failures.append(f"duplicate trial result scenario/kind: {trial_id}:{pair}")
                actual_pairs.add(pair)
                result_path = safe_result_path(directory, result["path"], failures, trial_id)
                if result_path is None:
                    continue
                name = result_path.name
                if name in referenced:
                    failures.append(f"cross-trial result reuse: {name}:{referenced[name]}:{trial_id}")
                referenced[name] = trial_id
                if not result_path.is_file():
                    failures.append(f"trial result missing: {trial_id}:{name}")
                    continue
                if sha256_bytes(result_path) != result["byte_sha256"]:
                    failures.append(f"trial result byte hash mismatch: {trial_id}:{name}")
                parsed = read_json(result_path, failures)
                if semantic_hash(parsed) != result["semantic_hash"]:
                    failures.append(f"trial result semantic hash mismatch: {trial_id}:{name}")
                validate_envelope(parsed, manifest, str(result["scenario"]), str(result["kind"]), failures)
                if result["kind"] == "metrics":
                    validate_metrics(parsed, failures)
                    metrics_by_scenario[str(result["scenario"])] = parsed
                elif result["kind"] == "equity":
                    points = validate_equity(parsed, protocol, failures)
                    if points is not None:
                        equity_by_scenario[str(result["scenario"])] = points
                elif result["kind"] == "trades":
                    completed = validate_trades(parsed, manifest, protocol, failures)
                    if completed is not None:
                        trade_counts[str(result["scenario"])] = completed
            if actual_pairs != expected_pairs:
                failures.append(f"trial result four-cost coverage mismatch: {trial_id}")
            for scenario in REQUIRED_COSTS:
                if scenario not in metrics_by_scenario or scenario not in equity_by_scenario or scenario not in trade_counts:
                    failures.append(f"trial result reconciliation inputs missing: {trial_id}:{scenario}")
                    continue
                recomputed_sharpe = reconcile_metrics(
                    metrics_by_scenario[scenario], equity_by_scenario[scenario], trade_counts[scenario], tolerance, failures
                )
                if scenario in {"Base", "CostX2"}:
                    trial_sharpes[scenario] = recomputed_sharpe
            if set(trial_sharpes) != {"Base", "CostX2"}:
                failures.append(f"DSR reconciled Sharpe inputs missing: {trial_id}")
        elif result_files:
            failures.append(f"unmaterialized trial references result files: {trial_id}")
        if not performance_materialized and manifest.get("status") == "pass":
            failures.append(f"unmaterialized trial cannot declare pass: {trial_id}")
        record = {
            "trial_id": trial_id,
            "candidate_id": candidate_id,
            "variant_type": variant_type,
            "materialized_utc": materialized_utc,
            "performance_materialized": performance_materialized,
            "status": manifest.get("status"),
            "metrics": metrics_by_scenario,
            "equity": equity_by_scenario,
            "sharpes": trial_sharpes,
            "valid": len(failures) == trial_failure_start,
        }
        trial_records.append(record)
        if variant_type == "original":
            original_records[candidate_id] = record
        elif variant_type == "modified":
            modified_records.append(record)
        manifest_hashes[path.name] = sha256_bytes(path)

    for candidate_id, count in original_counts.items():
        if count > 1:
            failures.append(f"more than one original manifest: {candidate_id}")
    for candidate_id, count in modified_counts.items():
        if count > 1:
            failures.append(f"more than one modified manifest: {candidate_id}")
    if len(set(modified_candidates)) > 3:
        failures.append("more than three modified candidates")
    nonempty_packages = [item for item in modified_packages if item != (None, None)]
    if len(nonempty_packages) != len(set(nonempty_packages)):
        failures.append("modified trials do not bind unique preregistered packages")
    for path in sorted(directory.iterdir()):
        if path.name.startswith(".") or path.name.endswith(".trial.json"):
            continue
        if path.name not in referenced:
            failures.append(f"orphan IS result: {path.name}")

    try:
        ledger = yaml.safe_load((root / "STRATEGY_TRIAL_LEDGER.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        failures.append(f"cannot read trial ledger: {exc}")
        ledger = {}
    rules = ledger.get("rules", {}) if isinstance(ledger, dict) else {}
    for label, value in (
        ("ledger", rules.get("selection_trial_count")),
        ("protocol", protocol.get("multiple_testing", {}).get("selection_trial_count")),
        ("candidate freeze", freeze.get("selection_trial_count")),
        ("DSR reference", dsr.get("selection_trial_count")),
    ):
        if value != materialized:
            failures.append(f"{label} selection_trial_count drift: {value} != {materialized}")
    if rules.get("historical_opened_oos_trial_count") != 3 or rules.get("dsr_trial_count_formula") != "3 + selection_trial_count":
        failures.append("ledger DSR formula changed")
    if dsr.get("required_trial_count") != 3 + materialized:
        failures.append("DSR reference trial count mismatch")
    materialized_records = [record for record in trial_records if record["performance_materialized"]]
    ordered = sorted(materialized_records, key=lambda item: (item["materialized_utc"], item["trial_id"]))
    derived = {
        scenario: [item["sharpes"][scenario] for item in ordered if scenario in item["sharpes"]]
        for scenario in ("Base", "CostX2")
    }
    declared = dsr.get("selection_trial_sharpes", {})
    if not isinstance(declared, dict) or set(declared) != {"Base", "CostX2"}:
        failures.append("DSR selection Sharpe scenarios must be exactly Base and CostX2")
        declared = declared if isinstance(declared, dict) else {}
    for scenario in ("Base", "CostX2"):
        if declared.get(scenario) != derived[scenario]:
            failures.append(f"DSR selection Sharpe sequence mismatch: {scenario}")
        if len(derived[scenario]) != materialized:
            failures.append(f"DSR selection Sharpe sequence length mismatch: {scenario}")
        if len(dsr.get("historical", {}).get(scenario, [])) + len(derived[scenario]) != dsr.get("required_trial_count"):
            failures.append(f"DSR total Sharpe sequence length mismatch: {scenario}")
    for record in materialized_records:
        for scenario in ("Base", "CostX2"):
            metrics = record["metrics"].get(scenario)
            points = record["equity"].get(scenario)
            if metrics is None or points is None:
                continue
            sequence = [float(value) for value in dsr.get("historical", {}).get(scenario, [])] + derived[scenario]
            recomputed_dsr = deflated_sharpe_ratio(daily_returns(points), sequence)
            if not finite_number(metrics.get("dsr")) or abs(float(metrics["dsr"]) - recomputed_dsr) > tolerance:
                failures.append(f"DSR/equity reconciliation mismatch: {record['trial_id']}:{scenario}")
                record["valid"] = False
    for record in modified_records:
        original = original_records.get(record["candidate_id"])
        original_pass = bool(
            original
            and original["performance_materialized"]
            and original["status"] == "pass"
            and original["valid"]
            and all(original["metrics"].get(scenario, {}).get("hard_gate_status") == "pass" for scenario in ("Base", "CostX2"))
        )
        if not original_pass:
            failures.append(f"modified trial cannot rescue absent, unmaterialized, failed, or unreconciled original: {record['candidate_id']}")
        elif original["materialized_utc"] >= record["materialized_utc"]:
            failures.append(f"modified trial must materialize strictly after original: {record['candidate_id']}")
    if rules.get("selection_trial_manifest_hashes", {}) != manifest_hashes:
        failures.append("append-only trial manifest hash ledger mismatch")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("external strategy trial accounting FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("external strategy trial accounting PASS: selection_trial_count=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
