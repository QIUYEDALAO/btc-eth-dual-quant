"""Canonical machine artifacts for liquid-universe V2 qualification."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from btc_eth_dual_quant.data.liquid_universe import canonical_hash

MANIFEST_TYPES = {
    "source_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "quarantine_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
}


def make_manifest(
    manifest_type: str,
    content: Any,
    *,
    contract_hash: str,
    registry_hash: str,
) -> dict[str, Any]:
    if manifest_type not in MANIFEST_TYPES:
        raise ValueError(f"unknown manifest type: {manifest_type}")
    document = {
        "schema_version": 2,
        "manifest_type": manifest_type,
        "contract_hash": contract_hash,
        "registry_hash": registry_hash,
        "content": content,
    }
    return {**document, "content_hash": canonical_hash(document)}


def verify_manifest(document: dict[str, Any], *, contract_hash: str, registry_hash: str) -> list[str]:
    failures: list[str] = []
    if document.get("schema_version") != 2 or document.get("manifest_type") not in MANIFEST_TYPES:
        failures.append("manifest identity mismatch")
    if document.get("contract_hash") != contract_hash:
        failures.append("manifest contract hash mismatch")
    if document.get("registry_hash") != registry_hash:
        failures.append("manifest registry hash mismatch")
    unsigned = {key: value for key, value in document.items() if key != "content_hash"}
    if document.get("content_hash") != canonical_hash(unsigned):
        failures.append("manifest content hash mismatch")
    return failures


def write_manifest(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True, default=_json_default) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def load_manifest(path: Path, *, contract_hash: str, registry_hash: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    failures = verify_manifest(document, contract_hash=contract_hash, registry_hash=registry_hash)
    if failures:
        raise ValueError("; ".join(failures))
    return document


def render_qualification_report(summary: dict[str, Any], manifest_hashes: dict[str, str]) -> str:
    authorizations = summary["authorizations"]
    lines = [
        "# Liquid Spot Universe V2 Qualification Report",
        "",
        f"- Status: {summary['status']}",
        f"- Contract: {summary['contract_id']}",
        f"- Actual range: {summary['research_start']} through {summary['end_month']}",
        f"- Historical symbols discovered: {summary['historical_symbols_discovered']}",
        f"- Expected months: {summary['expected_months']}",
        f"- Monthly memberships: {summary['monthly_memberships']}",
        f"- Membership rows: {summary['membership_rows']}",
        f"- Processing errors: {summary['processing_errors']}",
        f"- Unresolved gaps: {summary['unresolved_gaps']}",
        f"- Excluded-category members: {summary['excluded_category_members']}",
        f"- Invalid daily rows isolated after explicit asset exclusion: {summary.get('excluded_invalid_daily_rows', 0)}",
        f"- Synthetic fills: {summary['synthetic_fills']}",
        f"- Replacement members: {summary['replacement_members']}",
        f"- Strategy design authorized: {'yes' if authorizations['strategy_selection'] else 'no'}",
        f"- Event scan authorized: {'yes' if authorizations['event_scan'] else 'no'}",
        f"- Returns authorized: {'yes' if authorizations['returns'] else 'no'}",
        f"- Backtesting authorized: {'yes' if authorizations['freqtrade_backtesting'] else 'no'}",
        f"- OOS opened: {'yes' if authorizations['oos_access'] else 'no'}",
        f"- M2 authorized: {'yes' if authorizations['m2'] else 'no'}",
        "- Runtime artifacts committed: no",
        "",
        "## Manifest Hashes",
        "",
    ]
    lines.extend(f"- {name}: `{digest}`" for name, digest in sorted(manifest_hashes.items()))
    lines.extend(["", "## Monthly Membership", ""])
    for month in summary.get("members_by_month", []):
        lines.append(f"- {month['effective_month']}: " + ", ".join(month["symbols"]))
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in summary.get("blockers", []))
    if not summary.get("blockers"):
        lines.append("- none")
    return "\n".join(lines) + "\n"
