#!/usr/bin/env python3
"""Merge M0 public, scheduler, and private status reports.

The merged report is the only canonical M0 data-run gate artifact. Private
smoke details stay in the local ignored report; this script only carries a
coarse pass/fail/not_run status into the final report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m0_report import M0RunReport, parse_report, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge M0 data-run reports")
    parser.add_argument("--public", dest="public_reports", action="append", default=None)
    parser.add_argument("--public-report", dest="public_reports", action="append", default=None)
    parser.add_argument("--scheduler", dest="scheduler_report", default=None)
    parser.add_argument("--scheduler-report", dest="scheduler_report", default=None)
    parser.add_argument("--anomaly-review", default="reports/m0/M0_ANOMALY_REVIEW.md")
    parser.add_argument("--private-status-file", default="reports/m0/M0_PRIVATE_SMOKE_STATUS.md")
    parser.add_argument("--private-report", default="reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md")
    parser.add_argument(
        "--private-status",
        choices=("pass", "fail", "not_run"),
        default=None,
        help="Optional explicit private smoke status. Overrides --private-report.",
    )
    parser.add_argument("--out", dest="output", default=None)
    parser.add_argument("--output", dest="output", default=None)
    return parser.parse_args()


def _load_report_or_empty(path: str | Path) -> M0RunReport:
    source = Path(path)
    if not source.exists():
        return M0RunReport(data_start="not_run", data_end="not_run")
    return parse_report(source)


def _private_status(args: argparse.Namespace) -> str:
    if args.private_status is not None:
        return args.private_status
    status_file = Path(args.private_status_file)
    if status_file.exists():
        for line in status_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("run_status:"):
                value = line.split(":", 1)[1].strip()
                if value in {"not_run", "pass", "fail"}:
                    return value
                return "fail"
    source = Path(args.private_report)
    if not source.exists():
        return "not_run"
    private_report = parse_report(source)
    if private_report.private_smoke and not private_report.unexplained:
        return "pass"
    return "fail"


def _public_report_paths(args: argparse.Namespace) -> list[str]:
    return args.public_reports or ["reports/m0/M0_PUBLIC_RUN_REPORT.md"]


def _scheduler_report_path(args: argparse.Namespace) -> str:
    return args.scheduler_report or "reports/m0/M0_SCHEDULER_DRY_RUN_REPORT.md"


def _output_path(args: argparse.Namespace) -> str:
    return args.output or "reports/m0/M0_DATA_RUN_REPORT.md"


def _better_dataset(left, right):
    left_span = (left.end_ms or 0) - (left.start_ms or 0)
    right_span = (right.end_ms or 0) - (right.start_ms or 0)
    if right.rows > left.rows:
        return right
    if right.rows == left.rows and right_span > left_span:
        return right
    return left


def _combine_public_reports(paths: list[str]) -> M0RunReport:
    reports = [_load_report_or_empty(path) for path in paths]
    by_name = {}
    order: list[str] = []
    for report in reports:
        for dataset in report.datasets:
            if dataset.name not in by_name:
                by_name[dataset.name] = dataset
                order.append(dataset.name)
            else:
                by_name[dataset.name] = _better_dataset(by_name[dataset.name], dataset)
    data_starts = [report.data_start for report in reports if report.data_start not in {"not_run", "not_available"}]
    data_ends = [report.data_end for report in reports if report.data_end not in {"not_run", "not_available"}]
    return M0RunReport(
        data_start=min(data_starts) if data_starts else "not_run",
        data_end=max(data_ends) if data_ends else "not_run",
        datasets=[by_name[name] for name in order],
    )


def _parse_anomaly_review(path: str | Path) -> dict[str, dict[str, int]]:
    source = Path(path)
    if not source.exists():
        return {}
    counts: dict[str, dict[str, int]] = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 14:
            continue
        dataset = cells[0].strip("`")
        symbol = cells[1].strip("`")
        classification = cells[13].strip("`")
        full_name = f"{dataset}:{symbol}"
        counts.setdefault(full_name, {})
        counts[full_name][classification] = counts[full_name].get(classification, 0) + 1
    return counts


def _apply_anomaly_review(public_report: M0RunReport, review_path: str | Path) -> None:
    counts = _parse_anomaly_review(review_path)
    if not counts:
        return
    for dataset in public_report.datasets:
        reviewed = counts.get(dataset.name)
        if not reviewed:
            continue
        dataset.explained = []
        dataset.unexplained = []
        explained_market_move = reviewed.get("explained_market_move", 0)
        bad_data = reviewed.get("bad_data", 0)
        unresolved = reviewed.get("unresolved", 0)
        if explained_market_move:
            dataset.explained.append(
                f"anomaly review classified explained_market_move={explained_market_move}; see `{review_path}`"
            )
        if bad_data:
            dataset.explained.append(f"anomaly review classified bad_data={bad_data}; see `{review_path}`")
        if unresolved:
            dataset.unexplained.append(f"anomaly review classified unresolved={unresolved}; see `{review_path}`")


def main() -> int:
    args = parse_args()
    public_report = _combine_public_reports(_public_report_paths(args))
    scheduler_report = _load_report_or_empty(_scheduler_report_path(args))
    _apply_anomaly_review(public_report, args.anomaly_review)
    private_status = _private_status(args)
    private_smoke_complete = private_status == "pass"

    merged = M0RunReport(
        data_start=public_report.data_start,
        data_end=public_report.data_end,
        datasets=public_report.datasets,
        scheduler_dry_run=scheduler_report.scheduler_dry_run,
        private_smoke=[f"status={private_status}"],
        public_full_history_complete=public_report.public_full_history_complete,
        scheduler_dry_run_complete=scheduler_report.scheduler_dry_run_complete,
        private_smoke_complete=private_smoke_complete,
        required_checks_complete=public_report.required_checks_complete,
    )
    output = _output_path(args)
    write_report(merged, output)
    print(f"Wrote merged M0 report: {output}")
    print(f"private_smoke_status={private_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
