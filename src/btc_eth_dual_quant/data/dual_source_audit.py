"""Strict public ZIP/REST evidence for the M0 audit sidecar.

This module is deliberately pure: callers provide already decoded public rows
and payload hashes. Network access and ignored raw-response persistence belong
to the CLI orchestration layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
import re


CLASSIFICATIONS = (
    "exact_match",
    "format_only",
    "boundary_row",
    "source_revision",
    "timestamp_mismatch",
    "invalid_ohlcv",
    "network_blocked",
    "zip_unavailable",
)
BLOCKING_CLASSIFICATIONS = {
    "source_revision",
    "timestamp_mismatch",
    "invalid_ohlcv",
    "network_blocked",
    "zip_unavailable",
}
REQUIRED_DATASETS = (
    "spot_klines",
    "um_futures_klines",
    "mark_price_klines",
    "index_price_klines",
    "premium_index_klines",
)
PRICE_FIELDS = ("open", "high", "low", "close")
TRADING_FIELDS = (
    *PRICE_FIELDS,
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)
REFERENCE_FIELDS = (*PRICE_FIELDS, "close_time")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
LABEL_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


@dataclass(frozen=True)
class ScopePlan:
    dataset: str
    symbol: str
    interval: str
    month: str
    reasons: tuple[str, ...]

    @property
    def key(self) -> str:
        return f"{self.dataset}:{self.symbol}:{self.interval}:{self.month}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "symbol": self.symbol,
            "interval": self.interval,
            "month": self.month,
            "reasons": list(self.reasons),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ScopePlan":
        return cls(
            dataset=str(value["dataset"]),
            symbol=str(value["symbol"]),
            interval=str(value["interval"]),
            month=str(value["month"]),
            reasons=tuple(str(item) for item in value.get("reasons", [])),
        )


@dataclass(frozen=True)
class AuditDifference:
    classification: str
    open_time: int | None
    field: str
    zip_value: str
    rest_value: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "open_time": self.open_time,
            "field": self.field,
            "zip_value": self.zip_value,
            "rest_value": self.rest_value,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuditDifference":
        open_time = value.get("open_time")
        return cls(
            classification=str(value["classification"]),
            open_time=int(open_time) if open_time is not None else None,
            field=str(value.get("field", "")),
            zip_value=str(value.get("zip_value", "")),
            rest_value=str(value.get("rest_value", "")),
            note=str(value.get("note", "")),
        )


@dataclass(frozen=True)
class ScopeEvidence:
    plan: ScopePlan
    zip_rows: int
    rest_rows: int
    overlap_rows: int
    zip_only_rows: int
    rest_only_rows: int
    zip_payload_sha256: str
    rest_payload_sha256: str
    classification_counts: dict[str, int]
    differences: tuple[AuditDifference, ...]
    passed: bool
    rest_http_status: int | None = 200
    zip_http_status: int | None = 200
    error_category: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "zip_rows": self.zip_rows,
            "rest_rows": self.rest_rows,
            "overlap_rows": self.overlap_rows,
            "zip_only_rows": self.zip_only_rows,
            "rest_only_rows": self.rest_only_rows,
            "zip_payload_sha256": self.zip_payload_sha256,
            "rest_payload_sha256": self.rest_payload_sha256,
            "classification_counts": dict(self.classification_counts),
            "differences": [item.to_dict() for item in self.differences],
            "passed": self.passed,
            "rest_http_status": self.rest_http_status,
            "zip_http_status": self.zip_http_status,
            "error_category": self.error_category,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ScopeEvidence":
        rest_status = value.get("rest_http_status")
        zip_status = value.get("zip_http_status")
        counts = _empty_counts()
        counts.update({str(key): int(count) for key, count in dict(value.get("classification_counts", {})).items()})
        return cls(
            plan=ScopePlan.from_dict(value["plan"]),
            zip_rows=int(value.get("zip_rows", 0)),
            rest_rows=int(value.get("rest_rows", 0)),
            overlap_rows=int(value.get("overlap_rows", 0)),
            zip_only_rows=int(value.get("zip_only_rows", 0)),
            rest_only_rows=int(value.get("rest_only_rows", 0)),
            zip_payload_sha256=str(value.get("zip_payload_sha256", "")),
            rest_payload_sha256=str(value.get("rest_payload_sha256", "")),
            classification_counts=counts,
            differences=tuple(AuditDifference.from_dict(item) for item in value.get("differences", [])),
            passed=bool(value.get("passed", False)),
            rest_http_status=int(rest_status) if rest_status is not None else None,
            zip_http_status=int(zip_status) if zip_status is not None else None,
            error_category=str(value.get("error_category", "none")),
        )


@dataclass(frozen=True)
class AuditRunEvidence:
    execution_label: str
    generated_utc: str
    plans: tuple[ScopePlan, ...]
    scopes: tuple[ScopeEvidence, ...]

    def __post_init__(self) -> None:
        if not LABEL_RE.fullmatch(self.execution_label):
            raise ValueError("execution_label must be a sanitized logical label")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "execution_label": self.execution_label,
            "generated_utc": self.generated_utc,
            "plans": [item.to_dict() for item in self.plans],
            "scopes": [item.to_dict() for item in self.scopes],
            "api_key_used": False,
            "private_data_used": False,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AuditRunEvidence":
        if int(value.get("schema_version", 0)) != 1:
            raise ValueError("unsupported dual-source audit evidence schema")
        if value.get("api_key_used") is not False or value.get("private_data_used") is not False:
            raise ValueError("dual-source evidence must be public-only")
        return cls(
            execution_label=str(value["execution_label"]),
            generated_utc=str(value["generated_utc"]),
            plans=tuple(ScopePlan.from_dict(item) for item in value.get("plans", [])),
            scopes=tuple(ScopeEvidence.from_dict(item) for item in value.get("scopes", [])),
        )


@dataclass(frozen=True)
class AuditGate:
    passed: bool
    blockers: tuple[str, ...]


def _empty_counts() -> dict[str, int]:
    return {name: 0 for name in CLASSIFICATIONS}


def _fields(dataset: str) -> tuple[str, ...]:
    if dataset in {"spot_klines", "um_futures_klines"}:
        return TRADING_FIELDS
    if dataset in {"mark_price_klines", "index_price_klines", "premium_index_klines"}:
        return REFERENCE_FIELDS
    raise ValueError(f"unsupported dual-source dataset: {dataset}")


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite numeric value")
    return result


def _valid_hash(value: str) -> bool:
    return bool(HASH_RE.fullmatch(value))


def _index_rows(rows: Iterable[Mapping[str, Any]]) -> tuple[dict[int, Mapping[str, Any]], set[int]]:
    indexed: dict[int, Mapping[str, Any]] = {}
    duplicates: set[int] = set()
    for row in rows:
        timestamp = int(row["open_time"])
        if timestamp in indexed:
            duplicates.add(timestamp)
        indexed[timestamp] = row
    return indexed, duplicates


def _semantic_errors(row: Mapping[str, Any], dataset: str) -> list[str]:
    try:
        open_price = _decimal(row["open"])
        high = _decimal(row["high"])
        low = _decimal(row["low"])
        close = _decimal(row["close"])
        if high < max(open_price, low, close) or low > min(open_price, high, close):
            return ["illegal OHLC ordering"]
        if dataset in {"spot_klines", "um_futures_klines"} and _decimal(row["volume"]) < 0:
            return ["negative volume"]
        for field in _fields(dataset):
            _decimal(row[field])
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        return [f"invalid numeric field: {type(exc).__name__}"]
    return []


def _rows_semantically_equal(left: Mapping[str, Any], right: Mapping[str, Any], dataset: str) -> bool:
    try:
        return all(_decimal(left[field]) == _decimal(right[field]) for field in _fields(dataset))
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def source_failure(
    plan: ScopePlan,
    classification: str,
    error_category: str,
    *,
    rest_http_status: int | None = None,
    zip_http_status: int | None = None,
    zip_payload_sha256: str = "",
    rest_payload_sha256: str = "",
    zip_rows: int = 0,
    rest_rows: int = 0,
) -> ScopeEvidence:
    if classification not in {"network_blocked", "zip_unavailable"}:
        raise ValueError(f"unsupported source failure classification: {classification}")
    counts = _empty_counts()
    counts[classification] = 1
    difference = AuditDifference(classification, None, "source", "", "", error_category)
    return ScopeEvidence(
        plan=plan,
        zip_rows=zip_rows,
        rest_rows=rest_rows,
        overlap_rows=0,
        zip_only_rows=0,
        rest_only_rows=0,
        zip_payload_sha256=zip_payload_sha256,
        rest_payload_sha256=rest_payload_sha256,
        classification_counts=counts,
        differences=(difference,),
        passed=False,
        rest_http_status=rest_http_status,
        zip_http_status=zip_http_status,
        error_category=error_category,
    )


def compare_scope(
    *,
    plan: ScopePlan,
    zip_rows: Iterable[Mapping[str, Any]],
    rest_rows: Iterable[Mapping[str, Any]],
    zip_payload_sha256: str,
    rest_payload_sha256: str,
    adjacent_zip_rows: Iterable[Mapping[str, Any]] = (),
    adjacent_rest_rows: Iterable[Mapping[str, Any]] = (),
    rest_http_status: int | None = 200,
    zip_http_status: int | None = 200,
) -> ScopeEvidence:
    """Compare one selected month without numeric tolerances."""

    zip_list = list(zip_rows)
    rest_list = list(rest_rows)
    zip_by_time, zip_duplicates = _index_rows(zip_list)
    rest_by_time, rest_duplicates = _index_rows(rest_list)
    adjacent_zip, _ = _index_rows(adjacent_zip_rows)
    adjacent_rest, _ = _index_rows(adjacent_rest_rows)
    counts = _empty_counts()
    differences: list[AuditDifference] = []

    for source, duplicates in (("ZIP", zip_duplicates), ("REST", rest_duplicates)):
        for timestamp in sorted(duplicates):
            counts["timestamp_mismatch"] += 1
            differences.append(
                AuditDifference(
                    "timestamp_mismatch",
                    timestamp,
                    "open_time",
                    str(timestamp) if source == "ZIP" else "",
                    str(timestamp) if source == "REST" else "",
                    f"duplicate timestamp in {source}",
                )
            )

    for source, indexed in (("ZIP", zip_by_time), ("REST", rest_by_time)):
        for timestamp, item in sorted(indexed.items()):
            for note in _semantic_errors(item, plan.dataset):
                counts["invalid_ohlcv"] += 1
                differences.append(
                    AuditDifference(
                        "invalid_ohlcv",
                        timestamp,
                        "ohlcv",
                        source if source == "ZIP" else "",
                        source if source == "REST" else "",
                        note,
                    )
                )

    overlap_times = sorted(set(zip_by_time) & set(rest_by_time))
    for timestamp in overlap_times:
        left = zip_by_time[timestamp]
        right = rest_by_time[timestamp]
        row_difference = False
        for field in _fields(plan.dataset):
            try:
                left_value = _decimal(left[field])
                right_value = _decimal(right[field])
            except (KeyError, TypeError, ValueError, InvalidOperation):
                continue
            left_raw = str(left[field])
            right_raw = str(right[field])
            if left_value != right_value:
                row_difference = True
                counts["source_revision"] += 1
                differences.append(
                    AuditDifference(
                        "source_revision",
                        timestamp,
                        field,
                        left_raw,
                        right_raw,
                        "official sources contain different canonical values",
                    )
                )
            elif left_raw != right_raw:
                row_difference = True
                counts["format_only"] += 1
                differences.append(
                    AuditDifference(
                        "format_only",
                        timestamp,
                        field,
                        left_raw,
                        right_raw,
                        "raw strings differ but Decimal values are equal",
                    )
                )
        if not row_difference:
            counts["exact_match"] += 1

    zip_only = sorted(set(zip_by_time) - set(rest_by_time))
    rest_only = sorted(set(rest_by_time) - set(zip_by_time))
    for timestamp in rest_only:
        recovered = adjacent_zip.get(timestamp)
        if recovered is not None and _rows_semantically_equal(recovered, rest_by_time[timestamp], plan.dataset):
            classification = "boundary_row"
            note = "REST-only timestamp is present and equal in an adjacent official ZIP scope"
        else:
            classification = "timestamp_mismatch"
            note = "REST-only timestamp is absent from the selected and adjacent official ZIP scopes"
        counts[classification] += 1
        differences.append(AuditDifference(classification, timestamp, "open_time", "", str(timestamp), note))

    for timestamp in zip_only:
        recovered = adjacent_rest.get(timestamp)
        if recovered is not None and _rows_semantically_equal(zip_by_time[timestamp], recovered, plan.dataset):
            classification = "boundary_row"
            note = "ZIP-only timestamp is present and equal in an adjacent official REST scope"
        else:
            classification = "timestamp_mismatch"
            note = "ZIP-only timestamp is absent from the selected and adjacent official REST scopes"
        counts[classification] += 1
        differences.append(AuditDifference(classification, timestamp, "open_time", str(timestamp), "", note))

    hashes_present = _valid_hash(zip_payload_sha256) and _valid_hash(rest_payload_sha256)
    blocking_count = sum(counts[item] for item in BLOCKING_CLASSIFICATIONS)
    passed = bool(overlap_times) and hashes_present and blocking_count == 0
    return ScopeEvidence(
        plan=plan,
        zip_rows=len(zip_list),
        rest_rows=len(rest_list),
        overlap_rows=len(overlap_times),
        zip_only_rows=len(zip_only),
        rest_only_rows=len(rest_only),
        zip_payload_sha256=zip_payload_sha256,
        rest_payload_sha256=rest_payload_sha256,
        classification_counts=counts,
        differences=tuple(differences),
        passed=passed,
        rest_http_status=rest_http_status,
        zip_http_status=zip_http_status,
        error_category="none" if passed else "comparison_blocked",
    )


def _merge_plans(plans: Iterable[ScopePlan]) -> tuple[ScopePlan, ...]:
    merged: dict[str, ScopePlan] = {}
    for plan in plans:
        previous = merged.get(plan.key)
        reasons = set(plan.reasons)
        if previous:
            reasons.update(previous.reasons)
        merged[plan.key] = ScopePlan(plan.dataset, plan.symbol, plan.interval, plan.month, tuple(sorted(reasons)))
    return tuple(merged[key] for key in sorted(merged))


def evaluate_gate(evidence: Iterable[ScopeEvidence], expected_plans: Iterable[ScopePlan]) -> AuditGate:
    """Require at least one complete official dual-source result per planned scope."""

    expected = _merge_plans(expected_plans)
    by_key: dict[str, list[ScopeEvidence]] = {}
    for item in evidence:
        by_key.setdefault(item.plan.key, []).append(item)
    blockers: list[str] = []
    for plan in expected:
        candidates = by_key.get(plan.key, [])
        if not candidates:
            blockers.append(f"{plan.key}: evidence not_run")
            continue
        if not any(candidate.passed for candidate in candidates):
            categories = sorted(
                {
                    name
                    for candidate in candidates
                    for name, count in candidate.classification_counts.items()
                    if count and name in BLOCKING_CLASSIFICATIONS
                }
            )
            detail = ",".join(categories) or "missing overlap or payload hash"
            blockers.append(f"{plan.key}: {detail}")
    return AuditGate(passed=not blockers and bool(expected), blockers=tuple(blockers))


def _escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_diagnostics_report(runs: Iterable[AuditRunEvidence]) -> str:
    run_list = list(runs)
    plans = _merge_plans(plan for run in run_list for plan in run.plans)
    scopes = [scope for run in run_list for scope in run.scopes]
    gate = evaluate_gate(scopes, plans)
    generated = max((run.generated_utc for run in run_list), default="not_run")
    lines = [
        "# M0 Dual-Source Audit Diagnostics",
        "",
        f"- Status: {'pass' if gate.passed else 'blocked'}",
        f"- Generated UTC: {generated}",
        "- Scope: official public REST versus official public ZIP evidence only",
        "- API key used: no",
        "- Private data used: no",
        "- Private smoke rerun: no",
        "- VPN/proxy/region bypass used: no",
        "- Raw payload committed: no",
        "- Trading approval: no",
        "",
        "## Execution Nodes",
        "",
        "| Logical node | Generated UTC | Planned scopes | Completed scopes | Passed scopes |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for run in run_list:
        lines.append(
            f"| `{run.execution_label}` | `{run.generated_utc}` | {len(run.plans)} | "
            f"{len(run.scopes)} | {sum(1 for item in run.scopes if item.passed)} |"
        )

    lines.extend(
        [
            "",
            "## Scope Evidence",
            "",
            "| Node | Dataset | Symbol | Month | Reasons | REST | ZIP | REST rows | ZIP rows | Overlap | REST-only | ZIP-only | Exact | Format | Boundary | Revision | Timestamp | Invalid | Status | REST SHA256 | ZIP SHA256 |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for run in run_list:
        for item in run.scopes:
            counts = item.classification_counts
            lines.append(
                f"| `{run.execution_label}` | `{item.plan.dataset}` | `{item.plan.symbol}` | `{item.plan.month}` | "
                f"`{','.join(item.plan.reasons)}` | {item.rest_http_status or 'n/a'} | {item.zip_http_status or 'n/a'} | "
                f"{item.rest_rows} | {item.zip_rows} | {item.overlap_rows} | {item.rest_only_rows} | "
                f"{item.zip_only_rows} | {counts['exact_match']} | {counts['format_only']} | "
                f"{counts['boundary_row']} | {counts['source_revision']} | {counts['timestamp_mismatch']} | "
                f"{counts['invalid_ohlcv']} | {'pass' if item.passed else 'blocked'} | "
                f"`{item.rest_payload_sha256 or 'not_available'}` | `{item.zip_payload_sha256 or 'not_available'}` |"
            )

    visible_differences = [
        (run.execution_label, scope.plan, difference)
        for run in run_list
        for scope in run.scopes
        for difference in scope.differences
    ]
    lines.extend(
        [
            "",
            "## Classified Differences",
            "",
            "| Node | Dataset | Symbol | Month | Classification | Open time ms | Field | ZIP value | REST value | Note |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    if visible_differences:
        for label, plan, item in visible_differences:
            lines.append(
                f"| `{label}` | `{plan.dataset}` | `{plan.symbol}` | `{plan.month}` | "
                f"`{item.classification}` | {item.open_time if item.open_time is not None else 'n/a'} | "
                f"`{_escape(item.field)}` | `{_escape(item.zip_value)}` | `{_escape(item.rest_value)}` | "
                f"{_escape(item.note)} |"
            )
    else:
        lines.append("| none | none | none | none | `exact_match` | n/a | none | none | none | No differences. |")

    lines.extend(["", "## Strict Gate", "", f"- Status: {'pass' if gate.passed else 'blocked'}"])
    if gate.blockers:
        lines.append("- Blockers:")
        lines.extend(f"  - {item}" for item in gate.blockers)
    else:
        lines.append("- Blockers: none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- M0 audit status: {'pass' if gate.passed else 'audit_revalidation_required'}",
            "- M1A status remains failed_validation.",
            "- M1B status remains failed_validation.",
            "- M2 remains prohibited.",
            "- This report does not approve paper trading, live trading, execution, orders, or API trading permissions.",
            "",
        ]
    )
    return "\n".join(lines)


def render_revalidation_report(runs: Iterable[AuditRunEvidence]) -> str:
    """Render the compact, decision-facing M0 audit report from real evidence."""

    run_list = list(runs)
    plans = _merge_plans(plan for run in run_list for plan in run.plans)
    scopes = [scope for run in run_list for scope in run.scopes]
    gate = evaluate_gate(scopes, plans)
    generated = max((run.generated_utc for run in run_list), default="not_run")
    rows = [
        "# M0 Audit Revalidation Report",
        "",
        f"- Status: {'pass' if gate.passed else 'blocked'}",
        f"- Generated UTC: {generated}",
        "- Scope: BTCUSDT/ETHUSDT 1h official public REST versus official public ZIP",
        "- Evidence method: multi-network, exact Decimal and timestamp-set comparison",
        "- API key used: no",
        "- Private smoke rerun: no",
        "- Raw data committed: no",
        "- Trading approval: no",
        "",
        "## Evidence Summary",
        "",
        "| Dataset | Symbol | Planned scopes | Scopes with valid evidence | Revisions | Timestamp mismatches | Invalid OHLCV | Network blocked | ZIP unavailable | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    dataset_keys = sorted({(plan.dataset, plan.symbol) for plan in plans})
    for dataset, symbol in dataset_keys:
        dataset_plans = [plan for plan in plans if plan.dataset == dataset and plan.symbol == symbol]
        candidate_scopes = [scope for scope in scopes if scope.plan.dataset == dataset and scope.plan.symbol == symbol]
        passed_keys = {scope.plan.key for scope in candidate_scopes if scope.passed}
        counts = _empty_counts()
        for scope in candidate_scopes:
            for name, count in scope.classification_counts.items():
                counts[name] += count
        status = "pass" if all(plan.key in passed_keys for plan in dataset_plans) else "blocked"
        rows.append(
            f"| `{dataset}` | `{symbol}` | {len(dataset_plans)} | {len(passed_keys)} | "
            f"{counts['source_revision']} | {counts['timestamp_mismatch']} | {counts['invalid_ohlcv']} | "
            f"{counts['network_blocked']} | {counts['zip_unavailable']} | {status} |"
        )

    blocking_differences = [
        (scope.plan, difference)
        for scope in scopes
        for difference in scope.differences
        if difference.classification in BLOCKING_CLASSIFICATIONS
    ]
    rows.extend(
        [
            "",
            "## Blocking Evidence",
            "",
            "| Dataset | Symbol | Month | Classification | Open time ms | Field | ZIP value | REST value | Note |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    if blocking_differences:
        for plan, item in blocking_differences:
            rows.append(
                f"| `{plan.dataset}` | `{plan.symbol}` | `{plan.month}` | `{item.classification}` | "
                f"{item.open_time if item.open_time is not None else 'n/a'} | `{_escape(item.field)}` | "
                f"`{_escape(item.zip_value)}` | `{_escape(item.rest_value)}` | {_escape(item.note)} |"
            )
    else:
        rows.append("| none | none | none | none | n/a | none | none | none | No blocking evidence. |")

    rows.extend(["", "## Required Gate", "", f"- Status: {'pass' if gate.passed else 'blocked'}"])
    if gate.blockers:
        rows.append("- Blockers:")
        rows.extend(f"  - {item}" for item in gate.blockers)
    else:
        rows.append("- Blockers: none")
    rows.extend(
        [
            "",
            "## Decision",
            "",
            f"- M0 audit status: {'pass' if gate.passed else 'audit_revalidation_required'}",
            "- Detailed field evidence: `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md`",
            "- M1A and M1B remain failed_validation.",
            "- M2 remains prohibited.",
            "- No live trading, real-API paper trading, execution, order, or API permission is approved.",
            "",
        ]
    )
    return "\n".join(rows)
