#!/usr/bin/env python3
"""Verify V2 quarantine evidence without parsing Markdown."""
from __future__ import annotations

import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe_artifacts import load_manifest

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
    try:
        document = load_manifest(
            ROOT / "reports/m0/evidence/liquid_universe_v2/quarantine_manifest.json",
            contract_hash=contract["canonical_hash"],
            registry_hash=registry["canonical_hash"],
        )
        content = document["content"]
        if content.get("unresolved"):
            raise ValueError("unresolved gaps remain")
        if any(scope.get("decision") not in {"quarantine_global_window_all_members", "quarantine_entire_symbol_month_without_replacement"} for scope in content.get("scopes", [])):
            raise ValueError("invalid quarantine decision")
    except Exception as exc:
        print(f"liquid_universe_gap_attribution_check FAIL: {exc}")
        return 1
    print("liquid_universe_gap_attribution_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
