#!/usr/bin/env python3
"""Verify V2 machine artifacts and their generated Markdown report."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe import exclusion_record
from btc_eth_dual_quant.data.liquid_universe_artifacts import load_manifest, render_qualification_report

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "source_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "quarantine_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
)


def check(evidence_dir: Path, report_path: Path, contract: dict, registry: dict) -> list[str]:
    failures: list[str] = []
    manifests = {}
    for name in NAMES:
        try:
            manifests[name] = load_manifest(
                evidence_dir / f"{name}.json",
                contract_hash=contract["canonical_hash"],
                registry_hash=registry["canonical_hash"],
            )
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        return failures

    source_rows = manifests["source_manifest"]["content"]
    source_keys = [(row["symbol"], row["interval"], row["archive_month"]) for row in source_rows]
    if len(source_keys) != len(set(source_keys)):
        failures.append("source manifest contains duplicate authority keys")
    allowed_verification = {"official_checksum_verified", "official_checksum_unavailable_zip_crc_sha256_verified"}
    if any(row.get("verification_status") not in allowed_verification for row in source_rows):
        failures.append("source manifest contains unverified archives")

    memberships = manifests["membership_manifest"]["content"]
    by_month: dict[str, list[dict]] = defaultdict(list)
    for row in memberships:
        month = row["effective_month"][:7]
        by_month[month].append(row)
        if row.get("contract_hash") != contract["canonical_hash"] or row.get("asset_registry_hash") != registry["canonical_hash"]:
            failures.append(f"membership binding mismatch: {month}:{row.get('symbol')}")
        if exclusion_record(row["symbol"], date.fromisoformat(row["effective_month"]), contract, registry):
            failures.append(f"excluded asset entered membership: {month}:{row['symbol']}")
    for month, rows in by_month.items():
        ranks = sorted(row["rank"] for row in rows)
        if ranks != list(range(1, len(rows) + 1)) or not 1 <= len(rows) <= 15:
            failures.append(f"invalid rank sequence: {month}")
        if len({row["symbol"] for row in rows}) != len(rows):
            failures.append(f"duplicate monthly member: {month}")

    quarantine = manifests["quarantine_manifest"]["content"]
    inner = quarantine
    attribution_records = inner.get("attribution_records", [])
    attribution_keys = [
        (row["symbol"], row["month"], row["timestamp"], row["missing_count"])
        for row in attribution_records
    ]
    if len(attribution_keys) != len(set(attribution_keys)):
        failures.append("quarantine manifest contains duplicate attribution records")
    if any(row["missing_count"] <= 0 or row["duration_minutes"] != row["missing_count"] * 5 for row in attribution_records):
        failures.append("quarantine attribution duration conservation failed")
    if inner.get("unresolved"):
        failures.append("quarantine manifest contains unresolved gaps")
    member_sets = {month: {row["symbol"] for row in rows} for month, rows in by_month.items()}
    for scope in inner.get("scopes", []):
        if scope["scope"] == "global_window":
            if set(scope["affected_symbols"]) != member_sets.get(scope["month"], set()):
                failures.append(f"global quarantine does not cover every member: {scope['month']}:{scope['start']}")
        elif scope["scope"] == "symbol_month":
            if scope["symbol"] not in member_sets.get(scope["month"], set()):
                failures.append("symbol-month quarantine references non-member")
        else:
            failures.append("unknown quarantine scope")

    panel = manifests["qualified_panel_manifest"]["content"]
    if len(panel) != len(memberships):
        failures.append("qualified panel/membership row count mismatch")
    panel_keys = {(row["effective_month"], row["symbol"]) for row in panel}
    membership_keys = {(row["effective_month"][:7], row["symbol"]) for row in memberships}
    if panel_keys != membership_keys:
        failures.append("qualified panel membership keys mismatch")
    for row in panel:
        if row["valid_1h_count"] + row["quarantined_1h_count"] != row["expected_1h_count"]:
            failures.append(f"panel conservation failed: {row['effective_month']}:{row['symbol']}")
        if row["status"] not in {"clean", "global_window_quarantined", "symbol_month_quarantined", "blocked"}:
            failures.append("unknown panel status")

    summary = manifests["qualification_summary"]["content"]
    expected_months = len(by_month)
    if summary["monthly_memberships"] != expected_months or summary["membership_rows"] != len(memberships):
        failures.append("summary membership counts mismatch")
    if summary["expected_months"] != expected_months:
        failures.append("summary expected-month count mismatch")
    if summary["status"] == "pass" and any(summary[key] for key in ("processing_errors", "unresolved_gaps", "excluded_category_members", "synthetic_fills", "replacement_members")):
        failures.append("pass summary contains blockers")
    if summary.get("gap_records") != len(attribution_records):
        failures.append("summary/quarantine gap record count mismatch")
    if summary.get("gap_missing_slots") != sum(row["missing_count"] for row in attribution_records):
        failures.append("summary/quarantine missing-slot conservation failed")
    authorizations = summary["authorizations"]
    if any(value for key, value in authorizations.items() if key != "asset_data_qualification"):
        failures.append("downstream authorization enabled")
    hashes = {name: document["content_hash"] for name, document in manifests.items()}
    expected_report = render_qualification_report(summary, hashes)
    if not report_path.is_file() or report_path.read_text(encoding="utf-8") != expected_report:
        failures.append("Markdown report does not match machine artifacts")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v2")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_QUALIFICATION_REPORT.md")
    args = parser.parse_args()
    contract = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text(encoding="utf-8"))
    failures = check(args.evidence_dir, args.report, contract, registry)
    if failures:
        print("liquid_universe_qualification_check FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("liquid_universe_qualification_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
