#!/usr/bin/env python3
"""Render V2 gap attribution from verified machine manifests."""
from __future__ import annotations

import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe_artifacts import load_manifest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v2"
OUT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_GAP_ATTRIBUTION_REPORT.md"


def main() -> int:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
    quarantine = load_manifest(EVIDENCE / "quarantine_manifest.json", contract_hash=contract["canonical_hash"], registry_hash=registry["canonical_hash"])
    summary = load_manifest(EVIDENCE / "qualification_summary.json", contract_hash=contract["canonical_hash"], registry_hash=registry["canonical_hash"])["content"]
    inner = quarantine["content"]
    scopes = inner["scopes"]
    global_scopes = [scope for scope in scopes if scope["scope"] == "global_window"]
    symbol_scopes = [scope for scope in scopes if scope["scope"] == "symbol_month"]
    lines = [
        "# Liquid Spot Universe V2 Gap Attribution Report",
        "",
        f"- Status: {'pass_with_quarantine' if not inner['unresolved'] and summary['processing_errors'] == 0 else 'blocked'}",
        f"- Global quarantine windows: {len(global_scopes)}",
        f"- Symbol-month quarantines: {len(symbol_scopes)}",
        f"- Processing errors: {summary['processing_errors']}",
        f"- Unresolved gaps: {len(inner['unresolved'])}",
        "- Strategy design authorized: no",
        "- Event scan authorized: no",
        "- Returns authorized: no",
        "- OOS opened: false",
        "- M2 authorized: no",
        "",
        "## Quarantine Scopes",
        "",
    ]
    for scope in scopes:
        if scope["scope"] == "global_window":
            lines.append(f"- global_window {scope['month']} {scope['start']} to {scope['end_exclusive']}: {scope['affected_member_count']}/{scope['total_member_count']} members")
        else:
            lines.append(f"- symbol_month {scope['symbol']} {scope['month']}: {scope['reason']}")
    if not scopes:
        lines.append("- none")
    lines.extend(["", "## Unresolved", ""])
    lines.extend(f"- {json.dumps(item, sort_keys=True)}" for item in inner["unresolved"])
    if not inner["unresolved"]:
        lines.append("- none")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={'pass' if not inner['unresolved'] and summary['processing_errors'] == 0 else 'blocked'}")
    return 0 if not inner["unresolved"] and summary["processing_errors"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
