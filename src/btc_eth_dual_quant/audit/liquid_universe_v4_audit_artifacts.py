"""Independent artifact wrapping, comparison and implementation scanners."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .liquid_universe_v4_independent import audit_canonical_json, audit_content_hash


PROHIBITED_IMPORT_PREFIXES = (
    "btc_eth_dual_quant.data.liquid_universe",
    "btc_eth_dual_quant.data.lifecycle_availability",
    "btc_eth_dual_quant.data.lifecycle_artifacts",
    "btc_eth_dual_quant.data.kline_row_conflicts",
    "btc_eth_dual_quant.data.public_archive",
    "scripts.liquid_universe",
)
PROHIBITED_CALLS = frozenset({
    "build_membership_rows", "dispatch_daily_rows", "resolve_daily_key",
    "validate_symbol_month_grid", "validate_lifecycle_symbol_month_grid",
    "aggregate_one_hour", "make_v4_manifest", "canonical_hash", "artifact_set_hash",
})


def make_manifest(manifest_type: str, content: Any, schema_version: int = 1) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "manifest_type": manifest_type,
        "content": content,
        "content_hash": audit_content_hash(content),
    }


def audit_manifest_hash(manifest: Mapping[str, Any]) -> str:
    if manifest.get("content_hash") != audit_content_hash(manifest.get("content")):
        raise ValueError("manifest content hash is invalid")
    return audit_content_hash(dict(manifest))


def verify_manifest_wrapper(
    manifest: Mapping[str, Any],
    *,
    expected_type: str | None = None,
    expected_contract_hash: str | None = None,
    expected_registry_hash: str | None = None,
) -> str:
    required = {"schema_version", "manifest_type", "content", "content_hash"}
    if not required <= set(manifest):
        raise ValueError("manifest wrapper is incomplete")
    if not isinstance(manifest.get("schema_version"), int):
        raise ValueError("manifest schema_version must be an integer")
    if expected_type is not None and manifest.get("manifest_type") != expected_type:
        raise ValueError("manifest type changed")
    if expected_contract_hash is not None and manifest.get("contract_hash") != expected_contract_hash:
        raise ValueError("manifest contract binding changed")
    if expected_registry_hash is not None and manifest.get("lifecycle_registry_hash") != expected_registry_hash:
        raise ValueError("manifest lifecycle binding changed")
    return audit_manifest_hash(manifest)


def audit_artifact_set_hash(manifests: Mapping[str, Mapping[str, Any]]) -> str:
    rows = [{"name": name, "manifest_hash": audit_manifest_hash(value)} for name, value in sorted(manifests.items())]
    return audit_content_hash(rows)


def _first_difference(left: Any, right: Any, path: str = "$") -> str | None:
    if type(left) is not type(right):
        return f"{path}: type {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        if list(left) != list(right):
            return f"{path}: key/order mismatch"
        for key in left:
            difference = _first_difference(left[key], right[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (one, two) in enumerate(zip(left, right)):
            difference = _first_difference(one, two, f"{path}[{index}]")
            if difference:
                return difference
        return None
    return None if left == right else f"{path}: {left!r} != {right!r}"


def compare_manifest(production: Mapping[str, Any], independent: Mapping[str, Any]) -> dict[str, Any]:
    first = _first_difference(production, independent)
    exact = first is None
    return {
        "exact_content_match": exact,
        "row_count_match": _row_count(production.get("content")) == _row_count(independent.get("content")),
        "field_type_match": type(production.get("content")) is type(independent.get("content")),
        "production_content_hash": production.get("content_hash"),
        "independent_content_hash": independent.get("content_hash"),
        "first_mismatch": first,
        "mismatch_count": 0 if exact else 1,
    }


REQUIRED_AUDIT_ARTIFACTS = (
    "source_manifest",
    "row_conflict_resolution_manifest",
    "lifecycle_policy_manifest",
    "lifecycle_resolution_registry",
    "symbol_availability_manifest",
    "active_universe_manifest",
    "complete_day_mask",
    "expected_grid_manifest",
    "raw_row_quarantine_manifest",
    "lifecycle_event_quarantine_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
    "V3_V4_diff",
)


def build_audit_artifacts(
    contents: Mapping[str, Any],
    *,
    contract_hash: str,
    lifecycle_registry_hash: str,
) -> dict[str, dict[str, Any]]:
    if set(contents) != set(REQUIRED_AUDIT_ARTIFACTS):
        missing = sorted(set(REQUIRED_AUDIT_ARTIFACTS) - set(contents))
        extra = sorted(set(contents) - set(REQUIRED_AUDIT_ARTIFACTS))
        raise ValueError(f"audit artifact suite mismatch: missing={missing}, extra={extra}")
    output: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_AUDIT_ARTIFACTS:
        output[name] = {
            "schema_version": 1,
            "manifest_type": name,
            "contract_hash": contract_hash,
            "lifecycle_registry_hash": lifecycle_registry_hash,
            "content": contents[name],
            "content_hash": audit_content_hash(contents[name]),
        }
    return output


def compare_artifact_suite(
    production: Mapping[str, Mapping[str, Any]],
    independent: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if set(production) != set(independent):
        return {
            "exact": False,
            "artifact_set_match": False,
            "first_mismatch": "artifact names differ",
            "comparisons": {},
        }
    comparisons = {name: compare_manifest(production[name], independent[name]) for name in sorted(production)}
    exact = all(item["exact_content_match"] for item in comparisons.values())
    try:
        set_match = audit_artifact_set_hash(production) == audit_artifact_set_hash(independent)
    except ValueError:
        set_match = False
    first = next((f"{name}: {item['first_mismatch']}" for name, item in comparisons.items() if item["first_mismatch"]), None)
    return {"exact": exact and set_match, "artifact_set_match": set_match, "first_mismatch": first, "comparisons": comparisons}


def verify_run_manifest(manifest: Mapping[str, Any], *, expected_authorizations: Mapping[str, bool]) -> str:
    verify_manifest_wrapper(manifest, expected_type="liquid_universe_v4_requalification_run")
    content = manifest.get("content", {})
    if content.get("authorizations") != dict(expected_authorizations):
        raise ValueError("run manifest authorization changed")
    return audit_manifest_hash(manifest)


def verify_file_hash(path: Path, expected_sha256: str) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"file hash mismatch: {path}")
    return digest


def _row_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return sum(len(item) for item in value.values() if isinstance(item, list))
    return 0


def scan_independence(source: str) -> list[str]:
    findings: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PROHIBITED_IMPORT_PREFIXES):
                    findings.append(f"line {node.lineno}: prohibited import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(PROHIBITED_IMPORT_PREFIXES):
                findings.append(f"line {node.lineno}: prohibited import {module}")
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in PROHIBITED_CALLS:
                findings.append(f"line {node.lineno}: prohibited production call {name}")
    return findings


def scan_copied_production_functions(auditor_source: str, production_sources: Sequence[str]) -> list[str]:
    """Reject exact normalized function bodies copied from production under a new name."""

    def bodies(source: str) -> list[str]:
        tree = ast.parse(source)
        output: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) >= 2:
                clone = ast.FunctionDef(
                    name="_",
                    args=node.args,
                    body=node.body,
                    decorator_list=[],
                    returns=node.returns,
                    type_comment=node.type_comment,
                )
                output.append(ast.dump(clone, include_attributes=False))
        return output

    production = set().union(*(set(bodies(source)) for source in production_sources))
    return ["auditor contains a production-identical function body" for body in bodies(auditor_source) if body in production]


def scan_float_timestamp_paths(source: str) -> list[str]:
    findings: list[str] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        compact = line.replace(" ", "")
        if ".timestamp()" in compact:
            findings.append(f"line {line_number}: datetime.timestamp authority path")
        if "fromtimestamp(" in compact and "/1_000" in compact:
            findings.append(f"line {line_number}: float epoch reconstruction")
    return findings


def validate_authorization(value: Mapping[str, Any]) -> list[str]:
    return [f"authorization enabled: {key}" for key, enabled in value.items() if enabled is not False]


def changed_file_list_hash(paths: list[str]) -> str:
    encoded = json.dumps(sorted(paths), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def scan_files(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        findings.extend(f"{path}:{item}" for item in scan_independence(source))
    return findings
