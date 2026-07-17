"""Reviewed-run primitives for the frozen ADR-0015 independent audit."""
from __future__ import annotations

import json
import random
import subprocess
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

from .liquid_universe_v4_adr0015 import (
    IndependentMembershipAuthority,
    evaluate_candidate_slots,
    read_audit_five_minute_archive,
    wrap_policy_manifest,
)
from .liquid_universe_v4_audit_artifacts import (
    REQUIRED_AUDIT_ARTIFACTS,
    build_audit_artifacts,
    compare_manifest,
)
from .liquid_universe_v4_audit_run import (
    _build_contents,
    _gap_and_panel,
    _summary,
    load_json,
    month_sequence,
    utc_iso,
)
from .liquid_universe_v4_independent import (
    EPOCH,
    audit_content_hash,
    audit_identity_hash,
    expected_slots,
    month_bounds_ms,
    strict_json_loads,
    validate_lifecycle_registry,
)


ADR0015_ARTIFACTS = (
    "invalid_interval_policy_manifest",
    "invalid_interval_event_manifest",
    "invalid_interval_slot_mask_manifest",
    "invalid_interval_accounting_manifest",
)
ALL_ARTIFACTS = tuple(REQUIRED_AUDIT_ARTIFACTS) + ADR0015_ARTIFACTS


def _mixed_manifest_hash(manifest: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in manifest.items() if key != "content_hash"}
    if manifest.get("manifest_type") in ADR0015_ARTIFACTS:
        unsigned.pop("generated_utc", None)
    expected = audit_content_hash(unsigned)
    if manifest.get("content_hash") != expected:
        raise ValueError(f"manifest content hash invalid: {manifest.get('manifest_type')}")
    return expected


def _mixed_artifact_set_hash(manifests: Mapping[str, Mapping[str, Any]]) -> str:
    return audit_content_hash({name: _mixed_manifest_hash(value) for name, value in sorted(manifests.items())})


def _compare_mixed_suites(
    production: Mapping[str, Mapping[str, Any]], independent: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if set(production) != set(independent):
        return {"exact": False, "artifact_set_match": False, "first_mismatch": "artifact names differ", "comparisons": {}}
    comparisons = {name: compare_manifest(production[name], independent[name]) for name in sorted(production)}
    exact = all(item["exact_content_match"] for item in comparisons.values())
    set_match = _mixed_artifact_set_hash(production) == _mixed_artifact_set_hash(independent)
    first = next((f"{name}: {item['first_mismatch']}" for name, item in comparisons.items() if item["first_mismatch"]), None)
    return {"exact": exact and set_match, "artifact_set_match": set_match, "first_mismatch": first, "comparisons": comparisons}


def _runtime_protocol(repository: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    """Supply legacy audit recomputation bindings from independently hash-bound configs."""
    value = json.loads(json.dumps(protocol))
    bindings = value["authority_bindings"]
    bindings.update({
        "lifecycle_policy_hash": load_json(repository / "config/liquid_spot_lifecycle_policy_v4.json")["canonical_hash"],
        "lifecycle_event_registry_hash": load_json(repository / "config/liquid_spot_lifecycle_event_resolutions_v4.json")["canonical_hash"],
        "v3_row_conflict_registry_hash": load_json(repository / "config/liquid_spot_source_conflict_resolutions_v3.json")["canonical_hash"],
        "v4_contract_hash": load_json(repository / "config/liquid_spot_universe_contract_v4.json")["canonical_hash"],
    })
    return value


def _ordered_keys(values: list[tuple[str, str]], order: str) -> list[tuple[str, str]]:
    output = sorted(values)
    if order == "reverse":
        output.reverse()
    elif order in {"shuffled", "deterministic_shuffled"}:
        random.Random(314159).shuffle(output)
    elif order != "normal":
        raise ValueError(f"unknown ADR-0015 audit order: {order}")
    return output


def _enhance_adr0015_contents(
    *, repository: Path, raw_root: Path, order: str, contents: dict[str, Any],
) -> dict[str, Any]:
    evidence = repository / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
    freeze = load_json(evidence / "source_freeze_manifest.json")
    policy = load_json(repository / "config/liquid_spot_invalid_interval_policy_v1.json")
    if policy["bindings"]["source_freeze_content_hash"] != freeze["content_hash"]:
        raise ValueError("ADR-0015 source-freeze binding changed")
    membership = contents["membership_manifest"]
    contract_hash = load_json(repository / "config/liquid_spot_universe_contract_v4.json")["canonical_hash"]
    lifecycle_registry = load_json(repository / "config/liquid_spot_lifecycle_event_resolutions_v4.json")
    lifecycle_policy = load_json(repository / "config/liquid_spot_lifecycle_policy_v4.json")
    membership_hash = audit_content_hash({
        "schema_version": 4,
        "manifest_type": "membership_manifest",
        "contract_hash": contract_hash,
        "lifecycle_registry_hash": lifecycle_registry["canonical_hash"],
        "content": membership,
    })
    if membership_hash != policy["bindings"]["membership_manifest_content_hash"]:
        raise ValueError("independent membership identity changed")
    events = validate_lifecycle_registry(
        lifecycle_policy,
        lifecycle_registry,
        research_start="2020-01-01T00:00:00Z",
        expected_policy_hash=lifecycle_policy["canonical_hash"],
        expected_registry_hash=lifecycle_registry["canonical_hash"],
        expected_reviewed_event_set_hash=lifecycle_registry["reviewed_event_set_hash"],
    )
    authority = IndependentMembershipAuthority.build(
        membership,
        lifecycle_end_exclusive_ms={item.symbol: item.availability_end_exclusive_ms for item in events},
        membership_manifest_hash=membership_hash,
        lifecycle_registry_hash=lifecycle_registry["canonical_hash"],
    )
    frozen = {str(item["canonical_key"]): item for item in freeze["content"]["archives"]}
    needed = [(str(row["symbol"]), str(row["effective_month"])[:7]) for row in membership]
    grids: dict[tuple[str, str], dict[str, Any]] = {}
    candidates = []
    for symbol, month in _ordered_keys(needed, order):
        key = f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip"
        binding = frozen.get(key)
        if binding is None:
            raise ValueError(f"frozen active archive missing: {key}")
        rows = read_audit_five_minute_archive(
            raw_root / key,
            frozen=binding,
            symbol=symbol,
            month=month,
            source_freeze_hash=freeze["content_hash"],
        )
        start, end = month_bounds_ms(month)
        active_end = min(
            end,
            authority.lifecycle_end_exclusive_ms.get(symbol, end),
        )
        expected = set(expected_slots(start, end, 300_000, availability_end_exclusive=active_end if active_end < end else None))
        strict_times: list[int] = []
        defects = []
        for row in rows:
            if row.open_time_ms >= active_end:
                raise ValueError(f"unexpected post-lifecycle row:{symbol}:{row.open_time_ms}")
            if row.has_close_boundary_defect:
                defects.append(row)
            else:
                strict_times.append(row.open_time_ms)
        if len(strict_times) != len(set(strict_times)):
            raise ValueError(f"duplicate active 5m row:{symbol}:{month}")
        candidates.extend(defects)
        observed = set(strict_times)
        hour_counts = Counter(item // 3_600_000 for item in strict_times)
        grids[(symbol, month)] = {
            "symbol": symbol,
            "month": month,
            "archive_sha256": binding["sha256"],
            "expected_count": len(expected),
            "actual_count": len(observed),
            "missing": sorted(expected - observed),
            "errors": [],
            "hour_counts": hour_counts,
        }
    selected = {(row.symbol, row.open_time_ms): row for row in candidates}
    candidate_times = sorted({row.open_time_ms for row in candidates})
    targets: dict[tuple[str, str], set[int]] = defaultdict(set)
    for opened in candidate_times:
        month = next(row.month for row in candidates if row.open_time_ms == opened)
        for symbol in authority.active_members(month, opened):
            targets[(symbol, month)].add(opened)
    for symbol, month in _ordered_keys(list(targets), order):
        key = f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip"
        for row in read_audit_five_minute_archive(
            raw_root / key,
            frozen=frozen[key],
            symbol=symbol,
            month=month,
            source_freeze_hash=freeze["content_hash"],
        ):
            if row.open_time_ms in targets[(symbol, month)]:
                selected[(symbol, row.open_time_ms)] = row
    evaluation = evaluate_candidate_slots(
        selected.values(),
        authority=authority,
        source_freeze_hash=freeze["content_hash"],
        policy_version=policy["policy_version"],
        algorithm_hash=policy["algorithm_hash"],
    )
    masks: dict[tuple[str, str], set[int]] = defaultdict(set)
    for item in evaluation["slot_mask"]:
        masks[(item["symbol"], item["month"])].add(int(item["open_time_ms"]))
    for key, grid in grids.items():
        masked = masks.get(key, set())
        valid_masked = {opened for opened in masked if opened not in set(grid["missing"])}
        grid["actual_count"] -= len(valid_masked)
        grid["missing"] = [opened for opened in grid["missing"] if opened not in masked]
        grid["complete"] = not grid["missing"] and not grid["errors"]
    source_by_key = {
        (row["symbol"], row["archive_month"]): row
        for row in contents["source_manifest"] if row["interval"] == "5m"
    }
    for key, masked in masks.items():
        complete_masked_hours = {
            opened // 3_600_000 for opened in masked
            if grids[key]["hour_counts"][opened // 3_600_000] == 12
        }
        source_by_key[key]["derived_1h_count"] -= len(complete_masked_hours)
    confirmed = load_json(repository / "config/liquid_spot_confirmed_archive_gaps_v2.json")
    v3_contract = load_json(repository / "config/liquid_spot_universe_contract_v3.json")
    panel, gap = _gap_and_panel(
        memberships=membership,
        grids=grids,
        confirmed_gap_registry=confirmed,
        contract=v3_contract,
    )
    clean_blockers = [
        item for item in contents["qualification_summary"].get("blockers", [])
        if "5m interval boundary is invalid" not in item
    ]
    months = month_sequence("2020-01", "2026-06")
    summary = _summary(
        source_manifest=contents["source_manifest"],
        memberships=membership,
        panel=panel,
        gap=gap,
        resolution=contents["row_conflict_resolution_manifest"],
        lifecycle_events=events,
        blockers=clean_blockers,
        contract=load_json(repository / "config/liquid_spot_universe_contract_v4.json"),
        months=months,
        lifecycle_quarantine=contents["raw_row_quarantine_manifest"],
    )
    contents["expected_grid_manifest"] = [{
        "symbol": symbol,
        "month": month,
        "expected_count": value["expected_count"],
        "actual_count": value["actual_count"],
        "missing_count": len(value["missing"]),
        "errors": value["errors"],
        "complete": value["complete"],
        "invalid_interval_policy_masked_count": len(masks.get((symbol, month), set())),
        "complete_after_invalid_interval_mask": value["complete"],
    } for (symbol, month), value in sorted(grids.items())]
    masked_hours: dict[tuple[str, str], set[int]] = {
        key: {opened // 3_600_000 for opened in values} for key, values in masks.items()
    }
    for row in panel:
        hours = masked_hours.get((row["symbol"], row["effective_month"]), set())
        if hours:
            row["invalid_interval_quarantined_1h_count"] = len(hours)
            row["valid_1h_count"] = max(0, int(row["valid_1h_count"]) - len(hours))
            row["quarantined_1h_count"] = int(row["expected_1h_count"]) - int(row["valid_1h_count"])
            row["status"] = "synchronized_invalid_interval_quarantined"
    contents["qualified_panel_manifest"] = panel
    contents["complete_day_mask"]["invalid_interval_quarantined_days"] = [{
        "event_id": item["event_id"],
        "open_time_ms": item["open_time_ms"],
        "utc_day": (EPOCH + timedelta(milliseconds=item["open_time_ms"])).date().isoformat(),
        "active_members": item["active_members"],
        "window_eligible": False,
    } for item in evaluation["events"]]
    contents["complete_day_mask"]["invalid_interval_quarantined_days_window_eligible"] = False
    accounting = evaluation["accounting"]
    summary.update({
        "invalid_interval_policy_events": accounting["event_count"],
        "invalid_interval_rows_quarantined": accounting["invalid_rows_quarantined"],
        "invalid_interval_valid_minority_rows_quarantined": accounting["valid_minority_rows_quarantined"],
        "invalid_interval_total_rows_quarantined": accounting["total_rows_quarantined"],
        "invalid_interval_quarantined_hours": len({(key[1], hour) for key, values in masked_hours.items() for hour in values}),
        "invalid_interval_quarantined_days": len({(key[1], opened // 86_400_000) for key, values in masks.items() for opened in values}),
        "invalid_interval_policy_blockers": 0,
        "invalid_interval_policy_content_hash": accounting["evaluation_content_hash"],
    })
    contents["qualification_summary"] = summary
    contents["invalid_interval_policy_manifest"] = {
        "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
        "policy_canonical_hash": policy["canonical_hash"], "algorithm_hash": policy["algorithm_hash"],
        "authorizations": policy["authorizations"],
    }
    contents["invalid_interval_event_manifest"] = evaluation["events"]
    contents["invalid_interval_slot_mask_manifest"] = evaluation["slot_mask"]
    contents["invalid_interval_accounting_manifest"] = accounting
    return contents


def build_adr0015_independent_suite(
    *, repository: Path, raw_root: Path, protocol: Mapping[str, Any], order: str,
) -> dict[str, Any]:
    order_alias = "shuffled" if order == "deterministic_shuffled" else order
    contents, diagnostics = _build_contents(
        repository=repository,
        raw_root=raw_root,
        protocol=_runtime_protocol(repository, protocol),
        order=order_alias,
    )
    contents = _enhance_adr0015_contents(
        repository=repository, raw_root=raw_root, order=order, contents=contents,
    )
    normalized = strict_json_loads(json.dumps(contents, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    base_contents = {name: normalized[name] for name in REQUIRED_AUDIT_ARTIFACTS}
    contract_hash = load_json(repository / "config/liquid_spot_universe_contract_v4.json")["canonical_hash"]
    lifecycle_hash = load_json(repository / "config/liquid_spot_lifecycle_event_resolutions_v4.json")["canonical_hash"]
    manifests = build_audit_artifacts(
        base_contents,
        contract_hash=contract_hash,
        lifecycle_registry_hash=lifecycle_hash,
    )
    policy = load_json(repository / "config/liquid_spot_invalid_interval_policy_v1.json")
    events = normalized["invalid_interval_event_manifest"]
    if not events:
        raise ValueError("ADR-0015 independent audit found no candidate events")
    authority_hashes = {item["membership_authority_hash"] for item in events}
    if len(authority_hashes) != 1:
        raise ValueError("ADR-0015 membership authority is ambiguous")
    authority_hash = next(iter(authority_hashes))
    for name in ADR0015_ARTIFACTS:
        manifests[name] = wrap_policy_manifest(
            name,
            normalized[name],
            authority_hash=authority_hash,
            policy_hash=policy["canonical_hash"],
            source_freeze_hash=policy["bindings"]["source_freeze_content_hash"],
        )
    manifests = strict_json_loads(json.dumps(manifests, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    hashes = {name: _mixed_manifest_hash(value) for name, value in sorted(manifests.items())}
    return {
        "order": order,
        "manifests": manifests,
        "manifest_hashes": hashes,
        "artifact_set_hash": _mixed_artifact_set_hash(manifests),
        "content_identity_hash": audit_identity_hash(hashes),
        "diagnostics": {
            **diagnostics,
            "invalid_interval_events": normalized["invalid_interval_accounting_manifest"]["event_count"],
            "invalid_physical_rows": normalized["invalid_interval_accounting_manifest"]["invalid_rows_quarantined"],
            "valid_minority_rows": normalized["invalid_interval_accounting_manifest"]["valid_minority_rows_quarantined"],
            "total_active_slots_masked": normalized["invalid_interval_accounting_manifest"]["total_rows_quarantined"],
        },
    }


def compare_with_production(
    *, repository: Path, protocol: Mapping[str, Any], independent: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    evidence = repository / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
    production = {name: load_json(evidence / f"{name}.json") for name in ALL_ARTIFACTS}
    for name, expected in protocol["production_manifest_hashes"].items():
        if _mixed_manifest_hash(production[name]) != expected:
            raise ValueError(f"production manifest binding changed: {name}")
    return _compare_mixed_suites(production, independent)


def _validate_exact_head_review(
    *, repository: Path, protocol: Mapping[str, Any], review: Mapping[str, Any],
) -> None:
    """Fail closed unless the approval binds this protocol and auditor implementation."""
    if review.get("verdict") != "approve" or review.get("remaining_critical_findings") != 0 or review.get("remaining_high_findings") != 0:
        raise ValueError("exact-head auditor review does not authorize the audit run")
    if review.get("full_independent_audit_run_authorized") is not True:
        raise ValueError("full independent audit run is not authorized")
    implementation = load_json(
        repository / "config/liquid_universe_v4_adr0015_independent_auditor_implementation.json"
    )
    protocol_hash = audit_content_hash({
        key: value for key, value in protocol.items() if key != "generated_utc"
    })
    expected = {
        "protocol_content_hash": protocol_hash,
        "implementation_content_hash": implementation["implementation_content_hash"],
        "implementation_files": implementation["files"],
    }
    for key, value in expected.items():
        if review.get(key) != value:
            raise ValueError(f"exact-head auditor review binding changed: {key}")
    if protocol_hash != implementation["protocol_content_hash"]:
        raise ValueError("auditor implementation protocol binding changed")
    target = review.get("target_commit")
    if not isinstance(target, str) or len(target) != 40:
        raise ValueError("exact-head auditor review target is invalid")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", target, "HEAD"],
        cwd=repository, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if ancestor.returncode != 0:
        raise ValueError("reviewed auditor exact head is not an ancestor of the audit run")


def execute_adr0015_audit(
    *, repository: Path, raw_root: Path, protocol: Mapping[str, Any], review: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_exact_head_review(repository=repository, protocol=protocol, review=review)
    orders = tuple(protocol["audit_scope"]["traversal_orders"])
    runs = [
        build_adr0015_independent_suite(
            repository=repository, raw_root=raw_root, protocol=protocol, order=order,
        )
        for order in orders
    ]
    content_hashes = {run["content_identity_hash"] for run in runs}
    comparison = compare_with_production(
        repository=repository, protocol=protocol, independent=runs[0]["manifests"],
    )
    gate = protocol["comparison_gate"]
    accounting = runs[0]["diagnostics"]
    count_checks = {
        "events": accounting["invalid_interval_events"] == gate["expected_invalid_interval_events"],
        "invalid_physical_rows": accounting["invalid_physical_rows"] == gate["expected_invalid_physical_rows"],
        "valid_minority_rows": accounting["valid_minority_rows"] == gate["expected_valid_minority_rows"],
        "total_active_slots_masked": accounting["total_active_slots_masked"] == gate["expected_total_active_slots_masked"],
    }
    exact_count = sum(
        item["exact_content_match"] for item in comparison.get("comparisons", {}).values()
    )
    critical: list[str] = []
    high: list[str] = []
    if len(content_hashes) != 1:
        critical.append("traversal_content_identity_mismatch")
    if not comparison.get("exact") or exact_count != gate["production_manifests_exact_required"]:
        critical.append("production_manifest_exact_comparison_failed")
    if not all(count_checks.values()):
        critical.append("invalid_interval_accounting_gate_failed")
    verdict = "pass" if not critical and not high else "failed_audit"
    summary = {
        "schema_version": 1,
        "audit_id": "ADR0015-LIQUID-UNIVERSE-V4-INDEPENDENT-AUDIT-RUN-V1",
        "protocol_id": protocol["protocol_id"],
        "verdict": verdict,
        "orders": [{
            "order": run["order"],
            "content_identity_hash": run["content_identity_hash"],
            "artifact_set_hash": run["artifact_set_hash"],
        } for run in runs],
        "production_artifact_set_hash": protocol["authority_bindings"]["production_artifact_set_hash"],
        "independent_artifact_set_hash": runs[0]["artifact_set_hash"],
        "manifests_exact": exact_count,
        "manifests_total": len(ALL_ARTIFACTS),
        "count_checks": count_checks,
        "diagnostics": accounting,
        "critical_findings": critical,
        "high_findings": high,
        "production_evidence_mutated": False,
        "network_accessed": False,
        "authorization": {
            "u04": False, "strategy": False, "returns": False, "backtesting": False,
            "oos": False, "api_trading": False, "execution_live": False, "m2": False,
        },
    }
    summary["audit_summary_hash"] = audit_identity_hash(summary)
    return {"summary": summary, "comparison": comparison, "runs": runs}


def render_adr0015_audit_report(result: Mapping[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# ADR-0015 Liquid Universe V4 Independent Audit Report", "",
        f"- Verdict: `{summary['verdict']}`",
        f"- Exact manifests: {summary['manifests_exact']}/{summary['manifests_total']}",
        f"- Critical findings: {len(summary['critical_findings'])}",
        f"- High findings: {len(summary['high_findings'])}",
        f"- Production evidence mutated: {str(summary['production_evidence_mutated']).lower()}",
        f"- Network accessed: {str(summary['network_accessed']).lower()}", "",
        "## Traversal identity", "",
    ]
    lines.extend(
        f"- {run['order']}: content=`{run['content_identity_hash']}`; artifacts=`{run['artifact_set_hash']}`"
        for run in summary["orders"]
    )
    lines.extend(["", "## Accounting Gate", ""])
    lines.extend(f"- {key}: {str(value).lower()}" for key, value in summary["count_checks"].items())
    lines.extend(["", "## Findings", "", "### Critical", ""])
    lines.extend(f"- {item}" for item in summary["critical_findings"] or ["none"])
    lines.extend(["", "### High", ""])
    lines.extend(f"- {item}" for item in summary["high_findings"] or ["none"])
    lines.extend([
        "", "## Authorization", "",
        "This result is data-governance evidence only. U-04, strategy work, returns, OOS, API/trading, execution/live, and M2 remain unauthorized.", "",
    ])
    return "\n".join(lines)


def write_adr0015_audit_result(
    *, result: Mapping[str, Any], evidence_dir: Path, report_path: Path,
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    documents = {
        "audit_summary.json": result["summary"],
        "production_comparison.json": result["comparison"],
        "independent_manifest_hashes.json": result["runs"][0]["manifest_hashes"],
        "traversal_identity.json": result["summary"]["orders"],
    }
    for name, document in documents.items():
        (evidence_dir / name).write_text(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_adr0015_audit_report(result), encoding="utf-8")
