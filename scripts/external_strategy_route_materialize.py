#!/usr/bin/env python3
"""Build deterministic ADR-0016 evidence without importing strategy code."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "config/external_strategy_inventory_v1.json"
EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_source_screen_v1.json"
FREEZE = ROOT / "config/external_strategy_candidate_freeze_v1.json"
ARCHIVE_DIR = ROOT / "external_strategies/upstream_archives"
PARAMETER_CONFLICTS = {"Supertrend", "Diamond", "Heracles"}
BANNED = {
    "dynamic_execution": re.compile(r"\b(?:eval|exec)\s*\("),
    "network_access": re.compile(r"\b(?:requests|urllib|socket|aiohttp)\b"),
    "process_execution": re.compile(r"\b(?:subprocess|os\.system)\b"),
    "file_write": re.compile(r"\b(?:write_text|write_bytes|to_pickle|joblib\.dump)\b|open\s*\([^\n]+['\"](?:w|a|x|\+)"),
    "model_loading": re.compile(r"\b(?:torch|tensorflow|keras|joblib|pickle|GANs?)\b"),
    "position_adjustment": re.compile(r"position_adjustment_enable\s*=\s*True|def\s+adjust_trade_position"),
    "short_or_leverage": re.compile(r"can_short\s*=\s*True|def\s+leverage|trading_mode\s*=\s*['\"]futures"),
    "future_data": re.compile(r"shift\s*\(\s*-\d+|iloc\s*\[\s*-1\s*\]"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def canonical_hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def cached_archive(repo: str, commit: str) -> Path:
    cache = Path("/tmp/external-strategy-archives") / f"{repo.replace('/', '--')}--{commit}.tar.gz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        subprocess.run(["curl", "-fsSL", f"https://codeload.github.com/{repo}/tar.gz/{commit}", "-o", str(cache)], check=True)
    return cache


def archive_members(archive: Path) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if not member.isfile() or "/" not in member.name:
                continue
            handle = bundle.extractfile(member)
            if handle is not None:
                found[member.name.split("/", 1)[1]] = handle.read()
    return found


def file_license_record(text: str, repo_license: str) -> dict:
    spdx = re.findall(r"SPDX-License-Identifier:\s*([^\s*]+)", text, re.I)
    declared = re.findall(r"__license__\s*=\s*['\"]([^'\"]+)", text)
    authors = re.findall(r"(?:__author__\s*=\s*['\"]([^'\"]+)|(?:#|\*)\s*Author(?:@|\s*:)?\s*([^\n]+))", text, re.I)
    author_values = sorted({(a or b).strip() for a, b in authors if (a or b).strip()})
    file_license = spdx[0] if spdx else declared[0] if declared else None
    return {
        "spdx_identifiers": spdx,
        "declared_license": file_license,
        "authors": author_values,
        "repo_license": repo_license,
        "effective_license_decision": file_license or repo_license,
    }


def literal(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return ast.unparse(node)


def source_declaration(candidate_id: str, data: bytes) -> dict:
    tree = ast.parse(data.decode("utf-8"))
    assignments: dict[str, object] = {}
    parameters: list[dict] = []
    allowed = {
        "INTERFACE_VERSION", "timeframe", "minimal_roi", "stoploss", "trailing_stop",
        "trailing_stop_positive", "trailing_stop_positive_offset",
        "trailing_only_offset_is_reached", "startup_candle_count",
        "process_only_new_candles", "use_exit_signal", "exit_profit_only",
        "ignore_roi_if_entry_signal", "can_short", "position_adjustment_enable",
        "max_entry_position_adjustment", "use_custom_stoploss", "order_types",
        "order_time_in_force", "protections", "buy_params", "sell_params",
    }
    behavior_names = {
        "populate_indicators", "populate_entry_trend", "populate_exit_trend",
        "custom_stoploss", "custom_entry_price", "custom_exit_price",
        "confirm_trade_entry", "confirm_trade_exit", "custom_stake_amount",
        "adjust_trade_position", "leverage", "protections", "informative_pairs",
    }
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    imports = sorted({ast.unparse(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))})
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            for target in targets:
                if not isinstance(target, ast.Name) or value is None:
                    continue
                name = target.id
                if name in allowed or name.startswith(("trailing_", "buy_", "sell_")):
                    assignments[name] = literal(value)
                if isinstance(value, ast.Call):
                    func = ast.unparse(value.func).split(".")[-1]
                    if func in {"IntParameter", "DecimalParameter", "RealParameter", "BooleanParameter", "CategoricalParameter"}:
                        keywords = {kw.arg or "**": literal(kw.value) for kw in value.keywords}
                        positional = [literal(arg) for arg in value.args]
                        parameters.append({
                            "name": name,
                            "type": func,
                            "low": positional[0] if func in {"IntParameter", "DecimalParameter", "RealParameter"} and positional else None,
                            "high": positional[1] if func in {"IntParameter", "DecimalParameter", "RealParameter"} and len(positional) > 1 else None,
                            "choices": positional[0] if func == "CategoricalParameter" and positional else None,
                            "decimals": keywords.get("decimals"),
                            "default": keywords.get("default"),
                            "load": keywords.get("load"),
                            "optimize": keywords.get("optimize"),
                            "space": keywords.get("space"),
                            "args": positional,
                            "keywords": keywords,
                        })
    methods = sorted({node.name for cls in classes for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))})
    dynamic_attributes = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "delattr"}
        for node in ast.walk(tree)
    )
    external_config_loading = any(
        isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] in {"open", "load", "loads", "read_text", "read_bytes"}
        for node in ast.walk(tree)
    )
    parameter_json_lookup = any(
        isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower().endswith(".json")
        for node in ast.walk(tree)
    )
    position_increase = (
        assignments.get("position_adjustment_enable") is True
        or "adjust_trade_position" in methods
        or isinstance(assignments.get("max_entry_position_adjustment"), (int, float))
        and assignments["max_entry_position_adjustment"] > 0
    )
    assignments = {name: assignments.get(name) for name in sorted(allowed)}
    declaration = {
        "strategy_classes": [{"name": cls.name, "bases": [ast.unparse(base) for base in cls.bases]} for cls in classes],
        "imports": imports,
        "assignments": dict(sorted(assignments.items())),
        "parameter_declarations": sorted(parameters, key=lambda item: item["name"]),
        "behavior_methods": {name: name in methods for name in sorted(behavior_names)},
        "informative_timeframes": sorted({
            str(value) for parameter in parameters for value in parameter.get("args", [])
            if isinstance(value, str) and re.fullmatch(r"\d+[mhdw]", value)
        }),
        "dynamic_attribute_access": dynamic_attributes,
        "external_config_loading": external_config_loading,
        "parameter_json_lookup": parameter_json_lookup,
        "position_increase_capability": bool(position_increase),
        "required_external_parameter_file_count": 0,
        "required_config_override_count": 0,
        "observed_external_parameter_file_count": None,
        "observed_config_override_count": None,
        "runtime_resolution_status": "runtime_resolution_pending" if candidate_id in PARAMETER_CONFLICTS else "pending_vps_load",
        "class_parameter_default_conflict": candidate_id in PARAMETER_CONFLICTS,
        "runtime_effective_settings_hash": None,
        "runtime_resolved_parameters_hash": None,
    }
    declaration["source_declaration_hash"] = canonical_hash(declaration)
    return declaration


def main() -> int:
    inventory_bytes = INVENTORY.read_bytes()
    inv = json.loads(inventory_bytes)
    archives: dict[str, Path] = {}
    members: dict[str, dict[str, bytes]] = {}
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for key, repo in inv["repositories"].items():
        archive = cached_archive(repo["repository"], repo["commit"])
        archives[key] = archive
        members[key] = archive_members(archive)
        if repo["archive_path"]:
            shutil.copyfile(archive, ROOT / repo["archive_path"])

    results = []
    for candidate in inv["candidates"]:
        repo = inv["repositories"][candidate["repo"]]
        upstream = members[candidate["repo"]].get(candidate["source_path"])
        if upstream is None:
            raise SystemExit(f"missing candidate archive member: {candidate['source_path']}")
        materialized = candidate.get("source_materialized", True)
        source = ROOT / "external_strategies/original" / f"{candidate['order']:02d}-{candidate['id']}" / f"{candidate['id']}.py"
        if materialized and source.read_bytes() != upstream:
            raise SystemExit(f"local/upstream source mismatch: {candidate['id']}")
        if not materialized and source.exists():
            raise SystemExit(f"unlicensed source must not be redistributed: {candidate['id']}")
        text = upstream.decode("utf-8")
        findings = sorted(name for name, pattern in BANNED.items() if pattern.search(text))
        reasons: list[str] = []
        dependency_paths = [candidate["source_path"]]
        if candidate["repo"] == "nate":
            dependency_paths += ["SimpleStrategies/SimpleStrategy.py", "Framework/BaseStrategy.py", "utils/custom_indicators.py", "utils/DataframePopulator.py", "utils/DataframeUtils.py", "utils/Environment.py", "Framework/StrategyDiagnostics.py", "GANs/GANType.py"]
            reasons.append("dynamic_sys_path_and_model_framework_dependency_closure")
        dependency_closure = []
        missing_dependencies = []
        for path in dependency_paths:
            payload = members[candidate["repo"]].get(path)
            if payload is None:
                missing_dependencies.append(path)
            else:
                dependency_closure.append({"path": path, "sha256": sha256(payload), "git_blob_sha1": git_blob_sha(payload), "size": len(payload)})
        if missing_dependencies:
            reasons.append("missing_dependency_member")
        license_record = file_license_record(text, repo["repo_license"])
        if not materialized:
            reasons.append("unverified_repository_and_target_file_license")
        reasons.extend(findings)
        status = "PASS" if not reasons else "REJECT"
        result = {
            "order": candidate["order"], "id": candidate["id"], "status": status,
            "reasons": sorted(set(reasons)), "repository": repo["repository"], "commit": repo["commit"],
            "source_path": candidate["source_path"], "source_materialized": materialized,
            "local_read_only_source": str(source.relative_to(ROOT)) if materialized else None,
            "license_status": candidate.get("license_status", "redistributed_under_verified_license"),
            "license_evidence": license_record, "source_sha256": sha256(upstream),
            "git_blob_sha1": git_blob_sha(upstream), "source_size": len(upstream),
            "repository_archive_sha256": sha256(archives[candidate["repo"]].read_bytes()),
            "repository_archive_path": repo["archive_path"], "dependency_closure": dependency_closure,
            "missing_dependency_paths": missing_dependencies, "static_findings": findings,
        }
        if materialized:
            result["source_declaration"] = source_declaration(candidate["id"], upstream)
        results.append(result)

    passed = [item for item in results if item["status"] == "PASS"]
    frozen = passed[:6] if len(passed) >= 6 else passed if len(passed) == 5 else []
    evidence = {
        "schema_version": "external-strategy-source-screen-v2",
        "inventory_sha256": sha256(inventory_bytes),
        "scan_execution": "source_text_and_ast_only_never_imported_or_executed",
        "sandbox_contract": ["network_none", "read_only_source", "non_privileged_user", "no_secrets", "dependency_hash_allowlist"],
        "results": results, "pass_count": len(passed), "frozen_ids": [item["id"] for item in frozen],
        "hard_stop_less_than_five": len(frozen) < 5, "freqtrade_loads": 0, "causal_validations": 0,
        "selection_trial_count": 0, "is_rows_materialized": 0, "oos_rows_decoded": 0,
    }
    evidence["content_hash"] = canonical_hash(evidence)
    freeze = {
        "schema_version": "external-strategy-candidate-freeze-v2", "screen_content_hash": evidence["content_hash"],
        "selection_rule": inv["selection_rule"],
        "frozen_candidates": [{
            "order": item["order"], "id": item["id"], "commit": item["commit"], "source_sha256": item["source_sha256"],
            "source_declaration_hash": item["source_declaration"]["source_declaration_hash"],
            "adapter_hash": None,
            "base_adapter_hash": None,
            "runtime_resolution_status": item["source_declaration"]["runtime_resolution_status"],
            "runtime_effective_settings_hash": None,
            "runtime_resolved_parameters_hash": None,
            "observed_external_parameter_file_count": None,
            "observed_config_override_count": None,
            "modification_package": {"id": None, "before_hash": None, "after_hash": None, "atomic_changes": [], "package_hash": None},
        } for item in frozen],
        "required_external_parameter_file_count": 0, "required_config_override_count": 0,
        "observed_external_parameter_file_count": None, "observed_config_override_count": None,
        "modification_packages": {item["id"]: {"id": None, "before_hash": None, "after_hash": None, "atomic_changes": [], "package_hash": None} for item in frozen},
        "trial_manifest_limits": {"original_per_candidate":1,"modified_per_candidate":1,"maximum_modified_candidates":3,"modified_requires_passing_original":True,"modified_requires_unique_preregistered_package":True,"modified_must_materialize_strictly_after_original":True,"ordering":"first_materialized_utc_then_trial_id"},
        "result_contract": {"common_envelope_schema":"external-strategy-is-result-v1","kinds":["trades","equity","metrics"],"scenarios":["Base","CostX2","StressA","StressB"],"metric_authority":"equity_recomputed_unified_metrics","dsr_authority":"equity_recomputed_sharpe_plus_frozen_trial_sequence","variant_identity_fields":["base_adapter_hash","variant_executable_hash"]},
        "selection_trial_count": 0, "is_rows_materialized": 0, "oos_rows_decoded": 0,
    }
    freeze["content_hash"] = canonical_hash(freeze)
    EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(f"screen={evidence['content_hash']}\nfreeze={freeze['content_hash']}")
    return 2 if evidence["hard_stop_less_than_five"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
