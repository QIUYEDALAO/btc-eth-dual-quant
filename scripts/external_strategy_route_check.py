#!/usr/bin/env python3
"""Explicit fail-closed checker for ADR-0016; safe under ``python -O``."""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".deps"))
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ADR0016_PRE_RUNTIME_FREEZE_SHA256 = "aafbf0628109668b9d8c1ba193c54d8443c04e660cd105c899d66e6f1a172bc8"
ORIGINAL_U25_HASHES = {
    "config/u25_design_authorization_v1.json": "1d78f62bdf9284bd57619935f3e2e94d4ced15a403f058bff6fee3e91e0c5482",
    "reports/m0/U25_DESIGN_AUTHORIZATION_DECISION.md": "1033f7ba91540627609ef4e437099bd3add19f5eeb750827a91ffb6a303dc35d",
}
EXPECTED_STAGES = [
    "EXTERNAL-STRATEGY-SOURCE-INVENTORY", "EXTERNAL-STRATEGY-STATIC-SCREEN",
    "EXTERNAL-STRATEGY-CANDIDATE-FREEZE", "EXTERNAL-STRATEGY-COMPATIBILITY",
    "EXTERNAL-STRATEGY-CAUSAL-VALIDATION", "EXTERNAL-STRATEGY-ORIGINAL-IS",
    "EXTERNAL-STRATEGY-LIMITED-MODIFICATION", "EXTERNAL-STRATEGY-SELECTION",
    "EXTERNAL-STRATEGY-INDEPENDENT-AUDIT", "EXTERNAL-STRATEGY-OOS-PENDING-AUTHORIZATION",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def canonical_hash(value: dict) -> str:
    clone = dict(value)
    clone.pop("content_hash", None)
    return sha256(json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def canonical_named_hash(value: dict, name: str) -> str:
    clone = dict(value)
    clone.pop(name, None)
    return sha256(json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def selection_key(value: dict) -> tuple:
    """Exact ADR-0016 deterministic winner ordering; lower tuple wins."""
    return (
        0 if value["all_hard_gates_pass"] else 1,
        -float(value["base_dsr"]),
        -float(value["costx2_dsr"]),
        -float(value["costx2_daily_mtm_sharpe"]),
        float(value["costx2_max_drawdown"]),
        float(value["turnover"]),
        str(value["candidate_id"]),
    )


def read_json(root: Path, path: str, failures: list[str]):
    try:
        return json.loads((root / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"cannot read {path}: {exc}")
        return {}


def member_map(archive: Path, failures: list[str]) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle.getmembers():
                if member.isfile() and "/" in member.name:
                    handle = bundle.extractfile(member)
                    if handle is not None:
                        found[member.name.split("/", 1)[1]] = handle.read()
    except (OSError, tarfile.TarError) as exc:
        failures.append(f"cannot read upstream archive {archive}: {exc}")
    return found


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    root_freeze_path = root / "config/adr0016_pre_runtime_contract_freeze_v1.json"
    try:
        root_freeze_bytes = root_freeze_path.read_bytes()
    except OSError as exc:
        return [f"cannot read pre-runtime root freeze: {exc}"]
    if sha256(root_freeze_bytes) != EXPECTED_ADR0016_PRE_RUNTIME_FREEZE_SHA256:
        failures.append("pre-runtime root freeze byte hash mismatch")
    root_freeze = read_json(root, "config/adr0016_pre_runtime_contract_freeze_v1.json", failures)
    for relative, expected in root_freeze.get("contract_files", {}).items():
        try:
            actual = sha256((root / relative).read_bytes())
        except OSError as exc:
            failures.append(f"root-frozen contract missing: {relative}: {exc}")
            continue
        if actual != expected:
            failures.append(f"root-frozen contract byte mismatch: {relative}")
    expected_permissions = {"runtime_load": False, "causal_validation": False, "is": False, "oos": False, "dry_run": False, "api_live": False, "m2": False}
    if root_freeze.get("permissions") != expected_permissions:
        failures.append("pre-runtime root permissions changed")
    paths = {
        "inventory": "config/external_strategy_inventory_v1.json",
        "screen": "reports/m1/evidence/external_strategy_source_screen_v1.json",
        "freeze": "config/external_strategy_candidate_freeze_v1.json",
        "protocol": "config/external_strategy_unified_is_protocol_v1.json",
        "supersession": "config/u25_existing_strategy_supersession_v1.json",
        "oos_guard": "config/external_strategy_oos_guard_v1.json",
        "data_authority": "config/external_strategy_data_authority_v1.json",
        "benchmark": "config/external_strategy_benchmark_v1.json",
        "dsr_reference": "config/external_strategy_dsr_reference_trials_v1.json",
    }
    inv = read_json(root, paths["inventory"], failures)
    evidence = read_json(root, paths["screen"], failures)
    freeze = read_json(root, paths["freeze"], failures)
    protocol = read_json(root, paths["protocol"], failures)
    supersession = read_json(root, paths["supersession"], failures)
    oos = read_json(root, paths["oos_guard"], failures)
    data_authority = read_json(root, paths["data_authority"], failures)
    benchmark = read_json(root, paths["benchmark"], failures)
    dsr_reference = read_json(root, paths["dsr_reference"], failures)
    adr = read_json(root, "config/adr0016_existing_strategy_route_v1.json", failures)
    exact = adr.get("exact_hashes", {})
    if exact.get("adr_document_bytes_sha256") != sha256((root / "docs/decisions/ADR-0016-existing-strategy-adaptation-route.md").read_bytes()):
        failures.append("ADR-0016 document byte hash mismatch")
    exact_keys = {"protocol": "unified_is_protocol_bytes_sha256", "data_authority": "data_authority_bytes_sha256", "benchmark": "benchmark_contract_bytes_sha256", "dsr_reference": "dsr_reference_bytes_sha256"}
    for key, path in paths.items():
        expected = exact.get(exact_keys.get(key, f"{key}_bytes_sha256"))
        actual = sha256((root / path).read_bytes())
        if expected != actual:
            failures.append(f"ADR exact byte hash mismatch: {path}")
    trial_checker_path = root / str(adr.get("result_evidence_checker", ""))
    try:
        trial_checker_hash = sha256(trial_checker_path.read_bytes())
    except OSError as exc:
        failures.append(f"result evidence checker missing: {exc}")
    else:
        if exact.get("trial_checker_bytes_sha256") != trial_checker_hash:
            failures.append("result evidence checker byte hash mismatch")
    if evidence.get("inventory_sha256") != sha256((root / paths["inventory"]).read_bytes()):
        failures.append("inventory byte hash mismatch")
    if evidence.get("content_hash") != canonical_hash(evidence):
        failures.append("screen canonical hash mismatch")
    if freeze.get("content_hash") != canonical_hash(freeze):
        failures.append("freeze canonical hash mismatch")
    if protocol.get("content_hash") != canonical_hash(protocol) or protocol.get("content_hash") != exact.get("unified_is_protocol_content_hash"):
        failures.append("unified IS protocol canonical hash mismatch")
    if data_authority.get("canonical_content_hash") != canonical_named_hash(data_authority, "canonical_content_hash") or data_authority.get("canonical_content_hash") != exact.get("data_authority_content_hash"):
        failures.append("data authority canonical hash mismatch")
    if benchmark.get("canonical_content_hash") != canonical_named_hash(benchmark, "canonical_content_hash") or benchmark.get("canonical_content_hash") != exact.get("benchmark_contract_content_hash"):
        failures.append("benchmark contract canonical hash mismatch")
    if dsr_reference.get("canonical_content_hash") != canonical_named_hash(dsr_reference, "canonical_content_hash") or dsr_reference.get("canonical_content_hash") != exact.get("dsr_reference_content_hash"):
        failures.append("DSR reference canonical hash mismatch")
    root_canonical = root_freeze.get("canonical_content_hashes", {})
    expected_canonical = {"source_screen": evidence.get("content_hash"), "candidate_freeze": freeze.get("content_hash"), "unified_is_protocol": protocol.get("content_hash"), "data_authority": data_authority.get("canonical_content_hash"), "benchmark_contract": benchmark.get("canonical_content_hash"), "dsr_reference": dsr_reference.get("canonical_content_hash")}
    if root_canonical != expected_canonical:
        failures.append("root freeze canonical hash map mismatch")
    for record in data_authority.get("bound_manifests", []):
        manifest = read_json(root, str(record.get("path")), failures)
        try:
            manifest_bytes = (root / str(record.get("path"))).read_bytes()
        except OSError:
            continue
        if sha256(manifest_bytes) != record.get("byte_sha256"):
            failures.append(f"data authority byte hash drift: {record.get('path')}")
        semantic = manifest.get("content_hash") or manifest.get("audit_summary_hash") if isinstance(manifest, dict) else None
        if semantic is None:
            semantic = sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
        if semantic != record.get("semantic_hash"):
            failures.append(f"data authority semantic hash drift: {record.get('path')}")
    implementation = benchmark.get("implementation", {})
    try:
        benchmark_code_hash = sha256((root / str(implementation.get("path"))).read_bytes())
    except OSError as exc:
        failures.append(f"benchmark implementation missing: {exc}")
    else:
        if benchmark_code_hash != implementation.get("byte_sha256"):
            failures.append("benchmark implementation byte hash drift")

    candidates = inv.get("candidates", [])
    if [item.get("order") for item in candidates] != list(range(1, 21)) or len({item.get("id") for item in candidates}) != 20:
        failures.append("inventory order or identity changed")
    inventory_by_id = {item.get("id"): item for item in candidates}
    results = evidence.get("results", [])
    if len(results) != 20:
        failures.append("screen result count changed")
    archive_cache: dict[str, dict[str, bytes]] = {}
    for result in results:
        candidate = inventory_by_id.get(result.get("id"))
        if not candidate:
            failures.append(f"screen candidate absent from inventory: {result.get('id')}")
            continue
        repo = inv.get("repositories", {}).get(candidate.get("repo"), {})
        for field in ("repository", "commit"):
            if result.get(field) != repo.get(field):
                failures.append(f"inventory/screen {field} mismatch: {result.get('id')}")
        if result.get("source_path") != candidate.get("source_path"):
            failures.append(f"inventory/screen path mismatch: {result.get('id')}")
        materialized = candidate.get("source_materialized", True)
        if result.get("source_materialized") != materialized:
            failures.append(f"materialization state mismatch: {result.get('id')}")
        if not materialized:
            forbidden = root / "external_strategies/original" / f"{candidate['order']:02d}-{candidate['id']}" / f"{candidate['id']}.py"
            if forbidden.exists() or result.get("local_read_only_source") is not None or result.get("license_status") != "unverified_not_redistributed":
                failures.append(f"unverified source redistributed: {result.get('id')}")
            continue
        archive_rel = repo.get("archive_path")
        if not archive_rel:
            failures.append(f"materialized source lacks archive: {result.get('id')}")
            continue
        if archive_rel not in archive_cache:
            archive_path = root / archive_rel
            if not archive_path.is_file() or sha256(archive_path.read_bytes()) != result.get("repository_archive_sha256"):
                failures.append(f"repository archive identity mismatch: {archive_rel}")
            archive_cache[archive_rel] = member_map(archive_path, failures)
        upstream = archive_cache[archive_rel].get(candidate["source_path"])
        if upstream is None:
            failures.append(f"candidate archive member missing: {candidate['source_path']}")
            continue
        source_path = root / str(result.get("local_read_only_source"))
        try:
            local = source_path.read_bytes()
        except OSError as exc:
            failures.append(f"local source missing: {source_path}: {exc}")
            continue
        if local != upstream or sha256(local) != result.get("source_sha256") or git_blob_sha(local) != result.get("git_blob_sha1"):
            failures.append(f"local/upstream source identity mismatch: {result.get('id')}")
        members = archive_cache[archive_rel]
        for dependency in result.get("dependency_closure", []):
            payload = members.get(dependency.get("path"))
            if payload is None:
                failures.append(f"dependency archive member missing: {result.get('id')}:{dependency.get('path')}")
            elif sha256(payload) != dependency.get("sha256") or git_blob_sha(payload) != dependency.get("git_blob_sha1"):
                failures.append(f"dependency identity mismatch: {result.get('id')}:{dependency.get('path')}")

    if freeze.get("screen_content_hash") != evidence.get("content_hash") or [item.get("id") for item in freeze.get("frozen_candidates", [])] != evidence.get("frozen_ids"):
        failures.append("screen/freeze binding mismatch")
    if not 5 <= len(freeze.get("frozen_candidates", [])) <= 6:
        failures.append("frozen candidate count invalid")
    for item in freeze.get("frozen_candidates", []):
        if item.get("runtime_resolved_parameters_hash") is not None or item.get("runtime_effective_settings_hash") is not None:
            failures.append(f"runtime parameter hash materialized before VPS load: {item.get('id')}")
        if item.get("observed_external_parameter_file_count") is not None or item.get("observed_config_override_count") is not None:
            failures.append(f"runtime observed parameter counts materialized before VPS load: {item.get('id')}")
        if item.get("adapter_hash") is not None:
            failures.append(f"adapter hash materialized before compatibility: {item.get('id')}")
        if item.get("base_adapter_hash") is not None:
            failures.append(f"base adapter hash materialized before compatibility: {item.get('id')}")
        package = item.get("modification_package", {})
        if package != {"id": None, "before_hash": None, "after_hash": None, "atomic_changes": [], "package_hash": None}:
            failures.append(f"modification package changed before IS: {item.get('id')}")
        result = next((entry for entry in results if entry.get("id") == item.get("id")), {})
        declaration = result.get("source_declaration", {})
        if declaration.get("position_increase_capability") or declaration.get("behavior_methods", {}).get("leverage") or declaration.get("assignments", {}).get("can_short") is True:
            failures.append(f"forbidden static trading capability: {item.get('id')}")
    if freeze.get("required_external_parameter_file_count") != 0 or freeze.get("required_config_override_count") != 0:
        failures.append("required external parameter/config override contract changed")
    if freeze.get("trial_manifest_limits") != {"original_per_candidate":1,"modified_per_candidate":1,"maximum_modified_candidates":3,"modified_requires_passing_original":True,"modified_requires_unique_preregistered_package":True,"modified_must_materialize_strictly_after_original":True,"ordering":"first_materialized_utc_then_trial_id"}:
        failures.append("trial manifest cardinality contract changed")
    if freeze.get("result_contract") != {"common_envelope_schema":"external-strategy-is-result-v1","kinds":["trades","equity","metrics"],"scenarios":["Base","CostX2","StressA","StressB"],"metric_authority":"equity_recomputed_unified_metrics","dsr_authority":"equity_recomputed_sharpe_plus_frozen_trial_sequence","variant_identity_fields":["base_adapter_hash","variant_executable_hash"]}:
        failures.append("trial result envelope contract changed")
    if freeze.get("observed_external_parameter_file_count") is not None or freeze.get("observed_config_override_count") is not None:
        failures.append("observed parameter/config counts materialized before VPS load")

    if supersession.get("status") != "superseded_unexecuted_by_existing_strategy_route" or supersession.get("permissions", {}).get("u25_design") is not False:
        failures.append("U-25 supersession changed")
    if adr.get("state_machine") != EXPECTED_STAGES or adr.get("license") != "GPL-3.0-only" or adr.get("selected_candidate_limit") != 1:
        failures.append("ADR-0016 core changed")
    expected_trial_accounting = {"historical_opened_oos_trial_count":3,"selection_trial_count":0,"dsr_trial_count_formula":"3 + selection_trial_count","metrics_authority":"equity_recomputed_unified_metrics","metric_reconciliation_absolute_error_maximum":"0.0000000001","modified_requires_materialized_reconciled_passing_original":True,"variant_executable_identity_required":True}
    if adr.get("trial_accounting") != expected_trial_accounting:
        failures.append("ADR-0016 trial accounting contract changed")
    for forbidden in ("oos", "dry_run", "api", "paper_or_live", "order_placement", "execution_live", "m2"):
        if adr.get("permissions", {}).get(forbidden) is not False:
            failures.append(f"forbidden ADR permission enabled: {forbidden}")
    expected_oos = {"status": "pending_explicit_unique_oos_authorization", "oos_authorized": False, "oos_opened": False, "oos_runs": 0, "oos_rows_decoded": 0, "single_use_token": None, "result_materialized": False, "rerun_authorized": False, "crash_policy": "record_incident_and_stop_without_reuse_or_retry"}
    for key, value in expected_oos.items():
        if oos.get(key) != value:
            failures.append(f"OOS guard state changed: {key}")
    multiple = protocol.get("multiple_testing", {})
    if multiple.get("historical_opened_oos_trial_count") != 3 or multiple.get("selection_trial_count") != 0 or multiple.get("dsr_trial_count_formula") != "3 + selection_trial_count":
        failures.append("multiple-testing trial formula changed")
    expected_portfolio = {"initial_capital_usdt":"100000","stake_mode":"fixed_equal_notional","stake_amount_usdt":"10000","maximum_open_trades":5,"maximum_gross_exposure":"0.50","maximum_position_weight":"0.10","cash_reserve_target":"0.50","compounding":False,"multiple_positions_same_pair":False,"insufficient_cash_policy":"reject_new_entry","capital_contention_order":"point_in_time_active_universe_rank_then_symbol_asc"}
    if protocol.get("portfolio") != expected_portfolio:
        failures.append("unified portfolio contract changed")
    expected_order = ["all_hard_gates_pass","base_dsr_desc","costx2_dsr_desc","costx2_daily_mtm_sharpe_desc","costx2_max_drawdown_asc","turnover_asc","candidate_id_asc"]
    if protocol.get("selection_order") != expected_order:
        failures.append("selection order changed")
    calendar = protocol.get("calendar", {})
    try:
        parse = lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
        full_start = parse(calendar["evaluated_full_start"])
        is_start = parse(calendar["is_start"])
        is_end = parse(calendar["is_end_exclusive"])
        oos_start = parse(calendar["sealed_oos_start"])
        full_end = parse(calendar["evaluated_full_end_exclusive"])
        warmup = parse(calendar["source_warmup_start"])
        full_days = (full_end - full_start).days
        is_days = (is_end - is_start).days
        oos_days = (full_end - oos_start).days
        fraction = f"{oos_days / full_days:.12f}"
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        failures.append("calendar contract is malformed")
    else:
        if warmup.isoformat() != "2020-01-01T00:00:00+00:00" or not (full_start == is_start and is_end == oos_start):
            failures.append("calendar boundary continuity changed")
        if (full_days, is_days, oos_days, fraction) != (2191, 1533, 658, "0.300319488818"):
            failures.append("calendar day counts or OOS ratio changed")
        if (calendar.get("full_days"), calendar.get("is_days"), calendar.get("sealed_oos_days"), calendar.get("actual_sealed_oos_fraction")) != (full_days, is_days, oos_days, fraction):
            failures.append("declared calendar counts do not recompute")
        inventory_calendar = inv.get("calendar_authority", {})
        if inventory_calendar != {"path": paths["protocol"], "content_hash": protocol.get("content_hash")}:
            failures.append("inventory/unified protocol calendar authority mismatch")
        authority_boundaries = data_authority.get("time_boundaries", {})
        expected_authority = {
            "source_warmup_start": calendar.get("source_warmup_start"),
            "evaluated_full_start": calendar.get("evaluated_full_start"),
            "is_start": calendar.get("is_start"),
            "is_end": calendar.get("is_end_exclusive"),
            "sealed_oos_start": calendar.get("sealed_oos_start"),
            "sealed_oos_end": calendar.get("evaluated_full_end_exclusive"),
            "full_days": full_days,
            "is_days": is_days,
            "sealed_oos_days": oos_days,
            "actual_sealed_oos_fraction": fraction,
        }
        if authority_boundaries != expected_authority:
            failures.append("data authority/unified protocol calendar mismatch")
    curve = protocol.get("equity_curve", {})
    try:
        day = lambda name: datetime.fromisoformat(str(curve[name])).date()
        anchor, first, is_final = day("equity_anchor_day"), day("first_return_day"), day("is_final_return_day")
        oos_anchor, oos_first, final = day("oos_anchor_day"), day("oos_first_return_day"), day("final_return_day")
        recomputed = ((final - anchor).days, (is_final - anchor).days, (final - oos_anchor).days)
    except (KeyError, TypeError, ValueError):
        failures.append("equity half-open calendar is malformed")
    else:
        declared = (curve.get("full_return_count"), curve.get("is_return_count"), curve.get("oos_return_count"))
        if curve.get("evaluation_interval") != "half_open" or first != anchor + timedelta(days=1) or oos_first != oos_anchor + timedelta(days=1):
            failures.append("equity half-open anchor semantics changed")
        if (anchor.isoformat(), first.isoformat(), is_final.isoformat(), oos_anchor.isoformat(), oos_first.isoformat(), final.isoformat()) != ("2020-06-30", "2020-07-01", "2024-09-10", "2024-09-10", "2024-09-11", "2026-06-30"):
            failures.append("equity curve date labels changed")
        if recomputed != (2191, 1533, 658) or declared != recomputed or curve.get("candidate_and_benchmarks_share_identical_date_labels") is not True:
            failures.append("equity curve return counts or shared labels changed")
        if first.isoformat() != calendar.get("is_start", "")[:10] or oos_first.isoformat() != calendar.get("sealed_oos_start", "")[:10] or final.isoformat() != "2026-06-30":
            failures.append("equity labels/unified protocol calendar mismatch")
    expected_reconciliation = {"metric_reconciliation_absolute_error_maximum":"0.0000000001","metric_authority":"btc_eth_dual_quant.audit.unified_metrics.metrics_from_equity","metrics_recomputed_from_equity":["net_return","daily_mtm_sharpe","psr","max_drawdown"],"completed_trades_authority":"hash_bound_trades_result","base_costx2_dsr_recomputed_after_all_materialized_trials":True,"stress_scenarios_excluded_from_dsr_sequence":True}
    if protocol.get("result_reconciliation") != expected_reconciliation:
        failures.append("result reconciliation contract changed")
    if any(value is not True for value in protocol.get("prohibitions", {}).values()):
        failures.append("unified prohibition disabled")
    precondition = protocol.get("parameter_precondition", {})
    if precondition.get("required_external_parameter_file_count") != 0 or precondition.get("required_config_override_count") != 0 or any(precondition.get(name) is not None for name in ("observed_external_parameter_file_count", "observed_config_override_count", "runtime_effective_settings_hash", "runtime_resolved_parameters_hash")):
        failures.append("required/observed runtime parameter precondition changed")
    ledger = yaml.safe_load((root / "STRATEGY_TRIAL_LEDGER.yaml").read_text(encoding="utf-8"))
    rules = ledger.get("rules", {})
    if rules.get("historical_opened_oos_trial_count") != 3 or rules.get("selection_trial_count") != 0 or rules.get("dsr_trial_count_formula") != "3 + selection_trial_count":
        failures.append("trial ledger count migration changed")
    for rel_path, expected in ORIGINAL_U25_HASHES.items():
        if sha256((root / rel_path).read_bytes()) != expected:
            failures.append(f"immutable U-25 source changed: {rel_path}")
    counters = protocol.get("execution_counters", {})
    if counters != {"freqtrade_loads": 0, "causal_validations": 0, "is_trials": 0} or evidence.get("selection_trial_count") != 0 or evidence.get("oos_rows_decoded") != 0:
        failures.append("execution/result counters are nonzero")
    if protocol.get("dsr_reference", {}).get("canonical_content_hash") != dsr_reference.get("canonical_content_hash"):
        failures.append("protocol DSR reference binding mismatch")
    if dsr_reference.get("historical", {}).get("Base") != ["0.7367", "7.1534", "0.7882"] or dsr_reference.get("historical", {}).get("CostX2") != ["0.7271", "6.8357", "0.7528"]:
        failures.append("historical DSR Sharpe sequences changed")
    if dsr_reference.get("required_trial_count") != 3 or dsr_reference.get("selection_trial_count") != 0:
        failures.append("DSR reference zero-selection state changed")
    if (dsr_reference.get("heterogeneous_scope"), dsr_reference.get("deliberately_conservative"), dsr_reference.get("homogeneous_trial_distribution_claimed")) != (True, True, False):
        failures.append("DSR heterogeneous-scope ruling changed")
    from btc_eth_dual_quant.audit.unified_metrics import expected_maximum_sharpe
    for scenario, field in (("Base", "expected_maximum_sharpe_base"), ("CostX2", "expected_maximum_sharpe_costx2")):
        values = [float(value) for value in dsr_reference.get("historical", {}).get(scenario, [])]
        expected = f"{expected_maximum_sharpe(values):.12f}"
        if dsr_reference.get(field) != expected:
            failures.append(f"DSR expected maximum Sharpe mismatch: {scenario}")
    for record in dsr_reference.get("authoritative_trials", []):
        for prefix in ("metrics", "decision"):
            rel = record.get(f"{prefix}_report")
            expected_hash = record.get(f"{prefix}_report_byte_sha256")
            try:
                actual_hash = sha256((root / rel).read_bytes())
            except (OSError, TypeError) as exc:
                failures.append(f"DSR authoritative report missing: {rel}: {exc}")
            else:
                if actual_hash != expected_hash:
                    failures.append(f"DSR authoritative report hash mismatch: {rel}")
    implementation_path = root / "src/btc_eth_dual_quant/audit/unified_metrics.py"
    if benchmark.get("implementation", {}).get("byte_sha256") != sha256(implementation_path.read_bytes()):
        failures.append("benchmark implementation hash mismatch")
    if dsr_reference.get("implementation", {}).get("byte_sha256") != sha256(implementation_path.read_bytes()):
        failures.append("DSR implementation hash mismatch")
    candle = data_authority.get("timeframes", {}).get("implementation_authority", {})
    try:
        candle_hash = sha256((root / candle.get("path", "")).read_bytes())
    except OSError as exc:
        failures.append(f"completed-candle implementation missing: {exc}")
    else:
        if candle.get("byte_sha256") != candle_hash:
            failures.append("completed-candle implementation hash mismatch")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("ADR-0016 source route FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    evidence = json.loads((ROOT / "reports/m1/evidence/external_strategy_source_screen_v1.json").read_text())
    print(f"ADR-0016 source route PASS: {evidence['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
