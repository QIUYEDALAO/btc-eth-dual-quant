#!/usr/bin/env python3
"""Validate committed U-03E machine evidence without reading runtime caches."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_artifacts import load_manifest
from scripts.liquid_universe_qualification_check import check as qualification_check

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_BLOCKERS = [
    "BTTUSDT:2019-01:1d:ValueError:daily volume must be finite and non-negative",
    "BTTUSDT:2019-02:1d:ValueError:daily volume must be finite and non-negative",
    "daily_merge:duplicate official_monthly_zip daily evidence: AXSUSDT:2026-02-10",
]


def check(evidence_dir: Path, report_path: Path, diff_report_path: Path) -> list[str]:
    failures: list[str] = []
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
    failures.extend(qualification_check(evidence_dir, report_path, contract, registry))
    try:
        run_document = json.loads((evidence_dir / "requalification_run_manifest.json").read_text(encoding="utf-8"))
        unsigned = {key: value for key, value in run_document.items() if key != "content_hash"}
        if run_document.get("content_hash") != canonical_hash(unsigned):
            failures.append("requalification run manifest hash mismatch")
        content = run_document["content"]
        cold, warm = content["cold"], content["warm"]
        if content.get("status") != "blocked" or content.get("range") != {"start": "2020-01", "end": "2026-06"}:
            failures.append("requalification status/range mismatch")
        if (cold.get("workers"), warm.get("workers")) != (16, 3):
            failures.append("cold/warm worker counts mismatch")
        for key in ("artifact_set_hash", "manifest_hashes", "manifest_file_sha256", "generated_report_sha256"):
            if cold.get(key) != warm.get(key):
                failures.append(f"cold/warm mismatch: {key}")
        if content.get("deterministic_mismatches") != 0:
            failures.append("deterministic mismatch count is non-zero")
        if content.get("checksum_cache") != {"before": 27729, "after_cold": 27729, "after_warm": 27729}:
            failures.append("checksum cache evidence mismatch")
        if content.get("v1_v2_diff") != {
            "months_compared": 78,
            "changed_months": 6,
            "membership_additions": 7,
            "membership_removals": 7,
            "rank_changes": 33,
        }:
            failures.append("V1/V2 diff evidence mismatch")
        if any(content.get("authorizations", {}).values()):
            failures.append("requalification enabled a prohibited authorization")
    except Exception as exc:
        failures.append(f"requalification run manifest: {exc}")
        return failures

    try:
        summary = load_manifest(
            evidence_dir / "qualification_summary.json",
            contract_hash=contract["canonical_hash"],
            registry_hash=registry["canonical_hash"],
        )["content"]
        fixed = {
            "status": "blocked",
            "historical_symbols_discovered": 676,
            "expected_months": 78,
            "monthly_memberships": 78,
            "membership_rows": 1170,
            "processing_errors": 3,
            "unresolved_gaps": 0,
            "excluded_category_members": 0,
            "excluded_invalid_daily_rows": 1,
            "synthetic_fills": 0,
            "replacement_members": 0,
            "gap_records": 227,
            "gap_missing_slots": 15022,
            "global_windows": 15,
            "symbol_month_quarantines": 2,
        }
        for key, value in fixed.items():
            if summary.get(key) != value:
                failures.append(f"qualification summary mismatch: {key}")
        if summary.get("blockers") != EXPECTED_BLOCKERS:
            failures.append("qualification blocker evidence mismatch")
    except Exception as exc:
        failures.append(f"qualification summary: {exc}")

    if not diff_report_path.is_file():
        failures.append("V1/V2 diff report missing")
    else:
        text = diff_report_path.read_text(encoding="utf-8")
        for line in (
            "- Scope: historical membership comparison only; V1 Markdown is not a V2 qualification input.",
            "- Strategy/events/signals/returns computed: no",
            "- OOS accessed: no",
            "- M2 authorized: no",
        ):
            if line not in text:
                failures.append(f"V1/V2 diff report missing guard: {line}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v2")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_QUALIFICATION_REPORT.md")
    parser.add_argument("--diff-report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V1_V2_DIFF_REPORT.md")
    args = parser.parse_args()
    failures = check(args.evidence_dir, args.report, args.diff_report)
    if failures:
        print("liquid_universe_v2_requalification_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("liquid_universe_v2_requalification_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
