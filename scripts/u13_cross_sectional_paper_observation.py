#!/usr/bin/env python3
"""Execute the one authorized U-13 sealed-IS Paper observation."""
from __future__ import annotations

import argparse
import csv
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

from scripts.u04_cross_sectional_data_qualification import QualificationFailure, identity_hash, load_json, utc_ms
from scripts.u04_cross_sectional_paper_observation import EVIDENCE, FIVE_MINUTES_MS, ONE_DAY_MS, ONE_HOUR_MS, build_membership, decimal_text, median, month_for_ms
from scripts.u05_cross_sectional_data_qualification import git_json
from scripts.u12_cross_sectional_data_qualification import required_tasks

PROTOCOL_TARGET = "6ef1024033aa9a86ef3c8f07558ba966270625a7"
PROTOCOL_PATH = "config/u13_cross_sectional_paper_protocol_v1.json"
QUALIFICATION_HASH = "5c4a61efc177415b1bd0a03697f4a3028f9ab8bed908adc12100bc03e9b90590"
QUALIFICATION_PATH = ROOT / "reports/m1/evidence/u13_cross_sectional_data_qualification_v1.json"
EVIDENCE_DIR = ROOT / "reports/m1/evidence/u13_cross_sectional_paper_observation"
RUN_PATH = EVIDENCE_DIR / "run_manifest.json"
ORDERS = ("normal", "reverse", "deterministic_shuffled")
HORIZONS = (1, 2, 4, 8, 12, 24)


class ObservationFailure(ValueError):
    pass


def ordered(values: Iterable[tuple[str, str]], order: str) -> list[tuple[str, str]]:
    rows = sorted(values)
    if order == "reverse":
        rows.reverse()
    elif order == "deterministic_shuffled":
        random.Random(314159).shuffle(rows)
    elif order != "normal":
        raise ObservationFailure(f"unknown order: {order}")
    return rows


def read_rows(raw_root: Path, symbol: str, month: str, end_ms: int) -> Iterable[tuple[int, Decimal, Decimal, Decimal, Decimal]]:
    relative = Path(f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip")
    path = raw_root / relative
    if not path.is_file():
        return
    with zipfile.ZipFile(path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) != 1:
            raise ObservationFailure(f"archive member count changed: {relative.as_posix()}")
        previous: int | None = None
        with archive.open(members[0]) as handle:
            for raw_line in handle:
                first = raw_line.split(b",", 1)[0].strip()
                try:
                    opened = int(first)
                except ValueError:
                    if previous is None and first.lower() in {b"open_time", b"opentime"}:
                        continue
                    raise ObservationFailure(f"malformed open time: {symbol}:{month}")
                if opened >= end_ms:
                    break
                if opened % FIVE_MINUTES_MS or (previous is not None and opened <= previous):
                    raise ObservationFailure(f"invalid open-time order/grid: {symbol}:{month}:{opened}")
                previous = opened
                fields = next(csv.reader([raw_line.decode("utf-8").rstrip("\r\n")]))
                if len(fields) != 12:
                    raise ObservationFailure(f"5m schema changed: {symbol}:{month}")
                try:
                    opened_price, high, low, close = map(Decimal, (fields[1], fields[2], fields[3], fields[4]))
                except InvalidOperation as exc:
                    raise ObservationFailure(f"invalid OHLC: {symbol}:{month}:{opened}") from exc
                if min(opened_price, high, low, close) <= 0 or high < max(opened_price, close) or low > min(opened_price, close):
                    raise ObservationFailure(f"invalid OHLC bounds: {symbol}:{month}:{opened}")
                yield opened, opened_price, high, low, close


def build_hourly_returns(
    raw_root: Path,
    membership: Mapping[str, Sequence[str]],
    masked: set[tuple[str, int]],
    start: int,
    end: int,
    order: str,
) -> tuple[dict[int, dict[str, Decimal]], dict[int, Decimal], dict[str, int]]:
    counts: Counter[tuple[str, int]] = Counter()
    last_close: dict[tuple[str, int], Decimal] = {}
    tasks = required_tasks(membership, end)
    for month, symbol in ordered(tasks, order):
        for opened, _open, _high, _low, close in read_rows(raw_root, symbol, month, end):
            if opened < start - ONE_HOUR_MS or (symbol, opened) in masked:
                continue
            hour = (opened // ONE_HOUR_MS) * ONE_HOUR_MS
            counts[(symbol, hour)] += 1
            if opened == hour + ONE_HOUR_MS - FIVE_MINUTES_MS:
                last_close[(symbol, hour + ONE_HOUR_MS)] = close
    returns: dict[int, dict[str, Decimal]] = {}
    common: dict[int, Decimal] = {}
    accounting = {"hourly_intervals_considered": 0, "hourly_intervals_complete": 0, "hourly_intervals_ineligible": 0}
    with localcontext() as context:
        context.prec = 50
        boundary = start + ONE_HOUR_MS
        while boundary < end:
            accounting["hourly_intervals_considered"] += 1
            members = tuple(membership.get(month_for_ms(boundary - ONE_HOUR_MS), ()))
            row: dict[str, Decimal] = {}
            for symbol in members:
                current = last_close.get((symbol, boundary))
                prior = last_close.get((symbol, boundary - ONE_HOUR_MS))
                if counts.get((symbol, boundary - ONE_HOUR_MS)) != 12 or current is None or prior is None:
                    break
                row[symbol] = (current / prior).ln()
            if len(members) >= 10 and len(row) == len(members):
                returns[boundary] = row
                common[boundary] = median(list(row.values()))
                accounting["hourly_intervals_complete"] += 1
            else:
                accounting["hourly_intervals_ineligible"] += 1
            boundary += ONE_HOUR_MS
    return returns, common, accounting


def select_events(
    hourly_returns: Mapping[int, Mapping[str, Decimal]],
    common: Mapping[int, Decimal],
    membership: Mapping[str, Sequence[str]],
    start: int,
    end: int,
    protocol_hash: str,
    qualification_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    events: list[dict[str, Any]] = []
    accounting = {"decision_hours_considered": 0, "current_shock_failed": 0, "history_ineligible": 0, "candidate_gate_failed": 0, "simultaneous_candidates_discarded": 0}
    decision = start + 2160 * ONE_HOUR_MS
    with localcontext() as context:
        context.prec = 50
        while decision + 24 * ONE_HOUR_MS <= end:
            accounting["decision_hours_considered"] += 1
            current = tuple(membership.get(month_for_ms(decision - 1), ()))
            row_now = hourly_returns.get(decision)
            if row_now is None or len(row_now) != len(current) or common.get(decision, Decimal("-Infinity")) < Decimal("0.0060") or sum(value > 0 for value in row_now.values()) * 10 < len(current) * 7:
                accounting["current_shock_failed"] += 1; decision += ONE_HOUR_MS; continue
            candidates: list[str] = []
            stats: dict[str, dict[str, Any]] = {}
            history = range(decision - 2160 * ONE_HOUR_MS, decision - 4 * ONE_HOUR_MS + 1, ONE_HOUR_MS)
            for symbol in current:
                full: list[tuple[Decimal, Decimal]] = []; first: list[tuple[Decimal, Decimal]] = []; second: list[tuple[Decimal, Decimal]] = []
                for historical in history:
                    hist = hourly_returns.get(historical); hist_members = tuple(membership.get(month_for_ms(historical - 1), ()))
                    if hist is None or symbol not in hist or common.get(historical, Decimal("-Infinity")) < Decimal("0.0020") or sum(value > 0 for value in hist.values()) * 5 < len(hist) * 3:
                        continue
                    residual = hist[symbol] - common[historical]
                    if hist[symbol] < 0 or residual > Decimal("-0.0010"):
                        continue
                    followups = [hourly_returns.get(historical + offset * ONE_HOUR_MS) for offset in range(1, 5)]
                    if any(value is None or tuple(membership.get(month_for_ms(historical + offset * ONE_HOUR_MS - 1), ())) != hist_members for offset, value in enumerate(followups, 1)):
                        continue
                    peers = [peer for peer in hist_members if peer != symbol]
                    candidate_response = sum((value[symbol] for value in followups if value is not None), Decimal(0))
                    peer_response = median([sum((value[peer] for value in followups if value is not None), Decimal(0)) for peer in peers])
                    item = (residual, candidate_response - peer_response); full.append(item)
                    (first if historical < decision - 1080 * ONE_HOUR_MS else second).append(item)
                if len(full) < 30 or len(first) < 12 or len(second) < 12:
                    continue
                lag, lag_first, lag_second = median([x[1] for x in full]), median([x[1] for x in first]), median([x[1] for x in second])
                residual_median = median([x[0] for x in full])
                if lag < Decimal("0.0040") or lag_first < Decimal("0.0020") or lag_second < Decimal("0.0020") or residual_median + lag < 0:
                    continue
                current_residual = row_now[symbol] - common[decision]
                if row_now[symbol] >= 0 and current_residual <= Decimal("-0.0040"):
                    stats[symbol] = {"full_lag": lag, "first_lag": lag_first, "second_lag": lag_second, "residual_median": residual_median, "count": len(full), "first_count": len(first), "second_count": len(second), "current_residual": current_residual}
                    candidates.append(symbol)
            if not candidates:
                accounting["candidate_gate_failed"] += 1
                decision += ONE_HOUR_MS
                continue
            candidates.sort(key=lambda symbol: (-stats[symbol]["full_lag"], -min(stats[symbol]["first_lag"], stats[symbol]["second_lag"]), -stats[symbol]["count"], stats[symbol]["current_residual"], symbol))
            accounting["simultaneous_candidates_discarded"] += len(candidates) - 1
            symbol = candidates[0]
            row = stats[symbol]
            core = {
                "decision_time_ms": decision,
                "reference_open_time_ms": decision,
                "symbol": symbol,
                "active_members": list(current),
                "active_member_count": len(current),
                "full_median_lagged_relative_response": decimal_text(row["full_lag"]),
                "first_half_median_lagged_relative_response": decimal_text(row["first_lag"]),
                "second_half_median_lagged_relative_response": decimal_text(row["second_lag"]),
                "full_median_immediate_residual": decimal_text(row["residual_median"]),
                "current_residual": decimal_text(row["current_residual"]),
                "completed_occurrences_full": row["count"],
                "completed_occurrences_first_half": row["first_count"],
                "completed_occurrences_second_half": row["second_count"],
            }
            core["event_id"] = identity_hash({"protocol": protocol_hash, "qualification": qualification_hash, **core})
            events.append(core)
            decision += ONE_HOUR_MS
    return events, accounting


def cluster_events(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    previous: int | None = None
    number = -1
    for event in sorted(events, key=lambda row: (int(row["decision_time_ms"]), str(row["symbol"]))):
        decision = int(event["decision_time_ms"])
        if previous is None or decision - previous > 24 * ONE_HOUR_MS:
            number += 1
            row = dict(event)
            row["episode_id"] = identity_hash({"episode_number": number, "first_event_id": event["event_id"]})
            output.append(row)
        previous = decision
    return output


def capture_path_bars(raw_root: Path, episodes: Sequence[Mapping[str, Any]], end: int, order: str) -> dict[str, dict[int, tuple[Decimal, Decimal, Decimal, Decimal]]]:
    needed: dict[str, set[int]] = defaultdict(set)
    for event in episodes:
        ref = int(event["reference_open_time_ms"])
        for symbol in event["active_members"]:
            needed[str(symbol)].update(range(ref, ref + 24 * ONE_HOUR_MS, FIVE_MINUTES_MS))
    tasks: set[tuple[str, str]] = set()
    for symbol, opens in needed.items():
        tasks.update((month_for_ms(opened), symbol) for opened in opens)
    bars: dict[str, dict[int, tuple[Decimal, Decimal, Decimal, Decimal]]] = defaultdict(dict)
    for month, symbol in ordered(tasks, order):
        wanted = needed[symbol]
        for opened, opened_price, high, low, close in read_rows(raw_root, symbol, month, end):
            if opened in wanted:
                bars[symbol][opened] = (opened_price, high, low, close)
    return bars


def observe_paths(
    raw_root: Path,
    episodes: Sequence[Mapping[str, Any]],
    membership: Mapping[str, Sequence[str]],
    masked: set[tuple[str, int]],
    end: int,
    order: str,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    bars = capture_path_bars(raw_root, episodes, end, order)
    paths: list[dict[str, Any]] = []
    censored: Counter[str] = Counter()
    with localcontext() as context:
        context.prec = 50
        for event in episodes:
            ref = int(event["reference_open_time_ms"])
            active = tuple(event["active_members"])
            if ref + 24 * ONE_HOUR_MS > end:
                censored["is_boundary"] += 1
                continue
            if tuple(membership.get(month_for_ms(ref + 24 * ONE_HOUR_MS - 1), ())) != active:
                censored["membership_or_lifecycle_intersection"] += 1
                continue
            required = range(ref, ref + 24 * ONE_HOUR_MS, FIVE_MINUTES_MS)
            if any((symbol, opened) in masked or opened not in bars.get(symbol, {}) for symbol in active for opened in required):
                censored["missing_or_quarantined_5m_path"] += 1
                continue
            candidate = str(event["symbol"])
            peers = [symbol for symbol in active if symbol != candidate]
            candidate_ref = bars[candidate][ref][0]
            peer_ref = {symbol: bars[symbol][ref][0] for symbol in peers}
            absolute: dict[str, str] = {}
            peer_displacement: dict[str, str] = {}
            relative: dict[str, str] = {}
            for horizon in HORIZONS:
                opened = ref + horizon * ONE_HOUR_MS - FIVE_MINUTES_MS
                candidate_value = bars[candidate][opened][3] / candidate_ref - Decimal(1)
                peer_value = median([bars[symbol][opened][3] / peer_ref[symbol] - Decimal(1) for symbol in peers])
                absolute[str(horizon)] = decimal_text(candidate_value)
                peer_displacement[str(horizon)] = decimal_text(peer_value)
                relative[str(horizon)] = decimal_text(candidate_value - peer_value)
            highs = [bars[candidate][opened][1] / candidate_ref - Decimal(1) for opened in required]
            lows = [bars[candidate][opened][2] / candidate_ref - Decimal(1) for opened in required]
            recovery: int | None = None
            for index, opened in enumerate(required, start=1):
                candidate_value = bars[candidate][opened][3] / candidate_ref - Decimal(1)
                peer_value = median([bars[symbol][opened][3] / peer_ref[symbol] - Decimal(1) for symbol in peers])
                if candidate_value - peer_value >= Decimal("0.0030"):
                    recovery = index * 5
                    break
            row = dict(event)
            row.update({"candidate_absolute_close_displacement": absolute, "peer_median_close_displacement": peer_displacement, "relative_lagged_diffusion": relative, "candidate_mfe_through_24h": decimal_text(max(highs)), "candidate_mae_through_24h": decimal_text(min(lows)), "first_relative_recovery_to_base_cost_minutes": recovery})
            paths.append(row)
    return paths, censored


def evaluate_gates(paths: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any], mismatch: int) -> tuple[dict[str, Any], dict[str, bool]]:
    gates = protocol["paper_gates"]
    count = len(paths)
    years = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).year for row in paths)
    symbols = Counter(str(row["symbol"]) for row in paths)
    months = Counter(datetime.fromtimestamp(int(row["decision_time_ms"]) / 1000, tz=timezone.utc).strftime("%Y-%m") for row in paths)
    relative = [Decimal(str(row["relative_lagged_diffusion"]["24"])) for row in paths]
    absolute = [Decimal(str(row["candidate_absolute_close_displacement"]["24"])) for row in paths]
    relative_median = median(relative) if paths else Decimal("NaN")
    absolute_median = median(absolute) if paths else Decimal("NaN")
    positive = Decimal(sum(value > 0 for value in relative)) / Decimal(count) if count else Decimal("NaN")
    year_share = Decimal(max(years.values(), default=count or 1)) / Decimal(count or 1)
    symbol_share = Decimal(max(symbols.values(), default=count or 1)) / Decimal(count or 1)
    full = count * 2373 // 1715
    oos = count * 658 // 1715
    metrics = {"complete_is_independent_episodes": count, "projected_full_independent_episodes": full, "projected_sealed_oos_independent_episodes": oos, "years_with_twelve_complete_episodes": sum(value >= 12 for value in years.values()), "episodes_by_year": {str(key): value for key, value in sorted(years.items())}, "maximum_single_year_episode_share": decimal_text(year_share), "episodes_by_symbol": dict(sorted(symbols.items())), "maximum_single_symbol_episode_share": decimal_text(symbol_share), "distinct_event_symbols": len(symbols), "distinct_event_months": len(months), "median_24h_relative_lagged_diffusion": decimal_text(relative_median) if relative_median.is_finite() else None, "median_24h_candidate_absolute_close_displacement": decimal_text(absolute_median) if absolute_median.is_finite() else None, "fraction_complete_episodes_with_positive_24h_relative_lagged_diffusion": decimal_text(positive) if positive.is_finite() else None, "qualification_preflight_quarantine_lifecycle_or_order_mismatches": mismatch}
    checks = {"complete_is_independent_episodes": count >= gates["complete_is_independent_episodes_minimum"], "projected_full_independent_episodes": full >= gates["projected_full_independent_episodes_minimum"], "projected_sealed_oos_independent_episodes": oos >= gates["projected_sealed_oos_independent_episodes_minimum"], "years_with_twelve_complete_episodes": metrics["years_with_twelve_complete_episodes"] >= gates["minimum_years_with_twelve_complete_episodes"], "maximum_single_year_episode_share": year_share <= Decimal(gates["maximum_single_year_episode_share"]), "maximum_single_symbol_episode_share": symbol_share <= Decimal(gates["maximum_single_symbol_episode_share"]), "distinct_event_symbols": len(symbols) >= gates["minimum_distinct_event_symbols"], "distinct_event_months": len(months) >= gates["minimum_distinct_event_months"], "median_24h_relative_lagged_diffusion": relative_median.is_finite() and relative_median >= Decimal(gates["combined_median_24h_relative_lagged_diffusion_minimum"]), "median_24h_candidate_absolute_close_displacement": absolute_median.is_finite() and absolute_median >= Decimal(gates["combined_median_24h_candidate_absolute_close_displacement_minimum"]), "fraction_positive_24h_relative_lagged_diffusion": positive.is_finite() and positive >= Decimal(gates["fraction_complete_episodes_with_positive_24h_relative_lagged_diffusion_minimum"]), "authority_and_order_mismatches": mismatch <= gates["qualification_preflight_quarantine_lifecycle_or_order_mismatches_maximum"]}
    return metrics, checks


def wrap(name: str, content: Any) -> dict[str, Any]:
    document = {"schema_version": 1, "manifest_type": f"u13_{name}_manifest", "content": content}
    document["content_hash"] = identity_hash(document)
    return document


def run_order(raw_root: Path, protocol: Mapping[str, Any], qualification: Mapping[str, Any], order: str) -> dict[str, Any]:
    start = utc_ms(protocol["scope"]["is_start"])
    end = utc_ms(protocol["scope"]["is_end_exclusive"])
    membership = build_membership(load_json(EVIDENCE / "membership_manifest.json"))
    masked = {(str(row["symbol"]), int(row["open_time_ms"])) for row in load_json(EVIDENCE / "invalid_interval_slot_mask_manifest.json")["content"]}
    returns, common, hourly_accounting = build_hourly_returns(raw_root, membership, masked, start, end, order)
    events, event_accounting = select_events(returns, common, membership, start, end, protocol["content_hash"], qualification["qualification_content_hash"])
    episodes = cluster_events(events)
    paths, censored = observe_paths(raw_root, episodes, membership, masked, end, order)
    accounting = {**hourly_accounting, **event_accounting, "common_component_hours": len(common), "candidate_events": len(events), "independent_episodes": len(episodes), "complete_24h_episodes": len(paths), "right_censored_episodes": len(episodes) - len(paths), "right_censor_reasons": dict(sorted(censored.items())), "oos_rows_decoded": 0, "formal_returns_computed": 0, "fills_positions_or_equity_rows": 0}
    contents = {"events": events, "episodes": episodes, "paths": paths, "accounting": accounting}
    manifests = {name: wrap(name, contents[name]) for name in ("events", "episodes", "paths", "accounting")}
    hashes = {name: manifests[name]["content_hash"] for name in sorted(manifests)}
    return {"order": order, "manifests": manifests, "manifest_hashes": hashes, "content_identity_hash": identity_hash(hashes)}


def execute(raw_root: Path) -> dict[str, Any]:
    protocol = git_json(PROTOCOL_TARGET, PROTOCOL_PATH)
    qualification = load_json(QUALIFICATION_PATH)
    if protocol.get("content_hash") != "1cf6dade6e75900278ba5aeee30018d3f0ff93d83d982e212d58033800993288" or qualification.get("qualification_content_hash") != QUALIFICATION_HASH:
        raise ObservationFailure("protocol or qualification drift")
    runs = [run_order(raw_root, protocol, qualification, order) for order in ORDERS]
    mismatch = 0 if len({run["content_identity_hash"] for run in runs}) == 1 else 1
    primary = runs[0]
    metrics, checks = evaluate_gates(primary["manifests"]["paths"]["content"], protocol, mismatch)
    status = "pass" if all(checks.values()) else "failed_feasibility"
    summary = {"schema_version": 1, "run_id": "U13-06-SEALED-IS-PAPER-OBSERVATION-V1", "status": status, "protocol_target_commit": PROTOCOL_TARGET, "protocol_content_hash": protocol["content_hash"], "qualification_content_hash": qualification["qualification_content_hash"], "is_start": protocol["scope"]["is_start"], "is_end_exclusive": protocol["scope"]["is_end_exclusive"], "orders": [{"order": run["order"], "content_identity_hash": run["content_identity_hash"], "manifest_hashes": run["manifest_hashes"]} for run in runs], "metrics": metrics, "paper_gate_checks": checks, "oos_opened": False, "oos_rows_decoded": 0, "formal_returns_computed": False, "fills_positions_or_equity_generated": False, "parameters_changed_after_result": False, "second_run_executed": False, "network_accessed": False, "authorizations": {"paper_result_independent_review": status == "pass", "lifecycle_or_fixed_rule_work": False, "strategy": False, "backtesting": False, "oos": False, "api_trading": False, "execution_live": False, "m2": False}}
    summary["run_content_hash"] = identity_hash(summary)
    return {"summary": summary, "manifests": primary["manifests"]}


def render(result: Mapping[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    failed = [key for key, value in summary["paper_gate_checks"].items() if not value]
    return "\n".join(["# U-13 Sealed-IS Paper Observation", "", f"- Status: `{summary['status']}`", f"- Run hash: `{summary['run_content_hash']}`", f"- Complete independent episodes: `{metrics['complete_is_independent_episodes']}`", "", "## Frozen Paper Gates", "", *[f"- {key}: `{str(value).lower()}`" for key, value in summary["paper_gate_checks"].items()], "", "## Metrics", "", f"- Projected full / sealed OOS episodes: `{metrics['projected_full_independent_episodes']} / {metrics['projected_sealed_oos_independent_episodes']}`", f"- Median 24h relative lagged diffusion: `{metrics['median_24h_relative_lagged_diffusion']}`", f"- Median 24h candidate absolute displacement: `{metrics['median_24h_candidate_absolute_close_displacement']}`", f"- Positive relative fraction: `{metrics['fraction_complete_episodes_with_positive_24h_relative_lagged_diffusion']}`", f"- Failed Gates: `{', '.join(failed) if failed else 'none'}`", "", "## Isolation", "", "- OOS opened / rows decoded: `false / 0`", "- Formal returns, fills, positions or equity generated: `false`", "- Parameters changed or second run executed: `false / false`", "", "A failed Gate closes U-13 without tuning. A pass authorizes only independent Paper-result review.", ""])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m1/U13_CROSS_SECTIONAL_PAPER_OBSERVATION.md")
    args = parser.parse_args()
    if (args.evidence_dir / "run_manifest.json").exists():
        print("U-13 result already exists; a second result-bearing run is prohibited.", file=sys.stderr)
        return 2
    result = execute(args.raw_root)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, document in result["manifests"].items():
        (args.evidence_dir / f"{name}.json").write_text(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
    (args.evidence_dir / "run_manifest.json").write_text(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")) + "\n")
    args.report.write_text(render(result))
    print(json.dumps(result["summary"], sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
