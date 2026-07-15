#!/usr/bin/env python3
"""Run the frozen V2 public qualification twice and publish deterministic evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_pipeline import artifact_set_hash
from scripts.liquid_universe_public_run import run

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAMES = (
    "source_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "quarantine_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_v1_membership(report_path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- 20") or ": " not in line:
            continue
        month, symbols = line[2:].split(": ", 1)
        if len(month) == 7 and month[4] == "-":
            result[month] = [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
    if not result:
        raise ValueError("V1 report contains no monthly membership rows")
    return result


def membership_by_month(document: dict) -> dict[str, list[str]]:
    rows: dict[str, list[tuple[int, str]]] = {}
    for row in document["content"]:
        month = row["effective_month"][:7]
        rows.setdefault(month, []).append((int(row["rank"]), row["symbol"]))
    return {month: [symbol for _, symbol in sorted(values)] for month, values in sorted(rows.items())}


def membership_diff(v1: dict[str, list[str]], v2: dict[str, list[str]]) -> dict:
    months = sorted(set(v1) | set(v2))
    details = []
    for month in months:
        old = v1.get(month, [])
        new = v2.get(month, [])
        old_rank = {symbol: index + 1 for index, symbol in enumerate(old)}
        new_rank = {symbol: index + 1 for index, symbol in enumerate(new)}
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        rank_changes = [
            {"symbol": symbol, "v1_rank": old_rank[symbol], "v2_rank": new_rank[symbol]}
            for symbol in sorted(set(old) & set(new))
            if old_rank[symbol] != new_rank[symbol]
        ]
        if added or removed or rank_changes:
            details.append({
                "effective_month": month,
                "added": added,
                "removed": removed,
                "rank_changes": rank_changes,
            })
    return {
        "months_compared": len(months),
        "changed_months": len(details),
        "membership_additions": sum(len(row["added"]) for row in details),
        "membership_removals": sum(len(row["removed"]) for row in details),
        "rank_changes": sum(len(row["rank_changes"]) for row in details),
        "details": details,
    }


def render_diff_report(diff: dict) -> str:
    lines = [
        "# Liquid Spot Universe V1/V2 Diff Report",
        "",
        "- Scope: historical membership comparison only; V1 Markdown is not a V2 qualification input.",
        f"- Months compared: {diff['months_compared']}",
        f"- Changed months: {diff['changed_months']}",
        f"- Membership additions: {diff['membership_additions']}",
        f"- Membership removals: {diff['membership_removals']}",
        f"- Rank changes: {diff['rank_changes']}",
        "- Strategy/events/signals/returns computed: no",
        "- OOS accessed: no",
        "- M2 authorized: no",
        "",
        "## Changed Months",
        "",
    ]
    if not diff["details"]:
        lines.append("- none")
    for row in diff["details"]:
        changes = ", ".join(
            f"{item['symbol']}:{item['v1_rank']}->{item['v2_rank']}"
            for item in row["rank_changes"]
        ) or "none"
        lines.extend([
            f"### {row['effective_month']}",
            "",
            f"- Added: {', '.join(row['added']) or 'none'}",
            f"- Removed: {', '.join(row['removed']) or 'none'}",
            f"- Rank changes: {changes}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def assert_deterministic(cold: dict[str, dict], warm: dict[str, dict]) -> None:
    if set(cold) != set(warm):
        raise ValueError("cold/warm manifest sets differ")
    mismatches = [name for name in sorted(cold) if cold[name]["content_hash"] != warm[name]["content_hash"]]
    if mismatches or artifact_set_hash(cold) != artifact_set_hash(warm):
        raise ValueError("cold/warm deterministic mismatch: " + ",".join(mismatches))


def _write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def execute(
    *,
    raw_root: Path,
    work_root: Path,
    evidence_dir: Path,
    report_path: Path,
    diff_report_path: Path,
    end_month: str,
    workers_cold: int,
    workers_warm: int,
    offline: bool,
) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    cold_dir = work_root / "cold"
    warm_dir = work_root / "warm"
    cold_report = work_root / "cold.md"
    warm_report = work_root / "warm.md"
    checksum_count_before = sum(1 for _ in raw_root.rglob("*.CHECKSUM"))
    cold = run(
        raw_root=raw_root,
        evidence_dir=cold_dir,
        end_month=end_month,
        report_path=cold_report,
        offline=offline,
        workers=workers_cold,
    )
    checksum_count_after_cold = sum(1 for _ in raw_root.rglob("*.CHECKSUM"))
    warm = run(
        raw_root=raw_root,
        evidence_dir=warm_dir,
        end_month=end_month,
        report_path=warm_report,
        offline=offline,
        workers=workers_warm,
    )
    assert_deterministic(cold, warm)
    if cold_report.read_bytes() != warm_report.read_bytes():
        raise ValueError("cold/warm generated Markdown differs")
    qualification_status = cold["qualification_summary"]["content"]["status"]

    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name in MANIFEST_NAMES:
        shutil.copyfile(cold_dir / f"{name}.json", evidence_dir / f"{name}.json")
    shutil.copyfile(cold_report, report_path)

    v1 = parse_v1_membership(ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_QUALIFICATION_REPORT.md")
    v2 = membership_by_month(cold["membership_manifest"])
    diff = membership_diff(v1, v2)
    diff_report_path.write_text(render_diff_report(diff), encoding="utf-8")

    run_content = {
        "status": qualification_status,
        "range": {"start": "2020-01", "end": end_month},
        "cold": {
            "workers": workers_cold,
            "artifact_set_hash": artifact_set_hash(cold),
            "manifest_hashes": {name: cold[name]["content_hash"] for name in sorted(cold)},
            "manifest_file_sha256": {name: file_sha256(cold_dir / f"{name}.json") for name in MANIFEST_NAMES},
            "generated_report_sha256": file_sha256(cold_report),
        },
        "warm": {
            "workers": workers_warm,
            "artifact_set_hash": artifact_set_hash(warm),
            "manifest_hashes": {name: warm[name]["content_hash"] for name in sorted(warm)},
            "manifest_file_sha256": {name: file_sha256(warm_dir / f"{name}.json") for name in MANIFEST_NAMES},
            "generated_report_sha256": file_sha256(warm_report),
        },
        "checksum_cache": {
            "before": checksum_count_before,
            "after_cold": checksum_count_after_cold,
            "after_warm": sum(1 for _ in raw_root.rglob("*.CHECKSUM")),
        },
        "deterministic_mismatches": 0,
        "v1_v2_diff": {key: value for key, value in diff.items() if key != "details"},
        "authorizations": {
            "hypothesis_preregistration": False,
            "strategy_code": False,
            "event_scan": False,
            "returns": False,
            "backtesting": False,
            "oos_opened": False,
            "m2": False,
            "api_or_trading": False,
        },
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    run_manifest = {
        "schema_version": 1,
        "manifest_type": "liquid_universe_v2_requalification_run",
        "content": run_content,
    }
    run_manifest["content_hash"] = canonical_hash(run_manifest)
    _write_json(evidence_dir / "requalification_run_manifest.json", run_manifest)
    return run_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe/data/spot")
    parser.add_argument("--work-root", type=Path, default=ROOT / "storage/logs/liquid_universe_v2_requalification")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v2")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_QUALIFICATION_REPORT.md")
    parser.add_argument("--diff-report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V1_V2_DIFF_REPORT.md")
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--workers-cold", type=int, default=16)
    parser.add_argument("--workers-warm", type=int, default=3)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    document = execute(
        raw_root=args.raw_root,
        work_root=args.work_root,
        evidence_dir=args.evidence_dir,
        report_path=args.report,
        diff_report_path=args.diff_report,
        end_month=args.end_month,
        workers_cold=args.workers_cold,
        workers_warm=args.workers_warm,
        offline=args.offline,
    )
    status = document["content"]["status"]
    print(f"status={status} content_hash={document['content_hash']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
