#!/usr/bin/env python3
"""Execute the single preregistered U-04 sealed-IS paper observation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import (
    QualificationFailure,
    SealedOOSAccess,
    identity_hash,
    load_json,
    utc_ms,
)


EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification"
FIVE_MINUTES_MS = 300_000
ONE_HOUR_MS = 3_600_000
ONE_DAY_MS = 86_400_000
HORIZONS = (1, 2, 4, 8, 12, 24)


class ObservationFailure(ValueError):
    """Fail-closed paper-observation error."""


def median(values: Sequence[Decimal]) -> Decimal:
    if not values:
        raise ObservationFailure("median of empty values")
    ordered_values = sorted(values)
    middle = len(ordered_values) // 2
    if len(ordered_values) % 2:
        return ordered_values[middle]
    return (ordered_values[middle - 1] + ordered_values[middle]) / Decimal(2)


def decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ObservationFailure("non-finite decimal output")
    return format(value, "f")


def month_for_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).strftime("%Y-%m")


def month_end_ms(month: str) -> int:
    year, number = (int(part) for part in month.split("-"))
    if number == 12:
        return utc_ms(f"{year + 1:04d}-01-01T00:00:00Z")
    return utc_ms(f"{year:04d}-{number + 1:02d}-01T00:00:00Z")


def ordered(values: Iterable[Any], order: str, *, key) -> list[Any]:
    output = sorted(values, key=key)
    if order == "reverse":
        output.reverse()
    elif order == "deterministic_shuffled":
        random.Random(314159).shuffle(output)
    elif order != "normal":
        raise ObservationFailure(f"unknown order: {order}")
    return output


def _archive_path(raw_root: Path, symbol: str, month: str) -> Path:
    relative = Path(f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip")
    path = raw_root / relative
    if not path.is_file():
        raise ObservationFailure(f"qualified active archive missing: {relative.as_posix()}")
    return path


def read_five_minute_rows(
    raw_root: Path,
    symbol: str,
    month: str,
    *,
    is_start_ms: int,
    is_end_ms: int,
) -> Iterable[tuple[int, Decimal, Decimal, Decimal, Decimal]]:
    """Yield IS rows; stop on the boundary before decoding any OOS OHLC field."""
    path = _archive_path(raw_root, symbol, month)
    with zipfile.ZipFile(path) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        if len(files) != 1:
            raise ObservationFailure(f"archive member count changed: {symbol}:{month}")
        previous: int | None = None
        with archive.open(files[0]) as handle:
            for raw_line in handle:
                first = raw_line.split(b",", 1)[0]
                try:
                    opened = int(first)
                except ValueError:
                    if previous is None and first.strip().lower() in {b"open_time", b"opentime"}:
                        continue
                    raise ObservationFailure(f"malformed open time: {symbol}:{month}")
                if opened >= is_end_ms:
                    break
                if opened < is_start_ms:
                    continue
                if previous is not None and opened <= previous:
                    raise ObservationFailure(f"non-increasing 5m row: {symbol}:{month}")
                previous = opened
                fields = next(csv.reader([raw_line.decode("utf-8").rstrip("\r\n")]))
                if len(fields) != 12:
                    raise ObservationFailure(f"5m schema changed: {symbol}:{month}")
                try:
                    opened_value, high, low, close = map(Decimal, (fields[1], fields[2], fields[3], fields[4]))
                except InvalidOperation as exc:
                    raise ObservationFailure(f"invalid OHLC: {symbol}:{month}:{opened}") from exc
                if opened % FIVE_MINUTES_MS or min(opened_value, high, low, close) <= 0 or high < max(opened_value, close) or low > min(opened_value, close):
                    raise ObservationFailure(f"invalid 5m row: {symbol}:{month}:{opened}")
                yield opened, opened_value, high, low, close


def build_membership(document: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    output: dict[str, list[str]] = defaultdict(list)
    for row in document["content"]:
        if row.get("eligibility_status") == "qualified":
            output[str(row["effective_month"])[:7]].append(str(row["symbol"]))
    frozen = {month: tuple(sorted(symbols)) for month, symbols in output.items()}
    if any(len(symbols) != 15 or len(set(symbols)) != 15 for symbols in frozen.values()):
        raise ObservationFailure("membership authority is not exact Top-15")
    return frozen


def build_hourly_closes(
    *,
    raw_root: Path,
    membership: Mapping[str, Sequence[str]],
    masked_slots: set[tuple[str, int]],
    is_start_ms: int,
    is_end_ms: int,
    order: str,
) -> dict[str, dict[int, Decimal]]:
    closes: dict[str, dict[int, Decimal]] = defaultdict(dict)
    tasks = [(month, symbol) for month, symbols in membership.items() for symbol in symbols if utc_ms(f"{month}-01T00:00:00Z") < is_end_ms]
    for month, symbol in ordered(tasks, order, key=lambda item: (item[0], item[1])):
        hourly: dict[int, list[tuple[int, Decimal]]] = defaultdict(list)
        for opened, _open, _high, _low, close in read_five_minute_rows(
            raw_root, symbol, month, is_start_ms=is_start_ms, is_end_ms=is_end_ms,
        ):
            if (symbol, opened) in masked_slots:
                continue
            hourly[(opened // ONE_HOUR_MS) * ONE_HOUR_MS].append((opened, close))
        for hour, rows in hourly.items():
            expected = [hour + index * FIVE_MINUTES_MS for index in range(12)]
            if [item[0] for item in rows] == expected:
                decision = hour + ONE_HOUR_MS
                if is_start_ms < decision <= is_end_ms:
                    closes[symbol][decision] = rows[-1][1]
    return closes


def select_events(
    *,
    hourly_closes: Mapping[str, Mapping[int, Decimal]],
    membership: Mapping[str, Sequence[str]],
    is_start_ms: int,
    is_end_ms: int,
    protocol_hash: str,
    qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {"decision_times_evaluated": 0, "cross_section_ineligible": 0, "scale_ineligible": 0, "simultaneous_candidates_discarded": 0}
    with localcontext() as context:
        context.prec = 50
        decision = is_start_ms + ONE_HOUR_MS
        while decision <= is_end_ms:
            decision_close = decision - 1
            symbols = membership.get(month_for_ms(decision_close))
            if symbols is None or len(symbols) < 10:
                accounting["cross_section_ineligible"] += 1
                decision += ONE_HOUR_MS
                continue
            returns: dict[str, Decimal] = {}
            for symbol in symbols:
                current = hourly_closes.get(symbol, {}).get(decision)
                previous = hourly_closes.get(symbol, {}).get(decision - ONE_HOUR_MS)
                if current is None or previous is None:
                    break
                returns[symbol] = (current / previous).ln()
            if len(returns) != len(symbols):
                accounting["cross_section_ineligible"] += 1
                decision += ONE_HOUR_MS
                continue
            accounting["decision_times_evaluated"] += 1
            common = median(list(returns.values()))
            residuals = {symbol: value - common for symbol, value in returns.items()}
            mad = median([abs(value) for value in residuals.values()])
            scale = Decimal("1.4826") * mad
            if not scale.is_finite() or scale == 0:
                accounting["scale_ineligible"] += 1
                decision += ONE_HOUR_MS
                continue
            candidates = []
            for symbol, residual in residuals.items():
                standardized = residual / scale
                relative_simple = residual.exp() - Decimal(1)
                if standardized <= Decimal("-3.0") and relative_simple <= Decimal("-0.0180"):
                    candidates.append((standardized, residual, symbol, relative_simple, common, scale))
            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1], item[2]))
                accounting["simultaneous_candidates_discarded"] += len(candidates) - 1
                standardized, residual, symbol, relative_simple, common, scale = candidates[0]
                event_core = {
                    "decision_time_ms": decision_close,
                    "reference_open_time_ms": decision,
                    "symbol": symbol,
                    "active_members": list(symbols),
                    "member_count": len(symbols),
                    "common_log_return": decimal_text(common),
                    "raw_residual": decimal_text(residual),
                    "robust_scale": decimal_text(scale),
                    "standardized_residual": decimal_text(standardized),
                    "relative_simple_return": decimal_text(relative_simple),
                }
                event_core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": qualification_hash, **event_core})
                events.append(event_core)
            decision += ONE_HOUR_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    representatives: list[dict[str, Any]] = []
    previous_candidate: int | None = None
    episode_id = -1
    for event in sorted(events, key=lambda item: (int(item["decision_time_ms"]), str(item["symbol"]))):
        decision = int(event["decision_time_ms"])
        if previous_candidate is None or decision - previous_candidate > 24 * ONE_HOUR_MS:
            episode_id += 1
            row = dict(event)
            row["episode_id"] = identity_hash({"episode_number": episode_id, "first_event_id": event["event_id"]})
            representatives.append(row)
        previous_candidate = decision
    return representatives


def capture_path_rows(
    *,
    raw_root: Path,
    episodes: Sequence[Mapping[str, Any]],
    masked_slots: set[tuple[str, int]],
    is_start_ms: int,
    is_end_ms: int,
    order: str,
) -> tuple[dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]], dict[str, str]]:
    required: dict[tuple[str, str], set[int]] = defaultdict(set)
    censored: dict[str, str] = {}
    for episode in episodes:
        reference = int(episode["reference_open_time_ms"])
        end = reference + 24 * ONE_HOUR_MS
        month = month_for_ms(reference)
        if end > is_end_ms:
            censored[str(episode["episode_id"])] = "sealed_is_boundary"
            continue
        if end > month_end_ms(month):
            censored[str(episode["episode_id"])] = "membership_boundary"
            continue
        times = range(reference, end, FIVE_MINUTES_MS)
        for symbol in episode["active_members"]:
            required[(str(symbol), month)].update(times)
    captured: dict[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]] = {}
    for symbol, month in ordered(required, order, key=lambda item: (item[1], item[0])):
        wanted = required[(symbol, month)]
        for opened, opened_value, high, low, close in read_five_minute_rows(
            raw_root, symbol, month, is_start_ms=is_start_ms, is_end_ms=is_end_ms,
        ):
            if opened in wanted and (symbol, opened) not in masked_slots:
                captured[(symbol, opened)] = (opened_value, high, low, close)
    return captured, censored


def observe_paths(
    episodes: Sequence[Mapping[str, Any]],
    captured: Mapping[tuple[str, int], tuple[Decimal, Decimal, Decimal, Decimal]],
    censored: Mapping[str, str],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    paths: list[dict[str, Any]] = []
    censor_counts: Counter[str] = Counter(censored.values())
    with localcontext() as context:
        context.prec = 50
        for episode in episodes:
            episode_id = str(episode["episode_id"])
            if episode_id in censored:
                continue
            reference = int(episode["reference_open_time_ms"])
            candidate = str(episode["symbol"])
            peers = [str(symbol) for symbol in episode["active_members"] if symbol != candidate]
            all_symbols = [candidate, *peers]
            times = [reference + index * FIVE_MINUTES_MS for index in range(288)]
            if any((symbol, opened) not in captured for symbol in all_symbols for opened in times):
                censor_counts["missing_or_quarantined_5m"] += 1
                continue
            reference_opens = {symbol: captured[(symbol, reference)][0] for symbol in all_symbols}
            relative_series: list[Decimal] = []
            candidate_highs: list[Decimal] = []
            candidate_lows: list[Decimal] = []
            candidate_closes: list[Decimal] = []
            for opened in times:
                candidate_row = captured[(candidate, opened)]
                candidate_log = (candidate_row[3] / reference_opens[candidate]).ln()
                peer_logs = [(captured[(peer, opened)][3] / reference_opens[peer]).ln() for peer in peers]
                relative_series.append(candidate_log - median(peer_logs))
                candidate_highs.append(candidate_row[1])
                candidate_lows.append(candidate_row[2])
                candidate_closes.append(candidate_row[3])
            absolute = {}
            relative = {}
            for horizon in HORIZONS:
                index = horizon * 12 - 1
                absolute[str(horizon)] = decimal_text(candidate_closes[index] / reference_opens[candidate] - Decimal(1))
                relative[str(horizon)] = decimal_text(relative_series[index])
            first_recovery = next(((index + 1) * 5 for index, value in enumerate(relative_series) if value >= 0), None)
            paths.append({
                "episode_id": episode_id,
                "event_id": episode["event_id"],
                "decision_time_ms": int(episode["decision_time_ms"]),
                "reference_open_time_ms": reference,
                "symbol": candidate,
                "peer_count": len(peers),
                "absolute_close_displacement": absolute,
                "relative_peer_median_recovery": relative,
                "maximum_favorable_excursion_24h": decimal_text(max(candidate_highs) / reference_opens[candidate] - Decimal(1)),
                "maximum_adverse_excursion_24h": decimal_text(min(candidate_lows) / reference_opens[candidate] - Decimal(1)),
                "first_recovery_minutes": first_recovery,
                "complete_24h": True,
            })
    return paths, censor_counts


def evaluate_gates(paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], *, mismatch_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    projected_full = count * int(protocol["scope"]["full_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    projected_oos = count * int(protocol["scope"]["oos_calendar_days"]) // int(protocol["scope"]["is_calendar_days"])
    relative_24h = median([Decimal(str(row["relative_peer_median_recovery"]["24"])) for row in paths]) if paths else Decimal("NaN")
    absolute_24h = median([Decimal(str(row["absolute_close_displacement"]["24"])) for row in paths]) if paths else Decimal("NaN")
    maximum_year_share = max(years.values(), default=0) / count if count else 1.0
    maximum_symbol_share = max(symbols.values(), default=0) / count if count else 1.0
    metrics = {
        "complete_is_independent_episodes": count,
        "projected_full_independent_episodes": projected_full,
        "projected_sealed_oos_independent_episodes": projected_oos,
        "years_with_ten_complete_episodes": sum(value >= 10 for value in years.values()),
        "episodes_by_year": {str(key): value for key, value in sorted(years.items())},
        "maximum_single_year_episode_share": format(maximum_year_share, ".12f"),
        "episodes_by_symbol": dict(sorted(symbols.items())),
        "maximum_single_symbol_episode_share": format(maximum_symbol_share, ".12f"),
        "distinct_event_symbols": len(symbols),
        "median_24h_relative_recovery": decimal_text(relative_24h) if relative_24h.is_finite() else None,
        "median_24h_absolute_close_displacement": decimal_text(absolute_24h) if absolute_24h.is_finite() else None,
        "qualification_quarantine_lifecycle_or_order_mismatches": mismatch_count,
    }
    checks = {
        "complete_is_independent_episodes": count >= int(gates["complete_is_independent_episodes_minimum"]),
        "projected_full_independent_episodes": projected_full >= int(gates["projected_full_independent_episodes_minimum"]),
        "projected_sealed_oos_independent_episodes": projected_oos >= int(gates["projected_sealed_oos_independent_episodes_minimum"]),
        "years_with_ten_complete_episodes": metrics["years_with_ten_complete_episodes"] >= int(gates["minimum_years_with_ten_complete_episodes"]),
        "maximum_single_year_episode_share": Decimal(metrics["maximum_single_year_episode_share"]) <= Decimal(str(gates["maximum_single_year_episode_share"])),
        "maximum_single_symbol_episode_share": Decimal(metrics["maximum_single_symbol_episode_share"]) <= Decimal(str(gates["maximum_single_symbol_episode_share"])),
        "distinct_event_symbols": len(symbols) >= int(gates["minimum_distinct_event_symbols"]),
        "median_24h_relative_recovery": relative_24h.is_finite() and relative_24h >= Decimal(str(gates["combined_median_24h_relative_recovery_minimum"])),
        "median_24h_absolute_close_displacement": absolute_24h.is_finite() and absolute_24h >= Decimal(str(gates["combined_median_24h_absolute_close_displacement_minimum"])),
        "authority_and_order_mismatches": mismatch_count <= int(gates["qualification_quarantine_lifecycle_or_order_mismatches_maximum"]),
    }
    return metrics, checks


def wrap(manifest_type: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": manifest_type, "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(*, repository: Path, raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    if qualification.get("qualification_content_hash") != "4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c":
        raise ObservationFailure("data qualification binding changed")
    is_start_ms = utc_ms(protocol["scope"]["is_start"])
    is_end_ms = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    mask_document = load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in mask_document["content"]}
    hourly = build_hourly_closes(raw_root=raw_root, membership=membership, masked_slots=masked, is_start_ms=is_start_ms, is_end_ms=is_end_ms, order=order)
    events, scan_accounting = select_events(
        hourly_closes=hourly, membership=membership, is_start_ms=is_start_ms, is_end_ms=is_end_ms,
        protocol_hash=protocol["content_hash"], qualification_hash=qualification["qualification_content_hash"],
    )
    episodes = cluster_events(events)
    captured, pre_censored = capture_path_rows(
        raw_root=raw_root, episodes=episodes, masked_slots=masked,
        is_start_ms=is_start_ms, is_end_ms=is_end_ms, order=order,
    )
    paths, censor_counts = observe_paths(episodes, captured, pre_censored)
    content = {
        "events": sorted(events, key=lambda item: (item["decision_time_ms"], item["symbol"])),
        "episodes": sorted(episodes, key=lambda item: (item["decision_time_ms"], item["symbol"])),
        "paths": sorted(paths, key=lambda item: (item["decision_time_ms"], item["symbol"])),
        "accounting": {
            **scan_accounting,
            "candidate_events": len(events),
            "independent_episodes": len(episodes),
            "complete_24h_episodes": len(paths),
            "right_censored_episodes": len(episodes) - len(paths),
            "right_censor_reasons": dict(sorted(censor_counts.items())),
            "oos_rows_decoded": 0,
            "formal_returns_computed": 0,
            "fills_positions_or_equity_rows": 0,
        },
    }
    manifests = {name: wrap(f"u04_{name}_manifest", content[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(*, repository: Path, raw_root: Path) -> dict[str, Any]:
    protocol = load_json(repository / "config/u04_cross_sectional_paper_protocol_v1.json")
    qualification = load_json(repository / "reports/m1/evidence/u04_cross_sectional_data_qualification_v1.json")
    orders = ("normal", "reverse", "deterministic_shuffled")
    runs = [run_order(repository=repository, raw_root=raw_root, protocol=protocol, qualification=qualification, order=order) for order in orders]
    order_mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch_count=order_mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {
        "schema_version": 1,
        "run_id": "U04-05-SEALED-IS-PAPER-OBSERVATION-V1",
        "status": status,
        "protocol_content_hash": protocol["content_hash"],
        "qualification_content_hash": qualification["qualification_content_hash"],
        "is_start": protocol["scope"]["is_start"],
        "is_end_exclusive": protocol["scope"]["is_end_exclusive"],
        "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs],
        "metrics": metrics,
        "paper_gate_checks": checks,
        "oos_opened": False,
        "oos_rows_decoded": 0,
        "formal_returns_computed": False,
        "fills_positions_or_equity_generated": False,
        "parameters_changed_after_result": False,
        "second_run_executed": False,
        "network_accessed": False,
        "authorizations": {
            "paper_result_independent_review": status == "pass",
            "lifecycle_or_fixed_rule_work": False,
            "strategy": False, "backtesting": False, "oos": False,
            "api_trading": False, "execution_live": False, "m2": False,
        },
    }
    summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render_report(result: Mapping[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    lines = [
        "# U-04 Sealed-IS Paper Observation", "",
        f"- Status: `{summary['status']}`",
        f"- Run hash: `{summary['run_content_hash']}`",
        f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`", "",
        "## Frozen Paper Gates", "",
    ]
    lines.extend(f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items())
    lines.extend([
        "", "## Metrics", "",
        f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`",
        f"- Years with at least ten complete episodes: `{metrics['years_with_ten_complete_episodes']}`",
        f"- Maximum year / symbol share: `{metrics['maximum_single_year_episode_share']} / {metrics['maximum_single_symbol_episode_share']}`",
        f"- Distinct event symbols: `{metrics['distinct_event_symbols']}`",
        f"- Median 24h relative recovery: `{metrics['median_24h_relative_recovery']}`",
        f"- Median 24h absolute close displacement: `{metrics['median_24h_absolute_close_displacement']}`",
        "", "## Isolation", "",
        "- OOS opened / rows decoded: `false / 0`",
        "- Formal returns, fills, positions or equity generated: `false`",
        "- Parameters changed or second run executed: `false / false`", "",
        "A failed Gate closes the candidate without tuning. A pass authorizes only an independent paper-result review; it does not authorize fixed rules, strategy code, backtesting, OOS, trading or M2.", "",
    ])
    return "\n".join(lines)


def write_result(result: Mapping[str, Any], evidence_dir: Path, report: Path) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    (evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    report.write_text(render_report(result), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m1/evidence/u04_cross_sectional_paper_observation")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U04_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    result = execute(repository=ROOT, raw_root=args.raw_root)
    write_result(result, args.evidence_dir, args.report)
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0 if result["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
