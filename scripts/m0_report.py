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
    explained: list[str] = field(default_factory=list)
    unexplained: list[str] = field(default_factory=list)


@dataclass
class M0RunReport:
    data_start: str
    data_end: str
    datasets: list[DatasetRun] = field(default_factory=list)
    scheduler_dry_run: list[str] = field(default_factory=list)
    private_smoke: list[str] = field(default_factory=list)
    public_full_history_complete: bool = False
    scheduler_dry_run_complete: bool = False
    private_smoke_complete: bool = False
    required_checks_complete: bool = False

    @property
    def unexplained(self) -> list[str]:
        items: list[str] = []
        for dataset in self.datasets:
            items.extend(f"{dataset.name}: {item}" for item in dataset.unexplained)
        return items

    @property
    def explained(self) -> list[str]:
        items: list[str] = []
        for dataset in self.datasets:
            items.extend(f"{dataset.name}: {item}" for item in dataset.explained)
        return items


def _string_to_value(value: str) -> int | str:
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        return value


def _safe_int(value: str) -> int:
    try:
        return int(value.strip())
    except ValueError:
        return 0


def parse_report(path: str | Path) -> M0RunReport:
    """Parse the stable Markdown report sections emitted by this module."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    data_start = "not_run"
    data_end = "not_run"
    datasets: list[DatasetRun] = []
    scheduler_dry_run: list[str] = []
    private_smoke: list[str] = []
    explained: dict[str, list[str]] = {}
    unexplained: dict[str, list[str]] = {}
    section = ""

    for line in lines:
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if line.startswith("- Start:"):
            data_start = line.split("`", 2)[1] if "`" in line else line.split(":", 1)[1].strip()
            continue
        if line.startswith("- End:"):
            data_end = line.split("`", 2)[1] if "`" in line else line.split(":", 1)[1].strip()
            continue
        if section in {"Pull Summary", "Public Full-history Pull Summary"} and line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) < 9:
                continue
            datasets.append(
                DatasetRun(
                    name=cells[0].strip("`"),
                    interval=cells[1].strip("`"),
                    rows=_safe_int(cells[2]),
                    gaps=_safe_int(cells[3]),
                    zip_rest_differences=_string_to_value(cells[4]),
                    kline_anomalies=_safe_int(cells[5]),
                    funding_interval_warnings=_string_to_value(cells[6]),
                    archive_status=cells[7],
                    commission_status=cells[8],
                )
            )
            continue
        if section == "Scheduler Dry-run" and line.startswith("- ") and line != "- not_run":
            scheduler_dry_run.append(line[2:])
            continue
        if section == "Private Smoke" and line.startswith("- ") and line != "- not_run":
            private_smoke.append(line[2:])
            continue
        if section == "Explained Anomalies" and line.startswith("- ") and line != "- none":
            item = line[2:]
            if ": " in item:
                dataset_name, detail = item.split(": ", 1)
                explained.setdefault(dataset_name, []).append(detail)
            continue
        if section == "Unexplained Anomalies" and line.startswith("- ") and line != "- none":
            item = line[2:]
            if ": " in item:
                dataset_name, detail = item.split(": ", 1)
                unexplained.setdefault(dataset_name, []).append(detail)

    for dataset in datasets:
        dataset.explained = explained.get(dataset.name, [])
        dataset.unexplained = unexplained.get(dataset.name, [])

    return M0RunReport(
        data_start=data_start,
        data_end=data_end,
        datasets=datasets,
        scheduler_dry_run=scheduler_dry_run,
        private_smoke=private_smoke,
        public_full_history_complete=_public_full_history_complete(datasets),
        scheduler_dry_run_complete=bool(scheduler_dry_run),
        private_smoke_complete=any("status=pass" in item or "pass" == item for item in private_smoke),
        required_checks_complete=_required_checks_complete(datasets),
    )


def _public_full_history_complete(datasets: list[DatasetRun]) -> bool:
    required_names = {
        f"{name}:{symbol}"
        for symbol in ("BTCUSDT", "ETHUSDT")
        for name in (
            "spot_klines",
            "um_futures_klines",
            "mark_price_klines",
            "index_price_klines",
            "premium_index_klines",
            "funding_rate_history",
            "open_interest",
        )
    }
    required_names.update({f"funding_interval_{symbol}" for symbol in ("BTCUSDT", "ETHUSDT")})
    by_name = {dataset.name: dataset for dataset in datasets}
    return all(
        name in by_name
        and by_name[name].rows > 0
        and by_name[name].archive_status not in {"failed", "empty_response"}
        for name in required_names
    )


def _required_checks_complete(datasets: list[DatasetRun]) -> bool:
    if not datasets:
        return False
    incomplete_values = {"not_run"}
    for dataset in datasets:
        if dataset.rows <= 0:
            return False
        if str(dataset.zip_rest_differences) in incomplete_values:
            return False
        if str(dataset.funding_interval_warnings) in incomplete_values:
            return False
        if dataset.archive_status in {"not_run", "failed", "empty_response"}:
            return False
        if dataset.commission_status == "not_run":
            return False
    return True


def render_report(report: M0RunReport) -> str:
    generated = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    public_complete = report.public_full_history_complete or _public_full_history_complete(report.datasets)
    scheduler_complete = report.scheduler_dry_run_complete or bool(report.scheduler_dry_run)
    private_complete = report.private_smoke_complete or any(
        "status=pass" in item or item == "pass" for item in report.private_smoke
    )
    required_checks_complete = report.required_checks_complete or _required_checks_complete(report.datasets)
    zero_unexplained = not report.unexplained
    m1_gate_status = (
        "pass"
        if (
            public_complete
            and scheduler_complete
            and private_complete
            and required_checks_complete
            and zero_unexplained
        )
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
        "## Public Full-history Pull Summary",
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

    lines.extend(["", "## Explained Anomalies", ""])
    if report.explained:
        lines.extend(f"- {item}" for item in report.explained)
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
            f"- Public full-history: `{'pass' if public_complete else 'blocked'}`",
            f"- Scheduler dry-run: `{'pass' if scheduler_complete else 'blocked'}`",
            f"- Private read-only smoke: `{'pass' if private_complete else 'blocked'}`",
            f"- Required checks: `{'pass' if required_checks_complete else 'blocked'}`",
            f"- Zero unexplained anomalies: `{'pass' if zero_unexplained else 'blocked'}`",
            "- Rule: M1 may proceed only when public full-history, scheduler dry-run, private read-only smoke, all required checks, and zero unexplained anomalies are all pass.",
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
