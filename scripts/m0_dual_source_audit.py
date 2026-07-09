#!/usr/bin/env python3
"""Run the strict M0 public ZIP/REST audit without credentials.

Only official unauthenticated public GET resources are used. Environment proxy
discovery is disabled. Callers may explicitly select the approved
unauthenticated loopback HTTP proxy for REST while ZIP retrieval remains
direct. Raw responses go to an ignored append-only run directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.dual_source_audit import (
    REQUIRED_DATASETS,
    AuditRunEvidence,
    ScopeEvidence,
    ScopePlan,
    compare_scope,
    evaluate_gate,
    render_diagnostics_report,
    render_revalidation_report,
    source_failure,
)
from btc_eth_dual_quant.data.quality import interval_to_ms


ZIP_KIND = {
    "spot_klines": ("spot", "klines"),
    "um_futures_klines": ("futures/um", "klines"),
    "mark_price_klines": ("futures/um", "markPriceKlines"),
    "index_price_klines": ("futures/um", "indexPriceKlines"),
    "premium_index_klines": ("futures/um", "premiumIndexKlines"),
}
REST_PATH = {
    "spot_klines": "/api/v3/klines",
    "um_futures_klines": "/fapi/v1/klines",
    "mark_price_klines": "/fapi/v1/markPriceKlines",
    "index_price_klines": "/fapi/v1/indexPriceKlines",
    "premium_index_klines": "/fapi/v1/premiumIndexKlines",
}


@dataclass(frozen=True)
class FetchResult:
    status: int | None
    body: bytes
    error_category: str

    @property
    def ok(self) -> bool:
        return self.status == 200 and self.error_category == "none"


@dataclass
class ZipProfile:
    plans: list[ScopePlan]
    rows_by_month: dict[str, list[dict[str, Any]]]
    bodies_by_month: dict[str, bytes]
    status_by_month: dict[str, FetchResult]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M0 official public ZIP/REST dual-source audit")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--datasets", default=",".join(REQUIRED_DATASETS))
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--start-date", default="2019-09-01")
    parser.add_argument("--end-date", default=None, help="UTC date; defaults to yesterday")
    parser.add_argument("--spot-base-url", default="https://data-api.binance.vision")
    parser.add_argument("--futures-base-url", default="https://fapi.binance.com")
    parser.add_argument("--zip-base-url", default="https://data.binance.vision")
    parser.add_argument("--timeout-sec", type=int, default=20)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--proxy-url",
        default=None,
        help="Approved unauthenticated loopback HTTP proxy for official REST only",
    )
    parser.add_argument("--execution-label", default="local")
    parser.add_argument("--raw-root", default="storage/raw/m0_dual_source_audit")
    parser.add_argument("--evidence-out", default="storage/logs/m0_dual_source_audit_evidence.json")
    parser.add_argument("--out", default="reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md")
    parser.add_argument("--revalidation-out", default="reports/m0/M0_AUDIT_REVALIDATION_REPORT.md")
    parser.add_argument(
        "--merge-evidence",
        action="append",
        default=[],
        help="Render a combined report from sanitized evidence JSON files without network access",
    )
    return parser.parse_args()


def _epoch_ms(value: Any) -> int:
    timestamp = int(value)
    if abs(timestamp) >= 100_000_000_000_000:
        timestamp //= 1000
    return timestamp


def _month_start(value: str) -> date:
    parsed = date.fromisoformat(value)
    return parsed.replace(day=1)


def _next_month(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def _previous_month(value: date) -> date:
    return date(value.year - (value.month == 1), 12 if value.month == 1 else value.month - 1, 1)


def _month_range(start_date: str, end_date: str | None) -> list[date]:
    start = _month_start(start_date)
    end_day = date.fromisoformat(end_date) if end_date else datetime.now(timezone.utc).date() - timedelta(days=1)
    end_month = end_day.replace(day=1)
    if _next_month(end_month) - timedelta(days=1) != end_day:
        end_month = _previous_month(end_month)
    current_month = datetime.now(timezone.utc).date().replace(day=1)
    if end_month >= current_month:
        end_month = _previous_month(current_month)
    if end_month < start:
        raise ValueError("audit range contains no complete UTC month")
    result: list[date] = []
    current = start
    while current <= end_month:
        result.append(current)
        current = _next_month(current)
    return result


def _month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def _month_for_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc).strftime("%Y-%m")


def _month_bounds(value: str) -> tuple[int, int]:
    start = datetime.strptime(value, "%Y-%m").replace(tzinfo=timezone.utc)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000) - 1


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_error(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            return "timeout"
        return f"url_error_{type(reason).__name__.lower()}" if reason is not None else "url_error"
    return type(exc).__name__.lower()


def _validated_proxy_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("proxy URL scheme must be http or https")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("proxy URL host must be loopback")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("proxy URL must not contain credentials")
    if parsed.port is None or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("proxy URL must contain only scheme, loopback host, and port")
    return value.rstrip("/")


class PublicFetcher:
    def __init__(self, timeout_sec: int, retries: int, proxy_url: str | None = None) -> None:
        self.timeout_sec = timeout_sec
        self.retries = max(1, retries)
        validated = _validated_proxy_url(proxy_url)
        proxies = {} if validated is None else {"http": validated, "https": validated}
        self.opener = build_opener(ProxyHandler(proxies))

    def get(self, url: str) -> FetchResult:
        request = Request(url, headers={"User-Agent": "btc-eth-dual-quant-m0-audit/1"}, method="GET")
        last_error = "network_error"
        for attempt in range(self.retries):
            try:
                with self.opener.open(request, timeout=self.timeout_sec) as response:
                    return FetchResult(int(response.status), response.read(), "none")
            except HTTPError as exc:
                category = f"http_{exc.code}"
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.retries - 1:
                    return FetchResult(exc.code, b"", category)
                last_error = category
            except (TimeoutError, URLError, OSError) as exc:
                last_error = _safe_error(exc)
                if attempt == self.retries - 1:
                    return FetchResult(None, b"", last_error)
            time.sleep(min(2**attempt, 4))
        return FetchResult(None, b"", last_error)


class AppendOnlyRunStore:
    def __init__(self, root: str | Path, run_id: str) -> None:
        self.root = Path(root) / f"run={run_id}"

    def write(self, dataset: str, symbol: str, month: str, source: str, page: int, body: bytes) -> Path:
        suffix = "zip" if source.startswith("zip") else "json"
        path = self.root / dataset / symbol / f"month={month}" / source / f"response-{page:04d}.{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(body)
        return path


def _zip_url(base_url: str, dataset: str, symbol: str, interval: str, month: str) -> str:
    scope, kind = ZIP_KIND[dataset]
    return (
        f"{base_url.rstrip('/')}/data/{scope}/monthly/{kind}/{symbol}/{interval}/"
        f"{symbol}-{interval}-{month}.zip"
    )


def _daily_zip_url(base_url: str, dataset: str, symbol: str, interval: str, day: str) -> str:
    scope, kind = ZIP_KIND[dataset]
    return (
        f"{base_url.rstrip('/')}/data/{scope}/daily/{kind}/{symbol}/{interval}/"
        f"{symbol}-{interval}-{day}.zip"
    )


def _combined_sha256(parts: Iterable[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    found = False
    for label, body in sorted(parts):
        found = True
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(body)).encode("ascii"))
        digest.update(b"\0")
        digest.update(body)
        digest.update(b"\n")
    return digest.hexdigest() if found else ""


def _decode_zip_rows(body: bytes, dataset: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(names) != 1:
            raise ValueError("official ZIP must contain exactly one CSV")
        with archive.open(names[0]) as source:
            rows = list(csv.reader(io.TextIOWrapper(source, encoding="utf-8")))
    if rows and rows[0] and rows[0][0].strip().lower().replace(" ", "_") == "open_time":
        rows = rows[1:]
    return _decode_array_rows(rows, dataset)


def _decode_array_rows(payload: Iterable[Any], dataset: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, (list, tuple)) or len(item) < 7:
            continue
        record: dict[str, Any] = {
            "open_time": _epoch_ms(item[0]),
            "open": item[1],
            "high": item[2],
            "low": item[3],
            "close": item[4],
            "close_time": _epoch_ms(item[6]),
        }
        if dataset in {"spot_klines", "um_futures_klines"}:
            if len(item) < 11:
                continue
            record.update(
                {
                    "volume": item[5],
                    "quote_volume": item[7],
                    "trade_count": item[8],
                    "taker_buy_base_volume": item[9],
                    "taker_buy_quote_volume": item[10],
                }
            )
        result.append(record)
    return result


def _is_profile_anomaly(row: dict[str, Any], dataset: str) -> bool:
    try:
        open_price = Decimal(str(row["open"]))
        high = Decimal(str(row["high"]))
        low = Decimal(str(row["low"]))
        close = Decimal(str(row["close"]))
        values = (open_price, high, low, close)
        if not all(value.is_finite() for value in values):
            return True
        if high < max(values) or low > min(values):
            return True
        if (
            dataset != "premium_index_klines"
            and abs(open_price) > Decimal("1e-18")
            and (high - low) / abs(open_price) > Decimal("0.30")
        ):
            return True
        if dataset in {"spot_klines", "um_futures_klines"}:
            volume = Decimal(str(row["volume"]))
            return not volume.is_finite() or volume <= 0
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return True
    return False


def _select_scope_plans(
    dataset: str,
    symbol: str,
    interval: str,
    rows_by_month: dict[str, list[dict[str, Any]]],
    missing_after_inception: Iterable[str],
) -> list[ScopePlan]:
    available = sorted(month for month, rows in rows_by_month.items() if rows)
    if not available:
        return []
    reasons: dict[str, set[str]] = {month: set() for month in available}
    reasons[available[0]].add("first")
    reasons[available[len(available) // 2]].add("middle")
    reasons[available[-1]].add("latest_complete")

    all_rows = sorted((row for rows in rows_by_month.values() for row in rows), key=lambda item: int(item["open_time"]))
    for item in all_rows:
        if _is_profile_anomaly(item, dataset):
            reasons[_month_for_ms(int(item["open_time"]))].add("anomaly")

    step = interval_to_ms(interval)
    for left, right in zip(all_rows, all_rows[1:]):
        left_time = int(left["open_time"])
        right_time = int(right["open_time"])
        if right_time - left_time <= step:
            continue
        boundary_times = (left_time, left_time + step, right_time - step, right_time)
        for timestamp in boundary_times:
            month = _month_for_ms(timestamp)
            if month in reasons:
                reasons[month].add("gap")

    for month in missing_after_inception:
        reasons.setdefault(month, set()).add("zip_profile_missing")
    return [
        ScopePlan(dataset, symbol, interval, month, tuple(sorted(month_reasons)))
        for month, month_reasons in sorted(reasons.items())
        if month_reasons
    ]


def _build_zip_profile(
    *,
    fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    zip_base_url: str,
    dataset: str,
    symbol: str,
    interval: str,
    months: list[date],
) -> ZipProfile:
    rows_by_month: dict[str, list[dict[str, Any]]] = {}
    bodies_by_month: dict[str, bytes] = {}
    status_by_month: dict[str, FetchResult] = {}
    first_available_seen = False
    missing_after_inception: list[str] = []
    for value in months:
        month = _month_key(value)
        result = fetcher.get(_zip_url(zip_base_url, dataset, symbol, interval, month))
        status_by_month[month] = result
        if not result.ok:
            if first_available_seen:
                missing_after_inception.append(month)
            continue
        store.write(dataset, symbol, month, "zip", 0, result.body)
        try:
            rows = [row for row in _decode_zip_rows(result.body, dataset) if _month_for_ms(int(row["open_time"])) == month]
        except (ValueError, zipfile.BadZipFile, UnicodeError):
            status_by_month[month] = FetchResult(result.status, result.body, "zip_parse_error")
            if first_available_seen:
                missing_after_inception.append(month)
            continue
        if rows:
            first_available_seen = True
            rows_by_month[month] = rows
            bodies_by_month[month] = result.body
        elif first_available_seen:
            missing_after_inception.append(month)
    plans = _select_scope_plans(dataset, symbol, interval, rows_by_month, missing_after_inception)
    if not plans:
        first_month = _month_key(months[0])
        plans = [ScopePlan(dataset, symbol, interval, first_month, ("first", "source_unavailable"))]
    return ZipProfile(plans, rows_by_month, bodies_by_month, status_by_month)


def _rest_url(
    *,
    spot_base_url: str,
    futures_base_url: str,
    dataset: str,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
) -> str:
    base = spot_base_url if dataset == "spot_klines" else futures_base_url
    symbol_key = "pair" if dataset == "index_price_klines" else "symbol"
    params = {
        symbol_key: symbol,
        "interval": interval,
        "startTime": start_ms,
        "endTime": end_ms,
        "limit": 1000,
    }
    return f"{base.rstrip('/')}{REST_PATH[dataset]}?{urlencode(params)}"


def _fetch_rest_month(
    *,
    fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    spot_base_url: str,
    futures_base_url: str,
    dataset: str,
    symbol: str,
    interval: str,
    month: str,
) -> tuple[FetchResult, list[dict[str, Any]], str]:
    start_ms, end_ms = _month_bounds(month)
    current = start_ms
    rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    page = 0
    last_result = FetchResult(None, b"", "not_run")
    while current <= end_ms:
        result = fetcher.get(
            _rest_url(
                spot_base_url=spot_base_url,
                futures_base_url=futures_base_url,
                dataset=dataset,
                symbol=symbol,
                interval=interval,
                start_ms=current,
                end_ms=end_ms,
            )
        )
        last_result = result
        if not result.ok:
            return result, rows, digest.hexdigest() if rows else ""
        store.write(dataset, symbol, month, "rest", page, result.body)
        digest.update(result.body)
        digest.update(b"\n")
        try:
            payload = json.loads(result.body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            return FetchResult(result.status, result.body, "rest_parse_error"), rows, digest.hexdigest()
        page_rows = _decode_array_rows(payload, dataset)
        page_rows = [item for item in page_rows if start_ms <= int(item["open_time"]) <= end_ms]
        rows.extend(page_rows)
        if not page_rows or len(payload) < 1000:
            break
        next_start = max(int(item["close_time"]) for item in page_rows) + 1
        if next_start <= current:
            return FetchResult(result.status, result.body, "rest_pagination_stalled"), rows, digest.hexdigest()
        current = next_start
        page += 1
    unique_rows = {int(item["open_time"]): item for item in rows}
    return last_result, [unique_rows[key] for key in sorted(unique_rows)], digest.hexdigest()


def _failure_classification(result: FetchResult, source: str) -> str:
    if source == "zip":
        return "zip_unavailable"
    return "network_blocked"


def _supplemental_days(preliminary: ScopeEvidence) -> list[str]:
    timestamps = {
        item.open_time
        for item in preliminary.differences
        if item.open_time is not None
        and item.rest_value != ""
        and item.classification in {"source_revision", "timestamp_mismatch"}
    }
    return sorted({
        datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m-%d")
        for timestamp in timestamps
    })


def _fetch_supplemental_daily_zip(
    *,
    fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    zip_base_url: str,
    dataset: str,
    symbol: str,
    interval: str,
    days: Iterable[str],
) -> tuple[list[dict[str, Any]], list[tuple[str, bytes]], dict[str, str]]:
    rows: list[dict[str, Any]] = []
    payloads: list[tuple[str, bytes]] = []
    statuses: dict[str, str] = {}
    for day in sorted(set(days)):
        result = fetcher.get(_daily_zip_url(zip_base_url, dataset, symbol, interval, day))
        statuses[day] = f"{result.status if result.status is not None else 'n/a'}:{result.error_category}"
        if not result.ok:
            continue
        store.write(dataset, symbol, day, "zip_daily", 0, result.body)
        try:
            decoded = _decode_zip_rows(result.body, dataset)
        except (ValueError, zipfile.BadZipFile, UnicodeError):
            statuses[day] = f"{result.status}:zip_parse_error"
            continue
        rows.extend(
            item
            for item in decoded
            if datetime.fromtimestamp(int(item["open_time"]) / 1000, timezone.utc).strftime("%Y-%m-%d") == day
        )
        payloads.append((f"daily:{day}", result.body))
    unique_rows = {int(item["open_time"]): item for item in rows}
    return [unique_rows[key] for key in sorted(unique_rows)], payloads, statuses


def _run_dataset_symbol(
    *,
    zip_fetcher: PublicFetcher,
    rest_fetcher: PublicFetcher,
    store: AppendOnlyRunStore,
    args: argparse.Namespace,
    months: list[date],
    dataset: str,
    symbol: str,
    rest_circuits: dict[str, FetchResult],
) -> tuple[list[ScopePlan], list[ScopeEvidence]]:
    profile = _build_zip_profile(
        fetcher=zip_fetcher,
        store=store,
        zip_base_url=args.zip_base_url,
        dataset=dataset,
        symbol=symbol,
        interval=args.interval,
        months=months,
    )
    rest_results: dict[str, tuple[FetchResult, list[dict[str, Any]], str]] = {}
    market = "spot" if dataset == "spot_klines" else "futures"
    circuit_failure: FetchResult | None = rest_circuits.get(market)
    for plan in profile.plans:
        if plan.month not in profile.rows_by_month:
            continue
        if circuit_failure is not None:
            rest_results[plan.month] = (circuit_failure, [], "")
            continue
        result = _fetch_rest_month(
            fetcher=rest_fetcher,
            store=store,
            spot_base_url=args.spot_base_url,
            futures_base_url=args.futures_base_url,
            dataset=dataset,
            symbol=symbol,
            interval=args.interval,
            month=plan.month,
        )
        rest_results[plan.month] = result
        if not result[0].ok and (result[0].status in {403, 451} or result[0].status is None):
            circuit_failure = result[0]
            rest_circuits[market] = result[0]

    evidence: list[ScopeEvidence] = []
    for plan in profile.plans:
        zip_result = profile.status_by_month.get(plan.month, FetchResult(None, b"", "zip_not_run"))
        zip_rows = profile.rows_by_month.get(plan.month, [])
        zip_body = profile.bodies_by_month.get(plan.month, b"")
        if not zip_result.ok or not zip_rows:
            evidence.append(
                source_failure(
                    plan,
                    _failure_classification(zip_result, "zip"),
                    zip_result.error_category,
                    zip_http_status=zip_result.status,
                )
            )
            continue
        rest_result, rest_rows, rest_hash = rest_results.get(
            plan.month, (FetchResult(None, b"", "rest_not_run"), [], "")
        )
        if not rest_result.ok:
            evidence.append(
                source_failure(
                    plan,
                    _failure_classification(rest_result, "rest"),
                    rest_result.error_category,
                    rest_http_status=rest_result.status,
                    zip_http_status=zip_result.status,
                    zip_payload_sha256=_sha256(zip_body),
                    rest_payload_sha256=rest_hash,
                    zip_rows=len(zip_rows),
                    rest_rows=len(rest_rows),
                )
            )
            continue
        month_date = datetime.strptime(plan.month, "%Y-%m").date()
        adjacent_months = {_month_key(_previous_month(month_date)), _month_key(_next_month(month_date))}
        adjacent_zip_rows = [
            item
            for adjacent in adjacent_months
            for item in profile.rows_by_month.get(adjacent, [])
        ]
        adjacent_rest_rows = [
            item
            for adjacent in adjacent_months
            for item in rest_results.get(adjacent, (FetchResult(None, b"", ""), [], ""))[1]
        ]
        preliminary = compare_scope(
            plan=plan,
            zip_rows=zip_rows,
            rest_rows=rest_rows,
            adjacent_zip_rows=adjacent_zip_rows,
            adjacent_rest_rows=adjacent_rest_rows,
            zip_payload_sha256=_sha256(zip_body),
            rest_payload_sha256=rest_hash,
            rest_http_status=rest_result.status,
            zip_http_status=zip_result.status,
        )
        supplemental_rows, supplemental_payloads, supplemental_statuses = _fetch_supplemental_daily_zip(
            fetcher=zip_fetcher,
            store=store,
            zip_base_url=args.zip_base_url,
            dataset=dataset,
            symbol=symbol,
            interval=args.interval,
            days=_supplemental_days(preliminary),
        )
        zip_evidence_hash = _combined_sha256(
            [(f"monthly:{plan.month}", zip_body), *supplemental_payloads]
        )
        evidence.append(
            compare_scope(
                plan=plan,
                zip_rows=zip_rows,
                rest_rows=rest_rows,
                supplemental_zip_rows=supplemental_rows,
                supplemental_zip_statuses=supplemental_statuses,
                adjacent_zip_rows=adjacent_zip_rows,
                adjacent_rest_rows=adjacent_rest_rows,
                zip_payload_sha256=zip_evidence_hash,
                rest_payload_sha256=rest_hash,
                rest_http_status=rest_result.status,
                zip_http_status=zip_result.status,
            )
        )
    return profile.plans, evidence


def _load_evidence(paths: Iterable[str]) -> list[AuditRunEvidence]:
    runs: list[AuditRunEvidence] = []
    for value in paths:
        payload = json.loads(Path(value).read_text(encoding="utf-8"))
        runs.append(AuditRunEvidence.from_dict(payload))
    return runs


def _write_text(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    if args.merge_evidence:
        runs = _load_evidence(args.merge_evidence)
        report = render_diagnostics_report(runs)
        _write_text(args.out, report)
        _write_text(args.revalidation_out, render_revalidation_report(runs))
        gate = evaluate_gate(
            [scope for run in runs for scope in run.scopes],
            [plan for run in runs for plan in run.plans],
        )
        print(f"Wrote combined M0 dual-source audit report: {args.out}")
        return 0 if gate.passed else 2

    symbols = tuple(item.strip().upper() for item in args.symbols.split(",") if item.strip())
    datasets = tuple(item.strip() for item in args.datasets.split(",") if item.strip())
    unsupported = sorted(set(datasets) - set(REQUIRED_DATASETS))
    if unsupported:
        raise ValueError(f"unsupported datasets: {','.join(unsupported)}")
    if not symbols or not datasets:
        raise ValueError("symbols and datasets must not be empty")

    months = _month_range(args.start_date, args.end_date)
    generated = datetime.now(timezone.utc)
    run_id = generated.strftime("%Y%m%dT%H%M%S%fZ")
    store = AppendOnlyRunStore(args.raw_root, run_id)
    proxy_url = _validated_proxy_url(args.proxy_url)
    zip_fetcher = PublicFetcher(args.timeout_sec, args.retries)
    rest_fetcher = PublicFetcher(args.timeout_sec, args.retries, proxy_url=proxy_url)
    plans: list[ScopePlan] = []
    scopes: list[ScopeEvidence] = []
    rest_circuits: dict[str, FetchResult] = {}
    for symbol in symbols:
        for dataset in datasets:
            dataset_plans, dataset_scopes = _run_dataset_symbol(
                zip_fetcher=zip_fetcher,
                rest_fetcher=rest_fetcher,
                store=store,
                args=args,
                months=months,
                dataset=dataset,
                symbol=symbol,
                rest_circuits=rest_circuits,
            )
            plans.extend(dataset_plans)
            scopes.extend(dataset_scopes)
            print(
                f"audited {dataset}:{symbol} scopes={len(dataset_plans)} "
                f"pass={sum(1 for item in dataset_scopes if item.passed)}",
                flush=True,
            )

    run = AuditRunEvidence(
        execution_label=args.execution_label,
        generated_utc=generated.isoformat(timespec="seconds"),
        plans=tuple(plans),
        scopes=tuple(scopes),
        transport="rest_local_https_proxy_zip_direct" if proxy_url else "direct",
    )
    _write_json(args.evidence_out, run.to_dict())
    _write_text(args.out, render_diagnostics_report([run]))
    _write_text(args.revalidation_out, render_revalidation_report([run]))
    gate = evaluate_gate(scopes, plans)
    print(f"Wrote sanitized evidence: {args.evidence_out}")
    print(f"Wrote M0 dual-source audit report: {args.out}")
    print(f"M0 dual-source audit status: {'pass' if gate.passed else 'blocked'}")
    return 0 if gate.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
