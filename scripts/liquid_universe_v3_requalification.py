#!/usr/bin/env python3
"""Run frozen V3 public qualification three ways and publish exact evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_pipeline import artifact_set_hash
from scripts.liquid_universe_v2_requalification import (
    membership_by_month,
    membership_diff,
    parse_v1_membership,
)
from scripts.liquid_universe_v3_public_run import ROOT, run


MANIFEST_NAMES = (
    "source_manifest",
    "conflict_resolution_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "quarantine_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_membership_diff_report(diff: dict, *, left: str, right: str) -> str:
    lines = [
        f"# Liquid Spot Universe {left}/{right} Diff Report", "",
        "- Scope: historical membership comparison only; prior authority is not a V3 qualification input.",
        f"- Months compared: {diff['months_compared']}",
        f"- Changed months: {diff['changed_months']}",
        f"- Membership additions: {diff['membership_additions']}",
        f"- Membership removals: {diff['membership_removals']}",
        f"- Rank changes: {diff['rank_changes']}",
        "- Strategy/events/signals/returns computed: no",
        "- OOS accessed: no",
        "- M2 authorized: no", "", "## Changed Months", "",
    ]
    if not diff["details"]:
        lines.append("- none")
    for row in diff["details"]:
        changes = ", ".join(
            f"{item['symbol']}:{item[f'{left.lower()}_rank']}->{item[f'{right.lower()}_rank']}"
            for item in row["rank_changes"]
        ) or "none"
        lines.extend([
            f"### {row['effective_month']}", "",
            f"- Added: {', '.join(row['added']) or 'none'}",
            f"- Removed: {', '.join(row['removed']) or 'none'}",
            f"- Rank changes: {changes}", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _named_membership_diff(left: dict[str, list[str]], right: dict[str, list[str]], *, left_name: str, right_name: str) -> dict:
    base = membership_diff(left, right)
    details = []
    for row in base["details"]:
        details.append({
            **row,
            "rank_changes": [
                {
                    "symbol": item["symbol"],
                    f"{left_name.lower()}_rank": item["v1_rank"],
                    f"{right_name.lower()}_rank": item["v2_rank"],
                }
                for item in row["rank_changes"]
            ],
        })
    return {**base, "details": details}


def assert_three_way_determinism(
    builds: dict[str, dict[str, dict]],
    reports: dict[str, Path],
    extras: dict[str, dict[str, Path]],
) -> None:
    if set(builds) != {"cold", "warm", "worker"}:
        raise ValueError("cold/warm/worker builds are required")
    baseline = builds["cold"]
    for name in ("warm", "worker"):
        current = builds[name]
        if set(current) != set(baseline):
            raise ValueError(f"{name} manifest set mismatch")
        mismatches = [key for key in sorted(baseline) if baseline[key]["content_hash"] != current[key]["content_hash"]]
        if mismatches or artifact_set_hash(baseline) != artifact_set_hash(current):
            raise ValueError(f"{name} artifact mismatch: {','.join(mismatches)}")
        if reports["cold"].read_bytes() != reports[name].read_bytes():
            raise ValueError(f"{name} report mismatch")
        if set(extras["cold"]) != set(extras[name]):
            raise ValueError(f"{name} extra report set mismatch")
        for key in sorted(extras["cold"]):
            if extras["cold"][key].read_bytes() != extras[name][key].read_bytes():
                raise ValueError(f"{name} {key} mismatch")


def should_continue_after_cold(summary: dict) -> bool:
    return summary.get("status") == "pass"


def _write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def execute(
    *,
    raw_root: Path,
    work_root: Path,
    evidence_dir: Path,
    report_path: Path,
    v1_diff_report: Path,
    v2_diff_report: Path,
    end_month: str,
    workers_cold: int,
    workers_warm: int,
    workers_variant: int,
) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    builds: dict[str, dict[str, dict]] = {}
    reports: dict[str, Path] = {}
    extras: dict[str, dict[str, Path]] = {}
    workers = {"cold": workers_cold, "warm": workers_warm, "worker": workers_variant}
    v1 = parse_v1_membership(ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_QUALIFICATION_REPORT.md")
    v2_document = json.loads((ROOT / "reports/m0/evidence/liquid_universe_v2/membership_manifest.json").read_text())
    v2 = membership_by_month(v2_document)

    for name in ("cold", "warm", "worker"):
        build_dir = work_root / name
        report = work_root / f"{name}.md"
        print(f"build={name} workers={workers[name]} status=started", flush=True)
        builds[name] = run(
            raw_root=raw_root,
            evidence_dir=build_dir,
            end_month=end_month,
            report_path=report,
            offline=False,
            workers=workers[name],
            verify_remote_registry=True,
        )
        reports[name] = report
        v3 = membership_by_month(builds[name]["membership_manifest"])
        v1_diff = _named_membership_diff(v1, v3, left_name="V1", right_name="V3")
        v2_diff = _named_membership_diff(v2, v3, left_name="V2", right_name="V3")
        v1_path = work_root / f"{name}-v1-v3.md"
        v2_path = work_root / f"{name}-v2-v3.md"
        v1_path.write_text(render_membership_diff_report(v1_diff, left="V1", right="V3"), encoding="utf-8")
        v2_path.write_text(render_membership_diff_report(v2_diff, left="V2", right="V3"), encoding="utf-8")
        extras[name] = {"v1_v3_diff": v1_path, "v2_v3_diff": v2_path}
        print(
            f"build={name} status={builds[name]['qualification_summary']['content']['status']} "
            f"artifact_set_hash={artifact_set_hash(builds[name])}",
            flush=True,
        )
        if name == "cold" and not should_continue_after_cold(
            builds[name]["qualification_summary"]["content"]
        ):
            print("builds=warm,worker status=not_run_due_fail_closed_cold_block", flush=True)
            break

    all_builds_completed = set(builds) == {"cold", "warm", "worker"}
    if all_builds_completed:
        assert_three_way_determinism(builds, reports, extras)
    cold = builds["cold"]
    summary = cold["qualification_summary"]["content"]
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for manifest_name in MANIFEST_NAMES:
        shutil.copyfile(work_root / "cold" / f"{manifest_name}.json", evidence_dir / f"{manifest_name}.json")
    shutil.copyfile(reports["cold"], report_path)
    shutil.copyfile(extras["cold"]["v1_v3_diff"], v1_diff_report)
    shutil.copyfile(extras["cold"]["v2_v3_diff"], v2_diff_report)

    build_records = {}
    for name in builds:
        build_records[name] = {
            "workers": workers[name],
            "artifact_set_hash": artifact_set_hash(builds[name]),
            "manifest_hashes": {key: builds[name][key]["content_hash"] for key in sorted(builds[name])},
            "manifest_file_sha256": {
                key: file_sha256(work_root / name / f"{key}.json") for key in MANIFEST_NAMES
            },
            "qualification_report_sha256": file_sha256(reports[name]),
            "v1_v3_diff_sha256": file_sha256(extras[name]["v1_v3_diff"]),
            "v2_v3_diff_sha256": file_sha256(extras[name]["v2_v3_diff"]),
        }
    run_content = {
        "status": summary["status"],
        "range": {"start": "2020-01", "end": end_month},
        "builds": build_records,
        "builds_completed": list(builds),
        "determinism_status": "pass" if all_builds_completed else "not_run_due_fail_closed_cold_block",
        "deterministic_mismatches": 0 if all_builds_completed else None,
        "stop_reasons": summary.get("blockers", []) if not all_builds_completed else [],
        "processing_errors": summary["processing_errors"],
        "unresolved_row_conflicts": summary["unresolved_row_conflicts"],
        "unresolved_gaps": summary["unresolved_gaps"],
        "synthetic_fills": summary["synthetic_fills"],
        "replacement_members": summary["replacement_members"],
        "authorizations": {
            "strategy_code": False,
            "event_scan": False,
            "returns": False,
            "backtesting": False,
            "oos_access": False,
            "u03f": False,
            "u04": False,
            "api_or_trading": False,
            "m2": False,
        },
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    run_manifest = {
        "schema_version": 3,
        "manifest_type": "liquid_universe_v3_requalification_run",
        "content": run_content,
    }
    run_manifest["content_hash"] = canonical_hash(run_manifest)
    _write_json(evidence_dir / "requalification_run_manifest.json", run_manifest)
    return run_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe/data/spot")
    parser.add_argument("--work-root", type=Path, default=ROOT / "storage/logs/liquid_universe_v3_requalification")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v3")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_QUALIFICATION_REPORT.md")
    parser.add_argument("--v1-diff-report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V1_V3_DIFF_REPORT.md")
    parser.add_argument("--v2-diff-report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_V3_DIFF_REPORT.md")
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--workers-cold", type=int, default=16)
    parser.add_argument("--workers-warm", type=int, default=3)
    parser.add_argument("--workers-variant", type=int, default=7)
    args = parser.parse_args()
    document = execute(
        raw_root=args.raw_root,
        work_root=args.work_root,
        evidence_dir=args.evidence_dir,
        report_path=args.report,
        v1_diff_report=args.v1_diff_report,
        v2_diff_report=args.v2_diff_report,
        end_month=args.end_month,
        workers_cold=args.workers_cold,
        workers_warm=args.workers_warm,
        workers_variant=args.workers_variant,
    )
    print(f"status={document['content']['status']} content_hash={document['content_hash']}")
    return 0 if document["content"]["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
