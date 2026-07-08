"""Helpers for writing M0 run reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class DatasetRun:
    name: str
    interval: str
    rows: int = 0
    start_ms: int | None = None
    end_ms: int | None = None
    gaps: int = 0
    zip_rest_differences: int | str = "not_run"
    kline_anomalies: int = 0
    funding_interval_warnings: int | str = "not_run"
    archive_status: str = "not_run"
    commission_status: str = "not_run"
    unexplained: list[str] = field(default_factory=list)


@dataclass
class M0RunReport:
    data_start: str
    data_end: str
    datasets: list[DatasetRun] = field(default_factory=list)
    scheduler_dry_run: list[str] = field(default_factory=list)
    private_smoke: list[str] = field(default_factory=list)

    @property
    def unexplained(self) -> list[str]:
        items: list[str] = []
        for dataset in self.datasets:
            items.extend(f"{dataset.name}: {item}" for item in dataset.unexplained)
        return items


def render_report(report: M0RunReport) -> str:
    generated = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    has_actual_rows = any(dataset.rows > 0 for dataset in report.datasets)
    has_pending_status = any(
        "not_run"
        in {
            str(dataset.zip_rest_differences),
            str(dataset.funding_interval_warnings),
            dataset.archive_status,
            dataset.commission_status,
        }
        for dataset in report.datasets
    )
    private_pending = not report.private_smoke
    m1_gate_status = (
        "pass"
        if has_actual_rows and not has_pending_status and not report.unexplained and not private_pending
        else "blocked"
    )
    lines = [
        "# M0 Data Run Report",
        "",
        f"Generated UTC: {generated}",
        "",
        "## Data Range",
        "",
        f"- Start: `{report.data_start}`",
        f"- End: `{report.data_end}`",
        "",
        "## Pull Summary",
        "",
        "| Dataset | Interval | Rows | Gaps | ZIP/REST Diff | K-line Anomalies | Funding Interval Anomalies | Archive Status | Commission Status |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for dataset in report.datasets:
        lines.append(
            f"| `{dataset.name}` | `{dataset.interval}` | {dataset.rows} | {dataset.gaps} | "
            f"{dataset.zip_rest_differences} | {dataset.kline_anomalies} | "
            f"{dataset.funding_interval_warnings} | {dataset.archive_status} | {dataset.commission_status} |"
        )

    lines.extend(["", "## Scheduler Dry-run", ""])
    if report.scheduler_dry_run:
        lines.extend(f"- {item}" for item in report.scheduler_dry_run)
    else:
        lines.append("- not_run")

    lines.extend(["", "## Private Smoke", ""])
    if report.private_smoke:
        lines.extend(f"- {item}" for item in report.private_smoke)
    else:
        lines.append("- not_run")

    archive_notes = [
        f"`{dataset.name}`: Binance `openInterestHist` only retains a short recent window, so long-range stages archive the latest available OI and mark it `pass_retention_limited`."
        for dataset in report.datasets
        if dataset.archive_status == "pass_retention_limited"
    ]
    lines.extend(["", "## Archive Notes", ""])
    if archive_notes:
        lines.extend(f"- {item}" for item in archive_notes)
    else:
        lines.append("- none")

    lines.extend(["", "## Unexplained Anomalies", ""])
    if report.unexplained:
        lines.extend(f"- {item}" for item in report.unexplained)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## M1 Gate",
            "",
            f"- Status: `{m1_gate_status}`",
            "- Rule: M1 may proceed only when this report has actual M0 data runs, private smoke completed, all required checks complete, and zero unexplained anomalies.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: M0RunReport, path: str | Path = "reports/m0/M0_DATA_RUN_REPORT.md") -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(report), encoding="utf-8")
    return output


def write_baseline_report(path: str | Path = "reports/m0/M0_DATA_RUN_REPORT.md") -> Path:
    return write_report(
        M0RunReport(
            data_start="not_run",
            data_end="not_run",
            datasets=[],
            scheduler_dry_run=[],
            private_smoke=[],
        ),
        path,
    )
