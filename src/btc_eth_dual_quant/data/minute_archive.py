"""Canonical public 1m archive evidence for short-horizon research.

The module is pure and public-data only. Network retrieval and ignored raw
storage belong to the T1 orchestration script.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence


MINUTE_MS = 60_000
COMPLETENESS_THRESHOLD = Decimal("0.999")
SPREAD_PROXY_THRESHOLD = Decimal("0.001")
STRESS_MONTHS = ("2020-03", "2021-05", "2022-05", "2022-11")
KLINE_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
)


@dataclass(frozen=True)
class RestSampleEvidence:
    month: str
    reason: str
    start_ms: int
    overlap_rows: int
    field_differences: int
    archive_overlap_sha256: str
    rest_overlap_sha256: str
    passed: bool


@dataclass(frozen=True)
class MinuteMonthEvidence:
    symbol: str
    month: str
    expected_rows: int
    observed_rows: int
    first_open_ms: int | None
    last_open_ms: int | None
    monthly_zip_rows: int
    daily_supplement_rows: int
    daily_fetch_failures: int
    duplicate_rows: int
    invalid_rows: int
    missing_rows: int
    max_contiguous_gap: int
    completeness: str
    p95_spread_proxy: str
    monthly_zip_sha256: str
    daily_bundle_sha256: str
    rest_evidence_complete: bool
    rest_sampled: bool
    rest_sample_passed: bool
    audit_state: str
    qualifies: bool


@dataclass(frozen=True)
class MinuteArchiveManifest:
    generated_utc: str
    requested_start: str
    requested_end: str
    symbols: tuple[str, ...]
    months: tuple[MinuteMonthEvidence, ...]
    rest_samples: tuple[RestSampleEvidence, ...]
    research_start: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "generated_utc": self.generated_utc,
            "requested_start": self.requested_start,
            "requested_end": self.requested_end,
            "symbols": list(self.symbols),
            "months": [asdict(item) for item in self.months],
            "rest_samples": [asdict(item) for item in self.rest_samples],
            "research_start": self.research_start,
            "api_key_used": False,
            "private_data_used": False,
            "raw_data_committed": False,
            "spread_proxy": {
                "name": "corwin_schultz_two_bar",
                "raw_inputs": ["high", "low"],
                "percentile": 95,
                "threshold": str(SPREAD_PROXY_THRESHOLD),
            },
        }

    def canonical_sha256(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def month_bounds_ms(month: str) -> tuple[int, int]:
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def next_month(month: str) -> str:
    _, end_ms = month_bounds_ms(month)
    return datetime.fromtimestamp(end_ms / 1000, timezone.utc).strftime("%Y-%m")


def expected_minute_rows(month: str) -> int:
    start_ms, end_ms = month_bounds_ms(month)
    return (end_ms - start_ms) // MINUTE_MS


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise InvalidOperation("non-finite value")
    return result


def _valid_row(row: Mapping[str, Any]) -> bool:
    try:
        opened = _decimal(row["open"])
        high = _decimal(row["high"])
        low = _decimal(row["low"])
        closed = _decimal(row["close"])
        if min(opened, high, low, closed) <= 0:
            return False
        if high < max(opened, low, closed) or low > min(opened, high, closed):
            return False
        if _decimal(row["volume"]) < 0 or _decimal(row["quote_volume"]) < 0:
            return False
        return int(row["open_time"]) % MINUTE_MS == 0
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return False


def corwin_schultz_spread_proxies(rows: Iterable[Mapping[str, Any]]) -> list[Decimal]:
    """Return two-bar Corwin-Schultz spread estimates from high/low inputs."""
    ordered = sorted(rows, key=lambda item: int(item["open_time"]))
    result: list[Decimal] = []
    denominator = 3 - 2 * math.sqrt(2)
    for previous, current in zip(ordered, ordered[1:]):
        if int(current["open_time"]) - int(previous["open_time"]) != MINUTE_MS:
            continue
        try:
            previous_high = float(_decimal(previous["high"]))
            previous_low = float(_decimal(previous["low"]))
            current_high = float(_decimal(current["high"]))
            current_low = float(_decimal(current["low"]))
            if min(previous_low, current_low) <= 0:
                continue
            beta = math.log(previous_high / previous_low) ** 2 + math.log(current_high / current_low) ** 2
            gamma = math.log(max(previous_high, current_high) / min(previous_low, current_low)) ** 2
            alpha = (
                (math.sqrt(2 * beta) - math.sqrt(beta)) / denominator
                - math.sqrt(max(gamma, 0.0) / denominator)
            )
            exponent = math.exp(min(max(alpha, 0.0), 50.0))
            spread = 2 * (exponent - 1) / (1 + exponent)
            result.append(Decimal(str(spread)))
        except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
            continue
    return result


def percentile(values: Sequence[Decimal], percentile_value: int) -> Decimal:
    if not values:
        return Decimal("Infinity")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile_value / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = Decimal(str(rank - lower))
    return ordered[lower] * (Decimal(1) - weight) + ordered[upper] * weight


def deterministic_rest_sample_months(
    months: Sequence[str], symbol: str, random_count: int = 3
) -> dict[str, tuple[str, ...]]:
    """Select preregistered profile months without looking at strategy returns."""
    available = sorted(set(months))
    if not available:
        return {}
    reasons: dict[str, set[str]] = {month: set() for month in available}
    reasons[available[0]].add("first")
    reasons[available[len(available) // 2]].add("middle")
    reasons[available[-1]].add("latest_complete")
    for month in STRESS_MONTHS:
        if month in reasons:
            reasons[month].add("stress")

    remaining = [month for month in available if not reasons[month]]
    seed = int(hashlib.sha256(f"t1-rest-sample:{symbol}".encode()).hexdigest()[:16], 16)
    generator = random.Random(seed)
    for month in sorted(generator.sample(remaining, min(random_count, len(remaining)))):
        reasons[month].add("deterministic_random")
    return {month: tuple(sorted(reason)) for month, reason in reasons.items() if reason}


def deterministic_rest_start_ms(symbol: str, month: str) -> int:
    start_ms, end_ms = month_bounds_ms(month)
    window = 1_000 * MINUTE_MS
    slots = max(1, (end_ms - start_ms - window) // MINUTE_MS)
    seed = int(hashlib.sha256(f"t1-rest-window:{symbol}:{month}".encode()).hexdigest()[:16], 16)
    return start_ms + (seed % slots) * MINUTE_MS


def compare_rest_sample(
    *,
    month: str,
    reason: str,
    start_ms: int,
    archive_rows: Iterable[Mapping[str, Any]],
    rest_rows: Iterable[Mapping[str, Any]],
) -> RestSampleEvidence:
    archive = {int(row["open_time"]): row for row in archive_rows}
    rest = {int(row["open_time"]): row for row in rest_rows}
    overlap = sorted(set(archive) & set(rest))
    differences = 0
    left: list[dict[str, str]] = []
    right: list[dict[str, str]] = []
    for timestamp in overlap:
        left_row = {field: str(archive[timestamp][field]) for field in KLINE_FIELDS}
        right_row = {field: str(rest[timestamp][field]) for field in KLINE_FIELDS}
        for field in KLINE_FIELDS:
            try:
                equal = _decimal(left_row[field]) == _decimal(right_row[field])
            except (InvalidOperation, ValueError):
                equal = left_row[field] == right_row[field]
            if not equal:
                differences += 1
        left.append({"open_time": str(timestamp), **left_row})
        right.append({"open_time": str(timestamp), **right_row})

    def digest(rows: list[dict[str, str]]) -> str:
        payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest() if rows else ""

    return RestSampleEvidence(
        month=month,
        reason=reason,
        start_ms=start_ms,
        overlap_rows=len(overlap),
        field_differences=differences,
        archive_overlap_sha256=digest(left),
        rest_overlap_sha256=digest(right),
        passed=bool(overlap) and differences == 0,
    )


def analyze_month(
    *,
    symbol: str,
    month: str,
    monthly_rows: Iterable[Mapping[str, Any]],
    supplemental_rows: Iterable[Mapping[str, Any]] = (),
    monthly_zip_sha256: str,
    daily_bundle_sha256: str = "",
    rest_evidence_complete: bool,
    rest_sampled: bool = False,
    rest_sample_passed: bool = True,
    pending_archive: bool = False,
    allow_inception_partial: bool = False,
    daily_fetch_failures: int = 0,
) -> MinuteMonthEvidence:
    start_ms, end_ms = month_bounds_ms(month)
    base = [dict(row) for row in monthly_rows if start_ms <= int(row["open_time"]) < end_ms]
    supplement = [dict(row) for row in supplemental_rows if start_ms <= int(row["open_time"]) < end_ms]
    indexed: dict[int, dict[str, Any]] = {}
    duplicates = 0
    for row in base:
        timestamp = int(row["open_time"])
        if timestamp in indexed:
            duplicates += 1
        indexed[timestamp] = row
    added = 0
    for row in supplement:
        timestamp = int(row["open_time"])
        if timestamp not in indexed:
            indexed[timestamp] = row
            added += 1

    expected_start = min(indexed) if allow_inception_partial and indexed else start_ms
    expected = (end_ms - expected_start) // MINUTE_MS
    expected_times = set(range(expected_start, end_ms, MINUTE_MS))
    covered_times = expected_times & set(indexed)
    missing_times = sorted(expected_times - covered_times)
    max_gap = 0
    current_gap = 0
    previous: int | None = None
    for timestamp in missing_times:
        if previous is not None and timestamp == previous + MINUTE_MS:
            current_gap += 1
        else:
            current_gap = 1
        max_gap = max(max_gap, current_gap)
        previous = timestamp
    invalid = sum(not _valid_row(row) for row in indexed.values())
    observed = len(covered_times)
    completeness = Decimal(observed) / Decimal(expected)
    valid_grid_rows = [indexed[timestamp] for timestamp in covered_times if _valid_row(indexed[timestamp])]
    p95 = percentile(corwin_schultz_spread_proxies(valid_grid_rows), 95)

    if pending_archive:
        audit_state = "pending_archive"
    elif missing_times or invalid or daily_fetch_failures or not rest_evidence_complete:
        audit_state = "blocked"
    elif rest_sampled and not rest_sample_passed:
        audit_state = "audit_complete_with_quarantine"
    else:
        audit_state = "audit_complete"
    qualifies = (
        audit_state == "audit_complete"
        and completeness >= COMPLETENESS_THRESHOLD
        and max_gap == 0
        and p95 <= SPREAD_PROXY_THRESHOLD
    )
    return MinuteMonthEvidence(
        symbol=symbol,
        month=month,
        expected_rows=expected,
        observed_rows=observed,
        first_open_ms=min(covered_times) if covered_times else None,
        last_open_ms=max(covered_times) if covered_times else None,
        monthly_zip_rows=len(base),
        daily_supplement_rows=added,
        daily_fetch_failures=daily_fetch_failures,
        duplicate_rows=duplicates,
        invalid_rows=invalid,
        missing_rows=len(missing_times),
        max_contiguous_gap=max_gap,
        completeness=format(completeness, ".10f"),
        p95_spread_proxy=format(p95, ".10f"),
        monthly_zip_sha256=monthly_zip_sha256,
        daily_bundle_sha256=daily_bundle_sha256,
        rest_evidence_complete=rest_evidence_complete,
        rest_sampled=rest_sampled,
        rest_sample_passed=rest_sample_passed,
        audit_state=audit_state,
        qualifies=qualifies,
    )


def determine_research_start(
    evidence: Iterable[MinuteMonthEvidence], symbols: Sequence[str] = ("BTCUSDT", "ETHUSDT")
) -> str | None:
    by_symbol = {
        symbol: {item.month: item for item in evidence if item.symbol == symbol}
        for symbol in symbols
    }
    common = sorted(set.intersection(*(set(values) for values in by_symbol.values()))) if symbols else []
    run: list[str] = []
    for month in common:
        if run and next_month(run[-1]) != month:
            run = []
        if all(by_symbol[symbol][month].qualifies for symbol in symbols):
            run.append(month)
        else:
            run = []
        if len(run) >= 6:
            candidate = f"{next_month(run[-1])}-01"
            return max("2019-01-01", candidate)
    return None


def render_minute_archive_report(manifest: MinuteArchiveManifest) -> str:
    rows = sorted(manifest.months, key=lambda item: (item.symbol, item.month))
    blockers = [item for item in rows if item.audit_state != "audit_complete"]
    research_month = manifest.research_start[:7] if manifest.research_start else None
    relevant_blockers = [
        item for item in blockers if research_month is None or item.month >= research_month
    ]
    passed = bool(manifest.research_start) and not relevant_blockers
    lines = [
        "# T1 Canonical Public Minute Data Report",
        "",
        f"- Status: {'pass' if passed else 'blocked'}",
        "- Scope: public BTC/ETH spot 1m archive and liquidity qualification only",
        "- API key used: no",
        "- Private data used: no",
        "- Strategy returns computed: no",
        "- Raw data committed: no",
        f"- Requested range: {manifest.requested_start} through {manifest.requested_end}",
        f"- Research start: {manifest.research_start or 'not_qualified'}",
        f"- Manifest SHA256: `{manifest.canonical_sha256()}`",
        "",
        "## Method",
        "",
        "Monthly official ZIP is the base. Official daily ZIP may add only missing timestamps. "
        "Deterministic REST windows are comparison evidence and never overwrite ZIP rows.",
        "Liquidity proxy is the p95 two-bar Corwin-Schultz estimate using only 1m high/low inputs; "
        "the fixed threshold is 0.10%.",
        "",
        "## Summary",
        "",
        "| Symbol | Months | Complete | Qualified | Missing rows | Invalid rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for symbol in manifest.symbols:
        selected = [item for item in rows if item.symbol == symbol]
        lines.append(
            f"| {symbol} | {len(selected)} | {sum(item.audit_state == 'audit_complete' for item in selected)} "
            f"| {sum(item.qualifies for item in selected)} | {sum(item.missing_rows for item in selected)} "
            f"| {sum(item.invalid_rows for item in selected)} |"
        )
    lines.extend(
        [
            "",
            "## Actual Data Range",
            "",
            "| Symbol | First 1m open UTC | Last 1m open UTC |",
            "| --- | --- | --- |",
        ]
    )
    for symbol in manifest.symbols:
        selected = [item for item in rows if item.symbol == symbol]
        starts = [item.first_open_ms for item in selected if item.first_open_ms is not None]
        ends = [item.last_open_ms for item in selected if item.last_open_ms is not None]
        first = datetime.fromtimestamp(min(starts) / 1000, timezone.utc).isoformat() if starts else "unavailable"
        last = datetime.fromtimestamp(max(ends) / 1000, timezone.utc).isoformat() if ends else "unavailable"
        lines.append(f"| {symbol} | {first} | {last} |")
    lines.extend(
        [
            "",
            "## REST Samples",
            "",
            "| Month | Reason | Overlap | Field differences | Status | Archive hash | REST hash |",
            "| --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for item in manifest.rest_samples:
        lines.append(
            f"| {item.month} | {item.reason} | {item.overlap_rows} | {item.field_differences} "
            f"| {'pass' if item.passed else 'blocked'} | `{item.archive_overlap_sha256}` | `{item.rest_overlap_sha256}` |"
        )
    lines.extend(["", "## Quarantined or Blocking Months", ""])
    if blockers:
        lines.extend(
            [
                "| Dataset | Month | State | Research relevance | Missing | Max gap | Invalid | Daily failures | Completeness | p95 spread |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for item in blockers:
            lines.append(
                f"| {item.symbol} | {item.month} | {item.audit_state} "
                f"| {'blocking' if item in relevant_blockers else 'pre-start quarantine'} | {item.missing_rows} "
                f"| {item.max_contiguous_gap} | {item.invalid_rows} | {item.daily_fetch_failures} | {item.completeness} "
                f"| {item.p95_spread_proxy} |"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            f"- Exact public range recorded: {'pass' if rows and all(any(item.symbol == symbol and item.first_open_ms is not None for item in rows) for symbol in manifest.symbols) else 'blocked'}",
            f"- REST sampling plan completed: {'pass' if manifest.rest_samples and all(item.passed for item in manifest.rest_samples) else 'blocked'}",
            f"- Historical source anomalies registered: {'pass' if blockers else 'not_applicable'}",
            f"- Zero unexplained relevant gaps: {'pass' if not relevant_blockers else 'blocked'}",
            f"- Liquidity-qualified start frozen: {'pass' if manifest.research_start else 'blocked'}",
            "- T2 authorized: " + ("yes" if passed else "no"),
            "- M1D strategy code authorized: no",
            "- M2 authorized: no",
            "",
        ]
    )
    return "\n".join(lines)
