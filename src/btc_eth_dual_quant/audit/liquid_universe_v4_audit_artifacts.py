"""Independent artifact wrapping, comparison and implementation scanners."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

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
